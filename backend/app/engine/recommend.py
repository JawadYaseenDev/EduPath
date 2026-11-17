"""Full recommendation run: eligibility + preferences + ranking + no-match analysis.

Modes (see docs/RECOMMENDATION_ENGINE.md § 0.1):
  extended   - Eligible and Potentially Eligible are both recommended (in separate groups).
  strict_pdf - only Eligible offerings are recommended, as in the baseline PDF.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

from .evaluator import evaluate_offering
from .preferences import (
    OfferingFacts,
    Preferences,
    budget_fee,
    check_preferences,
    hard_misses,
    in_interest,
    match_score,
    sort_key,
)
from .types import (
    LEVEL_NAMES,
    Category,
    EligibilityResult,
    OfferingRules,
    Outcome,
    StudentInput,
    Vocabulary,
)

MODES = ("extended", "strict_pdf")


@dataclass(frozen=True)
class RecommendationItem:
    offering_id: str
    eligibility: EligibilityResult
    misses: list[str]
    within_preferences: bool
    score: float
    recommended: bool


@dataclass(frozen=True)
class FailReason:
    text: str
    count: int


@dataclass(frozen=True)
class DisciplineSuggestion:
    discipline_id: str
    field_id: str
    count: int


@dataclass(frozen=True)
class PreferenceSuggestion:
    miss: str
    count: int
    suggested_max_fee: int | None = None


@dataclass(frozen=True)
class NoMatch:
    kind: str  # "academic" | "preferences"
    reasons: list[FailReason] = field(default_factory=list)
    discipline_suggestions: list[DisciplineSuggestion] = field(default_factory=list)
    preference_suggestions: list[PreferenceSuggestion] = field(default_factory=list)
    qualifying_count: int = 0


@dataclass(frozen=True)
class RecommendationOutput:
    mode: str
    items: list[RecommendationItem]  # offerings in the student's interests, sorted
    hidden_by_preferences: int
    no_match: NoMatch | None


def _is_recommended(category: Category, mode: str) -> bool:
    if category == Category.ELIGIBLE:
        return True
    return category == Category.POTENTIALLY and mode == "extended"


def _generic_reason(code: str, vocab: Vocabulary) -> str | None:
    kind, _, value = code.partition(":")
    if kind == "missing_subject":
        return f"{vocab.subject(value)} is required"
    if kind == "group_not_accepted":
        return f"Your background ({vocab.group(value)}) is not accepted"
    if kind == "type_not_accepted":
        return f"Your qualification ({vocab.type(value)}) is not accepted"
    if kind == "below_min":
        return f"Your {LEVEL_NAMES.get(value, value)} percentage is below the published minimum"
    if kind == "missing_one_of":
        names = " or ".join(vocab.subject(s) for s in value.split("|"))
        return f"One of {names} is required"
    if kind in ("gender", "campus_gender"):
        return "Open only to students of another gender"
    if kind == "below_subject_min":
        return f"Your {vocab.subject(value)} marks are below the minimum"
    return None


def run(
    offerings: list[tuple[OfferingRules, OfferingFacts]],
    student: StudentInput,
    prefs: Preferences,
    vocab: Vocabulary,
    mode: str = "extended",
    weights: dict[str, float] | None = None,
) -> RecommendationOutput:
    if mode not in MODES:
        raise ValueError(f"Unknown mode: {mode}")

    interest: list[RecommendationItem] = []
    outside_recommended: list[tuple[OfferingFacts, EligibilityResult]] = []
    facts_by_id: dict[str, OfferingFacts] = {}

    for rules, facts in offerings:
        if not facts.is_offered:
            continue
        result = evaluate_offering(rules, student, vocab)
        if result is None:
            continue  # no rules entered: never recommended
        facts_by_id[facts.offering_id] = facts
        recommended = _is_recommended(result.category, mode)
        if not in_interest(facts, prefs):
            if recommended:
                outside_recommended.append((facts, result))
            continue
        misses = check_preferences(facts, prefs, student.gender)
        interest.append(
            RecommendationItem(
                offering_id=facts.offering_id,
                eligibility=result,
                misses=misses,
                within_preferences=not hard_misses(misses),
                score=match_score(facts, prefs, result, student.gender, weights),
                recommended=recommended,
            )
        )

    interest.sort(key=lambda i: sort_key(i.eligibility.category, i.score))
    qualifying = [i for i in interest if i.recommended]
    visible = [i for i in qualifying if i.within_preferences]
    hidden = len(qualifying) - len(visible)

    no_match: NoMatch | None = None
    if not qualifying:
        no_match = _academic_no_match(interest, outside_recommended, vocab)
    elif not visible:
        no_match = _preference_no_match(qualifying, facts_by_id, prefs, student.gender)

    return RecommendationOutput(mode=mode, items=interest, hidden_by_preferences=hidden,
                                no_match=no_match)


def _academic_no_match(
    interest: list[RecommendationItem],
    outside: list[tuple[OfferingFacts, EligibilityResult]],
    vocab: Vocabulary,
) -> NoMatch:
    counts: Counter[str] = Counter()
    for item in interest:
        seen = set()
        for r in item.eligibility.rule_results:
            if r.outcome != Outcome.FAIL:
                continue
            text = _generic_reason(r.reason_code, vocab) or r.message
            if text not in seen:
                counts[text] += 1
                seen.add(text)
    reasons = [FailReason(text, n) for text, n in counts.most_common(3)]

    by_discipline: Counter[tuple[str, str]] = Counter(
        (facts.discipline_id, facts.field_id) for facts, _ in outside
    )
    suggestions = [
        DisciplineSuggestion(discipline_id=d, field_id=f, count=n)
        for (d, f), n in by_discipline.most_common(6)
    ]
    return NoMatch(kind="academic", reasons=reasons, discipline_suggestions=suggestions)


def _preference_no_match(
    qualifying: list[RecommendationItem],
    facts_by_id: dict[str, OfferingFacts],
    prefs: Preferences,
    gender: str | None,
) -> NoMatch:
    single_miss: dict[str, list[RecommendationItem]] = {}
    for item in qualifying:
        hard = hard_misses(item.misses)
        if len(hard) == 1:
            single_miss.setdefault(hard[0], []).append(item)

    suggestions = []
    for miss, items in single_miss.items():
        suggested = None
        if miss == "over_budget":
            fees = [budget_fee(facts_by_id[i.offering_id], prefs, gender) for i in items]
            known = [f for f in fees if f is not None]
            if known:
                suggested = int(math.ceil(max(known) / 5000) * 5000)
        suggestions.append(PreferenceSuggestion(miss=miss, count=len(items),
                                                suggested_max_fee=suggested))
    suggestions.sort(key=lambda s: -s.count)
    return NoMatch(kind="preferences", preference_suggestions=suggestions,
                   qualifying_count=len(qualifying))
