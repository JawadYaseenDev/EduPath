"""Validated input for the admin API."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator

Sector = Literal["public", "private", "semi_government"]
GenderPolicy = Literal["coeducation", "women_only", "men_only"]


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _url(v):
    return str(HttpUrl(v)) if v else None


class UniversityIn(_In):
    name: str = Field(min_length=3, max_length=200)
    short_name: str | None = Field(default=None, max_length=40)
    aliases: list[str] = Field(default_factory=list, max_length=20)
    sector: Sector
    hec_recognised: bool = True
    gender_policy: GenderPolicy = "coeducation"
    website_url: str | None = None
    admissions_url: str | None = None
    description: str | None = Field(default=None, max_length=2000)
    source_id: str | None = None

    _urls = field_validator("website_url", "admissions_url")(_url)


class CampusIn(_In):
    name: str = Field(min_length=2, max_length=120)
    is_main_campus: bool = False
    city_id: str
    address: str | None = Field(default=None, max_length=300)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    gender_policy: GenderPolicy | None = None
    source_id: str | None = None


class CampusCreate(CampusIn):
    university_id: str


class ProgrammeIn(_In):
    discipline_code: str
    title: str = Field(min_length=2, max_length=200)
    degree_type: str = Field(min_length=2, max_length=30)
    duration_years: float = Field(gt=0, le=7)
    total_credit_hours: int | None = Field(default=None, gt=0, le=300)
    shift: Literal["morning", "evening", "weekend"] = "morning"
    accreditation_body: str | None = Field(default=None, max_length=20)
    accreditation_status: Literal["accredited", "provisional", "not_accredited", "unknown"] | None = None
    programme_url: str | None = None
    source_id: str | None = None

    _urls = field_validator("programme_url")(_url)


class ProgrammeCreate(ProgrammeIn):
    campus_id: str


class HostelIn(_In):
    for_gender: Literal["male", "female"]
    location: Literal["on_campus", "off_campus_university_managed", "affiliated_private"]
    availability: Literal["available", "limited", "not_available", "unknown"]
    fee_per_semester_pkr: int | None = Field(default=None, ge=0, le=2_000_000)
    notes: str | None = Field(default=None, max_length=1000)
    source_id: str | None = None


class HostelCreate(HostelIn):
    campus_id: str


class OfferingCreate(_In):
    programme_id: str
    copy_from_previous: bool = True


class OfferingIn(_In):
    is_offered: bool = True
    seats_total: int | None = Field(default=None, ge=0, le=100_000)
    notes: str | None = Field(default=None, max_length=2000)
    source_id: str | None = None


class FeeIn(_In):
    component: Literal["admission", "tuition", "registration", "exam", "library", "lab",
                       "security_refundable", "other"]
    amount_pkr: int = Field(ge=0, le=10_000_000)
    basis: Literal["one_time", "per_semester", "per_year", "per_credit_hour"]
    applies_to: Literal["all", "first_only"] = "all"
    is_estimated: bool = False


class TestIn(_In):
    test_code: str
    is_mandatory: bool = True


class DeadlineIn(_In):
    event: Literal["applications_open", "applications_close", "test_date", "merit_list",
                   "classes_start"]
    date: date
    is_tentative: bool = False


class RuleIn(_In):
    rule_type: str
    params: dict
    is_hard: bool = True


class RuleSetIn(_In):
    name: str
    rules: list[RuleIn]


class SourceIn(_In):
    kind: Literal["web_page", "pdf_prospectus", "official_notice", "email_from_university",
                  "phone_call_note"]
    title: str = Field(min_length=3, max_length=200)
    url: str | None = None
    page_numbers: str | None = Field(default=None, max_length=40)
    publisher: str | None = Field(default=None, max_length=160)
    is_official: bool = True

    _urls = field_validator("url")(_url)


class ReviewIn(_In):
    note: str = Field(default="", max_length=1000)


class RejectIn(_In):
    note: str = Field(min_length=3, max_length=1000)


class ReportStatusIn(_In):
    status: Literal["new", "in_review", "fixed", "rejected"]


class CycleIn(_In):
    year: int = Field(ge=2020, le=2100)
    label: str = Field(min_length=3, max_length=40)


class StaffIn(_In):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["super_admin", "data_editor", "data_verifier", "support"]


class RoleIn(_In):
    role: Literal["student", "super_admin", "data_editor", "data_verifier", "support"]


class RuleTestIn(_In):
    rule_sets: list[RuleSetIn]
    campus_gender_policy: GenderPolicy = "coeducation"
