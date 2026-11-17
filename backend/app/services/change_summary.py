"""Plain-English list of what a proposed change actually changes.

Reviewers should not have to read two long JSON blocks to spot "50 -> 55".
`describe_changes` returns only the differences, as rows of
{"where": ..., "what": ..., "before": ..., "after": ...}.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from ..engine.types import Vocabulary

FIELD_LABELS = {
    "name": "Name", "short_name": "Short name", "aliases": "Other names", "sector": "Sector",
    "hec_recognised": "HEC recognised", "gender_policy": "Admission policy",
    "website_url": "Website", "admissions_url": "Admissions page", "description": "Description",
    "source_id": "Source", "is_main_campus": "Main campus", "city_id": "City",
    "address": "Address", "latitude": "Latitude", "longitude": "Longitude",
    "discipline_code": "Discipline", "title": "Title", "degree_type": "Degree type",
    "duration_years": "Duration (years)", "total_credit_hours": "Total credit hours",
    "shift": "Shift", "accreditation_body": "Accreditation body",
    "accreditation_status": "Accreditation status", "programme_url": "Programme page",
    "for_gender": "For", "location": "Location", "availability": "Availability",
    "fee_per_semester_pkr": "Fee per semester", "notes": "Notes",
    "is_offered": "Offered this cycle", "seats_total": "Seats",
}

RULE_LABELS = {
    "accepted_qualification": "Accepted backgrounds",
    "required_subjects": "Required subjects",
    "min_percentage": "Minimum percentage",
    "min_subject_marks": "Minimum marks in a subject",
    "entry_test_required": "Entry test",
    "deficiency_allowed": "Deficiency course route",
    "result_status": "Part-I marks accepted",
    "ibcc_equivalence_required": "IBCC certificate required",
    "gender": "Gender restriction",
    "domicile": "Domicile / quota seats",
    "max_age": "Age limit",
    "passing_year_window": "Passing year",
    "improved_result_policy": "Improved results",
    "manual_note": "Needs manual check",
}

PARAM_LABELS = {
    "level": "Applies to", "types": "Qualification types", "groups": "Groups",
    "all_of": "Must have all of", "one_of": "Must have one of", "min": "Minimum %",
    "accept_part1": "Part-I marks accepted", "subject": "Subject",
    "min_percentage": "Minimum % in subject", "tests": "Tests",
    "min_score_percentage": "Minimum score %", "allowed": "Open to", "regions": "Domicile of",
    "seat_type": "Seat type", "years": "Maximum age", "on_date": "On date",
    "min_year": "Passed in or after", "for_groups": "Groups allowed", "missing_subject":
    "Missing subject", "course": "Course", "for_types": "For", "accepted": "Accepted",
    "text": "Note",
}

LEVELS = {"SSC": "Matric / O-Level", "HSSC": "Intermediate / A-Level", "DIPLOMA": "DAE"}
EVENTS = {"applications_open": "Applications open", "applications_close": "Applications close",
          "test_date": "Test date", "merit_list": "Merit list", "classes_start": "Classes start"}
FEE_BASIS = {"one_time": "one time", "per_semester": "per semester", "per_year": "per year",
             "per_credit_hour": "per credit hour"}
NONE = "(none)"


def _row(where: str, what: str, before: Any, after: Any) -> dict:
    return {"where": where, "what": what, "before": before, "after": after}


def _title(code: Any) -> str:
    return str(code).replace("_", " ").capitalize()


def _value(key: str, value: Any, vocab: Vocabulary, names: dict | None = None) -> str:
    """Format one value the way a reviewer would say it."""
    if value is None or value == [] or value == "":
        return NONE
    if key in ("source_id", "city_id") and names:
        return names.get(value, value)
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if key == "level":
        return LEVELS.get(value, value)
    if key in ("groups", "for_groups"):
        return ", ".join(vocab.group(v) for v in value)
    if key in ("types", "for_types"):
        return ", ".join(vocab.type(v) for v in value)
    if key in ("all_of",):
        return ", ".join(vocab.subject(v) for v in value)
    if key in ("subject", "missing_subject"):
        return vocab.subject(value)
    if key == "one_of":
        return "; ".join(" or ".join(vocab.subject(s) for s in g) for g in value)
    if key == "tests":
        return ", ".join(vocab.test(v) for v in value)
    if key == "regions":
        return ", ".join(vocab.region(v) for v in value)
    if key in ("min", "min_percentage", "min_score_percentage"):
        return f"{value}%"
    if key in ("fee_per_semester_pkr",):
        return f"PKR {value:,}"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if key in ("sector", "gender_policy", "shift", "location", "availability", "for_gender",
               "accreditation_status", "allowed"):
        return _title(value)
    return str(value)


# ------------------------------------------------------------------ per kind


def _fields(before: dict, after: dict, vocab: Vocabulary, names: dict | None) -> list[dict]:
    rows = []
    for key in after:
        b, a = before.get(key), after.get(key)
        if (b in (None, "", []) and a in (None, "", [])) or b == a:
            continue
        rows.append(_row("Details", FIELD_LABELS.get(key, _title(key)),
                         _value(key, b, vocab, names), _value(key, a, vocab, names)))
    return rows


def _fee_key(f: dict) -> tuple:
    return (f["component"], f["basis"], f.get("applies_to", "all"))


def _fee_label(f: dict) -> str:
    when = " (first semester only)" if f.get("applies_to") == "first_only" else ""
    return f"{_title(f['component'])} fee, {FEE_BASIS.get(f['basis'], f['basis'])}{when}"


def _fee_amount(f: dict | None) -> str:
    if f is None:
        return NONE
    return f"PKR {f['amount_pkr']:,}" + (" (estimated)" if f.get("is_estimated") else "")


def _fees(before: list, after: list) -> list[dict]:
    b = {_fee_key(f): f for f in before}
    a = {_fee_key(f): f for f in after}
    rows = []
    for key in list(b) + [k for k in a if k not in b]:
        fb, fa = b.get(key), a.get(key)
        if fb is not None and fa is not None and fb["amount_pkr"] == fa["amount_pkr"] \
                and bool(fb.get("is_estimated")) == bool(fa.get("is_estimated")):
            continue
        rows.append(_row("Fees", _fee_label(fa or fb), _fee_amount(fb), _fee_amount(fa)))
    return rows


def _tests(before: list, after: list, vocab: Vocabulary) -> list[dict]:
    b = {t["test_code"]: t.get("is_mandatory", True) for t in before}
    a = {t["test_code"]: t.get("is_mandatory", True) for t in after}
    rows = []
    for code in sorted(set(b) | set(a)):
        if code in b and code in a:
            if b[code] != a[code]:
                rows.append(_row("Entry tests", vocab.test(code),
                                 "Mandatory" if b[code] else "Optional",
                                 "Mandatory" if a[code] else "Optional"))
            continue
        rows.append(_row("Entry tests", vocab.test(code),
                         "Listed" if code in b else NONE, "Listed" if code in a else "Removed"))
    return rows


def _deadline_text(d: dict | None) -> str:
    if d is None:
        return NONE
    return f"{d['date']}{' (tentative)' if d.get('is_tentative') else ''}"


def _deadlines(before: list, after: list) -> list[dict]:
    def keyed(rows):
        seen: Counter[str] = Counter()
        out = {}
        for d in rows:
            seen[d["event"]] += 1
            out[(d["event"], seen[d["event"]])] = d
        return out

    b, a = keyed(before), keyed(after)
    rows = []
    for key in list(b) + [k for k in a if k not in b]:
        db, da = b.get(key), a.get(key)
        if db is not None and da is not None and str(db["date"]) == str(da["date"]) \
                and bool(db.get("is_tentative")) == bool(da.get("is_tentative")):
            continue
        rows.append(_row("Dates", EVENTS.get(key[0], _title(key[0])),
                         _deadline_text(db), _deadline_text(da)))
    return rows


def _rule_key_list(rules: list) -> dict[tuple[str, int], dict]:
    """Match rules by type (1st min_percentage with 1st min_percentage, ...)."""
    seen: Counter[str] = Counter()
    out = {}
    for r in rules:
        seen[r["rule_type"]] += 1
        out[(r["rule_type"], seen[r["rule_type"]])] = r
    return out


def _rules(before: list, after: list, vocab: Vocabulary) -> list[dict]:
    rows = []
    b_sets = {rs["name"]: rs for rs in before}
    a_sets = {rs["name"]: rs for rs in after}
    # A renamed group keeps its position: pair unmatched groups by order.
    b_only = [n for n in b_sets if n not in a_sets]
    a_only = [n for n in a_sets if n not in b_sets]
    pairs = [(n, n) for n in b_sets if n in a_sets]
    while b_only and a_only:
        old, new = b_only.pop(0), a_only.pop(0)
        rows.append(_row("Rule group", "Name", old, new))
        pairs.append((old, new))
    for name in b_only:
        rows.append(_row("Rule group", name, f"{len(b_sets[name]['rules'])} rules", "Removed"))
    for name in a_only:
        rows.append(_row("Rule group", name, NONE, f"Added with {len(a_sets[name]['rules'])} rules"))

    for old, new in pairs:
        where = new
        rb = _rule_key_list(b_sets[old]["rules"])
        ra = _rule_key_list(a_sets[new]["rules"])
        for key in list(rb) + [k for k in ra if k not in rb]:
            label = RULE_LABELS.get(key[0], _title(key[0]))
            xb, xa = rb.get(key), ra.get(key)
            if xb is None:
                rows.append(_row(where, label, NONE, "Rule added"))
                continue
            if xa is None:
                rows.append(_row(where, label, "Rule existed", "Removed"))
                continue
            if xb.get("is_hard", True) != xa.get("is_hard", True):
                rows.append(_row(where, f"{label} · strictness",
                                 "Must pass" if xb.get("is_hard", True) else "Check only",
                                 "Must pass" if xa.get("is_hard", True) else "Check only"))
            pb, pa = xb.get("params", {}), xa.get("params", {})
            for param in list(pb) + [p for p in pa if p not in pb]:
                vb, va = pb.get(param), pa.get(param)
                if vb == va or (vb in (None, [], "") and va in (None, [], "")):
                    continue
                if param != "one_of" and isinstance(vb, list) and isinstance(va, list):
                    # Lists: show only what was taken out and what was put in.
                    removed = [x for x in vb if x not in va]
                    added = [x for x in va if x not in vb]
                    rows.append(_row(
                        where, f"{label} · {PARAM_LABELS.get(param, _title(param))}",
                        f"Removed: {_value(param, removed, vocab)}" if removed else "Nothing removed",
                        f"Added: {_value(param, added, vocab)}" if added else "Nothing added"))
                    continue
                rows.append(_row(where, f"{label} · {PARAM_LABELS.get(param, _title(param))}",
                                 _value(param, vb, vocab), _value(param, va, vocab)))
    return rows


def describe_changes(kind: str, before: Any, after: Any, vocab: Vocabulary,
                     names: dict | None = None) -> list[dict]:
    """`names` maps ids (sources, cities) to readable names."""
    before = before or ([] if kind != "update" else {})
    if kind == "update":
        return _fields(before, after, vocab, names)
    if kind == "fees":
        return _fees(before, after)
    if kind == "tests":
        return _tests(before, after, vocab)
    if kind == "deadlines":
        return _deadlines(before, after)
    if kind == "rules":
        return _rules(before, after, vocab)
    return []
