"""Plain data types used by the eligibility engine.

The engine never touches the database. The service layer converts database rows
into these types, calls the engine, and saves the results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

ENGINE_VERSION = "0.1.0"


class Outcome(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class Category(StrEnum):
    ELIGIBLE = "eligible"
    POTENTIALLY = "potentially_eligible"
    NOT_ELIGIBLE = "not_eligible"


CATEGORY_RANK = {Category.ELIGIBLE: 2, Category.POTENTIALLY: 1, Category.NOT_ELIGIBLE: 0}


class ResultStatus(StrEnum):
    FINAL = "final"
    PART1_ONLY = "part1_only"
    AWAITED = "awaited"


class PctKind(StrEnum):
    FINAL = "final"
    PROVISIONAL = "provisional"  # Part-I marks only
    ESTIMATED = "estimated"  # IBCC equivalence entered by the student, not official
    MISSING = "missing"


LEVEL_NAMES = {
    "SSC": "Matric / O-Level",
    "HSSC": "Intermediate / A-Level",
    "DIPLOMA": "DAE / Diploma",
}

# Qualification types that use IBCC equivalence instead of board percentages.
IBCC_TYPES = {"A_LEVEL", "O_LEVEL"}


@dataclass(frozen=True)
class QualificationInput:
    level: str  # SSC, HSSC, DIPLOMA
    type_code: str  # MATRIC, O_LEVEL, INTERMEDIATE, A_LEVEL, DAE, ...
    group_code: str  # PRE_ENGINEERING, ICS, ...
    result_status: ResultStatus = ResultStatus.FINAL
    percentage: float | None = None
    part1_percentage: float | None = None
    subjects: frozenset[str] = frozenset()
    subject_percentages: dict[str, float] = field(default_factory=dict)
    ibcc_percentage: float | None = None
    ibcc_is_official: bool = False
    passing_year: int | None = None
    is_improved_result: bool = False


@dataclass(frozen=True)
class StudentInput:
    gender: str | None  # "male", "female", "other"
    date_of_birth: date | None
    domicile_region: str | None  # region code, e.g. "PB"
    qualifications: dict[str, QualificationInput]  # keyed by level
    test_scores: dict[str, float] = field(default_factory=dict)  # test code -> percentage


@dataclass(frozen=True)
class Rule:
    id: str | None
    rule_type: str
    params: dict
    is_hard: bool = True
    source_label: str | None = None


@dataclass(frozen=True)
class RuleSet:
    id: str | None
    name: str
    rules: list[Rule]


@dataclass(frozen=True)
class OfferingRules:
    offering_id: str
    rule_sets: list[RuleSet]
    campus_gender_policy: str = "coeducation"  # coeducation | women_only | men_only
    is_stale: bool = False
    stale_label: str | None = None  # e.g. "Fall 2026"


@dataclass(frozen=True)
class Vocabulary:
    """Human names for codes, so explanations read naturally."""

    groups: dict[str, str] = field(default_factory=dict)
    types: dict[str, str] = field(default_factory=dict)
    subjects: dict[str, str] = field(default_factory=dict)
    tests: dict[str, str] = field(default_factory=dict)
    regions: dict[str, str] = field(default_factory=dict)

    def group(self, code: str) -> str:
        return self.groups.get(code, code.replace("_", " ").title())

    def type(self, code: str) -> str:
        return self.types.get(code, code.replace("_", " ").title())

    def subject(self, code: str) -> str:
        return self.subjects.get(code, code.title())

    def test(self, code: str) -> str:
        return self.tests.get(code, code)

    def region(self, code: str) -> str:
        return self.regions.get(code, code)


@dataclass(frozen=True)
class RuleResult:
    rule_id: str | None
    rule_type: str
    outcome: Outcome
    message: str
    reason_code: str = ""
    next_step: str | None = None
    is_hard: bool = True
    margin: float | None = None  # how far above a minimum percentage (for sorting only)


@dataclass(frozen=True)
class EligibilityResult:
    offering_id: str
    category: Category
    rule_set_id: str | None
    rule_set_name: str | None
    rule_results: list[RuleResult]
    next_steps: list[str]

    @property
    def academic_margin(self) -> float | None:
        margins = [r.margin for r in self.rule_results if r.margin is not None]
        return min(margins) if margins else None
