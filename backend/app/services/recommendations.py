"""Run the engine for a student and save the results."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from ..config import get_settings
from ..engine import ENGINE_VERSION, run
from . import catalogue
from . import profile as profile_service


def result_mode(db: Session) -> str:
    setting = db.get(m.AppSetting, "result_mode")
    if setting and setting.value.get("mode") in ("extended", "strict_pdf"):
        return setting.value["mode"]
    return get_settings().result_mode


def run_for_student(db: Session, user: m.User) -> m.RecommendationRun:
    profile = profile_service.get_or_create_profile(db, user)
    student = profile_service.student_input(db, profile)
    prefs = profile_service.preferences(db, profile)
    vocab = profile_service.vocabulary(db)
    cycle = catalogue.current_cycle(db)
    offerings = catalogue.live_offerings(db)
    pairs = [(catalogue.to_rules(o, cycle), catalogue.to_facts(o, cycle)) for o in offerings]
    mode = result_mode(db)
    output = run(pairs, student, prefs, vocab, mode=mode)

    recommended = [i for i in output.items if i.recommended]
    counts = {c: sum(1 for i in output.items if i.eligibility.category == c)
              for c in ("eligible", "potentially_eligible", "not_eligible")}
    summary = {
        "counts": counts,
        "recommended": len(recommended),
        "shown_by_default": sum(1 for i in recommended if i.within_preferences),
        "hidden_by_preferences": output.hidden_by_preferences,
        "no_match": asdict(output.no_match) if output.no_match else None,
        "cycle_label": cycle.label,
    }
    db_run = m.RecommendationRun(
        user_id=user.id,
        engine_version=ENGINE_VERSION,
        mode=mode,
        inputs_snapshot={"student": _jsonable(asdict(student)), "preferences":
                         _jsonable(asdict(prefs))},
        summary=summary,
    )
    db.add(db_run)
    db.flush()
    for rank, item in enumerate(output.items):
        e = item.eligibility
        db.add(m.RecommendationResultRow(
            run_id=db_run.id,
            offering_id=item.offering_id,
            category=e.category.value,
            recommended=item.recommended,
            rule_set_name=e.rule_set_name,
            rule_outcomes=[{"type": r.rule_type, "outcome": r.outcome.value,
                            "message": r.message, "reason_code": r.reason_code,
                            "is_hard": r.is_hard} for r in e.rule_results],
            next_steps=e.next_steps,
            misses=item.misses,
            within_preferences=item.within_preferences,
            match_score=item.score,
            rank=rank,
        ))
    db.commit()
    return db_run


def _jsonable(value):
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_jsonable(v) for v in sorted(value, key=str)] if isinstance(
            value, (set, frozenset)) else [_jsonable(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _aware(value: datetime) -> datetime:
    # SQLite drops time zones; everything we store is UTC.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def latest_run(db: Session, user: m.User) -> m.RecommendationRun | None:
    return db.scalar(select(m.RecommendationRun)
                     .where(m.RecommendationRun.user_id == user.id)
                     .order_by(m.RecommendationRun.created_at.desc()).limit(1))


def run_payload(db: Session, run_row: m.RecommendationRun, profile: m.StudentProfile) -> dict:
    cycle = catalogue.current_cycle(db)
    rows = db.scalars(select(m.RecommendationResultRow)
                      .where(m.RecommendationResultRow.run_id == run_row.id)
                      .order_by(m.RecommendationResultRow.rank)).all()
    offerings = {o.id: o for o in catalogue.live_offerings(db)}
    results = []
    for r in rows:
        o = offerings.get(r.offering_id)
        if o is None:
            continue  # unpublished since the run
        results.append({
            "offering": catalogue.offering_card(o, cycle),
            "category": r.category,
            "recommended": r.recommended,
            "rule_set_name": r.rule_set_name,
            "rule_outcomes": r.rule_outcomes,
            "next_steps": r.next_steps,
            "misses": r.misses,
            "within_preferences": r.within_preferences,
            "match_score": r.match_score,
        })
    created = _aware(run_row.created_at)
    changed = _aware(profile.data_changed_at)
    return {
        "run_id": run_row.id,
        "created_at": created.isoformat(),
        "mode": run_row.mode,
        "engine_version": run_row.engine_version,
        "is_outdated": changed > created,
        "summary": run_row.summary,
        "results": results,
    }
