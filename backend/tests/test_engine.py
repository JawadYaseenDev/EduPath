from datetime import date

import pytest

from app.engine import RuleValidationError, evaluate_offering, run, validate_rule
from app.engine.preferences import HostelFact, OfferingFacts, Preferences
from app.engine.types import (
    Category,
    OfferingRules,
    Outcome,
    QualificationInput,
    ResultStatus,
    Rule,
    RuleSet,
    StudentInput,
    Vocabulary,
)

VOCAB = Vocabulary(
    groups={"PRE_ENGINEERING": "FSc Pre-Engineering", "PRE_MEDICAL": "FSc Pre-Medical",
            "ICS": "ICS"},
    subjects={"MATH": "Mathematics", "PHY": "Physics", "CS": "Computer Science",
              "BIO": "Biology", "CHEM": "Chemistry", "STAT": "Statistics"},
    tests={"ECAT": "ECAT"},
)

SSC = QualificationInput("SSC", "MATRIC", "SCIENCE", percentage=85.0,
                         subjects=frozenset({"MATH", "PHY", "CHEM", "BIO"}))


def student(group="PRE_ENGINEERING", pct=72.0, subjects=None, gender="male", **hssc_kw):
    subjects = subjects or {
        "PRE_ENGINEERING": {"MATH", "PHY", "CHEM"},
        "PRE_MEDICAL": {"BIO", "PHY", "CHEM"},
        "ICS": {"MATH", "CS", "PHY"},
    }[group]
    hssc = QualificationInput("HSSC", hssc_kw.pop("type_code", "INTERMEDIATE"), group,
                              percentage=pct, subjects=frozenset(subjects), **hssc_kw)
    return StudentInput(gender=gender, date_of_birth=date(2008, 5, 1), domicile_region="PB",
                        qualifications={"SSC": SSC, "HSSC": hssc})


def offering(*rules, sets=None, **kw):
    rule_sets = sets or [RuleSet("rs1", "Main", list(rules))]
    return OfferingRules("off1", rule_sets, **kw)


ACCEPT_ENG_ICS = Rule("r1", "accepted_qualification",
                      {"level": "HSSC", "groups": ["PRE_ENGINEERING", "ICS"]})
NEED_MATH = Rule("r2", "required_subjects", {"level": "HSSC", "all_of": ["MATH"]})
MIN_60 = Rule("r3", "min_percentage", {"level": "HSSC", "min": 60})


def evaluate(off, stu):
    result = evaluate_offering(off, stu, VOCAB)
    assert result is not None
    return result


def test_pre_engineering_student_is_eligible():
    r = evaluate(offering(ACCEPT_ENG_ICS, NEED_MATH, MIN_60), student())
    assert r.category == Category.ELIGIBLE
    assert "FSc Pre-Engineering background is accepted" in r.rule_results[0].message
    assert r.academic_margin == 12.0


def test_pre_medical_student_not_eligible():
    r = evaluate(offering(ACCEPT_ENG_ICS, NEED_MATH, MIN_60), student("PRE_MEDICAL"))
    assert r.category == Category.NOT_ELIGIBLE
    fails = [x for x in r.rule_results if x.outcome == Outcome.FAIL]
    assert fails[0].reason_code == "group_not_accepted:PRE_MEDICAL"
    assert fails[1].reason_code == "missing_subject:MATH"


def test_deficiency_route_makes_pre_medical_eligible_with_next_step():
    deficiency = Rule("r4", "deficiency_allowed", {
        "for_groups": ["PRE_MEDICAL"], "missing_subject": "MATH",
        "course": "Deficiency Mathematics in the first year"})
    r = evaluate(offering(ACCEPT_ENG_ICS, NEED_MATH, MIN_60, deficiency), student("PRE_MEDICAL"))
    assert r.category == Category.ELIGIBLE
    assert any("Deficiency Mathematics" in s for s in r.next_steps)


@pytest.mark.parametrize("pct,expected", [(60.0, Category.ELIGIBLE),
                                          (59.99, Category.NOT_ELIGIBLE)])
def test_minimum_percentage_boundary(pct, expected):
    assert evaluate(offering(MIN_60), student(pct=pct)).category == expected


def test_part1_marks_give_potentially_eligible():
    stu = student(pct=None, result_status=ResultStatus.PART1_ONLY, part1_percentage=64.0)
    r = evaluate(offering(MIN_60), stu)
    assert r.category == Category.POTENTIALLY
    assert "Part-I" in r.rule_results[0].message


def test_part1_marks_accepted_by_university_give_eligible():
    accept = Rule("r5", "result_status", {"level": "HSSC", "accept_part1": True})
    stu = student(pct=None, result_status=ResultStatus.PART1_ONLY, part1_percentage=64.0)
    r = evaluate(offering(MIN_60, accept), stu)
    assert r.category == Category.ELIGIBLE
    assert r.next_steps  # final result must also meet the minimum


def test_part1_below_minimum_is_not_eligible():
    stu = student(pct=None, result_status=ResultStatus.PART1_ONLY, part1_percentage=55.0)
    assert evaluate(offering(MIN_60), stu).category == Category.NOT_ELIGIBLE


def test_result_awaited_without_marks_is_unknown():
    stu = student(pct=None, result_status=ResultStatus.AWAITED)
    assert evaluate(offering(MIN_60), stu).category == Category.POTENTIALLY


def test_a_level_estimated_equivalence_is_potentially():
    stu = student(pct=None, type_code="A_LEVEL", ibcc_percentage=75.0)
    r = evaluate(offering(MIN_60), stu)
    assert r.category == Category.POTENTIALLY
    assert any("IBCC" in s for s in r.next_steps)


def test_a_level_official_equivalence_is_eligible():
    stu = student(pct=None, type_code="A_LEVEL", ibcc_percentage=75.0, ibcc_is_official=True)
    assert evaluate(offering(MIN_60), stu).category == Category.ELIGIBLE


def test_missing_level_is_unknown():
    stu = StudentInput("female", None, None, {"SSC": SSC})
    r = evaluate(offering(MIN_60), stu)
    assert r.category == Category.POTENTIALLY
    assert "Add your Intermediate / A-Level details" in r.rule_results[0].message


def test_dae_route_is_not_unknown_for_intermediate_student():
    """An ICS student has no DAE record; the DAE route must fail, not become 'unknown'."""
    dae = RuleSet("dae", "For DAE students", [
        Rule("d", "accepted_qualification", {"level": "DIPLOMA", "groups": ["DAE_ELECTRICAL"]}),
        Rule("m", "min_percentage", {"level": "DIPLOMA", "min": 60}),
    ])
    eng = RuleSet("eng", "For Pre-Engineering", [
        Rule("e", "accepted_qualification", {"level": "HSSC", "groups": ["PRE_ENGINEERING"]}),
    ])
    r = evaluate(offering(sets=[dae, eng]), student("ICS"))
    assert r.category == Category.NOT_ELIGIBLE


def test_women_only_campus_rejects_male_student():
    r = evaluate(offering(MIN_60, campus_gender_policy="women_only"), student(gender="male"))
    assert r.category == Category.NOT_ELIGIBLE
    assert r.rule_results[0].rule_type == "campus_gender_policy"


def test_stale_data_downgrades_eligible_to_potentially():
    r = evaluate(offering(MIN_60, is_stale=True, stale_label="Fall 2026"), student())
    assert r.category == Category.POTENTIALLY
    assert "Fall 2026" in r.rule_results[-1].message


def test_entry_test_without_minimum_adds_next_step_only():
    test = Rule("r6", "entry_test_required", {"tests": ["ECAT"]})
    r = evaluate(offering(MIN_60, test), student())
    assert r.category == Category.ELIGIBLE
    assert "Register for and take ECAT." in r.next_steps


def test_entry_test_with_minimum_and_no_score_is_unknown():
    test = Rule("r6", "entry_test_required", {"tests": ["ECAT"], "min_score_percentage": 33})
    assert evaluate(offering(test), student()).category == Category.POTENTIALLY


def test_soft_rule_failure_gives_potentially():
    soft = Rule("r7", "min_percentage", {"level": "HSSC", "min": 80}, is_hard=False)
    assert evaluate(offering(soft), student()).category == Category.POTENTIALLY


def test_best_rule_set_wins():
    eng = RuleSet("a", "For Pre-Engineering", [Rule("x", "accepted_qualification",
                                                     {"level": "HSSC",
                                                      "groups": ["PRE_ENGINEERING"]})])
    ics = RuleSet("b", "For ICS", [Rule("y", "accepted_qualification",
                                        {"level": "HSSC", "groups": ["ICS"]})])
    r = evaluate(offering(sets=[eng, ics]), student("ICS"))
    assert r.category == Category.ELIGIBLE
    assert r.rule_set_name == "For ICS"


def test_offering_without_rules_is_never_evaluated():
    assert evaluate_offering(offering(), student(), VOCAB) is None


def test_invalid_rule_is_rejected():
    with pytest.raises(RuleValidationError):
        validate_rule("min_percentage", {"level": "HSSC", "min": 150})
    with pytest.raises(RuleValidationError):
        validate_rule("not_a_rule", {})


# ------------------------------------------------------------- full runs


def facts(oid, discipline="CS", field_="COMPUTING", fee=50_000, region="PB", **kw):
    return OfferingFacts(oid, discipline, field_, region, "LHR", "public", "coeducation",
                         "morning", tuition_per_semester=fee, charges_per_semester=fee,
                         hostels={"male": HostelFact("available", "on_campus", 20_000)}, **kw)


def pair(oid, rules, **facts_kw):
    return OfferingRules(oid, [RuleSet("rs", "Main", rules)]), facts(oid, **facts_kw)


def test_run_sorts_and_hides_outside_preferences():
    offerings = [
        pair("cheap", [MIN_60], fee=40_000),
        pair("expensive", [MIN_60], fee=150_000),
        pair("potential", [MIN_60, Rule("m", "manual_note", {"text": "Interview required"})]),
    ]
    out = run(offerings, student(), Preferences(max_fee_per_semester=60_000), VOCAB)
    assert [i.offering_id for i in out.items][0] == "cheap"
    assert out.hidden_by_preferences == 1
    assert out.no_match is None
    potential = next(i for i in out.items if i.offering_id == "potential")
    assert potential.recommended


def test_strict_mode_does_not_recommend_potentially_eligible():
    offerings = [pair("p", [Rule("m", "manual_note", {"text": "Interview required"})])]
    out = run(offerings, student(), Preferences(), VOCAB, mode="strict_pdf")
    assert not out.items[0].recommended
    assert out.no_match is not None and out.no_match.kind == "academic"


def test_academic_no_match_suggests_other_disciplines():
    eng_rules = [ACCEPT_ENG_ICS, NEED_MATH]
    bio_rules = [Rule("b", "accepted_qualification",
                      {"level": "HSSC", "groups": ["PRE_MEDICAL"]})]
    offerings = [
        pair("ee", eng_rules, discipline="EE", field_="ENGINEERING"),
        pair("biotech", bio_rules, discipline="BIOTECH", field_="LIFE_SCIENCES"),
    ]
    prefs = Preferences(fields=frozenset({"ENGINEERING"}))
    out = run(offerings, student("PRE_MEDICAL"), prefs, VOCAB)
    assert out.no_match.kind == "academic"
    assert "Mathematics is required" in [r.text for r in out.no_match.reasons]
    assert out.no_match.discipline_suggestions[0].discipline_id == "BIOTECH"


def test_preference_no_match_suggests_budget():
    offerings = [pair("a", [MIN_60], fee=72_000), pair("b", [MIN_60], fee=68_000)]
    out = run(offerings, student(), Preferences(max_fee_per_semester=40_000), VOCAB)
    assert out.no_match.kind == "preferences"
    s = out.no_match.preference_suggestions[0]
    assert (s.miss, s.count, s.suggested_max_fee) == ("over_budget", 2, 75_000)


def test_preferences_never_change_eligibility():
    offerings = [pair("a", [MIN_60], fee=500_000, region="SD")]
    prefs = Preferences(max_fee_per_semester=10_000, regions=frozenset({"KP"}))
    out = run(offerings, student(), prefs, VOCAB)
    assert out.items[0].eligibility.category == Category.ELIGIBLE
    assert set(out.items[0].misses) == {"outside_location", "over_budget"}
