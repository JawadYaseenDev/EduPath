"""Admin API: permissions, four-eyes review, queued edits to live data, rule builder."""

import uuid

import pytest

PASSWORD = "Staff-pass-123"


def _staff(client, role):
    from app import models as m
    from app.db import SessionLocal
    from app.security import hash_password

    email = f"{role}-{uuid.uuid4().hex[:6]}@example.com"
    with SessionLocal() as db:
        db.add(m.User(email=email, password_hash=hash_password(PASSWORD), role=role,
                      email_verified=True))
        db.commit()
    token = client.post("/v1/auth/login", json={"email": email, "password": PASSWORD}).json()
    return {"Authorization": f"Bearer {token['access_token']}"}


@pytest.fixture
def editor(client):
    return _staff(client, "data_editor")


@pytest.fixture
def verifier(client):
    return _staff(client, "data_verifier")


def _ref(client):
    return client.get("/v1/reference").json()


def _source(client, h):
    r = client.post("/v1/admin/sources", headers=h, json={
        "kind": "pdf_prospectus", "title": "Test University Prospectus 2027",
        "url": "https://example.edu/prospectus.pdf", "page_numbers": "12-14"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


RULES = [{"name": "For Pre-Engineering and ICS students", "rules": [
    {"rule_type": "accepted_qualification",
     "params": {"level": "HSSC", "groups": ["PRE_ENGINEERING", "ICS"]}},
    {"rule_type": "required_subjects", "params": {"level": "HSSC", "all_of": ["MATH"]}},
    {"rule_type": "min_percentage", "params": {"level": "HSSC", "min": 60}},
]}]


def _build_university(client, h, source_id):
    """University -> campus -> programme -> offering, all as drafts with a source."""
    lahore = next(c["id"] for c in _ref(client)["cities"] if c["name"] == "Lahore")
    uni = client.post("/v1/admin/universities", headers=h, json={
        "name": f"Test University {uuid.uuid4().hex[:4]}", "sector": "public",
        "website_url": "https://example.edu", "source_id": source_id}).json()["id"]
    campus = client.post("/v1/admin/campuses", headers=h, json={
        "university_id": uni, "name": "Main Campus", "city_id": lahore,
        "source_id": source_id}).json()["id"]
    prog = client.post("/v1/admin/programmes", headers=h, json={
        "campus_id": campus, "discipline_code": "SE", "title": "BS Software Engineering",
        "degree_type": "BS", "duration_years": 4, "source_id": source_id}).json()["id"]
    off = client.post("/v1/admin/offerings", headers=h,
                      json={"programme_id": prog, "copy_from_previous": False}).json()["id"]
    assert client.put(f"/v1/admin/offerings/{off}", headers=h, json={
        "seats_total": 50, "source_id": source_id}).status_code == 200
    assert client.put(f"/v1/admin/offerings/{off}/rules", headers=h, json=RULES).status_code == 200
    assert client.put(f"/v1/admin/offerings/{off}/fees", headers=h, json=[
        {"component": "tuition", "amount_pkr": 40000, "basis": "per_semester"}]).status_code == 200
    return {"university": uni, "campus": campus, "programme": prog, "offering": off}


def _publish_all(client, editor, verifier, ids):
    for kind in ("university", "campus", "programme", "offering"):
        r = client.post(f"/v1/admin/records/{kind}/{ids[kind]}/submit", headers=editor)
        assert r.status_code == 200, r.text
        r = client.post(f"/v1/admin/records/{kind}/{ids[kind]}/approve", headers=verifier)
        assert r.status_code == 200, r.text


def _public_titles(client, university_id):
    return [c["programme_title"] for c in
            client.get("/v1/programmes", params={"university_id": university_id}).json()["results"]]


def test_students_cannot_use_admin(client, auth):
    assert client.get("/v1/admin/dashboard", headers=auth).status_code == 403
    assert client.get("/v1/admin/dashboard").status_code == 401


def test_editor_cannot_approve_and_support_cannot_edit(client, editor):
    support = _staff(client, "support")
    assert client.post("/v1/admin/universities", headers=support,
                       json={"name": "X University", "sector": "public"}).status_code == 403
    assert client.post("/v1/admin/records/university/abc/approve", headers=editor).status_code == 403


def test_draft_to_published_with_four_eyes(client, editor, verifier):
    source = _source(client, editor)
    ids = _build_university(client, editor, source)
    # Drafts are invisible to students.
    assert _public_titles(client, ids["university"]) == []
    # The author cannot approve their own record, even with verifier rights.
    own = client.post("/v1/admin/universities", headers=verifier, json={
        "name": "Verifier Own University", "sector": "public", "source_id": source}).json()["id"]
    assert client.post(f"/v1/admin/records/university/{own}/submit", headers=verifier).status_code == 200
    r = client.post(f"/v1/admin/records/university/{own}/approve", headers=verifier)
    assert r.status_code == 403 and "your own" in r.json()["detail"]
    _publish_all(client, editor, verifier, ids)
    assert _public_titles(client, ids["university"]) == ["BS Software Engineering"]


def test_submit_needs_source_and_rules(client, editor):
    uni = client.post("/v1/admin/universities", headers=editor,
                      json={"name": "No Source University", "sector": "private"}).json()["id"]
    r = client.post(f"/v1/admin/records/university/{uni}/submit", headers=editor)
    assert r.status_code == 422 and "official source" in r.json()["detail"]


def test_invalid_rules_are_rejected_with_clear_message(client, editor):
    source = _source(client, editor)
    ids = _build_university(client, editor, source)
    bad = [{"name": "Broken", "rules": [{"rule_type": "min_percentage",
                                         "params": {"level": "HSSC", "min": 150}}]}]
    r = client.put(f"/v1/admin/offerings/{ids['offering']}/rules", headers=editor, json=bad)
    assert r.status_code == 422 and "Broken, rule 1" in r.json()["detail"]
    unnamed = [{"name": "", "rules": RULES[0]["rules"]}]
    assert client.put(f"/v1/admin/offerings/{ids['offering']}/rules", headers=editor,
                      json=unnamed).status_code == 422


def test_edits_to_live_data_wait_for_review(client, editor, verifier):
    source = _source(client, editor)
    ids = _build_university(client, editor, source)
    _publish_all(client, editor, verifier, ids)
    off = ids["offering"]

    def public_fee():
        return client.get(f"/v1/offerings/{off}").json()["tuition_per_semester"]

    assert public_fee() == 40000
    r = client.put(f"/v1/admin/offerings/{off}/fees", headers=editor, json=[
        {"component": "tuition", "amount_pkr": 55000, "basis": "per_semester"}])
    assert r.status_code == 200 and r.json()["queued"] is True
    assert public_fee() == 40000  # students still see the published fee
    # Only one pending change per section.
    dup = client.put(f"/v1/admin/offerings/{off}/fees", headers=editor, json=[])
    assert dup.status_code == 409
    queue = client.get("/v1/admin/review", headers=verifier).json()
    change = next(c for c in queue["changes"] if c["entity_id"] == off)
    assert change["before"][0]["amount_pkr"] == 40000
    assert change["differences"] == [{"where": "Fees", "what": "Tuition fee, per semester",
                                      "before": "PKR 40,000", "after": "PKR 55,000"}]
    assert client.post(f"/v1/admin/changes/{change['id']}/approve", headers=editor).status_code == 403
    assert client.post(f"/v1/admin/changes/{change['id']}/approve", headers=verifier).status_code == 200
    assert public_fee() == 55000


def test_rejected_change_is_not_applied(client, editor, verifier):
    source = _source(client, editor)
    ids = _build_university(client, editor, source)
    _publish_all(client, editor, verifier, ids)
    r = client.put(f"/v1/admin/universities/{ids['university']}", headers=editor, json={
        "name": "Renamed University", "sector": "private", "source_id": source})
    cid = r.json()["change_request_id"]
    assert client.post(f"/v1/admin/changes/{cid}/reject", headers=verifier,
                       json={"note": "Name not in prospectus"}).status_code == 200
    uni = client.get(f"/v1/universities/{ids['university']}").json()
    assert uni["name"] != "Renamed University" and uni["sector"] == "public"


def test_rule_test_panel(client, editor):
    r = client.post("/v1/admin/rules/test", headers=editor, json={"rule_sets": RULES})
    assert r.status_code == 200
    rows = {row["student"]: row for row in r.json()}
    assert rows["FSc Pre-Engineering, 75%, male"]["category"] == "eligible"
    assert rows["FSc Pre-Medical, 82%, female"]["category"] == "not_eligible"
    assert rows["ICS, Part-I only 70%, female"]["category"] == "potentially_eligible"
    assert rows["DAE Electrical, 72%, male"]["category"] == "not_eligible"


def test_new_cycle_offering_copies_rules_but_needs_new_source(client, editor, verifier):
    source = _source(client, editor)
    ids = _build_university(client, editor, source)
    _publish_all(client, editor, verifier, ids)
    super_admin = _staff(client, "super_admin")
    cycle = client.post("/v1/admin/cycles", headers=super_admin,
                        json={"year": 2028 + int(uuid.uuid4().int % 50), "label": "Future"})
    assert cycle.status_code == 201
    cycle_id = cycle.json()["id"]
    try:
        assert client.put(f"/v1/admin/cycles/{cycle_id}/current", headers=super_admin).status_code == 200
        new = client.post("/v1/admin/offerings", headers=editor,
                          json={"programme_id": ids["programme"]}).json()["id"]
        detail = client.get(f"/v1/admin/offerings/{new}", headers=editor).json()
        assert [(rs["name"], [r["rule_type"] for r in rs["rules"]]) for rs in detail["rules"]] == \
            [(rs["name"], [r["rule_type"] for r in rs["rules"]]) for rs in RULES]
        assert detail["source_id"] is None and detail["status"] == "draft"
        # The previous year's data is still shown to students, marked as stale.
        card = client.get("/v1/programmes", params={"university_id": ids["university"]}).json()
        assert card["results"][0]["is_stale"] is True
    finally:
        current = next(c for c in client.get("/v1/admin/cycles", headers=super_admin).json()
                       if c["year"] == 2027)
        client.put(f"/v1/admin/cycles/{current['id']}/current", headers=super_admin)


def test_archive_hides_from_students_and_audit_records_it(client, editor, verifier):
    source = _source(client, editor)
    ids = _build_university(client, editor, source)
    _publish_all(client, editor, verifier, ids)
    assert client.post(f"/v1/admin/records/offering/{ids['offering']}/archive",
                       headers=editor).status_code == 200
    assert _public_titles(client, ids["university"]) == []
    super_admin = _staff(client, "super_admin")
    log = client.get("/v1/admin/audit", headers=super_admin,
                     params={"entity_id": ids["offering"]}).json()
    assert {"archive", "approve", "submit"} <= {e["action"] for e in log}


def test_student_report_queue(client, auth, editor):
    oid = client.get("/v1/programmes").json()["results"][0]["offering_id"]
    client.post("/v1/reports", headers=auth, json={
        "entity_type": "offering", "entity_id": oid, "message": "The fee has changed."})
    reports = client.get("/v1/admin/reports", headers=editor, params={"status": "new"}).json()
    report = next(r for r in reports if r["entity_id"] == oid)
    assert report["label"]
    assert client.put(f"/v1/admin/reports/{report['id']}", headers=editor,
                      json={"status": "fixed"}).status_code == 200


def test_dashboard(client, editor):
    d = client.get("/v1/admin/dashboard", headers=editor).json()
    assert d["counts"]["university"]["published"] >= 5
    assert "pending_reviews" in d
