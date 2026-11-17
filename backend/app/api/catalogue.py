from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models as m
from ..db import get_db
from ..engine import evaluate_offering
from ..schemas import ReportIn
from ..security import current_user
from ..services import catalogue as svc
from ..services import profile as profile_service

router = APIRouter(prefix="/v1", tags=["catalogue"])


def _matches_text(card: dict, q: str) -> bool:
    q = q.lower().strip()
    hay = " ".join(str(card[k] or "") for k in (
        "programme_title", "university_name", "university_short_name", "city", "campus_name"
    )).lower()
    return all(word in hay for word in q.split())


@router.get("/programmes")
def search_programmes(
    q: str | None = Query(default=None, max_length=100),
    field: list[str] = Query(default=[]),
    discipline: list[str] = Query(default=[]),
    region: list[str] = Query(default=[]),
    city_id: list[str] = Query(default=[]),
    sector: list[str] = Query(default=[]),
    max_fee: int | None = Query(default=None, ge=0),
    hostel_for: str | None = Query(default=None, pattern="^(male|female)$"),
    entry_test: str | None = None,
    accredited_only: bool = False,
    university_id: str | None = None,
    sort: str = Query(default="name", pattern="^(name|fee)$"),
    db: Session = Depends(get_db),
):
    """Search and filter programmes (FR-05). Works without logging in."""
    cycle = svc.current_cycle(db)
    cards = [svc.offering_card(o, cycle) for o in svc.live_offerings(db)]
    out = []
    for c in cards:
        if q and not _matches_text(c, q):
            continue
        if field and c["field_code"] not in field:
            continue
        if discipline and c["discipline_code"] not in discipline:
            continue
        if region and c["region_code"] not in region:
            continue
        if sector and c["sector"] not in sector:
            continue
        if max_fee is not None and (c["charges_per_semester"] is None
                                    or c["charges_per_semester"] > max_fee):
            continue
        if hostel_for and hostel_for not in c["hostel_for"]:
            continue
        if entry_test and entry_test not in c["entry_tests"]:
            continue
        if accredited_only and c["accreditation_status"] != "accredited":
            continue
        if university_id and c["university_id"] != university_id:
            continue
        out.append(c)
    if city_id:
        city_names = {c.name for c in (db.get(m.City, cid) for cid in city_id) if c}
        out = [c for c in out if c["city"] in city_names]
    if sort == "fee":
        out.sort(key=lambda c: (c["charges_per_semester"] is None,
                                c["charges_per_semester"] or 0))
    else:
        out.sort(key=lambda c: (c["university_name"], c["programme_title"]))
    return {"count": len(out), "results": out}


@router.get("/offerings/{offering_id}")
def offering_detail(offering_id: str, db: Session = Depends(get_db)):
    offering = svc.get_offering(db, offering_id)
    if offering is None:
        raise HTTPException(404, "This programme could not be found.")
    return svc.offering_detail(db, offering, svc.current_cycle(db))


@router.get("/offerings/{offering_id}/my-eligibility")
def my_eligibility(offering_id: str, user: m.User = Depends(current_user),
                   db: Session = Depends(get_db)):
    """Check one programme against the student's profile ("Check my eligibility")."""
    offering = svc.get_offering(db, offering_id)
    if offering is None:
        raise HTTPException(404, "This programme could not be found.")
    profile = profile_service.get_or_create_profile(db, user)
    result = evaluate_offering(svc.to_rules(offering, svc.current_cycle(db)),
                               profile_service.student_input(db, profile),
                               profile_service.vocabulary(db))
    if result is None:
        return {"category": None, "message": "Eligibility details are not available yet.",
                "rule_outcomes": [], "next_steps": []}
    return {
        "category": result.category.value,
        "rule_set_name": result.rule_set_name,
        "rule_outcomes": [{"type": r.rule_type, "outcome": r.outcome.value,
                           "message": r.message, "is_hard": r.is_hard}
                          for r in result.rule_results],
        "next_steps": result.next_steps,
    }


@router.get("/universities")
def list_universities(db: Session = Depends(get_db)):
    return [{
        "id": u.id, "name": u.name, "short_name": u.short_name, "sector": u.sector,
        "is_demo": u.is_demo, "gender_policy": u.gender_policy,
        "cities": sorted({c.city.name for c in u.campuses}),
    } for u in svc.universities(db)]


@router.get("/universities/{university_id}")
def university_detail(university_id: str, db: Session = Depends(get_db)):
    uni = next((u for u in svc.universities(db) if u.id == university_id), None)
    if uni is None:
        raise HTTPException(404, "This university could not be found.")
    cycle = svc.current_cycle(db)
    cards = [svc.offering_card(o, cycle) for o in svc.live_offerings(db)
             if o.programme.campus.university_id == uni.id]
    return {
        "id": uni.id, "name": uni.name, "short_name": uni.short_name, "sector": uni.sector,
        "is_demo": uni.is_demo, "gender_policy": uni.gender_policy,
        "hec_recognised": uni.hec_recognised, "description": uni.description,
        "website_url": uni.website_url, "admissions_url": uni.admissions_url,
        "verified_at": uni.verified_at.date().isoformat() if uni.verified_at else None,
        "campuses": [{
            "id": c.id, "name": c.name, "city": c.city.name, "region_code": c.city.region_code,
            "gender_policy": c.effective_gender_policy,
            "hostels": [{"for_gender": h.for_gender, "location": h.location,
                         "availability": h.availability,
                         "fee_per_semester_pkr": h.fee_per_semester_pkr}
                        for h in c.hostels if h.status == svc.LIVE],
        } for c in uni.campuses if c.status == svc.LIVE],
        "programmes": sorted(cards, key=lambda c: c["programme_title"]),
    }


@router.post("/reports", status_code=201)
def report_error(body: ReportIn, user: m.User = Depends(current_user),
                 db: Session = Depends(get_db)):
    """'Report incorrect information' button (REC-12)."""
    db.add(m.DataReport(user_id=user.id, **body.model_dump()))
    db.commit()
    return {"ok": True, "message": "Thank you. Our team will check this information."}
