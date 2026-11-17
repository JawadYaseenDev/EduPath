"""Eligibility and recommendation engine (pure Python, no database access)."""

from .evaluator import evaluate_offering
from .recommend import run
from .rules import RULE_TYPES, RuleValidationError, validate_rule
from .types import ENGINE_VERSION

__all__ = [
    "ENGINE_VERSION",
    "RULE_TYPES",
    "RuleValidationError",
    "evaluate_offering",
    "run",
    "validate_rule",
]
