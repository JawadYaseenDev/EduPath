"""Build the EduRecommend showcase PDF (plain language) from the screenshots.

Run from the backend folder after capture.py:
  uv run --with pillow python ../tools/showcase/make_report.py

Output: showcase/EduRecommend-Project-Overview.pdf
"""

from __future__ import annotations

import base64
import html
import shutil
import sys
from datetime import date
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from capture import ROOT, Browser  # noqa: E402

SHOW = ROOT / "showcase"
SHOTS = SHOW / "screenshots"


# ----------------------------------------------------------------- tidy screenshots


def trim_bottom(path: Path, skip_left: int = 0, margin: int = 60) -> None:
    """Remove empty space below the last content (tall full-page captures)."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    bg = im.getpixel((w - 5, h - 5))
    px = im.load()
    last = 0
    for y in range(h - 1, -1, -4):
        if any(sum(abs(a - b) for a, b in zip(px[x, y], bg)) > 30 for x in range(skip_left, w, 6)):
            last = y
            break
    new_h = min(h, last + margin)
    if new_h < h - 40:
        im.crop((0, 0, w, new_h)).save(path)


# ----------------------------------------------------------------- content

STUDENT = [
    ("01-student-welcome", "Welcome screen", "The first screen. It explains what the app does and reminds students that meeting the minimum requirements does not guarantee admission."),
    ("02-student-login", "Log in", "Students create an account or log in with email and password. Errors are shown in simple words."),
    ("03-student-home-dashboard", "Home (dashboard)", "After logging in the student sees a summary: how many programmes they are eligible for, potentially eligible for, and upcoming application deadlines."),
    ("04-student-profile-intermediate-marks", "Entering education and marks", "The student chooses their qualification (e.g. ICS), board, subjects and marks. Subjects are filled in automatically for their group. Students still waiting for their final result can enter Part-I marks. The percentage is calculated automatically."),
    ("05-student-preferences", "Preferences", "Provinces, budget per semester, type of university, hostel need, campus type and class timing. These only change the order and filtering of results, never the eligibility itself."),
    ("06-student-results-eligible", "Results: Eligible", "Programmes where the student meets every published requirement, sorted by how well they match the preferences."),
    ("07-student-results-potentially-eligible", "Results: Potentially eligible", "The student fails no known requirement, but something must still be confirmed, e.g. the final Intermediate result. The reason is shown on every card."),
    ("08-student-programme-why-eligible", "Programme details and “why” (top of the page)", "For each programme the app explains why the student is (or is not) eligible, rule by rule, and what to do next. It also shows the admission requirements, fee breakdown, entry test, dates, hostel and the official source."),
    ("09-student-explore-search", "Search and filters", "Anyone can search all programmes by name and filter by field, province, university type, fee and hostel."),
    ("10-student-university-page", "University page", "Campuses, hostels and all programmes of one university, with links to the official website and admissions page."),
    ("11-student-shortlist", "Shortlist", "Students save programmes they like, see their eligibility and deadlines, and open the official admission page."),
    ("12-student-compare", "Compare", "Two or three saved programmes side by side: status, fees, first-year cost, hostel, entry test, accreditation and deadline."),
    ("13-student-profile", "Profile and privacy", "Students can edit every part of their profile, download their data or delete their account."),
    ("14-student-no-match-suggestions", "When nothing matches", "If the student's background does not fit the chosen field (here: ICS student choosing only Engineering), the app explains the main reason and suggests other fields they do qualify for."),
]

ADMIN = [
    ("15-admin-login", "Admin login", "A separate website for staff only. Student accounts cannot open it."),
    ("16-admin-dashboard", "Admin dashboard", "Overview for the team: items waiting for review, student error reports, programmes still using last year's data, and counts of published records."),
    ("17-admin-universities", "Universities list", "All universities with their sector, number of campuses and programmes, status (draft / waiting for review / published) and last verified date."),
    ("18-admin-university-editor", "University editor", "Staff add and edit universities, campuses, hostels and programmes using simple forms. Every record needs an official source."),
    ("19-admin-rule-builder", "Eligibility rule builder (no coding, first rules shown)", "Admission rules from a prospectus are entered by choosing options: accepted groups, required subjects, minimum percentage, entry tests, deficiency courses, Part-I marks and more."),
    ("20-admin-rule-test-sample-students", "Testing rules with sample students", "Before saving, staff can test the rules against nine typical students (FSc, ICS, I.Com, FA, A-Levels, DAE) and see who would be eligible and why."),
    ("21-admin-fees", "Fees editor", "Fees are entered as items (admission, tuition, exam...) per semester, per year, one time or per credit hour. Totals are calculated automatically."),
    ("22-admin-review-queue", "Review queue (two-person check)", "Every change to live data must be approved by a second staff member. The card shows only what changed (old value crossed out, new value highlighted). Nobody can approve their own change."),
    ("23-admin-settings", "Settings", "Admission year (cycle), staff accounts and roles, and the result display mode."),
]

TECH = [
    ("Flutter (Dart language)", "Student mobile app and admin website", "Google's toolkit for building apps. One codebase runs on Android, iPhone and the web."),
    ("Python + FastAPI", "Server (back end)", "The “brain” of the system. It stores data, checks eligibility and sends results to the apps."),
    ("Eligibility rules engine", "Inside the server", "Our own code that compares a student's education with each programme's published rules and explains every decision. It does not guess and does not use AI."),
    ("SQLite (now) / PostgreSQL (later)", "Database", "Where universities, programmes, rules, fees and student profiles are stored. SQLite is used for development; PostgreSQL (e.g. Supabase) for the live version."),
    ("Secure login (Argon2 + tokens)", "Accounts", "Passwords are stored in a scrambled form that cannot be read back. Each login gets a time-limited token."),
    ("Riverpod, go_router, Dio", "Inside the Flutter apps", "Standard building blocks for screens, navigation and talking to the server."),
    ("Automated tests (pytest, Flutter test)", "Quality", "64 automatic checks run in seconds to make sure eligibility, the server and key screens keep working."),
    ("Git", "Version control", "Keeps the full history of every change to the project."),
]

FR = [
    ("FR-01", "User registration and authentication", "Sign up, log in, clear errors, dashboard after login, log out (also on all devices)."),
    ("FR-02", "Student profile and preferences", "Matric and Intermediate/A-Level/DAE records, subjects, marks, Part-I marks, interests, budget, location and more."),
    ("FR-03", "Course and university information (admin)", "Admin website to add and update universities, campuses, programmes, fees, rules, hostels and official links, with a two-person check."),
    ("FR-04", "Eligibility checking and recommendations", "Rule-by-rule eligibility, preferences, ranking, “why” explanations and helpful no-match suggestions."),
    ("FR-05", "Search, filtering and comparison", "Search by name, filter by field, province, fee and hostel, programme and university pages, compare up to three."),
    ("FR-06", "Shortlist and admission guidance", "Save and remove programmes, see requirements and deadlines, open official admission pages."),
]

GLOSSARY = [
    ("Eligible", "Meets every published minimum requirement. It does NOT mean admission is guaranteed."),
    ("Potentially eligible", "Fails no known requirement, but something must still be confirmed (e.g. final result, IBCC certificate, interview)."),
    ("Not currently eligible", "Fails at least one published requirement. The app shows which one."),
    ("Part-I marks", "Marks of the first year of Intermediate, used by many students before the final result is out."),
    ("IBCC equivalence", "The percentage that IBCC gives to O-Level/A-Level grades so they can be compared with Matric/Intermediate."),
    ("Deficiency course", "An extra course (e.g. Mathematics) a university allows some students to take if a subject is missing."),
    ("Server / back end", "The program that runs in the background, stores data and does the calculations."),
    ("Admission cycle", "One admission year, e.g. Fall 2027. Rules and fees are stored per year."),
]


def esc(s: str) -> str:
    return html.escape(s)


PDF_IMAGES = SHOW / "_pdf_images"
# Very tall captures are cropped for the PDF so the important part stays readable.
# (top, height) in pixels; a negative top means "from the bottom". The full images stay in screenshots/.
PDF_CROPS = {
    "08-student-programme-why-eligible": (0, 2750),
    "19-admin-rule-builder": (0, 1900),
    "20-admin-rule-test-sample-students": (-1300, 1300),
}


def prepare_pdf_images() -> None:
    PDF_IMAGES.mkdir(exist_ok=True)
    for f in SHOTS.glob("*.png"):
        im = Image.open(f)
        if f.stem in PDF_CROPS:
            top, height = PDF_CROPS[f.stem]
            if top < 0:
                top = max(0, im.height + top)
            im = im.crop((0, top, im.width, min(im.height, top + height)))
        im.save(PDF_IMAGES / f.name)


def img_tag(name: str, cls: str) -> str:
    return f'<img class="{cls}" src="_pdf_images/{name}.png" alt="{esc(name)}">'


def figure(name, title, text, cls):
    return (f'<figure class="{cls}">{img_tag(name, "shot")}'
            f"<figcaption><b>{esc(title)}</b><br>{esc(text)}</figcaption></figure>")


def build_html() -> str:
    logo = base64.b64encode((ROOT / "branding" / "logo-icon-512.png").read_bytes()).decode()
    phone_figs = "".join(figure(n, t, d, "phone") for n, t, d in STUDENT)
    admin_figs = "".join(figure(n, t, d, "desk") for n, t, d in ADMIN)
    tech_rows = "".join(f"<tr><td><b>{esc(a)}</b></td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in TECH)
    fr_rows = "".join(f"<tr><td class='id'><b>{a}</b></td><td>{esc(b)}</td><td>{esc(c)}</td><td class='ok'>Done</td></tr>" for a, b, c in FR)
    gl_rows = "".join(f"<tr><td><b>{esc(a)}</b></td><td>{esc(b)}</td></tr>" for a, b in GLOSSARY)
    today = date.today().strftime("%d %B %Y")
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>EduRecommend - Project Overview</title>
<style>
@page {{ size: A4; margin: 16mm 14mm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #1d2a26; font-size: 10.5pt; line-height: 1.5; margin: 0; }}
h1 {{ font-size: 26pt; margin: 0; color: #0f6e56; }}
h2 {{ font-size: 16pt; color: #0f6e56; border-bottom: 2px solid #cfe7df; padding-bottom: 4px; margin: 26px 0 10px; }}
h3 {{ font-size: 12pt; margin: 14px 0 6px; }}
.cover {{ height: 255mm; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; page-break-after: always; }}
.cover img {{ width: 150px; margin-bottom: 18px; }}
.cover .sub {{ font-size: 14pt; color: #3b5a52; margin-top: 8px; }}
.cover .meta {{ margin-top: 40px; color: #66807a; font-size: 10pt; }}
.box {{ background: #eef7f3; border-left: 4px solid #0f6e56; padding: 10px 14px; border-radius: 6px; margin: 10px 0; }}
.warn {{ background: #fff6e0; border-left-color: #c58a00; }}
table {{ border-collapse: collapse; width: 100%; margin: 6px 0 10px; }}
th, td {{ border: 1px solid #d6e3de; padding: 6px 8px; vertical-align: top; text-align: left; }}
th {{ background: #e2f1eb; }}
td.ok {{ color: #1b7f4b; font-weight: 600; white-space: nowrap; }}
td.id {{ white-space: nowrap; }}
.steps {{ display: flex; gap: 6px; align-items: stretch; margin: 12px 0; }}
.step {{ flex: 1; background: #eef7f3; border-radius: 8px; padding: 8px; text-align: center; font-size: 9.5pt; }}
.step b {{ display: block; color: #0f6e56; font-size: 18pt; }}
.arch {{ display: flex; align-items: center; justify-content: center; gap: 10px; margin: 14px 0; }}
.node {{ border: 2px solid #0f6e56; border-radius: 10px; padding: 10px 12px; text-align: center; width: 150px; font-size: 9.5pt; background: #fff; }}
.node b {{ display: block; color: #0f6e56; }}
.arrow {{ font-size: 18pt; color: #0f6e56; }}
.groups {{ display: flex; gap: 8px; }}
.group {{ flex: 1; border-radius: 8px; padding: 8px 10px; font-size: 9.5pt; }}
.g1 {{ background: #e3f4ea; }} .g2 {{ background: #fff3d6; }} .g3 {{ background: #fbe3e0; }}
.phones {{ display: flex; flex-wrap: wrap; gap: 10px 14px; }}
figure {{ margin: 0; page-break-inside: avoid; }}
figure.phone {{ width: 31%; }}
figure.phone img {{ width: 100%; max-height: 175mm; object-fit: contain; object-position: top; border: 1px solid #cfdcd7; border-radius: 10px; }}
figure.desk {{ width: 100%; margin-bottom: 14px; }}
figure.desk img {{ width: 100%; max-height: 190mm; object-fit: contain; object-position: top; border: 1px solid #cfdcd7; border-radius: 6px; }}
figcaption {{ font-size: 9pt; color: #33463f; margin-top: 4px; }}
.pb {{ page-break-before: always; }}
.keep {{ page-break-inside: avoid; }}
h2, h3 {{ page-break-after: avoid; }}
tr {{ page-break-inside: avoid; }}
.small {{ font-size: 9pt; color: #5b6f69; }}
</style></head><body>

<section class="cover">
  <img src="data:image/png;base64,{logo}" alt="EduRecommend logo">
  <h1>EduRecommend</h1>
  <div class="sub">University and programme guidance for students in Pakistan</div>
  <div class="sub">Project overview &middot; screenshots &middot; how it works &middot; technology</div>
  <div class="meta">Version 1.0 (development) &middot; {today}</div>
</section>

<h2>1. What is EduRecommend?</h2>
<p>EduRecommend is a mobile app that helps students in Pakistan find universities and degree programmes
they can apply to. The student enters their education (Matric, Intermediate / A-Levels / DAE), subjects,
marks and preferences (city, budget, hostel...). The app then checks every programme against its
<b>published admission requirements</b> and shows the results in three clear groups, with a simple
explanation for each one.</p>
<div class="box"><b>The problem it solves:</b> admission rules are spread across hundreds of university websites
and prospectuses, they differ by background (FSc, ICS, I.Com, A-Levels, DAE) and change every year.
Students often depend on social-media posts. EduRecommend puts verified rules in one place and explains them.</div>

<h3>Who uses it?</h3>
<table><tr><th>User</th><th>What they do</th></tr>
<tr><td><b>Students</b> (mobile app)</td><td>Create a profile, get eligibility results, search, save and compare programmes.</td></tr>
<tr><td><b>Data editors</b> (admin website)</td><td>Enter universities, programmes, rules, fees and hostels from official prospectuses.</td></tr>
<tr><td><b>Data verifiers</b> (admin website)</td><td>Check and approve every change before students can see it.</td></tr>
</table>

<h2>2. How it works</h2>
<div class="steps">
  <div class="step"><b>1</b>Student creates an account</div>
  <div class="step"><b>2</b>Enters education, subjects and marks</div>
  <div class="step"><b>3</b>Chooses interests and preferences</div>
  <div class="step"><b>4</b>App checks every programme's rules</div>
  <div class="step"><b>5</b>Results with reasons, shortlist, official link</div>
</div>
<h3>The three result groups</h3>
<div class="groups">
  <div class="group g1"><b>&#10004; Eligible</b><br>Meets every published minimum requirement.</div>
  <div class="group g2"><b>? Potentially eligible</b><br>Fails nothing known, but something must still be confirmed (e.g. final result).</div>
  <div class="group g3"><b>&#10006; Not currently eligible</b><br>Fails at least one requirement &ndash; the app says which one.</div>
</div>
<div class="box warn"><b>Important:</b> “Eligible” means the student meets the <i>minimum</i> requirements.
It does not guarantee admission; that depends on merit, seats and the university. The app says this on every results screen.</div>
<p><b>Preferences never change eligibility.</b> Budget, city or hostel only change the order of results and
which ones are shown first. If nothing fits, the app explains why and suggests changes (for example other fields
the student qualifies for, or a higher budget).</p>

<h3>Keeping the information correct</h3>
<ul>
<li>Every rule, fee and hostel record must have an <b>official source</b> (prospectus or university website) and shows when it was last verified.</li>
<li><b>Two-person check:</b> one staff member enters a change, a different person approves it. Students keep seeing the old, published information until then.</li>
<li>Rules are stored per <b>admission year</b>. If this year's data is not confirmed yet, the app warns the student.</li>
<li>Students can tap <b>“Report incorrect information”</b>; reports go to the admin team.</li>
</ul>
<div class="box"><b>Note about the data shown:</b> the screenshots use <b>fictional sample universities</b> (named “Demo ...” and
marked “SAMPLE DATA”) for testing. Real university data must be entered from official prospectuses through the admin website.</div>

<h2>3. Student app screenshots</h2>
<div class="phones">{phone_figs}</div>

<h2 class="pb">4. Admin website screenshots</h2>
{admin_figs}

<h2 class="pb">5. Technology used (in simple words)</h2>
<div class="arch">
  <div class="node"><b>Student app</b>Flutter<br>(Android, iPhone, web)</div>
  <div class="arrow">&#8644;</div>
  <div class="node"><b>Server</b>Python + FastAPI<br>+ eligibility engine</div>
  <div class="arrow">&#8644;</div>
  <div class="node"><b>Database</b>SQLite now,<br>PostgreSQL later</div>
</div>
<div class="arch">
  <div class="node"><b>Admin website</b>Flutter Web<br>(staff only)</div>
  <div class="arrow">&#8599;</div>
  <div class="small" style="width:330px">The admin website talks to the same server. Students and staff never touch the database directly.</div>
</div>
<table><tr><th>Technology</th><th>Used for</th><th>What it means</th></tr>{tech_rows}</table>

<div class="keep"><h2>6. Requirements covered</h2>
<p>The project follows the agreed requirements document (FR-01 to FR-06):</p>
<table><tr><th>ID</th><th>Requirement</th><th>What was built</th><th>Status</th></tr>{fr_rows}</table></div>

<h2>7. Security and privacy</h2>
<ul>
<li>Passwords are stored scrambled (Argon2) and can never be read back.</li>
<li>Students only see their own data. Staff need a staff role to open the admin website.</li>
<li>Students can download all their data or delete their account at any time.</li>
<li>Every staff action is recorded in a change history.</li>
</ul>

<h2>8. Testing</h2>
<ul>
<li><b>58 automatic server tests</b> check eligibility rules (e.g. exactly 60.00% vs 59.99%, Part-I marks, A-Levels, DAE, women-only campuses), the student features and the admin workflow.</li>
<li><b>6 automatic app tests</b> check key screens and the rule builder.</li>
<li>All main journeys were also tested by hand in the browser.</li>
</ul>

<h2>9. What comes next</h2>
<table><tr><th>Next step</th><th>Why</th></tr>
<tr><td>Enter real university data from official prospectuses</td><td>The app currently uses sample data.</td></tr>
<tr><td>Publish online (cloud server, PostgreSQL)</td><td>So students can use it from anywhere.</td></tr>
<tr><td>Android release, then iPhone</td><td>Reach students on their phones.</td></tr>
<tr><td>AI help assistant (version 1.1)</td><td>Answer questions using only verified information.</td></tr>
<tr><td>Deadline notifications (version 1.1)</td><td>Remind students before applications close.</td></tr>
</table>

<h2>10. Glossary</h2>
<table><tr><th>Word</th><th>Meaning</th></tr>{gl_rows}</table>
</body></html>"""


def main():
    for name, skip in [("04-student-profile-intermediate-marks", 0), ("05-student-preferences", 0),
                       ("08-student-programme-why-eligible", 0), ("10-student-university-page", 0),
                       ("14-student-no-match-suggestions", 0), ("18-admin-university-editor", 160),
                       ("19-admin-rule-builder", 160), ("20-admin-rule-test-sample-students", 160),
                       ("22-admin-review-queue", 160), ("23-admin-settings", 160)]:
        trim_bottom(SHOTS / f"{name}.png", skip_left=skip)
    prepare_pdf_images()
    page = SHOW / "EduRecommend-Project-Overview.html"
    page.write_text(build_html(), encoding="utf-8")
    b = Browser()
    try:
        b.send("Page.navigate", url=page.as_uri())
        import time
        time.sleep(3)
        pdf = b.send("Page.printToPDF", printBackground=True, preferCSSPageSize=True,
                     displayHeaderFooter=True, headerTemplate="<span></span>",
                     footerTemplate='<div style="font-size:8px;width:100%;text-align:center;color:#777">'
                                    'EduRecommend &middot; page <span class="pageNumber"></span> of '
                                    '<span class="totalPages"></span></div>')["data"]
    finally:
        b.close()
    out = SHOW / "EduRecommend-Project-Overview.pdf"
    out.write_bytes(base64.b64decode(pdf))
    page.unlink()
    shutil.rmtree(PDF_IMAGES)
    shutil.copy(ROOT / "branding" / "logo-1024.png", SHOW / "EduRecommend-logo.png")
    print("Wrote", out)


if __name__ == "__main__":
    main()
