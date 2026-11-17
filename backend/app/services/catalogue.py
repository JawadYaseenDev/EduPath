"""Catalogue queries, fee calculations, and conversion to engine inputs."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from .. import models as m
from ..engine.preferences import HostelFact, OfferingFacts
from ..engine.types import OfferingRules, Rule, RuleSet

LIVE = "published"


def current_cycle(db: Session) -> m.AdmissionCycle:
    cycle = db.scalar(select(m.AdmissionCycle).where(m.AdmissionCycle.is_current))
    if cycle is None:
        raise RuntimeError("No current admission cycle is set.")
    return cycle


def _per_semester(fee: m.OfferingFee, programme: m.Programme) -> float | None:
    if fee.basis == "per_semester":
        return fee.amount_pkr
    if fee.basis == "per_year":
        return fee.amount_pkr / 2
    if fee.basis == "per_credit_hour":
        if not programme.total_credit_hours:
            return None
        semesters = programme.duration_years * 2
        return fee.amount_pkr * programme.total_credit_hours / semesters
    return None


def fee_summary(offering: m.Offering) -> dict:
    """Comparable fee totals (whole rupees). None when data is missing."""
    programme = offering.programme
    fees = offering.fees
    empty = {"tuition_per_semester": None, "charges_per_semester": None,
             "first_semester_total": None, "first_year_total": None,
             "degree_estimate": None, "has_estimates": False,
             "items": []}
    if not fees:
        return empty
    one_time = sum(f.amount_pkr for f in fees if f.basis == "one_time")
    tuition = 0.0
    recurring = 0.0
    first_only = 0.0
    estimated = any(f.is_estimated for f in fees)
    for f in fees:
        if f.basis == "one_time":
            continue
        value = _per_semester(f, programme)
        if value is None:
            return {**empty, "items": _items(fees)}
        if f.basis == "per_credit_hour":
            estimated = True
        if f.applies_to == "first_only":
            first_only += value
            continue
        recurring += value
        if f.component == "tuition":
            tuition += value
    semesters = int(programme.duration_years * 2)
    return {
        "tuition_per_semester": round(tuition) if tuition else None,
        "charges_per_semester": round(recurring) if recurring else None,
        "first_semester_total": round(one_time + recurring + first_only),
        "first_year_total": round(one_time + 2 * recurring + first_only),
        "degree_estimate": round(one_time + semesters * recurring + first_only),
        "has_estimates": estimated,
        "items": _items(fees),
    }


def _items(fees: list[m.OfferingFee]) -> list[dict]:
    return [{"component": f.component, "amount_pkr": f.amount_pkr, "basis": f.basis,
             "applies_to": f.applies_to, "is_estimated": f.is_estimated} for f in fees]


def _offering_options():
    return (
        joinedload(m.Offering.programme).joinedload(m.Programme.discipline),
        joinedload(m.Offering.programme).joinedload(m.Programme.campus)
        .joinedload(m.Campus.university),
        joinedload(m.Offering.programme).joinedload(m.Programme.campus)
        .joinedload(m.Campus.city),
        joinedload(m.Offering.programme).joinedload(m.Programme.campus)
        .selectinload(m.Campus.hostels),
        joinedload(m.Offering.cycle),
        selectinload(m.Offering.fees),
        selectinload(m.Offering.entry_tests).joinedload(m.OfferingEntryTest.test),
        selectinload(m.Offering.deadlines),
        selectinload(m.Offering.rule_sets).selectinload(m.RuleSetRow.rules),
    )


def live_offerings(db: Session) -> list[m.Offering]:
    """Published offerings to recommend from.

    For each programme: the current-cycle offering if published, otherwise the latest
    older published offering (shown as stale).
    """
    cycle = current_cycle(db)
    rows = db.scalars(
        select(m.Offering)
        .join(m.Offering.programme)
        .join(m.Programme.campus)
        .join(m.Campus.university)
        .where(m.Offering.status == LIVE, m.Programme.status == LIVE,
               m.Campus.status == LIVE, m.University.status == LIVE)
        .options(*_offering_options())
    ).unique().all()
    best: dict[str, m.Offering] = {}
    for o in rows:
        current = best.get(o.programme_id)
        if o.cycle.year > cycle.year:
            continue
        if current is None or o.cycle.year > current.cycle.year:
            best[o.programme_id] = o
    return list(best.values())


def get_offering(db: Session, offering_id: str) -> m.Offering | None:
    return db.scalars(
        select(m.Offering).where(m.Offering.id == offering_id, m.Offering.status == LIVE)
        .options(*_offering_options())
    ).unique().first()


def is_stale(offering: m.Offering, cycle: m.AdmissionCycle) -> bool:
    return offering.cycle.year < cycle.year


def to_rules(offering: m.Offering, cycle: m.AdmissionCycle) -> OfferingRules:
    campus = offering.programme.campus
    return OfferingRules(
        offering_id=offering.id,
        rule_sets=[
            RuleSet(rs.id, rs.name,
                    [Rule(r.id, r.rule_type, r.params, r.is_hard) for r in rs.rules])
            for rs in offering.rule_sets
        ],
        campus_gender_policy=campus.effective_gender_policy,
        is_stale=is_stale(offering, cycle),
        stale_label=offering.cycle.label,
    )


def to_facts(offering: m.Offering, cycle: m.AdmissionCycle) -> OfferingFacts:
    programme = offering.programme
    campus = programme.campus
    fees = fee_summary(offering)
    accredited = None
    if programme.accreditation_status == "accredited":
        accredited = True
    elif programme.accreditation_status == "not_accredited":
        accredited = False
    hostels = {
        h.for_gender: HostelFact(h.availability, h.location, h.fee_per_semester_pkr)
        for h in campus.hostels if h.status == LIVE
    }
    return OfferingFacts(
        offering_id=offering.id,
        discipline_id=programme.discipline_code,
        field_id=programme.discipline.field_code,
        region_code=campus.city.region_code,
        city_id=campus.city_id,
        sector=campus.university.sector,
        gender_policy=campus.effective_gender_policy,
        shift=programme.shift,
        latitude=campus.latitude,
        longitude=campus.longitude,
        accredited=accredited,
        tests=tuple(t.test_code for t in offering.entry_tests),
        tuition_per_semester=fees["tuition_per_semester"],
        charges_per_semester=fees["charges_per_semester"],
        hostels=hostels,
        is_stale=is_stale(offering, cycle),
        is_offered=offering.is_offered,
    )


def offering_card(offering: m.Offering, cycle: m.AdmissionCycle) -> dict:
    """Compact data for lists."""
    programme = offering.programme
    campus = programme.campus
    uni = campus.university
    fees = fee_summary(offering)
    hostel_genders = sorted(h.for_gender for h in campus.hostels
                            if h.status == LIVE and h.availability in ("available", "limited"))
    close = next((d.date.isoformat() for d in offering.deadlines
                  if d.event == "applications_close"), None)
    return {
        "offering_id": offering.id,
        "programme_id": programme.id,
        "programme_title": programme.title,
        "discipline_code": programme.discipline_code,
        "field_code": programme.discipline.field_code,
        "degree_type": programme.degree_type,
        "duration_years": programme.duration_years,
        "shift": programme.shift,
        "university_id": uni.id,
        "university_name": uni.name,
        "university_short_name": uni.short_name,
        "sector": uni.sector,
        "is_demo": uni.is_demo,
        "campus_name": campus.name,
        "city": campus.city.name,
        "region_code": campus.city.region_code,
        "gender_policy": campus.effective_gender_policy,
        "cycle_label": offering.cycle.label,
        "is_stale": is_stale(offering, cycle),
        "is_offered": offering.is_offered,
        "tuition_per_semester": fees["tuition_per_semester"],
        "charges_per_semester": fees["charges_per_semester"],
        "first_year_total": fees["first_year_total"],
        "fee_is_estimated": fees["has_estimates"],
        "entry_tests": [t.test_code for t in offering.entry_tests],
        "hostel_for": hostel_genders,
        "accreditation_body": programme.accreditation_body,
        "accreditation_status": programme.accreditation_status,
        "applications_close": close,
        "verified_at": offering.verified_at.date().isoformat() if offering.verified_at else None,
    }


def offering_detail(db: Session, offering: m.Offering, cycle: m.AdmissionCycle) -> dict:
    programme = offering.programme
    campus = programme.campus
    uni = campus.university
    source = db.get(m.Source, offering.source_id) if offering.source_id else None
    return {
        **offering_card(offering, cycle),
        "seats_total": offering.seats_total,
        "notes": offering.notes,
        "fees": fee_summary(offering),
        "rule_sets": [
            {"name": rs.name,
             "rules": [{"type": r.rule_type, "params": r.params, "is_hard": r.is_hard}
                       for r in rs.rules]}
            for rs in offering.rule_sets
        ],
        "entry_test_details": [{"code": t.test_code, "name": t.test.name,
                                "is_mandatory": t.is_mandatory} for t in offering.entry_tests],
        "deadlines": [{"event": d.event, "date": d.date.isoformat(),
                       "is_tentative": d.is_tentative} for d in offering.deadlines],
        "hostels": [{"for_gender": h.for_gender, "location": h.location,
                     "availability": h.availability,
                     "fee_per_semester_pkr": h.fee_per_semester_pkr}
                    for h in campus.hostels if h.status == LIVE],
        "website_url": uni.website_url,
        "admissions_url": uni.admissions_url,
        "programme_url": programme.programme_url,
        "source": {"title": source.title, "url": source.url, "is_official": source.is_official}
        if source else None,
    }


def universities(db: Session) -> list[m.University]:
    return db.scalars(
        select(m.University).where(m.University.status == LIVE)
        .options(selectinload(m.University.campuses).joinedload(m.Campus.city))
        .order_by(m.University.name)
    ).unique().all()
