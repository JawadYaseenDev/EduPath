from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from ..db import get_db
from ..services.catalogue import current_cycle

router = APIRouter(prefix="/v1/reference", tags=["reference"])


@router.get("")
def reference(db: Session = Depends(get_db)):
    """All lookup lists in one call. The app caches this."""
    group_subjects: dict[str, list] = {}
    for gs in db.scalars(select(m.GroupSubject)):
        group_subjects.setdefault(gs.group_code, []).append(
            {"code": gs.subject_code, "is_compulsory": gs.is_compulsory,
             "choice_set": gs.choice_set})
    cycle = current_cycle(db)
    return {
        "current_cycle": {"year": cycle.year, "label": cycle.label},
        "regions": [{"code": r.code, "name": r.name, "kind": r.kind}
                    for r in db.scalars(select(m.Region).order_by(m.Region.sort_order))],
        "cities": [{"id": c.id, "name": c.name, "region_code": c.region_code}
                   for c in db.scalars(select(m.City).order_by(m.City.name))],
        "boards": [{"id": b.id, "name": b.name, "short_name": b.short_name, "kind": b.kind,
                    "region_code": b.region_code}
                   for b in db.scalars(select(m.ExamBoard).order_by(m.ExamBoard.short_name))],
        "qualification_types": [
            {"code": t.code, "level": t.level, "name": t.name, "uses_ibcc": t.uses_ibcc}
            for t in db.scalars(select(m.QualificationType)
                                .order_by(m.QualificationType.sort_order))],
        "qualification_groups": [
            {"code": g.code, "type_code": g.type_code, "name": g.name,
             "allows_custom_subjects": g.allows_custom_subjects,
             "subjects": group_subjects.get(g.code, [])}
            for g in db.scalars(select(m.QualificationGroup)
                                .order_by(m.QualificationGroup.sort_order))],
        "subjects": [{"code": s.code, "name": s.name}
                     for s in db.scalars(select(m.Subject).order_by(m.Subject.name))],
        "fields": [{"code": f.code, "name": f.name, "icon": f.icon}
                   for f in db.scalars(select(m.ProgrammeField)
                                       .order_by(m.ProgrammeField.sort_order))],
        "disciplines": [{"code": d.code, "field_code": d.field_code, "name": d.name}
                        for d in db.scalars(select(m.Discipline).order_by(m.Discipline.name))],
        "entry_tests": [{"code": t.code, "name": t.name, "conducted_by": t.conducted_by}
                        for t in db.scalars(select(m.EntryTest))],
    }
