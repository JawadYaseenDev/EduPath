"""Capture showcase screenshots of the EduRecommend student app and admin panel.

Needs (all local):
  * backend on http://localhost:8000 with fresh demo data (delete backend/dev.db first)
  * student web build served on http://localhost:5173 and admin build on :5174,
    both built with --dart-define=ENABLE_SEMANTICS=true
  * Google Chrome installed

Run from the backend folder (uses its Python packages):
  uv run python ../tools/showcase/capture.py

Screenshots go to showcase/screenshots/.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import httpx
from websockets.sync.client import connect

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "showcase" / "screenshots"
API = "http://localhost:8000"
STUDENT_URL = "http://localhost:5173"
ADMIN_URL = "http://localhost:5174"

# Local demo account created only on this machine's demo database.
STUDENT_EMAIL = "ayesha.showcase@example.com"
STUDENT_PASSWORD = "Showcase-Demo-2027"

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]


def staff_password() -> str:
    for line in (ROOT / "backend" / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("UNIRAH_DEV_STAFF_PASSWORD="):
            return line.split("=", 1)[1].strip()
    sys.exit("backend/.env has no UNIRAH_DEV_STAFF_PASSWORD")


# ======================================================================= demo data


def prepare_data() -> dict:
    c = httpx.Client(base_url=API, timeout=30)
    r = c.post("/v1/auth/register", json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD,
                                          "full_name": "Ayesha Khan", "accept_terms": True})
    if r.status_code == 409:
        r = c.post("/v1/auth/login", json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD})
    r.raise_for_status()
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    ref = c.get("/v1/reference").json()
    lahore = next(x["id"] for x in ref["cities"] if x["name"] == "Lahore")
    board = next(x["id"] for x in ref["boards"] if x["short_name"] == "BISE Lahore")
    c.put("/v1/profile", headers=h, json={"full_name": "Ayesha Khan", "gender": "female",
                                          "current_city_id": lahore, "domicile_region_code": "PB"}).raise_for_status()
    c.put("/v1/profile/qualifications", headers=h, json={
        "type_code": "MATRIC", "group_code": "MATRIC_SCIENCE_COMP", "board_id": board,
        "passing_year": 2025, "obtained_marks": 1010, "total_marks": 1200,
        "subjects": [{"code": s} for s in ["MATH", "PHY", "CHEM", "CS", "ENG"]]}).raise_for_status()
    c.put("/v1/profile/qualifications", headers=h, json={
        "type_code": "INTERMEDIATE", "group_code": "ICS", "board_id": board, "passing_year": 2027,
        "result_status": "part1_only", "part1_obtained": 430, "part1_total": 550,
        "subjects": [{"code": s} for s in ["MATH", "CS", "PHY", "ENG"]]}).raise_for_status()
    prefs = {"fields": ["COMPUTING", "BUSINESS"], "regions": ["PB", "ICT", "KP"],
             "max_fee_per_semester": 60000, "hostel_need": "needed"}
    c.put("/v1/profile/preferences", headers=h, json=prefs).raise_for_status()
    c.post("/v1/recommendations/run", headers=h).raise_for_status()

    cs = c.get("/v1/programmes", params={"q": "computer science"}).json()["results"]
    uet_cs = next(x for x in cs if x["university_short_name"] == "Demo UET")
    wu_cs = next(x for x in cs if x["university_short_name"] == "Demo WU")
    for o in (uet_cs, wu_cs):
        c.post("/v1/shortlist", headers=h, json={"offering_id": o["offering_id"]})

    # A pending change for the admin review screen (proposed by the super admin).
    pw = staff_password()
    at = c.post("/v1/auth/login", json={"email": "admin@example.com", "password": pw}).json()["access_token"]
    ah = {"Authorization": f"Bearer {at}"}
    detail = c.get(f"/v1/admin/offerings/{uet_cs['offering_id']}", headers=ah).json()
    fees = detail["fees"]
    for f in fees:
        if f["component"] == "tuition":
            f["amount_pkr"] = 34000
    if not detail["pending_changes"]:
        c.put(f"/v1/admin/offerings/{uet_cs['offering_id']}/fees", headers=ah, json=fees).raise_for_status()
    return {"student_headers": h, "prefs": prefs, "uet_cs": uet_cs, "client": c}


# ======================================================================= browser


class Browser:
    def __init__(self):
        chrome = next((p for p in CHROME_PATHS if Path(p).exists()), None)
        if chrome is None:
            sys.exit("Google Chrome not found")
        self.profile = tempfile.mkdtemp(prefix="edurec-shots-")
        self.proc = subprocess.Popen([chrome, "--headless=new", "--remote-debugging-port=9333",
                                      f"--user-data-dir={self.profile}", "--no-first-run",
                                      "--hide-scrollbars", "--force-color-profile=srgb",
                                      "--lang=en-GB", "about:blank"])
        for _ in range(50):
            try:
                pages = json.load(urllib.request.urlopen("http://127.0.0.1:9333/json/list"))
                page = next(p for p in pages if p["type"] == "page")
                break
            except Exception:
                time.sleep(0.2)
        else:
            sys.exit("Chrome did not start")
        self.ws = connect(page["webSocketDebuggerUrl"], max_size=None)
        self.n = 0
        self.send("Page.enable")
        self.send("Runtime.enable")
        # Light mode reads and prints better in documents.
        self.send("Emulation.setEmulatedMedia",
                  features=[{"name": "prefers-color-scheme", "value": "light"}])
        self.width = self.height = 0

    def send(self, method, **params):
        self.n += 1
        my = self.n
        self.ws.send(json.dumps({"id": my, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == my:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    def js(self, expr):
        r = self.send("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        return r.get("result", {}).get("value")

    def viewport(self, width, height, scale, mobile):
        self.width, self.height = width, height
        self.send("Emulation.setDeviceMetricsOverride", width=width, height=height,
                  deviceScaleFactor=scale, mobile=mobile)

    def goto(self, url, wait_for=None):
        self.send("Page.navigate", url=url)
        time.sleep(1.5)
        if wait_for:
            try:
                self.wait_text(wait_for)
            except TimeoutError:
                # Flutter sometimes misses its first frame in a background page: reload once.
                self.send("Page.reload", ignoreCache=True)
                time.sleep(2)
                self.wait_text(wait_for)
        self.settle()

    def settle(self, seconds=1.2):
        time.sleep(seconds)

    def find(self, text, exact=False):
        expr = """
        (() => {
          const t = %s, exact = %s;
          const els = [...document.querySelectorAll('flt-semantics, [role], input, textarea, button')];
          let best = null;
          for (const e of els) {
            const label = ((e.getAttribute('aria-label') || '') + ' ' + (e.textContent || '')).trim();
            const ok = exact ? (e.getAttribute('aria-label') || '').trim() === t || (e.textContent || '').trim() === t
                             : label.includes(t);
            if (!ok) continue;
            const r = e.getBoundingClientRect();
            if (r.width < 2 || r.height < 2) continue;
            const area = r.width * r.height;
            if (!best || area < best.area) best = {x: r.x + r.width / 2, y: r.y + r.height / 2, area};
          }
          return best;
        })()""" % (json.dumps(text), "true" if exact else "false")
        return self.js(expr)

    def wait_text(self, text, timeout=25):
        end = time.time() + timeout
        while time.time() < end:
            if self.find(text):
                return
            time.sleep(0.4)
        self.shot("debug-timeout")
        print("  url:", self.js("location.href"))
        raise TimeoutError(f"Text not found: {text}")

    def click_xy(self, x, y):
        for kind in ("mousePressed", "mouseReleased"):
            self.send("Input.dispatchMouseEvent", type=kind, x=x, y=y, button="left", clickCount=1)
        time.sleep(0.6)

    def click(self, text, exact=False):
        self.wait_text(text)
        el = self.find(text, exact)
        if el is None:
            raise RuntimeError(f"Cannot click {text}")
        if el["y"] > self.height - 10 or el["y"] < 0:
            self.scroll_to(text, exact)
            el = self.find(text, exact)
        self.click_xy(el["x"], el["y"])

    def scroll_to(self, text, exact=False):
        for _ in range(40):
            el = self.find(text, exact)
            if el and 60 < el["y"] < self.height - 60:
                return
            delta = 300 if (el is None or el["y"] >= self.height - 60) else -300
            self.send("Input.dispatchMouseEvent", type="mouseWheel", x=self.width / 2,
                      y=self.height / 2, deltaX=0, deltaY=delta)
            time.sleep(0.25)

    def type_into(self, label, text):
        self.click(label)
        self.send("Input.insertText", text=text)
        time.sleep(0.3)

    def shot(self, name):
        data = self.send("Page.captureScreenshot", format="png")["data"]
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"{name}.png").write_bytes(base64.b64decode(data))
        print("  saved", name)

    def close(self):
        try:
            self.send("Browser.close")
        except Exception:
            pass
        self.proc.wait(timeout=10)


# ======================================================================= screens


def student_screens(b: Browser, d: dict):
    print("Student app")
    phone = (390, 844, 3, True)
    b.viewport(*phone)
    b.goto(f"{STUDENT_URL}/#/welcome", wait_for="Create account")
    b.shot("01-student-welcome")

    b.goto(f"{STUDENT_URL}/#/login", wait_for="Email address")
    b.type_into("Email address", STUDENT_EMAIL)
    b.type_into("Password", STUDENT_PASSWORD)
    b.settle(0.5)
    b.shot("02-student-login")
    b.click("Log in", exact=True)
    b.wait_text("Your results")
    b.settle(2)
    b.shot("03-student-home-dashboard")

    b.viewport(390, 1500, 3, True)
    b.goto(f"{STUDENT_URL}/#/edit/qualification/HSSC", wait_for="Result status")
    b.settle(1.5)
    b.shot("04-student-profile-intermediate-marks")
    b.goto(f"{STUDENT_URL}/#/edit/preferences", wait_for="University type")
    b.shot("05-student-preferences")

    b.viewport(*phone)
    b.goto(f"{STUDENT_URL}/#/results", wait_for="Eligible (")
    b.settle(1.5)
    b.shot("06-student-results-eligible")
    b.click("Potentially (")
    b.settle(1.5)
    b.shot("07-student-results-potentially-eligible")

    b.viewport(390, 2300, 3, True)
    b.goto(f"{STUDENT_URL}/#/programme/{d['uet_cs']['offering_id']}", wait_for="Your eligibility")
    b.settle(2)
    b.shot("08-student-programme-why-eligible")

    b.viewport(*phone)
    b.goto(f"{STUDENT_URL}/#/explore", wait_for="programmes")
    b.type_into("Search programme", "computer")
    b.settle(2.5)
    b.shot("09-student-explore-search")

    b.viewport(390, 1600, 3, True)
    b.goto(f"{STUDENT_URL}/#/university/{d['uet_cs']['university_id']}", wait_for="Campuses")
    b.settle(1.5)
    b.shot("10-student-university-page")

    b.viewport(*phone)
    b.goto(f"{STUDENT_URL}/#/shortlist", wait_for="Select 2 or 3 to compare")
    b.settle(1.5)
    b.shot("11-student-shortlist")
    boxes = b.js("""[...document.querySelectorAll('[role="checkbox"], input[type="checkbox"]')]
                    .map(e => { const r = e.getBoundingClientRect(); return {x: r.x + r.width/2, y: r.y + r.height/2}; })
                    .filter(p => p.y > 0)""") or []
    for p in boxes[:2]:
        b.click_xy(p["x"], p["y"])
    b.click("Compare 2")
    b.wait_text("First year total")
    b.settle(1.5)
    b.shot("12-student-compare")

    b.goto(f"{STUDENT_URL}/#/profile", wait_for="Your details")
    b.settle(1.5)
    b.shot("13-student-profile")

    # No-match example: only Engineering, which an ICS student cannot join.
    c, h = d["client"], d["student_headers"]
    c.put("/v1/profile/preferences", headers=h, json={**d["prefs"], "fields": ["ENGINEERING"]}).raise_for_status()
    c.post("/v1/recommendations/run", headers=h).raise_for_status()
    b.viewport(390, 1000, 3, True)
    b.goto(f"{STUDENT_URL}/?r=2#/results", wait_for="You may consider")
    b.settle(2)
    b.shot("14-student-no-match-suggestions")
    # Restore the normal preferences.
    c.put("/v1/profile/preferences", headers=h, json=d["prefs"]).raise_for_status()
    c.post("/v1/recommendations/run", headers=h).raise_for_status()


def admin_screens(b: Browser, d: dict):
    print("Admin panel")
    desk = (1440, 900, 2, False)
    b.viewport(*desk)
    b.goto(f"{ADMIN_URL}/#/login", wait_for="Sign in")
    b.type_into("Email", "admin@example.com")
    b.type_into("Password", staff_password())
    b.settle(0.5)
    b.shot("15-admin-login")
    b.click("Sign in", exact=True)
    b.wait_text("Records by status")
    b.settle(1.5)
    b.shot("16-admin-dashboard")

    b.goto(f"{ADMIN_URL}/#/universities", wait_for="Add university")
    b.settle(1.5)
    b.shot("17-admin-universities")

    b.viewport(1440, 1500, 2, False)
    b.goto(f"{ADMIN_URL}/#/universities/{d['uet_cs']['university_id']}", wait_for="Campuses")
    b.settle(1.5)
    b.shot("18-admin-university-editor")

    b.viewport(1440, 2600, 2, False)
    b.goto(f"{ADMIN_URL}/#/offerings/{d['uet_cs']['offering_id']}", wait_for="Test with sample students")
    b.settle(1.5)
    b.shot("19-admin-rule-builder")
    b.click("Test with sample students")
    b.wait_text("Results for sample students")
    b.viewport(1440, 3300, 2, False)
    b.settle(2)
    b.shot("20-admin-rule-test-sample-students")

    b.viewport(*desk)
    b.goto(f"{ADMIN_URL}/?r=2#/offerings/{d['uet_cs']['offering_id']}", wait_for="Eligibility rules")
    b.click("Fees", exact=True)
    b.settle(1.5)
    b.shot("21-admin-fees")

    b.viewport(1440, 1000, 2, False)
    b.goto(f"{ADMIN_URL}/#/review", wait_for="Changes to live data")
    b.settle(1.5)
    b.shot("22-admin-review-queue")

    b.viewport(1440, 1300, 2, False)
    b.goto(f"{ADMIN_URL}/#/settings", wait_for="Result display mode")
    b.settle(1.5)
    b.shot("23-admin-settings")


if __name__ == "__main__":
    data = prepare_data()
    browser = Browser()
    try:
        student_screens(browser, data)
        admin_screens(browser, data)
    finally:
        browser.close()
    print("Done:", OUT)
