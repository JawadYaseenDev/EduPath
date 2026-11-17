from app.engine.types import Vocabulary
from app.services.change_summary import describe_changes

VOCAB = Vocabulary(groups={"ICS": "ICS", "PRE_MEDICAL": "FSc Pre-Medical"},
                   subjects={"MATH": "Mathematics"}, tests={"ECAT": "ECAT", "NAT": "NAT"})

RULES = [{"name": "For ICS students", "rules": [
    {"rule_type": "accepted_qualification", "is_hard": True,
     "params": {"level": "HSSC", "types": [], "groups": ["ICS"]}},
    {"rule_type": "min_percentage", "is_hard": True,
     "params": {"level": "HSSC", "min": 50, "accept_part1": False}},
]}]


def _copy(x):
    import copy
    return copy.deepcopy(x)


def test_only_the_changed_rule_value_is_listed():
    after = _copy(RULES)
    after[0]["rules"][1]["params"]["min"] = 55.0
    rows = describe_changes("rules", RULES, after, VOCAB)
    assert rows == [{"where": "For ICS students", "what": "Minimum percentage · Minimum %",
                     "before": "50%", "after": "55%"}]


def test_identical_rules_give_no_rows():
    assert describe_changes("rules", RULES, _copy(RULES), VOCAB) == []


def test_rule_added_removed_and_strictness():
    after = _copy(RULES)
    after[0]["rules"][1]["is_hard"] = False
    after[0]["rules"][0]["params"]["groups"] = ["ICS", "PRE_MEDICAL"]
    after[0]["rules"].append({"rule_type": "entry_test_required", "is_hard": True,
                              "params": {"tests": ["ECAT"]}})
    rows = describe_changes("rules", RULES, after, VOCAB)
    whats = {r["what"]: (r["before"], r["after"]) for r in rows}
    assert whats["Accepted backgrounds · Groups"] == ("Nothing removed", "Added: FSc Pre-Medical")
    assert whats["Minimum percentage · strictness"] == ("Must pass", "Check only")
    assert whats["Entry test"] == ("(none)", "Rule added")


def test_renamed_and_new_groups():
    after = _copy(RULES)
    after[0]["name"] = "For ICS (Physics) students"
    after.append({"name": "For DAE students", "rules": RULES[0]["rules"]})
    rows = describe_changes("rules", RULES, after, VOCAB)
    assert {"where": "Rule group", "what": "Name", "before": "For ICS students",
            "after": "For ICS (Physics) students"} in rows
    assert any(r["what"] == "For DAE students" and r["after"].startswith("Added") for r in rows)


def test_fee_tests_and_dates():
    fees_b = [{"component": "tuition", "amount_pkr": 40000, "basis": "per_semester"},
              {"component": "admission", "amount_pkr": 10000, "basis": "one_time"}]
    fees_a = [{"component": "tuition", "amount_pkr": 55000, "basis": "per_semester"},
              {"component": "admission", "amount_pkr": 10000, "basis": "one_time"},
              {"component": "lab", "amount_pkr": 3000, "basis": "per_semester"}]
    rows = describe_changes("fees", fees_b, fees_a, VOCAB)
    assert [(r["what"], r["before"], r["after"]) for r in rows] == [
        ("Tuition fee, per semester", "PKR 40,000", "PKR 55,000"),
        ("Lab fee, per semester", "(none)", "PKR 3,000"),
    ]
    tests = describe_changes("tests", [{"test_code": "ECAT"}], [{"test_code": "NAT"}], VOCAB)
    assert {(r["what"], r["after"]) for r in tests} == {("ECAT", "Removed"), ("NAT", "Listed")}
    dates = describe_changes(
        "deadlines", [{"event": "applications_close", "date": "2027-07-31", "is_tentative": True}],
        [{"event": "applications_close", "date": "2027-08-05", "is_tentative": False}], VOCAB)
    assert dates == [{"where": "Dates", "what": "Applications close",
                      "before": "2027-07-31 (tentative)", "after": "2027-08-05"}]


def test_field_updates_use_names():
    rows = describe_changes("update", {"name": "Old", "sector": "public", "source_id": "s1"},
                            {"name": "New", "sector": "public", "source_id": "s2"}, VOCAB,
                            names={"s1": "Prospectus 2026", "s2": "Prospectus 2027"})
    assert [(r["what"], r["before"], r["after"]) for r in rows] == [
        ("Name", "Old", "New"), ("Source", "Prospectus 2026", "Prospectus 2027")]
