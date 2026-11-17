"""Evaluate a student against the rule sets of one offering."""

from __future__ import annotations

from .rules import Context, evaluate_rule
from .types import (
    CATEGORY_RANK,
    Category,
    EligibilityResult,
    OfferingRules,
    Outcome,
    RuleResult,
    RuleSet,
    StudentInput,
    Vocabulary,
)

_POLICY_ALLOWED = {"women_only": "female", "men_only": "male"}


def _campus_gender_check(policy: str, student: StudentInput) -> RuleResult | None:
    allowed = _POLICY_ALLOWED.get(policy)
    if allowed is None:
        return None
    label = "women" if allowed == "female" else "men"
    if student.gender is None:
        return RuleResult(
            None, "campus_gender_policy", Outcome.UNKNOWN,
            f"This campus admits {label} only. Add your gender to check this.", "missing_gender",
        )
    if student.gender == allowed:
        return RuleResult(
            None, "campus_gender_policy", Outcome.PASS, f"This campus admits {label} only."
        )
    return RuleResult(
        None, "campus_gender_policy", Outcome.FAIL,
        f"This campus admits {label} only.", "campus_gender",
    )


def categorise(results: list[RuleResult]) -> Category:
    if any(r.outcome == Outcome.FAIL and r.is_hard for r in results):
        return Category.NOT_ELIGIBLE
    if any(r.outcome != Outcome.PASS for r in results):
        return Category.POTENTIALLY
    return Category.ELIGIBLE


def _evaluate_set(rule_set: RuleSet, student: StudentInput, vocab: Vocabulary) -> list[RuleResult]:
    ctx = Context(student=student, rule_set=rule_set, vocab=vocab)
    out = []
    seen: set[tuple[str, str]] = set()
    for rule in rule_set.rules:
        result = evaluate_rule(rule, ctx)
        if result is None:
            continue
        # Several rules can fail for the same reason (e.g. "this route is for DAE students").
        key = (result.outcome.value, result.message)
        if key in seen:
            continue
        seen.add(key)
        out.append(result)
    return out


def _problems(results: list[RuleResult]) -> int:
    return sum(r.outcome != Outcome.PASS for r in results)


def evaluate_offering(
    offering: OfferingRules, student: StudentInput, vocab: Vocabulary
) -> EligibilityResult | None:
    """Return the best result across rule sets, or None if no rules are entered yet.

    Offerings without rules must never be shown as eligible, so the caller leaves them
    out of recommendations.
    """
    if not offering.rule_sets or not any(rs.rules for rs in offering.rule_sets):
        return None

    campus_check = _campus_gender_check(offering.campus_gender_policy, student)
    best: tuple[RuleSet, list[RuleResult], Category] | None = None
    for rule_set in offering.rule_sets:
        results = _evaluate_set(rule_set, student, vocab)
        if campus_check is not None:
            results = [campus_check, *results]
        category = categorise(results)
        if best is None:
            best = (rule_set, results, category)
            continue
        better_category = CATEGORY_RANK[category] > CATEGORY_RANK[best[2]]
        same_but_cleaner = category == best[2] and _problems(results) < _problems(best[1])
        if better_category or same_but_cleaner:
            best = (rule_set, results, category)

    assert best is not None
    rule_set, results, category = best

    if offering.is_stale and category == Category.ELIGIBLE:
        category = Category.POTENTIALLY
        cycle = offering.stale_label or "a previous admission cycle"
        results = [
            *results,
            RuleResult(
                None, "data_freshness", Outcome.UNKNOWN,
                f"Requirements for this year are not confirmed yet. This check uses rules from "
                f"{cycle}.",
                "stale_data",
                next_step="Check the official admission page for this year's requirements.",
            ),
        ]

    next_steps: list[str] = []
    for r in results:
        if r.next_step and r.next_step not in next_steps:
            next_steps.append(r.next_step)

    return EligibilityResult(
        offering_id=offering.offering_id,
        category=category,
        rule_set_id=rule_set.id,
        rule_set_name=rule_set.name,
        rule_results=results,
        next_steps=next_steps,
    )
