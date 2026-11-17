from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .. import models as m
from ..db import get_db
from ..schemas import PreferencesIn, ProfileIn, QualificationIn, TestScoreIn
from ..security import current_user
from ..services import profile as svc

router = APIRouter(prefix="/v1/profile", tags=["profile"])


def _qualification_out(q: m.StudentQualification) -> dict:
    return {
        "id": q.id, "level": q.level, "type_code": q.type_code, "group_code": q.group_code,
        "board_id": q.board_id, "passing_year": q.passing_year,
        "result_status": q.result_status, "obtained_marks": q.obtained_marks,
        "total_marks": q.total_marks, "percentage": svc.pct(q.obtained_marks, q.total_marks),
        "part1_obtained": q.part1_obtained, "part1_total": q.part1_total,
        "part1_percentage": svc.pct(q.part1_obtained, q.part1_total),
        "ibcc_percentage": q.ibcc_percentage, "ibcc_is_official": q.ibcc_is_official,
        "is_improved_result": q.is_improved_result, "subjects": q.subjects,
    }


def profile_payload(db: Session, profile: m.StudentProfile) -> dict:
    quals = db.scalars(select(m.StudentQualification)
                       .where(m.StudentQualification.user_id == profile.user_id)).all()
    scores = db.scalars(select(m.StudentTestScore)
                        .where(m.StudentTestScore.user_id == profile.user_id)).all()
    return {
        "full_name": profile.full_name, "phone": profile.phone, "gender": profile.gender,
        "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
        "current_city_id": profile.current_city_id,
        "domicile_region_code": profile.domicile_region_code,
        "qualifications": [_qualification_out(q) for q in quals],
        "test_scores": [{"id": s.id, "test_code": s.test_code, "year": s.year,
                         "score": s.score, "total": s.total} for s in scores],
        "preferences": {**svc.PREFERENCE_DEFAULTS, **(profile.preferences or {})},
        "completeness": svc.completeness(db, profile),
    }


def _touch(profile: m.StudentProfile) -> None:
    profile.data_changed_at = m.now()


@router.get("")
def get_profile(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    return profile_payload(db, svc.get_or_create_profile(db, user))


@router.put("")
def update_profile(body: ProfileIn, user: m.User = Depends(current_user),
                   db: Session = Depends(get_db)):
    profile = svc.get_or_create_profile(db, user)
    if body.current_city_id and not db.get(m.City, body.current_city_id):
        raise HTTPException(422, "Please choose a city from the list.")
    if body.domicile_region_code and not db.get(m.Region, body.domicile_region_code):
        raise HTTPException(422, "Please choose a province or region from the list.")
    for key, value in body.model_dump().items():
        setattr(profile, key, value)
    _touch(profile)
    db.commit()
    return profile_payload(db, profile)


@router.put("/qualifications")
def upsert_qualification(body: QualificationIn, user: m.User = Depends(current_user),
                         db: Session = Depends(get_db)):
    qtype = db.get(m.QualificationType, body.type_code)
    group = db.get(m.QualificationGroup, body.group_code)
    if qtype is None or group is None or group.type_code != qtype.code:
        raise HTTPException(422, "Please choose a valid qualification and group.")
    if body.board_id and not db.get(m.ExamBoard, body.board_id):
        raise HTTPException(422, "Please choose a board from the list.")
    known = set(db.scalars(select(m.Subject.code)))
    unknown = [s.code for s in body.subjects if s.code not in known]
    if unknown:
        raise HTTPException(422, f"Unknown subject: {', '.join(unknown)}")
    if not qtype.uses_ibcc:
        if body.result_status == "final" and (body.obtained_marks is None
                                              or body.total_marks is None):
            raise HTTPException(422, "Please enter your obtained and total marks.")
        if body.result_status == "part1_only" and (body.part1_obtained is None
                                                   or body.part1_total is None):
            raise HTTPException(422, "Please enter your Part-I obtained and total marks.")

    profile = svc.get_or_create_profile(db, user)
    q = db.scalar(select(m.StudentQualification).where(
        m.StudentQualification.user_id == user.id,
        m.StudentQualification.level == qtype.level))
    if q is None:
        q = m.StudentQualification(user_id=user.id, level=qtype.level)
        db.add(q)
    data = body.model_dump()
    data["subjects"] = [s.model_dump(exclude_none=True) for s in body.subjects]
    for key, value in data.items():
        setattr(q, key, value)
    _touch(profile)
    db.commit()
    return profile_payload(db, profile)


@router.delete("/qualifications/{level}")
def delete_qualification(level: str, user: m.User = Depends(current_user),
                         db: Session = Depends(get_db)):
    profile = svc.get_or_create_profile(db, user)
    db.execute(delete(m.StudentQualification).where(
        m.StudentQualification.user_id == user.id, m.StudentQualification.level == level))
    _touch(profile)
    db.commit()
    return profile_payload(db, profile)


@router.post("/test-scores")
def add_test_score(body: TestScoreIn, user: m.User = Depends(current_user),
                   db: Session = Depends(get_db)):
    if not db.get(m.EntryTest, body.test_code):
        raise HTTPException(422, "Please choose a test from the list.")
    profile = svc.get_or_create_profile(db, user)
    db.add(m.StudentTestScore(user_id=user.id, **body.model_dump()))
    _touch(profile)
    db.commit()
    return profile_payload(db, profile)


@router.delete("/test-scores/{score_id}")
def delete_test_score(score_id: str, user: m.User = Depends(current_user),
                      db: Session = Depends(get_db)):
    profile = svc.get_or_create_profile(db, user)
    db.execute(delete(m.StudentTestScore).where(m.StudentTestScore.id == score_id,
                                                m.StudentTestScore.user_id == user.id))
    _touch(profile)
    db.commit()
    return profile_payload(db, profile)


@router.put("/preferences")
def update_preferences(body: PreferencesIn, user: m.User = Depends(current_user),
                       db: Session = Depends(get_db)):
    regions = set(db.scalars(select(m.Region.code)))
    fields = set(db.scalars(select(m.ProgrammeField.code)))
    disciplines = set(db.scalars(select(m.Discipline.code)))
    if not set(body.regions) <= regions:
        raise HTTPException(422, "Unknown province or region.")
    if not set(body.fields) <= fields or not set(body.disciplines) <= disciplines:
        raise HTTPException(422, "Unknown field or programme.")
    profile = svc.get_or_create_profile(db, user)
    profile.preferences = body.model_dump()
    _touch(profile)
    db.commit()
    return profile_payload(db, profile)


account = APIRouter(prefix="/v1/account", tags=["account"])


@account.get("/export")
def export_data(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    """Everything we store about the student (privacy requirement AUTH-08)."""
    profile = svc.get_or_create_profile(db, user)
    shortlist = db.scalars(select(m.Shortlist.offering_id)
                           .where(m.Shortlist.user_id == user.id)).all()
    return {"account": {"email": user.email, "created_at": user.created_at.isoformat()},
            "profile": profile_payload(db, profile), "shortlist": list(shortlist)}


@account.delete("", status_code=204)
def delete_account(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    """Permanently deletes the student's account and personal data (AUTH-07)."""
    run_ids = select(m.RecommendationRun.id).where(m.RecommendationRun.user_id == user.id)
    db.execute(delete(m.RecommendationResultRow)
               .where(m.RecommendationResultRow.run_id.in_(run_ids)))
    for model in (m.RecommendationRun, m.Shortlist, m.StudentTestScore,
                  m.StudentQualification, m.StudentProfile):
        db.execute(delete(model).where(model.user_id == user.id))
    db.execute(delete(m.DataReport).where(m.DataReport.user_id == user.id))
    db.execute(delete(m.User).where(m.User.id == user.id))
    db.commit()
    return Response(status_code=204)
