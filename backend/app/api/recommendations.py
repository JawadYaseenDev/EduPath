from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .. import models as m
from ..db import get_db
from ..schemas import ShortlistIn
from ..security import current_user
from ..services import catalogue
from ..services import profile as profile_service
from ..services import recommendations as svc

router = APIRouter(prefix="/v1", tags=["recommendations"])


@router.post("/recommendations/run")
def run_recommendations(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    profile = profile_service.get_or_create_profile(db, user)
    status = profile_service.completeness(db, profile)
    if not status["ready_for_recommendations"]:
        raise HTTPException(
            422,
            "Please complete your personal details and Intermediate / A-Level / DAE record "
            "first.",
        )
    run = svc.run_for_student(db, user)
    return svc.run_payload(db, run, profile)


@router.get("/recommendations/latest")
def latest(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    run = svc.latest_run(db, user)
    if run is None:
        return None
    return svc.run_payload(db, run, profile_service.get_or_create_profile(db, user))


# --------------------------------------------------------------- shortlist (FR-06)


def _shortlist_payload(db: Session, user: m.User) -> list[dict]:
    cycle = catalogue.current_cycle(db)
    ids = db.scalars(select(m.Shortlist.offering_id).where(m.Shortlist.user_id == user.id)
                     .order_by(m.Shortlist.created_at.desc())).all()
    latest_run = svc.latest_run(db, user)
    categories: dict[str, str] = {}
    if latest_run:
        for r in db.scalars(select(m.RecommendationResultRow)
                            .where(m.RecommendationResultRow.run_id == latest_run.id)):
            categories[r.offering_id] = r.category
    out = []
    for oid in ids:
        offering = catalogue.get_offering(db, oid)
        if offering is None:
            continue
        out.append({**catalogue.offering_card(offering, cycle),
                    "category": categories.get(oid)})
    return out


@router.get("/shortlist")
def get_shortlist(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    return _shortlist_payload(db, user)


@router.post("/shortlist", status_code=201)
def add_to_shortlist(body: ShortlistIn, user: m.User = Depends(current_user),
                     db: Session = Depends(get_db)):
    if catalogue.get_offering(db, body.offering_id) is None:
        raise HTTPException(404, "This programme could not be found.")
    exists = db.scalar(select(m.Shortlist).where(m.Shortlist.user_id == user.id,
                                                 m.Shortlist.offering_id == body.offering_id))
    if not exists:
        db.add(m.Shortlist(user_id=user.id, offering_id=body.offering_id))
        db.commit()
    return _shortlist_payload(db, user)


@router.delete("/shortlist/{offering_id}")
def remove_from_shortlist(offering_id: str, user: m.User = Depends(current_user),
                          db: Session = Depends(get_db)):
    db.execute(delete(m.Shortlist).where(m.Shortlist.user_id == user.id,
                                         m.Shortlist.offering_id == offering_id))
    db.commit()
    return _shortlist_payload(db, user)
