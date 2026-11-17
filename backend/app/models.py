"""Database tables. See docs/DATABASE_DESIGN.md for the full design and reasons.

Written for SQLAlchemy 2 so the same models run on SQLite (local development) and
PostgreSQL / Supabase (staging and production).
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def new_id() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now(UTC)


class IdMixin:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class VerifiedMixin:
    """Every catalogue fact carries a status and a source."""

    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|pending_review|verified|published|archived
    source_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[str | None] = mapped_column(String(36), nullable=True)


# ===================================================================== reference


class Region(Base):
    __tablename__ = "regions"
    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    name_ur: Mapped[str | None] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(20))  # province | territory
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class City(Base, IdMixin):
    __tablename__ = "cities"
    region_code: Mapped[str] = mapped_column(ForeignKey("regions.code"))
    name: Mapped[str] = mapped_column(String(80))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)


class ExamBoard(Base, IdMixin):
    __tablename__ = "exam_boards"
    name: Mapped[str] = mapped_column(String(160))
    short_name: Mapped[str] = mapped_column(String(40))
    kind: Mapped[str] = mapped_column(String(20))  # bise | federal | private | foreign | technical
    region_code: Mapped[str | None] = mapped_column(ForeignKey("regions.code"))


class QualificationType(Base):
    __tablename__ = "qualification_types"
    code: Mapped[str] = mapped_column(String(30), primary_key=True)
    level: Mapped[str] = mapped_column(String(10))  # SSC | HSSC | DIPLOMA
    name: Mapped[str] = mapped_column(String(80))
    uses_ibcc: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class QualificationGroup(Base):
    __tablename__ = "qualification_groups"
    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    type_code: Mapped[str] = mapped_column(ForeignKey("qualification_types.code"))
    name: Mapped[str] = mapped_column(String(80))
    allows_custom_subjects: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Subject(Base):
    __tablename__ = "subjects"
    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))


class GroupSubject(Base):
    __tablename__ = "group_subjects"
    group_code: Mapped[str] = mapped_column(ForeignKey("qualification_groups.code"), primary_key=True)
    subject_code: Mapped[str] = mapped_column(ForeignKey("subjects.code"), primary_key=True)
    is_compulsory: Mapped[bool] = mapped_column(Boolean, default=True)
    choice_set: Mapped[str | None] = mapped_column(String(20))  # same value = "pick one"


class ProgrammeField(Base):
    __tablename__ = "programme_fields"
    code: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    icon: Mapped[str | None] = mapped_column(String(40))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Discipline(Base):
    __tablename__ = "disciplines"
    code: Mapped[str] = mapped_column(String(30), primary_key=True)
    field_code: Mapped[str] = mapped_column(ForeignKey("programme_fields.code"))
    name: Mapped[str] = mapped_column(String(80))


class EntryTest(Base):
    __tablename__ = "entry_tests"
    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    conducted_by: Mapped[str | None] = mapped_column(String(120))


class AdmissionCycle(Base, IdMixin):
    __tablename__ = "admission_cycles"
    year: Mapped[int] = mapped_column(Integer, unique=True)
    label: Mapped[str] = mapped_column(String(40))
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)


class Source(Base, IdMixin, TimestampMixin):
    __tablename__ = "sources"
    kind: Mapped[str] = mapped_column(String(30))  # web_page | pdf_prospectus | official_notice | demo
    title: Mapped[str] = mapped_column(String(200))
    url: Mapped[str | None] = mapped_column(String(500))
    page_numbers: Mapped[str | None] = mapped_column(String(40))
    publisher: Mapped[str | None] = mapped_column(String(160))
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AppSetting(Base):
    __tablename__ = "app_settings"
    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)


# ===================================================================== catalogue


class University(Base, IdMixin, TimestampMixin, VerifiedMixin):
    __tablename__ = "universities"
    name: Mapped[str] = mapped_column(String(200))
    short_name: Mapped[str | None] = mapped_column(String(40))
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    sector: Mapped[str] = mapped_column(String(20))  # public | private | semi_government
    hec_recognised: Mapped[bool] = mapped_column(Boolean, default=True)
    gender_policy: Mapped[str] = mapped_column(String(20), default="coeducation")
    website_url: Mapped[str | None] = mapped_column(String(300))
    admissions_url: Mapped[str | None] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    # Demo records are fictional sample data and are always labelled in the app.
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    campuses: Mapped[list[Campus]] = relationship(back_populates="university",
                                                  cascade="all, delete-orphan")


class Campus(Base, IdMixin, TimestampMixin, VerifiedMixin):
    __tablename__ = "campuses"
    university_id: Mapped[str] = mapped_column(ForeignKey("universities.id"))
    name: Mapped[str] = mapped_column(String(120))
    is_main_campus: Mapped[bool] = mapped_column(Boolean, default=False)
    city_id: Mapped[str] = mapped_column(ForeignKey("cities.id"))
    address: Mapped[str | None] = mapped_column(String(300))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    gender_policy: Mapped[str | None] = mapped_column(String(20))  # overrides university

    university: Mapped[University] = relationship(back_populates="campuses")
    city: Mapped[City] = relationship()
    programmes: Mapped[list[Programme]] = relationship(back_populates="campus",
                                                       cascade="all, delete-orphan")
    hostels: Mapped[list[Hostel]] = relationship(back_populates="campus",
                                                 cascade="all, delete-orphan")

    @property
    def effective_gender_policy(self) -> str:
        return self.gender_policy or self.university.gender_policy


class Programme(Base, IdMixin, TimestampMixin, VerifiedMixin):
    __tablename__ = "programmes"
    campus_id: Mapped[str] = mapped_column(ForeignKey("campuses.id"))
    discipline_code: Mapped[str] = mapped_column(ForeignKey("disciplines.code"))
    title: Mapped[str] = mapped_column(String(200))
    degree_type: Mapped[str] = mapped_column(String(30))
    duration_years: Mapped[float] = mapped_column(Float, default=4)
    total_credit_hours: Mapped[int | None] = mapped_column(Integer)
    shift: Mapped[str] = mapped_column(String(20), default="morning")
    accreditation_body: Mapped[str | None] = mapped_column(String(20))
    accreditation_status: Mapped[str | None] = mapped_column(String(20))  # accredited|provisional|not_accredited|unknown
    programme_url: Mapped[str | None] = mapped_column(String(300))

    campus: Mapped[Campus] = relationship(back_populates="programmes")
    discipline: Mapped[Discipline] = relationship()
    offerings: Mapped[list[Offering]] = relationship(back_populates="programme",
                                                     cascade="all, delete-orphan")


class Offering(Base, IdMixin, TimestampMixin, VerifiedMixin):
    """One programme in one admission cycle."""

    __tablename__ = "offerings"
    __table_args__ = (UniqueConstraint("programme_id", "cycle_id"),)
    programme_id: Mapped[str] = mapped_column(ForeignKey("programmes.id"))
    cycle_id: Mapped[str] = mapped_column(ForeignKey("admission_cycles.id"))
    is_offered: Mapped[bool] = mapped_column(Boolean, default=True)
    seats_total: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    carried_from_cycle_id: Mapped[str | None] = mapped_column(ForeignKey("admission_cycles.id"))

    programme: Mapped[Programme] = relationship(back_populates="offerings")
    cycle: Mapped[AdmissionCycle] = relationship(foreign_keys=[cycle_id])
    rule_sets: Mapped[list[RuleSetRow]] = relationship(back_populates="offering",
                                                       cascade="all, delete-orphan",
                                                       order_by="RuleSetRow.priority")
    fees: Mapped[list[OfferingFee]] = relationship(back_populates="offering",
                                                   cascade="all, delete-orphan")
    entry_tests: Mapped[list[OfferingEntryTest]] = relationship(back_populates="offering",
                                                                cascade="all, delete-orphan")
    deadlines: Mapped[list[OfferingDeadline]] = relationship(back_populates="offering",
                                                             cascade="all, delete-orphan",
                                                             order_by="OfferingDeadline.date")
    source: Mapped[Source | None] = relationship()


class RuleSetRow(Base, IdMixin, TimestampMixin):
    __tablename__ = "eligibility_rule_sets"
    offering_id: Mapped[str] = mapped_column(ForeignKey("offerings.id"))
    name: Mapped[str] = mapped_column(String(120))
    priority: Mapped[int] = mapped_column(Integer, default=0)

    offering: Mapped[Offering] = relationship(back_populates="rule_sets")
    rules: Mapped[list[RuleRow]] = relationship(back_populates="rule_set",
                                                cascade="all, delete-orphan")


class RuleRow(Base, IdMixin, TimestampMixin):
    __tablename__ = "eligibility_rules"
    rule_set_id: Mapped[str] = mapped_column(ForeignKey("eligibility_rule_sets.id"))
    rule_type: Mapped[str] = mapped_column(String(40))
    params: Mapped[dict] = mapped_column(JSON)
    is_hard: Mapped[bool] = mapped_column(Boolean, default=True)
    source_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id"))

    rule_set: Mapped[RuleSetRow] = relationship(back_populates="rules")


class OfferingFee(Base, IdMixin):
    __tablename__ = "offering_fees"
    offering_id: Mapped[str] = mapped_column(ForeignKey("offerings.id"))
    component: Mapped[str] = mapped_column(String(30))  # admission|tuition|registration|exam|lab|security_refundable|other
    amount_pkr: Mapped[int] = mapped_column(Integer)
    basis: Mapped[str] = mapped_column(String(20))  # one_time|per_semester|per_year|per_credit_hour
    applies_to: Mapped[str] = mapped_column(String(20), default="all")  # all | first_only
    is_estimated: Mapped[bool] = mapped_column(Boolean, default=False)

    offering: Mapped[Offering] = relationship(back_populates="fees")


class OfferingEntryTest(Base, IdMixin):
    __tablename__ = "offering_entry_tests"
    offering_id: Mapped[str] = mapped_column(ForeignKey("offerings.id"))
    test_code: Mapped[str] = mapped_column(ForeignKey("entry_tests.code"))
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    weightage_percent: Mapped[float | None] = mapped_column(Float)

    offering: Mapped[Offering] = relationship(back_populates="entry_tests")
    test: Mapped[EntryTest] = relationship()


class OfferingDeadline(Base, IdMixin):
    __tablename__ = "offering_deadlines"
    offering_id: Mapped[str] = mapped_column(ForeignKey("offerings.id"))
    event: Mapped[str] = mapped_column(String(30))  # applications_open|applications_close|test_date|classes_start
    date: Mapped[date] = mapped_column(Date)
    is_tentative: Mapped[bool] = mapped_column(Boolean, default=False)

    offering: Mapped[Offering] = relationship(back_populates="deadlines")


class Hostel(Base, IdMixin, TimestampMixin, VerifiedMixin):
    __tablename__ = "hostels"
    campus_id: Mapped[str] = mapped_column(ForeignKey("campuses.id"))
    for_gender: Mapped[str] = mapped_column(String(10))  # male | female
    location: Mapped[str] = mapped_column(String(40))
    availability: Mapped[str] = mapped_column(String(20))  # available|limited|not_available|unknown
    fee_per_semester_pkr: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)

    campus: Mapped[Campus] = relationship(back_populates="hostels")


# ===================================================================== students


class User(Base, IdMixin, TimestampMixin):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20), default="student")
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    token_version: Mapped[int] = mapped_column(Integer, default=0)  # bump to log out everywhere
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    profile: Mapped[StudentProfile | None] = relationship(back_populates="user",
                                                          cascade="all, delete-orphan")


class StudentProfile(Base, TimestampMixin):
    __tablename__ = "student_profiles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(20))
    gender: Mapped[str | None] = mapped_column(String(10))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    current_city_id: Mapped[str | None] = mapped_column(ForeignKey("cities.id"))
    domicile_region_code: Mapped[str | None] = mapped_column(ForeignKey("regions.code"))
    # Preferences kept as JSON on the profile for now (small, per user).
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    data_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    user: Mapped[User] = relationship(back_populates="profile")
    qualifications: Mapped[list[StudentQualification]] = relationship(
        cascade="all, delete-orphan", primaryjoin="StudentProfile.user_id == foreign(StudentQualification.user_id)")
    test_scores: Mapped[list[StudentTestScore]] = relationship(
        cascade="all, delete-orphan", primaryjoin="StudentProfile.user_id == foreign(StudentTestScore.user_id)")


class StudentQualification(Base, IdMixin, TimestampMixin):
    __tablename__ = "student_qualifications"
    __table_args__ = (UniqueConstraint("user_id", "level"),)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    level: Mapped[str] = mapped_column(String(10))
    type_code: Mapped[str] = mapped_column(ForeignKey("qualification_types.code"))
    group_code: Mapped[str] = mapped_column(ForeignKey("qualification_groups.code"))
    board_id: Mapped[str | None] = mapped_column(ForeignKey("exam_boards.id"))
    passing_year: Mapped[int | None] = mapped_column(Integer)
    result_status: Mapped[str] = mapped_column(String(20), default="final")
    obtained_marks: Mapped[float | None] = mapped_column(Float)
    total_marks: Mapped[float | None] = mapped_column(Float)
    part1_obtained: Mapped[float | None] = mapped_column(Float)
    part1_total: Mapped[float | None] = mapped_column(Float)
    ibcc_percentage: Mapped[float | None] = mapped_column(Float)
    ibcc_is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    is_improved_result: Mapped[bool] = mapped_column(Boolean, default=False)
    # [{"code": "MATH", "obtained": 180, "total": 200}]
    subjects: Mapped[list] = mapped_column(JSON, default=list)


class StudentTestScore(Base, IdMixin):
    __tablename__ = "student_test_scores"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    test_code: Mapped[str] = mapped_column(ForeignKey("entry_tests.code"))
    year: Mapped[int] = mapped_column(Integer)
    score: Mapped[float] = mapped_column(Float)
    total: Mapped[float] = mapped_column(Float)


class Shortlist(Base, IdMixin):
    __tablename__ = "shortlists"
    __table_args__ = (UniqueConstraint("user_id", "offering_id"),)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    offering_id: Mapped[str] = mapped_column(ForeignKey("offerings.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class RecommendationRun(Base, IdMixin):
    __tablename__ = "recommendation_runs"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    engine_version: Mapped[str] = mapped_column(String(20))
    mode: Mapped[str] = mapped_column(String(20))
    inputs_snapshot: Mapped[dict] = mapped_column(JSON)
    summary: Mapped[dict] = mapped_column(JSON)  # counts + no-match info
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    results: Mapped[list[RecommendationResultRow]] = relationship(cascade="all, delete-orphan")


class RecommendationResultRow(Base, IdMixin):
    __tablename__ = "recommendation_results"
    run_id: Mapped[str] = mapped_column(ForeignKey("recommendation_runs.id"), index=True)
    offering_id: Mapped[str] = mapped_column(ForeignKey("offerings.id"))
    category: Mapped[str] = mapped_column(String(30))
    recommended: Mapped[bool] = mapped_column(Boolean)
    rule_set_name: Mapped[str | None] = mapped_column(String(120))
    rule_outcomes: Mapped[list] = mapped_column(JSON)
    next_steps: Mapped[list] = mapped_column(JSON)
    misses: Mapped[list] = mapped_column(JSON)
    within_preferences: Mapped[bool] = mapped_column(Boolean)
    match_score: Mapped[float] = mapped_column(Float)
    rank: Mapped[int] = mapped_column(Integer)


class DataReport(Base, IdMixin, TimestampMixin):
    __tablename__ = "data_reports"
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    entity_type: Mapped[str] = mapped_column(String(30))
    entity_id: Mapped[str] = mapped_column(String(36))
    field: Mapped[str | None] = mapped_column(String(60))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="new")


class AuditLog(Base, IdMixin):
    __tablename__ = "audit_log"
    actor_id: Mapped[str | None] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(30))
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str | None] = mapped_column(String(36))
    before: Mapped[dict | None] = mapped_column(JSON)
    after: Mapped[dict | None] = mapped_column(JSON)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
