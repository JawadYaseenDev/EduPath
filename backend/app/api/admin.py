"""Minimal admin endpoints. The full admin panel (docs/ADMIN_PANEL_PLAN.md) comes later."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from ..db import get_db
from ..engine import RULE_TYPES, RuleValidationError, validate_rule
from ..schemas import ResultModeIn, RuleCheckIn
from ..security import require_role

router = APIRouter(prefix="/v1/admin", tags=["admin"])
admin_only = require_role("super_admin")
data_staff = require_role("super_admin", "data_editor", "data_verifier")


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
    db.add(m.AuditLog(actor_id=user.id, action="update", entity_type="app_setting",
                      entity_id=None, before=before, after=setting.value))
    db.commit()
    return setting.value


@router.get("/reports")
def list_reports(_: m.User = Depends(data_staff), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.DataReport).order_by(m.DataReport.created_at.desc())).all()
    return [{"id": r.id, "entity_type": r.entity_type, "entity_id": r.entity_id,
             "field": r.field, "message": r.message, "status": r.status,
             "created_at": r.created_at.isoformat()} for r in rows]
