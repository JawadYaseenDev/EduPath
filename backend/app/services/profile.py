"""Student profile helpers: percentages, engine inputs, completeness."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from ..engine.preferences import Preferences
from ..engine.types import QualificationInput, ResultStatus, StudentInput, Vocabulary

PREFERENCE_DEFAULTS = {
    "regions": [], "city_ids": [], "max_distance_km": None,
    "max_fee_per_semester": None, "budget_includes": "university_charges",
    "sectors": [], "hostel_need": "none", "gender_campus_pref": "any", "shifts": [],
    "require_accreditation": False, "willing_tests": None, "disciplines": [], "fields": [],
}


def pct(obtained: float | None, total: float | None) -> float | None:
    if obtained is None or not total:
        return None
    return round(obtained / total * 100, 2)


def get_or_create_profile(db: Session, user: m.User) -> m.StudentProfile:
    profile = db.get(m.StudentProfile, user.id)
    if profile is None:
        profile = m.StudentProfile(user_id=user.id, preferences=dict(PREFERENCE_DEFAULTS))
        db.add(profile)
        db.commit()
    return profile


def qualification_to_input(q: m.StudentQualification) -> QualificationInput:
    subjects = {s["code"] for s in q.subjects}
    subject_pcts = {s["code"]: p for s in q.subjects
                    if (p := pct(s.get("obtained"), s.get("total"))) is not None}
    return QualificationInput(
        level=q.level,
        type_code=q.type_code,
        group_code=q.group_code,
        result_status=ResultStatus(q.result_status),
        percentage=pct(q.obtained_marks, q.total_marks),
        part1_percentage=pct(q.part1_obtained, q.part1_total),
        subjects=frozenset(subjects),
        subject_percentages=subject_pcts,
        ibcc_percentage=q.ibcc_percentage,
        ibcc_is_official=q.ibcc_is_official,
        passing_year=q.passing_year,
        is_improved_result=q.is_improved_result,
    )


def student_input(db: Session, profile: m.StudentProfile) -> StudentInput:
    quals = db.scalars(select(m.StudentQualification)
                       .where(m.StudentQualification.user_id == profile.user_id)).all()
    scores = db.scalars(select(m.StudentTestScore)
                        .where(m.StudentTestScore.user_id == profile.user_id)).all()
    best: dict[str, float] = {}
    for s in scores:
        value = pct(s.score, s.total)
        if value is not None:
            best[s.test_code] = max(best.get(s.test_code, 0.0), value)
    qualifications = {q.level: qualification_to_input(q) for q in quals}
    # DAE is a higher secondary qualification. If the student has no HSSC record,
    # nothing changes: DAE rules target level DIPLOMA directly.
    return StudentInput(
        gender=profile.gender,
        date_of_birth=profile.date_of_birth,
        domicile_region=profile.domicile_region_code,
        qualifications=qualifications,
        test_scores=best,
    )


def preferences(db: Session, profile: m.StudentProfile) -> Preferences:
    p = {**PREFERENCE_DEFAULTS, **(profile.preferences or {})}
    home = db.get(m.City, profile.current_city_id) if profile.current_city_id else None
    willing = p.get("willing_tests")
    return Preferences(
        regions=frozenset(p["regions"]),
        cities=frozenset(p["city_ids"]),
        max_distance_km=p["max_distance_km"],
        home_latitude=home.latitude if home else None,
        home_longitude=home.longitude if home else None,
        max_fee_per_semester=p["max_fee_per_semester"],
        budget_includes=p["budget_includes"],
        sectors=frozenset(p["sectors"]),
        hostel_need=p["hostel_need"],
        gender_campus_pref=p["gender_campus_pref"],
        shifts=frozenset(p["shifts"]),
        require_accreditation=p["require_accreditation"],
        willing_tests=frozenset(willing) if willing is not None else None,
        disciplines=frozenset(p["disciplines"]),
        fields=frozenset(p["fields"]),
    )


def vocabulary(db: Session) -> Vocabulary:
    return Vocabulary(
        groups={g.code: g.name for g in db.scalars(select(m.QualificationGroup))},
        types={t.code: t.name for t in db.scalars(select(m.QualificationType))},
        subjects={s.code: s.name for s in db.scalars(select(m.Subject))},
        tests={t.code: t.name.split(" (")[-1].rstrip(")") if "(" in t.name else t.name
               for t in db.scalars(select(m.EntryTest))},
        regions={r.code: r.name for r in db.scalars(select(m.Region))},
    )


def completeness(db: Session, profile: m.StudentProfile) -> dict:
    levels = set(db.scalars(select(m.StudentQualification.level)
                            .where(m.StudentQualification.user_id == profile.user_id)))
    prefs = profile.preferences or {}
    checks = {
        "personal": bool(profile.full_name and profile.gender and profile.current_city_id),
        "domicile": profile.domicile_region_code is not None,
        "secondary": "SSC" in levels,
        "higher_secondary": bool({"HSSC", "DIPLOMA"} & levels),
        "interests": bool(prefs.get("fields") or prefs.get("disciplines")),
    }
    done = sum(checks.values())
    missing = [k for k, ok in checks.items() if not ok]
    return {"percent": round(done / len(checks) * 100), "missing": missing,
            "ready_for_recommendations": checks["higher_secondary"] and checks["personal"]}
