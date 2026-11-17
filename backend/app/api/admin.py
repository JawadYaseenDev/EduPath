"""Admin API used by the admin web panel (docs/ADMIN_PANEL_PLAN.md)."""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from .. import models as m
from ..db import get_db
from ..engine import RULE_TYPES, RuleValidationError, evaluate_offering, validate_rule
from ..engine.types import OfferingRules, Rule, RuleSet
from ..schemas import ResultModeIn, RuleCheckIn
from ..schemas_admin import (
    CampusCreate,
    CampusIn,
    CycleIn,
    DeadlineIn,
    FeeIn,
    HostelCreate,
    HostelIn,
    OfferingCreate,
    OfferingIn,
    ProgrammeCreate,
    ProgrammeIn,
    RejectIn,
    ReportStatusIn,
    RoleIn,
    RuleSetIn,
    RuleTestIn,
    SourceIn,
    StaffIn,
    TestIn,
    UniversityIn,
)
from ..security import hash_password, password_problem, require_role
from ..services import admin as svc
from ..services import catalogue
from ..services.change_summary import describe_changes
from ..services.profile import vocabulary

router = APIRouter(prefix="/v1/admin", tags=["admin"])
admin_only = require_role("super_admin")
data_staff = require_role("super_admin", "data_editor", "data_verifier")
verifiers = require_role("super_admin", "data_verifier")
any_staff = require_role("super_admin", "data_editor", "data_verifier", "support")

STAFF_ROLES = ("super_admin", "data_editor", "data_verifier", "support")


def _user_names(db: Session, ids) -> dict[str, str]:
    ids = {i for i in ids if i}
    if not ids:
        return {}
    return {u.id: u.email for u in db.scalars(select(m.User).where(m.User.id.in_(ids)))}


def _status(obj) -> dict:
    return {"status": obj.status, "verified_at": obj.verified_at.isoformat() if obj.verified_at else None,
            "edited_by": obj.edited_by, "review_note": obj.review_note, "source_id": obj.source_id}


def _pending(db: Session, entity_type: str, entity_id: str) -> list[dict]:
    rows = db.scalars(select(m.ChangeRequest).where(
        m.ChangeRequest.entity_type == entity_type, m.ChangeRequest.entity_id == entity_id,
        m.ChangeRequest.status == "pending")).all()
    return [{"id": r.id, "kind": r.kind, "summary": r.summary} for r in rows]


# ================================================================== dashboard


@router.get("/dashboard")
def dashboard(_: m.User = Depends(any_staff), db: Session = Depends(get_db)):
    cycle = catalogue.current_cycle(db)
    counts = {}
    for name, model in svc.ENTITY_MODELS.items():
        counts[name] = dict(db.execute(select(model.status, func.count()).group_by(model.status)).all())
    programmes = db.scalars(select(m.Programme).where(m.Programme.status != "archived")
                            .options(selectinload(m.Programme.offerings))).all()
    missing_current = [p for p in programmes
                       if not any(o.cycle_id == cycle.id for o in p.offerings)]
    pending_records = sum(c.get("pending_review", 0) for c in counts.values())
    pending_changes = db.scalar(select(func.count()).select_from(m.ChangeRequest)
                                .where(m.ChangeRequest.status == "pending"))
    new_reports = db.scalar(select(func.count()).select_from(m.DataReport)
                            .where(m.DataReport.status.in_(("new", "in_review"))))
    students = db.scalar(select(func.count()).select_from(m.User).where(m.User.role == "student"))
    runs = db.scalar(select(func.count()).select_from(m.RecommendationRun))
    return {
        "cycle": {"id": cycle.id, "label": cycle.label},
        "counts": counts,
        "programmes_without_current_offering": len(missing_current),
        "pending_reviews": pending_records + (pending_changes or 0),
        "open_reports": new_reports or 0,
        "students": students or 0,
        "recommendation_runs": runs or 0,
    }


# ================================================================== sources


@router.get("/sources")
def list_sources(_: m.User = Depends(data_staff), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.Source).order_by(m.Source.created_at.desc())).all()
    return [{"id": s.id, "kind": s.kind, "title": s.title, "url": s.url,
             "page_numbers": s.page_numbers, "publisher": s.publisher,
             "is_official": s.is_official} for s in rows]


@router.post("/sources", status_code=201)
def create_source(body: SourceIn, user: m.User = Depends(data_staff), db: Session = Depends(get_db)):
    source = m.Source(**body.model_dump(), retrieved_at=m.now())
    db.add(source)
    db.flush()
    svc.audit(db, user, "create", "source", source.id, after=body.model_dump())
    db.commit()
    return {"id": source.id}


# ================================================================== universities


@router.get("/universities")
def list_universities(q: str | None = None, status: str | None = None,
                      _: m.User = Depends(any_staff), db: Session = Depends(get_db)):
    stmt = select(m.University).options(selectinload(m.University.campuses)
                                        .selectinload(m.Campus.programmes))
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(m.University.name).like(like),
                              func.lower(m.University.short_name).like(like)))
    if status:
        stmt = stmt.where(m.University.status == status)
    unis = db.scalars(stmt.order_by(m.University.name)).unique().all()
    pending = Counter(db.scalars(select(m.ChangeRequest.entity_id)
                                 .where(m.ChangeRequest.status == "pending")).all())
    return [{
        "id": u.id, "name": u.name, "short_name": u.short_name, "sector": u.sector,
        "is_demo": u.is_demo, **_status(u),
        "campus_count": len(u.campuses),
        "programme_count": sum(len(c.programmes) for c in u.campuses),
        "pending_changes": pending.get(u.id, 0),
    } for u in unis]


@router.post("/universities", status_code=201)
def create_university(body: UniversityIn, user: m.User = Depends(data_staff),
                      db: Session = Depends(get_db)):
    uni = m.University(**body.model_dump(), status="draft", edited_by=user.id)
    db.add(uni)
    db.flush()
    svc.audit(db, user, "create", "university", uni.id, after=body.model_dump())
    db.commit()
    return {"id": uni.id}


@router.get("/universities/{university_id}")
def university_tree(university_id: str, _: m.User = Depends(any_staff),
                    db: Session = Depends(get_db)):
    uni = db.scalars(select(m.University).where(m.University.id == university_id).options(
        selectinload(m.University.campuses).selectinload(m.Campus.hostels),
        selectinload(m.University.campuses).selectinload(m.Campus.programmes)
        .selectinload(m.Programme.offerings).selectinload(m.Offering.cycle),
        selectinload(m.University.campuses).selectinload(m.Campus.city),
    )).first()
    if uni is None:
        raise HTTPException(404, "This university could not be found.")
    names = _user_names(db, [uni.edited_by])
    return {
        "id": uni.id, **svc.snapshot("university", uni), **_status(uni), "is_demo": uni.is_demo,
        "edited_by_email": names.get(uni.edited_by),
        "pending_changes": _pending(db, "university", uni.id),
        "campuses": [{
            "id": c.id, **svc.snapshot("campus", c), **_status(c), "city_name": c.city.name,
            "pending_changes": _pending(db, "campus", c.id),
            "hostels": [{"id": h.id, **svc.snapshot("hostel", h), **_status(h),
                         "pending_changes": _pending(db, "hostel", h.id)} for h in c.hostels],
            "programmes": [{
                "id": p.id, **svc.snapshot("programme", p), **_status(p),
                "pending_changes": _pending(db, "programme", p.id),
                "offerings": sorted([{
                    "id": o.id, "cycle_label": o.cycle.label, "cycle_year": o.cycle.year,
                    "is_offered": o.is_offered, **_status(o),
                    "pending_changes": len(_pending(db, "offering", o.id)),
                } for o in p.offerings], key=lambda o: -o["cycle_year"]),
            } for p in sorted(c.programmes, key=lambda p: p.title)],
        } for c in uni.campuses],
    }


@router.put("/universities/{university_id}")
def update_university(university_id: str, body: UniversityIn, user: m.User = Depends(data_staff),
                      db: Session = Depends(get_db)):
    uni = svc.get_entity(db, "university", university_id)
    return svc.edit(db, user, "university", uni, "update", body.model_dump(),
                    f"Update university details: {body.name}")


# ================================================================== campuses, hostels, programmes


@router.post("/campuses", status_code=201)
def create_campus(body: CampusCreate, user: m.User = Depends(data_staff),
                  db: Session = Depends(get_db)):
    svc.get_entity(db, "university", body.university_id)
    if not db.get(m.City, body.city_id):
        raise HTTPException(422, "Please choose a city from the list.")
    campus = m.Campus(**body.model_dump(), status="draft", edited_by=user.id)
    db.add(campus)
    db.flush()
    svc.audit(db, user, "create", "campus", campus.id, after=body.model_dump())
    db.commit()
    return {"id": campus.id}


@router.put("/campuses/{campus_id}")
def update_campus(campus_id: str, body: CampusIn, user: m.User = Depends(data_staff),
                  db: Session = Depends(get_db)):
    campus = svc.get_entity(db, "campus", campus_id)
    if not db.get(m.City, body.city_id):
        raise HTTPException(422, "Please choose a city from the list.")
    return svc.edit(db, user, "campus", campus, "update", body.model_dump(),
                    f"Update campus: {body.name}")


@router.post("/hostels", status_code=201)
def create_hostel(body: HostelCreate, user: m.User = Depends(data_staff),
                  db: Session = Depends(get_db)):
    svc.get_entity(db, "campus", body.campus_id)
    hostel = m.Hostel(**body.model_dump(), status="draft", edited_by=user.id)
    db.add(hostel)
    db.flush()
    svc.audit(db, user, "create", "hostel", hostel.id, after=body.model_dump())
    db.commit()
    return {"id": hostel.id}


@router.put("/hostels/{hostel_id}")
def update_hostel(hostel_id: str, body: HostelIn, user: m.User = Depends(data_staff),
                  db: Session = Depends(get_db)):
    hostel = svc.get_entity(db, "hostel", hostel_id)
    return svc.edit(db, user, "hostel", hostel, "update", body.model_dump(),
                    f"Update {body.for_gender} hostel")


def _check_discipline(db: Session, code: str) -> None:
    if not db.get(m.Discipline, code):
        raise HTTPException(422, "Please choose a programme discipline from the list.")


@router.post("/programmes", status_code=201)
def create_programme(body: ProgrammeCreate, user: m.User = Depends(data_staff),
                     db: Session = Depends(get_db)):
    svc.get_entity(db, "campus", body.campus_id)
    _check_discipline(db, body.discipline_code)
    programme = m.Programme(**body.model_dump(), status="draft", edited_by=user.id)
    db.add(programme)
    db.flush()
    svc.audit(db, user, "create", "programme", programme.id, after=body.model_dump())
    db.commit()
    return {"id": programme.id}


@router.put("/programmes/{programme_id}")
def update_programme(programme_id: str, body: ProgrammeIn, user: m.User = Depends(data_staff),
                     db: Session = Depends(get_db)):
    programme = svc.get_entity(db, "programme", programme_id)
    _check_discipline(db, body.discipline_code)
    return svc.edit(db, user, "programme", programme, "update", body.model_dump(),
                    f"Update programme: {body.title}")


# ================================================================== offerings


def _copy_offering(db: Session, src: m.Offering, dst: m.Offering) -> None:
    for part in svc.OFFERING_PARTS:
        svc.apply_offering_part(db, dst, part, svc.offering_part(src, part))
    dst.seats_total = src.seats_total
    dst.notes = src.notes
    dst.source_id = None  # must be re-checked against this year's prospectus
    dst.carried_from_cycle_id = src.cycle_id


@router.post("/offerings", status_code=201)
def create_offering(body: OfferingCreate, user: m.User = Depends(data_staff),
                    db: Session = Depends(get_db)):
    programme = svc.get_entity(db, "programme", body.programme_id)
    cycle = catalogue.current_cycle(db)
    if any(o.cycle_id == cycle.id for o in programme.offerings):
        raise HTTPException(409, f"This programme already has a {cycle.label} offering.")
    offering = m.Offering(programme_id=programme.id, cycle_id=cycle.id, status="draft",
                          edited_by=user.id)
    db.add(offering)
    db.flush()
    previous = sorted((o for o in programme.offerings if o.id != offering.id),
                      key=lambda o: o.cycle.year, reverse=True)
    if body.copy_from_previous and previous:
        _copy_offering(db, previous[0], offering)
    svc.audit(db, user, "create", "offering", offering.id,
              after={"programme_id": programme.id, "cycle": cycle.label,
                     "copied_from": previous[0].id if body.copy_from_previous and previous else None})
    db.commit()
    return {"id": offering.id}


@router.get("/offerings/{offering_id}")
def offering_detail(offering_id: str, _: m.User = Depends(any_staff),
                    db: Session = Depends(get_db)):
    o = svc.get_entity(db, "offering", offering_id)
    p = o.programme
    names = _user_names(db, [o.edited_by])
    return {
        "id": o.id, **svc.snapshot("offering", o), **_status(o),
        "edited_by_email": names.get(o.edited_by),
        "cycle_label": o.cycle.label,
        "carried_from_cycle_id": o.carried_from_cycle_id,
        "programme": {"id": p.id, "title": p.title, "status": p.status,
                      "duration_years": p.duration_years,
                      "total_credit_hours": p.total_credit_hours},
        "campus": {"id": p.campus.id, "name": p.campus.name, "status": p.campus.status,
                   "gender_policy": p.campus.effective_gender_policy},
        "university": {"id": p.campus.university.id, "name": p.campus.university.name,
                       "status": p.campus.university.status},
        **{part: svc.offering_part(o, part) for part in svc.OFFERING_PARTS},
        "fee_summary": {k: v for k, v in catalogue.fee_summary(o).items() if k != "items"},
        "pending_changes": [{**c, **_change_detail(db, c["id"])}
                            for c in _pending(db, "offering", o.id)],
    }


def _id_names(db: Session) -> dict[str, str]:
    names = {s.id: s.title for s in db.scalars(select(m.Source))}
    names.update({c.id: c.name for c in db.scalars(select(m.City))})
    return names


def _differences(db: Session, cr: m.ChangeRequest, vocab=None, names=None) -> list[dict]:
    return describe_changes(cr.kind, cr.before, cr.payload, vocab or vocabulary(db),
                            names if names is not None else _id_names(db))


def _change_detail(db: Session, change_id: str) -> dict:
    cr = db.get(m.ChangeRequest, change_id)
    return {"payload": cr.payload, "before": cr.before, "differences": _differences(db, cr)}


@router.put("/offerings/{offering_id}")
def update_offering(offering_id: str, body: OfferingIn, user: m.User = Depends(data_staff),
                    db: Session = Depends(get_db)):
    o = svc.get_entity(db, "offering", offering_id)
    return svc.edit(db, user, "offering", o, "update", body.model_dump(),
                    f"Update {o.programme.title} ({o.cycle.label}) details")


@router.put("/offerings/{offering_id}/fees")
def update_fees(offering_id: str, body: list[FeeIn], user: m.User = Depends(data_staff),
                db: Session = Depends(get_db)):
    o = svc.get_entity(db, "offering", offering_id)
    return svc.edit(db, user, "offering", o, "fees", [f.model_dump() for f in body],
                    f"Update fees for {o.programme.title} ({o.cycle.label})")


@router.put("/offerings/{offering_id}/tests")
def update_tests(offering_id: str, body: list[TestIn], user: m.User = Depends(data_staff),
                 db: Session = Depends(get_db)):
    o = svc.get_entity(db, "offering", offering_id)
    known = set(db.scalars(select(m.EntryTest.code)))
    if any(t.test_code not in known for t in body):
        raise HTTPException(422, "Please choose entry tests from the list.")
    return svc.edit(db, user, "offering", o, "tests", [t.model_dump() for t in body],
                    f"Update entry tests for {o.programme.title} ({o.cycle.label})")


@router.put("/offerings/{offering_id}/deadlines")
def update_deadlines(offering_id: str, body: list[DeadlineIn], user: m.User = Depends(data_staff),
                     db: Session = Depends(get_db)):
    o = svc.get_entity(db, "offering", offering_id)
    return svc.edit(db, user, "offering", o, "deadlines",
                    [d.model_dump(mode="json") for d in body],
                    f"Update dates for {o.programme.title} ({o.cycle.label})")


@router.put("/offerings/{offering_id}/rules")
def update_rules(offering_id: str, body: list[RuleSetIn], user: m.User = Depends(data_staff),
                 db: Session = Depends(get_db)):
    o = svc.get_entity(db, "offering", offering_id)
    cleaned = svc.validate_rule_sets([rs.model_dump() for rs in body])
    return svc.edit(db, user, "offering", o, "rules", cleaned,
                    f"Update eligibility rules for {o.programme.title} ({o.cycle.label})")


@router.post("/rules/test")
def test_rules(body: RuleTestIn, _: m.User = Depends(data_staff), db: Session = Depends(get_db)):
    """Run (possibly unsaved) rule groups against typical students."""
    cleaned = svc.validate_rule_sets([rs.model_dump() for rs in body.rule_sets])
    rules = OfferingRules(
        offering_id="test",
        rule_sets=[RuleSet(None, rs["name"], [Rule(None, r["rule_type"], r["params"], r["is_hard"])
                                               for r in rs["rules"]]) for rs in cleaned],
        campus_gender_policy=body.campus_gender_policy,
    )
    vocab = vocabulary(db)
    out = []
    for label, student in svc.SAMPLE_STUDENTS:
        result = evaluate_offering(rules, student, vocab)
        out.append({
            "student": label,
            "category": result.category.value if result else None,
            "rule_set_name": result.rule_set_name if result else None,
            "reasons": [r.message for r in result.rule_results if r.outcome.value != "pass"]
            if result else [],
        })
    return out


# ================================================================== review workflow


@router.post("/records/{entity_type}/{entity_id}/submit")
def submit_record(entity_type: str, entity_id: str, user: m.User = Depends(data_staff),
                  db: Session = Depends(get_db)):
    svc.submit(db, user, entity_type, svc.get_entity(db, entity_type, entity_id))
    return {"ok": True, "message": "Submitted for review."}


@router.post("/records/{entity_type}/{entity_id}/approve")
def approve_record(entity_type: str, entity_id: str, user: m.User = Depends(verifiers),
                   db: Session = Depends(get_db)):
    svc.approve_record(db, user, entity_type, svc.get_entity(db, entity_type, entity_id))
    return {"ok": True, "message": "Approved and published."}


@router.post("/records/{entity_type}/{entity_id}/reject")
def reject_record(entity_type: str, entity_id: str, body: RejectIn,
                  user: m.User = Depends(verifiers), db: Session = Depends(get_db)):
    svc.reject_record(db, user, entity_type, svc.get_entity(db, entity_type, entity_id), body.note)
    return {"ok": True, "message": "Sent back to draft."}


@router.post("/records/{entity_type}/{entity_id}/archive")
def archive_record(entity_type: str, entity_id: str, user: m.User = Depends(data_staff),
                   db: Session = Depends(get_db)):
    obj = svc.get_entity(db, entity_type, entity_id)
    before = obj.status
    obj.status = "archived"
    svc.audit(db, user, "archive", entity_type, entity_id, {"status": before}, {"status": "archived"})
    db.commit()
    return {"ok": True, "message": "Archived. It is no longer shown to students."}


@router.post("/records/{entity_type}/{entity_id}/restore")
def restore_record(entity_type: str, entity_id: str, user: m.User = Depends(data_staff),
                   db: Session = Depends(get_db)):
    obj = svc.get_entity(db, entity_type, entity_id)
    if obj.status != "archived":
        raise HTTPException(409, "Only archived records can be restored.")
    obj.status = "draft"
    obj.edited_by = user.id
    svc.audit(db, user, "restore", entity_type, entity_id)
    db.commit()
    return {"ok": True, "message": "Restored as a draft."}


def _record_label(db: Session, entity_type: str, obj) -> str:
    if entity_type == "university":
        return obj.name
    if entity_type == "campus":
        return f"{obj.university.name} - {obj.name}"
    if entity_type == "programme":
        return f"{obj.title} - {obj.campus.university.name}"
    if entity_type == "hostel":
        return f"{obj.for_gender.title()} hostel - {obj.campus.university.name}, {obj.campus.name}"
    return f"{obj.programme.title} ({obj.cycle.label}) - {obj.programme.campus.university.name}"


@router.get("/review")
def review_queue(_: m.User = Depends(any_staff), db: Session = Depends(get_db)):
    records = []
    for entity_type, model in svc.ENTITY_MODELS.items():
        for obj in db.scalars(select(model).where(model.status == "pending_review")):
            records.append({"entity_type": entity_type, "entity_id": obj.id,
                            "label": _record_label(db, entity_type, obj),
                            "edited_by": obj.edited_by,
                            "updated_at": obj.updated_at.isoformat()})
    changes = db.scalars(select(m.ChangeRequest).where(m.ChangeRequest.status == "pending")
                         .order_by(m.ChangeRequest.created_at)).all()
    names = _user_names(db, [r["edited_by"] for r in records] + [c.author_id for c in changes])
    vocab = vocabulary(db)
    id_names = _id_names(db)
    for r in records:
        r["edited_by_email"] = names.get(r["edited_by"])
    return {
        "records": records,
        "changes": [{
            "id": c.id, "entity_type": c.entity_type, "entity_id": c.entity_id, "kind": c.kind,
            "summary": c.summary, "author_id": c.author_id,
            "author_email": names.get(c.author_id),
            "created_at": c.created_at.isoformat(), "before": c.before, "payload": c.payload,
            "differences": _differences(db, c, vocab, id_names),
            "label": _record_label(db, c.entity_type, svc.get_entity(db, c.entity_type, c.entity_id)),
        } for c in changes],
    }


@router.post("/changes/{change_id}/approve")
def approve_change(change_id: str, user: m.User = Depends(verifiers),
                   db: Session = Depends(get_db)):
    cr = db.get(m.ChangeRequest, change_id)
    if cr is None:
        raise HTTPException(404, "This change could not be found.")
    svc.approve_change(db, user, cr)
    return {"ok": True, "message": "Change approved. Students now see the new information."}


@router.post("/changes/{change_id}/reject")
def reject_change(change_id: str, body: RejectIn, user: m.User = Depends(verifiers),
                  db: Session = Depends(get_db)):
    cr = db.get(m.ChangeRequest, change_id)
    if cr is None:
        raise HTTPException(404, "This change could not be found.")
    svc.reject_change(db, user, cr, body.note)
    return {"ok": True, "message": "Change rejected."}


# ================================================================== cycles


@router.get("/cycles")
def list_cycles(_: m.User = Depends(any_staff), db: Session = Depends(get_db)):
    return [{"id": c.id, "year": c.year, "label": c.label, "is_current": c.is_current}
            for c in db.scalars(select(m.AdmissionCycle).order_by(m.AdmissionCycle.year.desc()))]


@router.post("/cycles", status_code=201)
def create_cycle(body: CycleIn, user: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    if db.scalar(select(m.AdmissionCycle).where(m.AdmissionCycle.year == body.year)):
        raise HTTPException(409, "An admission cycle for this year already exists.")
    cycle = m.AdmissionCycle(year=body.year, label=body.label)
    db.add(cycle)
    db.flush()
    svc.audit(db, user, "create", "admission_cycle", cycle.id, after=body.model_dump())
    db.commit()
    return {"id": cycle.id}


@router.put("/cycles/{cycle_id}/current")
def set_current_cycle(cycle_id: str, user: m.User = Depends(admin_only),
                      db: Session = Depends(get_db)):
    target = db.get(m.AdmissionCycle, cycle_id)
    if target is None:
        raise HTTPException(404, "This admission cycle could not be found.")
    for c in db.scalars(select(m.AdmissionCycle)):
        c.is_current = c.id == target.id
    svc.audit(db, user, "set_current", "admission_cycle", target.id)
    db.commit()
    return {"ok": True}


# ================================================================== reports, audit, staff, settings


@router.get("/reports")
def list_reports(status: str | None = None, _: m.User = Depends(any_staff),
                 db: Session = Depends(get_db)):
    stmt = select(m.DataReport).order_by(m.DataReport.created_at.desc())
    if status:
        stmt = stmt.where(m.DataReport.status == status)
    rows = db.scalars(stmt).all()
    labels = {}
    for r in rows:
        try:
            obj = svc.get_entity(db, r.entity_type, r.entity_id)
            labels[r.id] = _record_label(db, r.entity_type, obj)
        except HTTPException:
            labels[r.id] = "(deleted record)"
    return [{"id": r.id, "entity_type": r.entity_type, "entity_id": r.entity_id,
             "label": labels[r.id], "field": r.field, "message": r.message, "status": r.status,
             "created_at": r.created_at.isoformat()} for r in rows]


@router.put("/reports/{report_id}")
def update_report(report_id: str, body: ReportStatusIn, user: m.User = Depends(any_staff),
                  db: Session = Depends(get_db)):
    report = db.get(m.DataReport, report_id)
    if report is None:
        raise HTTPException(404, "This report could not be found.")
    before = report.status
    report.status = body.status
    svc.audit(db, user, "update", "data_report", report.id, {"status": before}, {"status": body.status})
    db.commit()
    return {"ok": True}


@router.get("/audit")
def audit_log(limit: int = Query(default=100, le=500), entity_id: str | None = None,
              _: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    stmt = select(m.AuditLog).order_by(m.AuditLog.at.desc()).limit(limit)
    if entity_id:
        stmt = stmt.where(m.AuditLog.entity_id == entity_id)
    rows = db.scalars(stmt).all()
    names = _user_names(db, [r.actor_id for r in rows])
    return [{"id": r.id, "at": r.at.isoformat(), "actor": names.get(r.actor_id, r.actor_id),
             "action": r.action, "entity_type": r.entity_type, "entity_id": r.entity_id,
             "before": r.before, "after": r.after} for r in rows]


@router.get("/staff")
def list_staff(_: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.User).where(m.User.role.in_(STAFF_ROLES)).order_by(m.User.email))
    return [{"id": u.id, "email": u.email, "role": u.role, "is_active": u.is_active} for u in rows]


@router.post("/staff", status_code=201)
def create_staff(body: StaffIn, user: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    problem = password_problem(body.password)
    if problem:
        raise HTTPException(422, problem)
    if db.scalar(select(m.User).where(func.lower(m.User.email) == body.email.lower())):
        raise HTTPException(409, "An account with this email already exists.")
    staff = m.User(email=body.email.lower(), password_hash=hash_password(body.password),
                   role=body.role, email_verified=True)
    db.add(staff)
    db.flush()
    svc.audit(db, user, "create", "staff", staff.id, after={"email": staff.email, "role": body.role})
    db.commit()
    return {"id": staff.id}


@router.put("/users/{user_id}/role")
def set_role(user_id: str, body: RoleIn, user: m.User = Depends(admin_only),
             db: Session = Depends(get_db)):
    target = db.get(m.User, user_id)
    if target is None:
        raise HTTPException(404, "This user could not be found.")
    if target.id == user.id:
        raise HTTPException(409, "You cannot change your own role.")
    before = target.role
    target.role = body.role
    target.token_version += 1  # sign them out so the new role applies immediately
    svc.audit(db, user, "set_role", "user", target.id, {"role": before}, {"role": body.role})
    db.commit()
    return {"ok": True}


@router.get("/rule-types")
def rule_types(_: m.User = Depends(data_staff)):
    return {name: model.model_json_schema() for name, (model, _e) in RULE_TYPES.items()}


@router.post("/rules/validate")
def check_rule(body: RuleCheckIn, _: m.User = Depends(data_staff)):
    try:
        return {"valid": True, "params": validate_rule(body.rule_type, body.params)}
    except RuleValidationError as exc:
        raise HTTPException(422, str(exc)) from None


@router.get("/settings/result-mode")
def get_result_mode(_: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    setting = db.get(m.AppSetting, "result_mode")
    return setting.value if setting else {"mode": "extended"}


@router.put("/settings/result-mode")
def set_result_mode(body: ResultModeIn, user: m.User = Depends(admin_only),
                    db: Session = Depends(get_db)):
    setting = db.get(m.AppSetting, "result_mode")
    before = dict(setting.value) if setting else None
    if setting is None:
        setting = m.AppSetting(key="result_mode", value={})
        db.add(setting)
    setting.value = {"mode": body.mode}
    svc.audit(db, user, "update", "app_setting", None, before, setting.value)
    db.commit()
    return setting.value
