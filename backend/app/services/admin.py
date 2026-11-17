"""Admin data management: edits, the four-eyes review workflow, and the rule test panel.

How edits work (docs/ADMIN_PANEL_PLAN.md § 3.9):
  * A record that is NOT published yet (draft) is edited directly.
    Staff then submit it for review; a different person approves it -> published.
  * A record that IS published is never changed directly. The edit becomes a
    ChangeRequest. Students keep seeing the published version until a different
    staff member approves the change.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from ..engine.rules import RuleValidationError, validate_rule
from ..engine.types import QualificationInput, ResultStatus, StudentInput

ENTITY_MODELS: dict[str, type] = {
    "university": m.University,
    "campus": m.Campus,
    "programme": m.Programme,
    "hostel": m.Hostel,
    "offering": m.Offering,
}

EDITABLE_FIELDS = {
    "university": ["name", "short_name", "aliases", "sector", "hec_recognised", "gender_policy",
                   "website_url", "admissions_url", "description", "source_id"],
    "campus": ["name", "is_main_campus", "city_id", "address", "latitude", "longitude",
               "gender_policy", "source_id"],
    "programme": ["discipline_code", "title", "degree_type", "duration_years",
                  "total_credit_hours", "shift", "accreditation_body", "accreditation_status",
                  "programme_url", "source_id"],
    "hostel": ["for_gender", "location", "availability", "fee_per_semester_pkr", "notes",
               "source_id"],
    "offering": ["is_offered", "seats_total", "notes", "source_id"],
}

OFFERING_PARTS = ("fees", "tests", "deadlines", "rules")


def _now() -> datetime:
    return m.now()


def audit(db: Session, actor: m.User, action: str, entity_type: str, entity_id: str | None,
          before: Any = None, after: Any = None) -> None:
    db.add(m.AuditLog(actor_id=actor.id, action=action, entity_type=entity_type,
                      entity_id=entity_id, before=_json(before), after=_json(after)))


def _json(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json(v) for v in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def get_entity(db: Session, entity_type: str, entity_id: str):
    model = ENTITY_MODELS.get(entity_type)
    if model is None:
        raise HTTPException(404, "Unknown record type.")
    obj = db.get(model, entity_id)
    if obj is None:
        raise HTTPException(404, "This record could not be found.")
    return obj


# ------------------------------------------------------------------ snapshots


def snapshot(entity_type: str, obj) -> dict:
    return {f: _json(getattr(obj, f)) for f in EDITABLE_FIELDS[entity_type]}


def offering_part(offering: m.Offering, part: str) -> list:
    if part == "fees":
        return [{"component": f.component, "amount_pkr": f.amount_pkr, "basis": f.basis,
                 "applies_to": f.applies_to, "is_estimated": f.is_estimated}
                for f in offering.fees]
    if part == "tests":
        return [{"test_code": t.test_code, "is_mandatory": t.is_mandatory} for t in offering.entry_tests]
    if part == "deadlines":
        return [{"event": d.event, "date": d.date.isoformat(), "is_tentative": d.is_tentative}
                for d in offering.deadlines]
    if part == "rules":
        return [{"name": rs.name,
                 "rules": [{"rule_type": r.rule_type, "params": r.params, "is_hard": r.is_hard}
                           for r in rs.rules]}
                for rs in offering.rule_sets]
    raise HTTPException(404, "Unknown offering section.")


# ------------------------------------------------------------------ validation


def validate_rule_sets(rule_sets: list[dict]) -> list[dict]:
    cleaned = []
    for i, rs in enumerate(rule_sets, start=1):
        name = (rs.get("name") or "").strip()
        if not name:
            raise HTTPException(422, f"Rule group {i} needs a name, e.g. \"For ICS students\".")
        rules = []
        for j, r in enumerate(rs.get("rules", []), start=1):
            try:
                params = validate_rule(r["rule_type"], r.get("params", {}))
            except RuleValidationError as exc:
                raise HTTPException(
                    422, f"{name}, rule {j} ({r.get('rule_type')}): {exc}") from None
            rules.append({"rule_type": r["rule_type"], "params": params,
                          "is_hard": bool(r.get("is_hard", True))})
        if not rules:
            raise HTTPException(422, f"Rule group \"{name}\" has no rules.")
        cleaned.append({"name": name, "rules": rules})
    return cleaned


# ------------------------------------------------------------------ apply


def apply_fields(entity_type: str, obj, payload: dict) -> None:
    for field in EDITABLE_FIELDS[entity_type]:
        if field in payload:
            setattr(obj, field, payload[field])


def apply_offering_part(db: Session, offering: m.Offering, part: str, payload: list) -> None:
    if part == "fees":
        offering.fees.clear()
        db.flush()
        for f in payload:
            offering.fees.append(m.OfferingFee(**f))
    elif part == "tests":
        offering.entry_tests.clear()
        db.flush()
        for t in payload:
            offering.entry_tests.append(m.OfferingEntryTest(**t))
    elif part == "deadlines":
        offering.deadlines.clear()
        db.flush()
        for d in payload:
            offering.deadlines.append(m.OfferingDeadline(
                event=d["event"], date=date.fromisoformat(str(d["date"])),
                is_tentative=d.get("is_tentative", False)))
    elif part == "rules":
        offering.rule_sets.clear()
        db.flush()
        for priority, rs in enumerate(payload):
            row = m.RuleSetRow(name=rs["name"], priority=priority)
            offering.rule_sets.append(row)
            for r in rs["rules"]:
                row.rules.append(m.RuleRow(rule_type=r["rule_type"], params=r["params"],
                                           is_hard=r["is_hard"], source_id=offering.source_id))


def edit(db: Session, user: m.User, entity_type: str, obj, kind: str, payload, summary: str) -> dict:
    """Apply an edit directly (unpublished record) or queue it for review (published)."""
    if obj.status == "archived":
        raise HTTPException(409, "This record is archived. Restore it before editing.")
    before = snapshot(entity_type, obj) if kind == "update" else offering_part(obj, kind)
    if obj.status == "published":
        pending = db.scalar(select(m.ChangeRequest).where(
            m.ChangeRequest.entity_type == entity_type, m.ChangeRequest.entity_id == obj.id,
            m.ChangeRequest.kind == kind, m.ChangeRequest.status == "pending"))
        if pending is not None:
            raise HTTPException(
                409, "A change to this section is already waiting for review. Ask a verifier "
                     "to approve or reject it first.")
        cr = m.ChangeRequest(entity_type=entity_type, entity_id=obj.id, kind=kind,
                             payload=_json(payload), before=before, author_id=user.id,
                             summary=summary[:300])
        db.add(cr)
        audit(db, user, "propose_change", entity_type, obj.id, before, payload)
        db.commit()
        return {"queued": True, "change_request_id": cr.id,
                "message": "Saved for review. Students will see this change after a verifier "
                           "approves it."}
    if kind == "update":
        apply_fields(entity_type, obj, payload)
    else:
        apply_offering_part(db, obj, kind, payload)
    obj.edited_by = user.id
    if obj.status == "pending_review":
        obj.status = "draft"  # edited again: needs a fresh submit
    audit(db, user, "update", entity_type, obj.id, before, payload)
    db.commit()
    return {"queued": False, "message": "Saved as draft."}


# ------------------------------------------------------------------ workflow


def _check_not_author(user: m.User, author_id: str | None) -> None:
    if author_id is not None and author_id == user.id:
        raise HTTPException(403, "You cannot approve your own change. Another staff member "
                                 "must review it.")


def submit(db: Session, user: m.User, entity_type: str, obj) -> None:
    if obj.status not in ("draft",):
        raise HTTPException(409, f"Only drafts can be submitted (this one is {obj.status}).")
    if obj.source_id is None:
        raise HTTPException(422, "Add an official source before submitting for review.")
    if entity_type == "offering" and not obj.rule_sets:
        raise HTTPException(422, "Add eligibility rules before submitting this programme for "
                                 "review.")
    obj.status = "pending_review"
    obj.edited_by = obj.edited_by or user.id
    audit(db, user, "submit", entity_type, obj.id)
    db.commit()


def approve_record(db: Session, user: m.User, entity_type: str, obj) -> None:
    if obj.status != "pending_review":
        raise HTTPException(409, "Only records waiting for review can be approved.")
    _check_not_author(user, obj.edited_by)
    source = db.get(m.Source, obj.source_id) if obj.source_id else None
    if source is None or not (source.is_official or source.kind == "demo"):
        raise HTTPException(422, "Only official sources can be published.")
    obj.status = "published"
    obj.verified_at = _now()
    obj.verified_by = user.id
    obj.review_note = None
    audit(db, user, "approve", entity_type, obj.id)
    db.commit()


def reject_record(db: Session, user: m.User, entity_type: str, obj, note: str) -> None:
    if obj.status != "pending_review":
        raise HTTPException(409, "Only records waiting for review can be rejected.")
    obj.status = "draft"
    obj.review_note = note
    audit(db, user, "reject", entity_type, obj.id, after={"note": note})
    db.commit()


def approve_change(db: Session, user: m.User, cr: m.ChangeRequest) -> None:
    if cr.status != "pending":
        raise HTTPException(409, "This change has already been reviewed.")
    _check_not_author(user, cr.author_id)
    obj = get_entity(db, cr.entity_type, cr.entity_id)
    if cr.kind == "update":
        apply_fields(cr.entity_type, obj, cr.payload)
    else:
        if cr.kind == "rules":
            validate_rule_sets(cr.payload)
        apply_offering_part(db, obj, cr.kind, cr.payload)
    obj.edited_by = cr.author_id
    obj.verified_at = _now()
    obj.verified_by = user.id
    cr.status = "approved"
    cr.reviewer_id = user.id
    audit(db, user, "approve_change", cr.entity_type, cr.entity_id, cr.before, cr.payload)
    db.commit()


def reject_change(db: Session, user: m.User, cr: m.ChangeRequest, note: str) -> None:
    if cr.status != "pending":
        raise HTTPException(409, "This change has already been reviewed.")
    cr.status = "rejected"
    cr.reviewer_id = user.id
    cr.review_note = note
    audit(db, user, "reject_change", cr.entity_type, cr.entity_id, after={"note": note})
    db.commit()


# ------------------------------------------------------------------ test panel

def _q(level, type_code, group, pct=None, subjects=(), **kw) -> QualificationInput:
    return QualificationInput(level=level, type_code=type_code, group_code=group,
                              percentage=pct, subjects=frozenset(subjects), **kw)


_SSC = _q("SSC", "MATRIC", "MATRIC_SCIENCE_BIO", 80.0, ("MATH", "PHY", "CHEM", "BIO", "ENG"))


def _student(gender: str, hssc: QualificationInput, level: str = "HSSC") -> StudentInput:
    return StudentInput(gender=gender, date_of_birth=date(2008, 1, 1), domicile_region="PB",
                        qualifications={"SSC": _SSC, level: hssc})


# Typical students used to check rules before they go live (ADMIN_PANEL_PLAN § 3.4).
SAMPLE_STUDENTS: list[tuple[str, StudentInput]] = [
    ("FSc Pre-Engineering, 75%, male",
     _student("male", _q("HSSC", "INTERMEDIATE", "PRE_ENGINEERING", 75.0,
                         ("MATH", "PHY", "CHEM", "ENG")))),
    ("FSc Pre-Engineering, 52%, female",
     _student("female", _q("HSSC", "INTERMEDIATE", "PRE_ENGINEERING", 52.0,
                           ("MATH", "PHY", "CHEM", "ENG")))),
    ("FSc Pre-Medical, 82%, female",
     _student("female", _q("HSSC", "INTERMEDIATE", "PRE_MEDICAL", 82.0,
                           ("BIO", "PHY", "CHEM", "ENG")))),
    ("ICS (Physics), 68%, male",
     _student("male", _q("HSSC", "INTERMEDIATE", "ICS", 68.0, ("MATH", "CS", "PHY", "ENG")))),
    ("ICS, Part-I only 70%, female",
     _student("female", _q("HSSC", "INTERMEDIATE", "ICS", None, ("MATH", "CS", "STAT", "ENG"),
                           result_status=ResultStatus.PART1_ONLY, part1_percentage=70.0))),
    ("I.Com, 65%, male",
     _student("male", _q("HSSC", "INTERMEDIATE", "ICOM", 65.0,
                         ("ACCT", "COMM", "ECON", "BMATH", "ENG")))),
    ("FA, 60%, female",
     _student("female", _q("HSSC", "INTERMEDIATE", "FA", 60.0, ("ENG", "PSY", "EDU")))),
    ("A-Levels (Maths, Physics), IBCC 80% estimated, male",
     _student("male", _q("HSSC", "A_LEVEL", "A_LEVEL", None, ("MATH", "PHY", "CHEM"),
                         ibcc_percentage=80.0))),
    ("DAE Electrical, 72%, male",
     _student("male", _q("DIPLOMA", "DAE", "DAE_ELECTRICAL", 72.0, ("MATH", "PHY", "CHEM")),
              level="DIPLOMA")),
]
