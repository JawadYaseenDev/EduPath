"""End-to-end API tests covering PDF FR-01 to FR-06 against the demo catalogue."""


def _ref(client):
    return client.get("/v1/reference").json()


def _city(client, name):
    return next(c["id"] for c in _ref(client)["cities"] if c["name"] == name)


def _setup_student(client, auth, group="PRE_ENGINEERING", obtained=880, gender="male",
                   fields=("COMPUTING", "ENGINEERING"), **prefs):
    r = client.put("/v1/profile", headers=auth, json={
        "full_name": "Ali Khan", "gender": gender, "current_city_id": _city(client, "Lahore"),
        "domicile_region_code": "PB"})
    assert r.status_code == 200, r.text
    subjects = {"PRE_ENGINEERING": ["MATH", "PHY", "CHEM", "ENG"],
                "PRE_MEDICAL": ["BIO", "PHY", "CHEM", "ENG"],
                "ICS": ["MATH", "CS", "PHY", "ENG"]}[group]
    r = client.put("/v1/profile/qualifications", headers=auth, json={
        "type_code": "MATRIC", "group_code": "MATRIC_SCIENCE_BIO", "passing_year": 2024,
        "obtained_marks": 1000, "total_marks": 1200})
    assert r.status_code == 200, r.text
    r = client.put("/v1/profile/qualifications", headers=auth, json={
        "type_code": "INTERMEDIATE", "group_code": group, "passing_year": 2026,
        "obtained_marks": obtained, "total_marks": 1100,
        "subjects": [{"code": s} for s in subjects]})
    assert r.status_code == 200, r.text
    r = client.put("/v1/profile/preferences", headers=auth,
                   json={"fields": list(fields), **prefs})
    assert r.status_code == 200, r.text
    return r.json()


# ------------------------------------------------------------------ FR-01


def test_register_login_and_errors(client):
    body = {"email": "ayesha@example.com", "password": "Strong-pass-1", "accept_terms": True}
    assert client.post("/v1/auth/register", json=body).status_code == 201
    dup = client.post("/v1/auth/register", json=body)
    assert dup.status_code == 409 and "already exists" in dup.json()["detail"]
    weak = client.post("/v1/auth/register", json={**body, "email": "x@example.com",
                                                   "password": "short"})
    assert weak.status_code == 422
    bad = client.post("/v1/auth/login", json={"email": body["email"], "password": "wrong-pass"})
    assert bad.status_code == 401 and bad.json()["detail"] == "Wrong email or password."
    ok = client.post("/v1/auth/login", json={"email": "AYESHA@example.com",
                                             "password": body["password"]})
    assert ok.status_code == 200


def test_logout_everywhere_invalidates_token(client, auth):
    assert client.get("/v1/auth/me", headers=auth).status_code == 200
    assert client.post("/v1/auth/logout-all", headers=auth).status_code == 200
    assert client.get("/v1/auth/me", headers=auth).status_code == 401


def test_protected_endpoints_need_login(client):
    assert client.get("/v1/profile").status_code == 401


# ------------------------------------------------------------------ FR-02


def test_profile_validation_messages(client, auth):
    r = client.put("/v1/profile/qualifications", headers=auth, json={
        "type_code": "INTERMEDIATE", "group_code": "ICS", "obtained_marks": 1200,
        "total_marks": 1100})
    assert r.status_code == 422
    assert r.json()["detail"] == "Obtained marks cannot be more than total marks."
    r = client.put("/v1/profile/qualifications", headers=auth, json={
        "type_code": "INTERMEDIATE", "group_code": "MATRIC_ARTS"})
    assert r.status_code == 422


def test_profile_completeness_and_percentage(client, auth):
    data = _setup_student(client, auth)
    hssc = next(q for q in data["qualifications"] if q["level"] == "HSSC")
    assert hssc["percentage"] == 80.0
    assert data["completeness"]["percent"] == 100


# ------------------------------------------------------------------ FR-04


def test_recommendations_need_complete_profile(client, auth):
    r = client.post("/v1/recommendations/run", headers=auth)
    assert r.status_code == 422


def test_pre_engineering_student_gets_ranked_results_with_reasons(client, auth):
    _setup_student(client, auth)
    r = client.post("/v1/recommendations/run", headers=auth)
    assert r.status_code == 200, r.text
    data = r.json()
    titles = [x["offering"]["programme_title"] for x in data["results"]
              if x["category"] == "eligible"]
    assert "BSc Electrical Engineering" in titles
    first = data["results"][0]
    assert first["category"] == "eligible"
    assert any("background is accepted" in o["message"] for o in first["rule_outcomes"])
    # Male student: the women's university is never eligible.
    wu = [x for x in data["results"] if x["offering"]["university_short_name"] == "Demo WU"]
    assert wu and all(x["category"] == "not_eligible" for x in wu)
    # Stale (previous cycle) data is never shown as plain "eligible".
    stale = [x for x in data["results"] if x["offering"]["is_stale"]]
    assert stale and all(x["category"] != "eligible" for x in stale)
    assert data["summary"]["no_match"] is None


def test_academic_no_match_for_pre_medical_in_engineering(client, auth):
    _setup_student(client, auth, group="PRE_MEDICAL", fields=("ENGINEERING",))
    data = client.post("/v1/recommendations/run", headers=auth).json()
    no_match = data["summary"]["no_match"]
    assert no_match["kind"] == "academic"
    assert no_match["discipline_suggestions"]


def test_preference_no_match_suggests_budget(client, auth):
    _setup_student(client, auth, fields=("BUSINESS",), max_fee_per_semester=5000,
                   regions=["SD"])
    data = client.post("/v1/recommendations/run", headers=auth).json()
    no_match = data["summary"]["no_match"]
    assert no_match["kind"] == "preferences"
    assert no_match["preference_suggestions"]


def test_profile_change_marks_results_outdated(client, auth):
    _setup_student(client, auth)
    client.post("/v1/recommendations/run", headers=auth)
    assert client.get("/v1/recommendations/latest", headers=auth).json()["is_outdated"] is False
    client.put("/v1/profile/preferences", headers=auth, json={"fields": ["BUSINESS"]})
    assert client.get("/v1/recommendations/latest", headers=auth).json()["is_outdated"] is True


# ------------------------------------------------------------------ FR-05


def test_search_and_filters(client):
    all_ = client.get("/v1/programmes").json()
    assert all_["count"] >= 10
    cs = client.get("/v1/programmes", params={"q": "computer science"}).json()
    assert cs["count"] >= 3
    cheap = client.get("/v1/programmes", params={"max_fee": 30000}).json()
    assert all(c["charges_per_semester"] <= 30000 for c in cheap["results"])
    sindh = client.get("/v1/programmes", params={"region": "SD"}).json()
    assert {c["city"] for c in sindh["results"]} == {"Karachi"}
    detail = client.get(f"/v1/offerings/{cs['results'][0]['offering_id']}").json()
    assert detail["rule_sets"] and detail["fees"]["first_year_total"]
    assert detail["is_demo"] is True


def test_credit_hour_fees_are_estimated(client):
    ai = client.get("/v1/programmes", params={"q": "artificial intelligence"}).json()
    card = ai["results"][0]
    assert card["fee_is_estimated"] is True
    # 9,500 x 133 credit hours / 8 semesters
    assert card["tuition_per_semester"] == round(9500 * 133 / 8)


# ------------------------------------------------------------------ FR-06


def test_shortlist_add_view_remove(client, auth):
    oid = client.get("/v1/programmes").json()["results"][0]["offering_id"]
    assert len(client.post("/v1/shortlist", headers=auth, json={"offering_id": oid}).json()) == 1
    assert len(client.post("/v1/shortlist", headers=auth, json={"offering_id": oid}).json()) == 1
    assert client.get("/v1/shortlist", headers=auth).json()[0]["offering_id"] == oid
    assert client.delete(f"/v1/shortlist/{oid}", headers=auth).json() == []


# ------------------------------------------------------------------ privacy


def test_export_and_delete_account(client, auth):
    _setup_student(client, auth)
    export = client.get("/v1/account/export", headers=auth).json()
    assert export["profile"]["full_name"] == "Ali Khan"
    assert client.delete("/v1/account", headers=auth).status_code == 204
    assert client.get("/v1/profile", headers=auth).status_code == 401
