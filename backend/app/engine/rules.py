"""Rule types: parameter schemas + evaluators + plain-English messages.

To add a new rule type:
  1. add a Params model,
  2. add an evaluator function,
  3. register both in RULE_TYPES,
  4. add tests in tests/test_engine.py.
No database or mobile-app change is needed.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .types import (
    IBCC_TYPES,
    LEVEL_NAMES,
    Outcome,
    PctKind,
    QualificationInput,
    ResultStatus,
    Rule,
    RuleResult,
    RuleSet,
    StudentInput,
    Vocabulary,
)

Level = Literal["SSC", "HSSC", "DIPLOMA"]
HIGHER_LEVELS = frozenset({"HSSC", "DIPLOMA"})


class _Params(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AcceptedQualificationParams(_Params):
    level: Level
    types: list[str] = Field(default_factory=list)  # empty = any type at this level
    groups: list[str] = Field(default_factory=list)  # empty = any group


class RequiredSubjectsParams(_Params):
    level: Level
    all_of: list[str] = Field(default_factory=list)
    one_of: list[list[str]] = Field(default_factory=list)


class MinPercentageParams(_Params):
    level: Level
    min: float = Field(ge=0, le=100)
    accept_part1: bool = False


class MinSubjectMarksParams(_Params):
    level: Level
    subject: str
    min_percentage: float = Field(ge=0, le=100)


class EntryTestRequiredParams(_Params):
    tests: list[str] = Field(min_length=1)
    min_score_percentage: float | None = Field(default=None, ge=0, le=100)


class GenderParams(_Params):
    allowed: list[Literal["male", "female", "other"]] = Field(min_length=1)


class DomicileParams(_Params):
    regions: list[str] = Field(min_length=1)
    seat_type: str = "quota"


class MaxAgeParams(_Params):
    years: int = Field(gt=0, lt=100)
    on_date: date


class PassingYearWindowParams(_Params):
    level: Level
    min_year: int


class ResultStatusParams(_Params):
    level: Level
    accept_part1: bool = True


class DeficiencyAllowedParams(_Params):
    for_groups: list[str] = Field(min_length=1)
    missing_subject: str | None = None
    course: str


class IbccEquivalenceRequiredParams(_Params):
    for_types: list[str] = Field(default_factory=lambda: sorted(IBCC_TYPES))


class ImprovedResultPolicyParams(_Params):
    accepted: bool


class ManualNoteParams(_Params):
    text: str = Field(min_length=3)


@dataclass(frozen=True)
class Context:
    student: StudentInput
    rule_set: RuleSet
    vocab: Vocabulary


# An evaluator returns a RuleResult, or None when the rule does not apply to this
# student (for example, an IBCC rule for a student who did FSc).
Evaluator = Callable[[BaseModel, Rule, Context], RuleResult | None]


# ---------------------------------------------------------------- helpers


def effective_percentage(q: QualificationInput) -> tuple[float | None, PctKind]:
    if q.type_code in IBCC_TYPES:
        if q.ibcc_percentage is None:
            return None, PctKind.MISSING
        return q.ibcc_percentage, PctKind.FINAL if q.ibcc_is_official else PctKind.ESTIMATED
    if q.result_status == ResultStatus.FINAL and q.percentage is not None:
        return q.percentage, PctKind.FINAL
    if q.part1_percentage is not None and q.result_status != ResultStatus.FINAL:
        return q.part1_percentage, PctKind.PROVISIONAL
    return None, PctKind.MISSING


def _fmt(pct: float) -> str:
    return f"{pct:.2f}".rstrip("0").rstrip(".")


def _join(items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " or " + items[-1]


def _result(rule: Rule, outcome: Outcome, message: str, reason: str = "", **kw) -> RuleResult:
    return RuleResult(
        rule_id=rule.id,
        rule_type=rule.rule_type,
        outcome=outcome,
        message=message,
        reason_code=reason,
        is_hard=rule.is_hard,
        **kw,
    )


def _missing_level(rule: Rule, level: str, ctx: Context | None = None) -> RuleResult:
    # Intermediate/A-Level (HSSC) and DAE (DIPLOMA) are alternative routes. A student who
    # entered one of them is not "missing" the other: that rule set is simply not their route.
    if ctx is not None and level in HIGHER_LEVELS:
        other = next((q for lvl, q in ctx.student.qualifications.items()
                      if lvl in HIGHER_LEVELS and lvl != level), None)
        if other is not None:
            return _result(
                rule,
                Outcome.FAIL,
                f"This route is for {LEVEL_NAMES[level]} students. Your qualification is "
                f"{ctx.vocab.type(other.type_code)}.",
                f"type_not_accepted:{other.type_code}",
            )
    return _result(
        rule,
        Outcome.UNKNOWN,
        f"Add your {LEVEL_NAMES[level]} details to check this requirement.",
        f"missing_level:{level}",
    )


def _deficiency_for(
    ctx: Context, group: str, subject: str | None = None
) -> DeficiencyAllowedParams | None:
    for r in ctx.rule_set.rules:
        if r.rule_type != "deficiency_allowed":
            continue
        p = DeficiencyAllowedParams.model_validate(r.params)
        if group in p.for_groups and (subject is None or p.missing_subject in (None, subject)):
            return p
    return None


def _accept_part1(ctx: Context, level: str, own: bool) -> bool:
    if own:
        return True
    for r in ctx.rule_set.rules:
        if r.rule_type == "result_status":
            p = ResultStatusParams.model_validate(r.params)
            if p.level == level and p.accept_part1:
                return True
    return False


# ---------------------------------------------------------------- evaluators


def eval_accepted_qualification(p: AcceptedQualificationParams, rule: Rule, ctx: Context):
    q = ctx.student.qualifications.get(p.level)
    if q is None:
        return _missing_level(rule, p.level, ctx)
    v = ctx.vocab
    if p.types and q.type_code not in p.types:
        accepted = _join([v.type(t) for t in p.types])
        return _result(
            rule,
            Outcome.FAIL,
            f"This programme accepts {accepted}. Your qualification is {v.type(q.type_code)}.",
            f"type_not_accepted:{q.type_code}",
        )
    if p.groups and q.group_code not in p.groups:
        deficiency = _deficiency_for(ctx, q.group_code)
        if deficiency:
            return _result(
                rule,
                Outcome.PASS,
                f"{v.group(q.group_code)} students can join if they complete: {deficiency.course}.",
                "deficiency_route",
                next_step=f"You will need to complete: {deficiency.course}.",
            )
        accepted = _join([v.group(g) for g in p.groups])
        return _result(
            rule,
            Outcome.FAIL,
            f"This programme accepts {accepted}. Your background is {v.group(q.group_code)}.",
            f"group_not_accepted:{q.group_code}",
        )
    return _result(
        rule, Outcome.PASS, f"Your {v.group(q.group_code)} background is accepted for this programme."
    )


def eval_required_subjects(p: RequiredSubjectsParams, rule: Rule, ctx: Context):
    q = ctx.student.qualifications.get(p.level)
    if q is None:
        return _missing_level(rule, p.level, ctx)
    v = ctx.vocab
    level = LEVEL_NAMES[p.level]
    next_steps: list[str] = []
    for subject in p.all_of:
        if subject in q.subjects:
            continue
        deficiency = _deficiency_for(ctx, q.group_code, subject)
        if deficiency:
            next_steps.append(f"You will need to complete: {deficiency.course}.")
            continue
        return _result(
            rule,
            Outcome.FAIL,
            f"{v.subject(subject)} at {level} level is required. You did not study it.",
            f"missing_subject:{subject}",
        )
    for options in p.one_of:
        if not set(options) & q.subjects:
            names = _join([v.subject(s) for s in options])
            return _result(
                rule,
                Outcome.FAIL,
                f"One of {names} at {level} level is required. You did not study any of these.",
                f"missing_one_of:{'|'.join(options)}",
            )
    parts = [v.subject(s) for s in p.all_of if s in q.subjects]
    message = (
        f"Required subjects ({', '.join(parts)}) are in your {level} subjects."
        if parts
        else f"Your {level} subjects meet the subject requirements."
    )
    if next_steps:
        return _result(
            rule, Outcome.PASS, message + " A deficiency course applies.", "deficiency_route",
            next_step=" ".join(next_steps),
        )
    return _result(rule, Outcome.PASS, message)


def eval_min_percentage(p: MinPercentageParams, rule: Rule, ctx: Context):
    q = ctx.student.qualifications.get(p.level)
    if q is None:
        return _missing_level(rule, p.level, ctx)
    level = LEVEL_NAMES[p.level]
    value, kind = effective_percentage(q)
    minimum = _fmt(p.min)
    if value is None:
        if q.type_code in IBCC_TYPES:
            return _result(
                rule,
                Outcome.UNKNOWN,
                f"The published minimum is {minimum}% in {level}. Add your IBCC equivalence "
                "percentage to check this.",
                "missing_ibcc",
                next_step="Apply to IBCC for your equivalence certificate.",
            )
        return _result(
            rule,
            Outcome.UNKNOWN,
            f"The published minimum is {minimum}% in {level}. Your result is not available yet.",
            "result_awaited",
            next_step="Update your marks when your result is announced.",
        )
    pct = round(value, 2)
    shown = _fmt(pct)
    margin = round(pct - p.min, 2)
    if kind == PctKind.PROVISIONAL:
        if pct < p.min:
            return _result(
                rule,
                Outcome.FAIL,
                f"Based on your Part-I marks ({shown}%), you are below the published minimum of "
                f"{minimum}% in {level}. Update your marks when your final result is announced.",
                f"below_min:{p.level}",
            )
        if _accept_part1(ctx, p.level, p.accept_part1):
            return _result(
                rule,
                Outcome.PASS,
                f"Your Part-I percentage ({shown}%) is above the published minimum of {minimum}%. "
                "This university accepts Part-I marks for applying.",
                margin=margin,
                next_step=f"Your final {level} result must also be {minimum}% or more.",
            )
        return _result(
            rule,
            Outcome.UNKNOWN,
            f"Based on your Part-I marks ({shown}%) you are above the {minimum}% minimum. "
            "Your final result must also meet it.",
            "provisional_marks",
            margin=margin,
            next_step="Check again when your final result is announced.",
        )
    if kind == PctKind.ESTIMATED:
        if pct < p.min:
            return _result(
                rule,
                Outcome.FAIL,
                f"Your estimated IBCC equivalence ({shown}%) is below the published minimum of "
                f"{minimum}%.",
                f"below_min:{p.level}",
            )
        return _result(
            rule,
            Outcome.UNKNOWN,
            f"Your estimated IBCC equivalence ({shown}%) is above the {minimum}% minimum. "
            "It must be confirmed by an official IBCC certificate.",
            "ibcc_estimated",
            margin=margin,
            next_step="Get your official IBCC equivalence certificate.",
        )
    if pct >= p.min:
        return _result(
            rule,
            Outcome.PASS,
            f"Your {level} percentage ({shown}%) meets the published minimum of {minimum}%.",
            margin=margin,
        )
    return _result(
        rule,
        Outcome.FAIL,
        f"The published minimum is {minimum}% in {level}. Your percentage is {shown}%.",
        f"below_min:{p.level}",
    )


def eval_min_subject_marks(p: MinSubjectMarksParams, rule: Rule, ctx: Context):
    q = ctx.student.qualifications.get(p.level)
    if q is None:
        return _missing_level(rule, p.level, ctx)
    name = ctx.vocab.subject(p.subject)
    minimum = _fmt(p.min_percentage)
    if p.subject not in q.subjects:
        return _result(
            rule,
            Outcome.FAIL,
            f"At least {minimum}% in {name} is required. You did not study {name}.",
            f"missing_subject:{p.subject}",
        )
    value = q.subject_percentages.get(p.subject)
    if value is None:
        return _result(
            rule,
            Outcome.UNKNOWN,
            f"At least {minimum}% in {name} is required. Add your {name} marks to check this.",
            f"missing_subject_marks:{p.subject}",
        )
    if round(value, 2) >= p.min_percentage:
        return _result(
            rule,
            Outcome.PASS,
            f"Your {name} marks ({_fmt(value)}%) meet the minimum of {minimum}%.",
        )
    return _result(
        rule,
        Outcome.FAIL,
        f"At least {minimum}% in {name} is required. You have {_fmt(value)}%.",
        f"below_subject_min:{p.subject}",
    )


def eval_entry_test_required(p: EntryTestRequiredParams, rule: Rule, ctx: Context):
    names = _join([ctx.vocab.test(t) for t in p.tests])
    scores = [ctx.student.test_scores[t] for t in p.tests if t in ctx.student.test_scores]
    if p.min_score_percentage is None:
        if scores:
            return _result(rule, Outcome.PASS, f"An entry test is required: {names}.")
        return _result(
            rule,
            Outcome.PASS,
            f"An entry test is required: {names}.",
            next_step=f"Register for and take {names}.",
        )
    minimum = _fmt(p.min_score_percentage)
    if not scores:
        return _result(
            rule,
            Outcome.UNKNOWN,
            f"You need at least {minimum}% in {names}. Add your test score to check this.",
            "missing_test_score",
            next_step=f"Register for and take {names}.",
        )
    best = max(scores)
    if best >= p.min_score_percentage:
        return _result(
            rule, Outcome.PASS, f"Your test score ({_fmt(best)}%) meets the {minimum}% minimum."
        )
    return _result(
        rule,
        Outcome.FAIL,
        f"You need at least {minimum}% in {names}. Your best score is {_fmt(best)}%.",
        "below_test_min",
    )


def eval_gender(p: GenderParams, rule: Rule, ctx: Context):
    gender = ctx.student.gender
    allowed = _join(sorted(p.allowed))
    if gender is None:
        return _result(
            rule,
            Outcome.UNKNOWN,
            f"This programme is open to {allowed} students. Add your gender to check this.",
            "missing_gender",
        )
    if gender in p.allowed:
        return _result(rule, Outcome.PASS, f"This programme is open to {allowed} students.")
    return _result(
        rule, Outcome.FAIL, f"This programme is only open to {allowed} students.", "gender"
    )


def eval_domicile(p: DomicileParams, rule: Rule, ctx: Context):
    regions = _join([ctx.vocab.region(r) for r in p.regions])
    d = ctx.student.domicile_region
    if d is None:
        return _result(
            rule,
            Outcome.UNKNOWN,
            f"These seats need a domicile of {regions}. Add your domicile to check this.",
            "missing_domicile",
        )
    if d in p.regions:
        return _result(rule, Outcome.PASS, f"Your domicile ({ctx.vocab.region(d)}) is accepted.")
    return _result(
        rule, Outcome.FAIL, f"These seats need a domicile of {regions}.", "domicile"
    )


def eval_max_age(p: MaxAgeParams, rule: Rule, ctx: Context):
    dob = ctx.student.date_of_birth
    if dob is None:
        return _result(
            rule,
            Outcome.UNKNOWN,
            f"The age limit is {p.years} years. Add your date of birth to check this.",
            "missing_dob",
        )
    d = p.on_date
    age = d.year - dob.year - ((d.month, d.day) < (dob.month, dob.day))
    if age <= p.years:
        return _result(rule, Outcome.PASS, f"You are within the age limit of {p.years} years.")
    return _result(
        rule,
        Outcome.FAIL,
        f"The age limit is {p.years} years on {d:%d %B %Y}. You will be {age}.",
        "over_age",
    )


def eval_passing_year_window(p: PassingYearWindowParams, rule: Rule, ctx: Context):
    q = ctx.student.qualifications.get(p.level)
    if q is None:
        return _missing_level(rule, p.level, ctx)
    level = LEVEL_NAMES[p.level]
    if q.result_status != ResultStatus.FINAL:
        return None  # still studying, so the year will be current
    if q.passing_year is None:
        return _result(
            rule, Outcome.UNKNOWN, f"Add your {level} passing year to check this.", "missing_year"
        )
    if q.passing_year >= p.min_year:
        return _result(rule, Outcome.PASS, f"Your {level} passing year is accepted.")
    return _result(
        rule,
        Outcome.FAIL,
        f"Only students who passed {level} in {p.min_year} or later can apply.",
        "passing_year",
    )


def eval_info_only(p: BaseModel, rule: Rule, ctx: Context):
    """Rules that only change how other rules behave (result_status, deficiency_allowed)."""
    return None


def eval_ibcc_required(p: IbccEquivalenceRequiredParams, rule: Rule, ctx: Context):
    for q in ctx.student.qualifications.values():
        if q.type_code in p.for_types and not q.ibcc_is_official:
            return _result(
                rule,
                Outcome.UNKNOWN,
                "An official IBCC equivalence certificate is required for "
                f"{ctx.vocab.type(q.type_code)} students.",
                "ibcc_certificate",
                next_step="Get your official IBCC equivalence certificate.",
            )
    return None


def eval_improved_result(p: ImprovedResultPolicyParams, rule: Rule, ctx: Context):
    improved = any(q.is_improved_result for q in ctx.student.qualifications.values())
    if improved and not p.accepted:
        return _result(
            rule,
            Outcome.FAIL,
            "This university does not accept improved (supplementary) results.",
            "improved_result",
        )
    return None


def eval_manual_note(p: ManualNoteParams, rule: Rule, ctx: Context):
    return _result(rule, Outcome.UNKNOWN, p.text, "manual_check", next_step=p.text)


RULE_TYPES: dict[str, tuple[type[BaseModel], Evaluator]] = {
    "accepted_qualification": (AcceptedQualificationParams, eval_accepted_qualification),
    "required_subjects": (RequiredSubjectsParams, eval_required_subjects),
    "min_percentage": (MinPercentageParams, eval_min_percentage),
    "min_subject_marks": (MinSubjectMarksParams, eval_min_subject_marks),
    "entry_test_required": (EntryTestRequiredParams, eval_entry_test_required),
    "gender": (GenderParams, eval_gender),
    "domicile": (DomicileParams, eval_domicile),
    "max_age": (MaxAgeParams, eval_max_age),
    "passing_year_window": (PassingYearWindowParams, eval_passing_year_window),
    "result_status": (ResultStatusParams, eval_info_only),
    "deficiency_allowed": (DeficiencyAllowedParams, eval_info_only),
    "ibcc_equivalence_required": (IbccEquivalenceRequiredParams, eval_ibcc_required),
    "improved_result_policy": (ImprovedResultPolicyParams, eval_improved_result),
    "manual_note": (ManualNoteParams, eval_manual_note),
}


class RuleValidationError(ValueError):
    pass


def validate_rule(rule_type: str, params: dict) -> dict:
    """Check a rule before an admin can save it. Returns the cleaned params."""
    if rule_type not in RULE_TYPES:
        raise RuleValidationError(f"Unknown rule type: {rule_type}")
    model, _ = RULE_TYPES[rule_type]
    try:
        return model.model_validate(params).model_dump(mode="json")
    except ValidationError as exc:
        raise RuleValidationError(_friendly(exc)) from exc


def _friendly(exc: ValidationError) -> str:
    """Short, plain messages for admins instead of the raw validation report."""
    parts = []
    for e in exc.errors():
        field = ".".join(str(p) for p in e["loc"]) or "value"
        kind = e["type"]
        if kind == "missing":
            msg = "is required"
        elif kind == "extra_forbidden":
            msg = "is not allowed for this rule"
        elif kind == "too_short":
            msg = "needs at least one choice"
        else:
            msg = e["msg"].removeprefix("Value error, ").lower()
        parts.append(f"{field} {msg}")
    return "; ".join(parts)


def evaluate_rule(rule: Rule, ctx: Context) -> RuleResult | None:
    model, evaluator = RULE_TYPES[rule.rule_type]
    return evaluator(model.model_validate(rule.params), rule, ctx)
