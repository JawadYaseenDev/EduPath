"""Preference checks and ranking.

Preferences NEVER change eligibility. They only decide which results are shown by
default and in what order.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .types import Category, EligibilityResult

# Misses that do not hide a result. They are shown with a label instead,
# because "we don't know" is not the same as "it does not fit".
SOFT_MISSES = frozenset({"fee_unknown", "hostel_unknown"})

DEFAULT_WEIGHTS = {
    "discipline": 30,
    "budget": 20,
    "location": 20,
    "hostel": 10,
    "academic_margin": 10,
    "accreditation": 5,
    "freshness": 5,
}


@dataclass(frozen=True)
class HostelFact:
    availability: str  # available | limited | not_available | unknown
    location: str  # on_campus | off_campus_university_managed | affiliated_private
    fee_per_semester: int | None = None


@dataclass(frozen=True)
class OfferingFacts:
    offering_id: str
    discipline_id: str
    field_id: str
    region_code: str
    city_id: str
    sector: str
    gender_policy: str
    shift: str
    latitude: float | None = None
    longitude: float | None = None
    accredited: bool | None = None  # None = not applicable or unknown
    tests: tuple[str, ...] = ()
    tuition_per_semester: int | None = None
    charges_per_semester: int | None = None  # tuition + other recurring charges
    hostels: dict[str, HostelFact] = field(default_factory=dict)  # by gender: male/female
    is_stale: bool = False
    is_offered: bool = True


@dataclass(frozen=True)
class Preferences:
    regions: frozenset[str] = frozenset()
    cities: frozenset[str] = frozenset()
    max_distance_km: float | None = None
    home_latitude: float | None = None
    home_longitude: float | None = None
    max_fee_per_semester: int | None = None
    budget_includes: str = "university_charges"  # tuition_only | university_charges | with_hostel
    sectors: frozenset[str] = frozenset()
    hostel_need: str = "none"  # none | needed | on_campus_only
    gender_campus_pref: str = "any"  # any | coeducation | single_gender
    shifts: frozenset[str] = frozenset()
    require_accreditation: bool = False
    willing_tests: frozenset[str] | None = None  # None = willing to take any test
    disciplines: frozenset[str] = frozenset()
    fields: frozenset[str] = frozenset()


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def in_interest(facts: OfferingFacts, prefs: Preferences) -> bool:
    if not prefs.disciplines and not prefs.fields:
        return True
    return facts.discipline_id in prefs.disciplines or facts.field_id in prefs.fields


def budget_fee(facts: OfferingFacts, prefs: Preferences, gender: str | None) -> int | None:
    if prefs.budget_includes == "tuition_only":
        return facts.tuition_per_semester
    base = facts.charges_per_semester
    if prefs.budget_includes == "with_hostel":
        hostel = facts.hostels.get(gender or "")
        if base is None or hostel is None or hostel.fee_per_semester is None:
            return None
        return base + hostel.fee_per_semester
    return base


def _distance(facts: OfferingFacts, prefs: Preferences) -> float | None:
    if None in (facts.latitude, facts.longitude, prefs.home_latitude, prefs.home_longitude):
        return None
    return distance_km(prefs.home_latitude, prefs.home_longitude, facts.latitude, facts.longitude)


def check_preferences(facts: OfferingFacts, prefs: Preferences, gender: str | None) -> list[str]:
    misses: list[str] = []

    if prefs.cities or prefs.regions:
        ok = facts.city_id in prefs.cities or facts.region_code in prefs.regions
        if not ok:
            misses.append("outside_location")
    if prefs.max_distance_km is not None:
        d = _distance(facts, prefs)
        if d is not None and d > prefs.max_distance_km and "outside_location" not in misses:
            misses.append("outside_location")

    if prefs.max_fee_per_semester is not None:
        fee = budget_fee(facts, prefs, gender)
        if fee is None:
            misses.append("fee_unknown")
        elif fee > prefs.max_fee_per_semester:
            misses.append("over_budget")

    if prefs.sectors and facts.sector not in prefs.sectors:
        misses.append("sector")

    if prefs.hostel_need != "none":
        hostel = facts.hostels.get(gender or "")
        if hostel is None or hostel.availability == "unknown":
            misses.append("hostel_unknown")
        elif hostel.availability == "not_available":
            misses.append("no_hostel")
        elif prefs.hostel_need == "on_campus_only" and hostel.location != "on_campus":
            misses.append("no_hostel")

    if prefs.gender_campus_pref == "coeducation" and facts.gender_policy != "coeducation":
        misses.append("campus_type")
    if prefs.gender_campus_pref == "single_gender" and facts.gender_policy == "coeducation":
        misses.append("campus_type")

    if prefs.shifts and facts.shift not in prefs.shifts:
        misses.append("shift")

    if prefs.require_accreditation and facts.accredited is False:
        misses.append("not_accredited")

    if prefs.willing_tests is not None and facts.tests:
        if not set(facts.tests) & prefs.willing_tests:
            misses.append("test_not_willing")

    return misses


def hard_misses(misses: list[str]) -> list[str]:
    return [m for m in misses if m not in SOFT_MISSES]


def match_score(
    facts: OfferingFacts,
    prefs: Preferences,
    result: EligibilityResult,
    gender: str | None,
    weights: dict[str, float] | None = None,
) -> float:
    """0-100 score used ONLY for ordering results. Never shown as a chance of admission."""
    w = weights or DEFAULT_WEIGHTS
    f: dict[str, float] = {}

    if not prefs.disciplines and not prefs.fields:
        f["discipline"] = 1.0
    elif facts.discipline_id in prefs.disciplines:
        f["discipline"] = 1.0
    elif facts.field_id in prefs.fields:
        f["discipline"] = 0.75 if not prefs.disciplines else 0.5
    else:
        f["discipline"] = 0.0

    fee = budget_fee(facts, prefs, gender)
    if prefs.max_fee_per_semester is None:
        f["budget"] = 1.0
    elif fee is None:
        f["budget"] = 0.5
    elif fee <= prefs.max_fee_per_semester:
        f["budget"] = 1.0
    else:
        over = (fee - prefs.max_fee_per_semester) / max(prefs.max_fee_per_semester, 1)
        f["budget"] = max(0.0, 1.0 - over)

    if not prefs.cities and not prefs.regions:
        f["location"] = 1.0
    elif facts.city_id in prefs.cities:
        f["location"] = 1.0
    elif facts.region_code in prefs.regions:
        f["location"] = 0.7
    else:
        d = _distance(facts, prefs)
        f["location"] = 0.3 if d is None else max(0.0, 0.5 * (1 - d / 1000))

    if prefs.hostel_need == "none":
        f["hostel"] = 1.0
    else:
        hostel = facts.hostels.get(gender or "")
        if hostel is None or hostel.availability == "unknown":
            f["hostel"] = 0.5
        elif hostel.availability == "not_available":
            f["hostel"] = 0.0
        else:
            f["hostel"] = 1.0 if hostel.availability == "available" else 0.7

    margin = result.academic_margin
    f["academic_margin"] = 0.5 if margin is None else max(0.0, min(margin, 20.0)) / 20.0
    f["accreditation"] = {True: 1.0, None: 0.5, False: 0.0}[facts.accredited]
    f["freshness"] = 0.0 if facts.is_stale else 1.0

    total = sum(w.values())
    return round(sum(w[k] * f[k] for k in w) / total * 100, 1)


def sort_key(category: Category, score: float) -> tuple[int, float]:
    order = {Category.ELIGIBLE: 0, Category.POTENTIALLY: 1, Category.NOT_ELIGIBLE: 2}
    return order[category], -score
