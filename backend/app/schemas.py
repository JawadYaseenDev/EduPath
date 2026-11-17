"""Request bodies (validated input). Responses are plain dicts built by services."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RegisterIn(_In):
    email: EmailStr
    password: str = Field(max_length=128)
    full_name: str | None = Field(default=None, max_length=120)
    accept_terms: bool


class LoginIn(_In):
    email: EmailStr
    password: str = Field(max_length=128)


class ProfileIn(_In):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9 \-]{7,20}$")
    gender: Literal["male", "female", "other"] | None = None
    date_of_birth: date | None = None
    current_city_id: str | None = None
    domicile_region_code: str | None = None

    @model_validator(mode="after")
    def _dob(self):
        if self.date_of_birth and not (date(1960, 1, 1) < self.date_of_birth < date.today()):
            raise ValueError("Please enter a valid date of birth.")
        return self


class SubjectMarkIn(_In):
    code: str
    obtained: float | None = Field(default=None, ge=0)
    total: float | None = Field(default=None, gt=0)
    grade: str | None = Field(default=None, max_length=4)

    @model_validator(mode="after")
    def _marks(self):
        if self.obtained is not None and self.total is not None and self.obtained > self.total:
            raise ValueError(f"{self.code}: obtained marks cannot be more than total marks.")
        return self


class QualificationIn(_In):
    type_code: str
    group_code: str
    board_id: str | None = None
    passing_year: int | None = Field(default=None, ge=1980, le=2035)
    result_status: Literal["final", "part1_only", "awaited"] = "final"
    obtained_marks: float | None = Field(default=None, ge=0)
    total_marks: float | None = Field(default=None, gt=0)
    part1_obtained: float | None = Field(default=None, ge=0)
    part1_total: float | None = Field(default=None, gt=0)
    ibcc_percentage: float | None = Field(default=None, ge=0, le=100)
    ibcc_is_official: bool = False
    is_improved_result: bool = False
    subjects: list[SubjectMarkIn] = Field(default_factory=list, max_length=15)

    @model_validator(mode="after")
    def _check(self):
        if (self.obtained_marks is not None and self.total_marks is not None
                and self.obtained_marks > self.total_marks):
            raise ValueError("Obtained marks cannot be more than total marks.")
        if (self.part1_obtained is not None and self.part1_total is not None
                and self.part1_obtained > self.part1_total):
            raise ValueError("Part-I obtained marks cannot be more than Part-I total marks.")
        codes = [s.code for s in self.subjects]
        if len(codes) != len(set(codes)):
            raise ValueError("Each subject can only be added once.")
        return self


class TestScoreIn(_In):
    test_code: str
    year: int = Field(ge=2015, le=2035)
    score: float = Field(ge=0)
    total: float = Field(gt=0)

    @model_validator(mode="after")
    def _check(self):
        if self.score > self.total:
            raise ValueError("Score cannot be more than total.")
        return self


class PreferencesIn(_In):
    regions: list[str] = Field(default_factory=list)
    city_ids: list[str] = Field(default_factory=list)
    max_distance_km: float | None = Field(default=None, gt=0, le=3000)
    max_fee_per_semester: int | None = Field(default=None, ge=0, le=5_000_000)
    budget_includes: Literal["tuition_only", "university_charges", "with_hostel"] = (
        "university_charges")
    sectors: list[Literal["public", "private", "semi_government"]] = Field(default_factory=list)
    hostel_need: Literal["none", "needed", "on_campus_only"] = "none"
    gender_campus_pref: Literal["any", "coeducation", "single_gender"] = "any"
    shifts: list[Literal["morning", "evening", "weekend"]] = Field(default_factory=list)
    require_accreditation: bool = False
    willing_tests: list[str] | None = None
    disciplines: list[str] = Field(default_factory=list)
    fields: list[str] = Field(default_factory=list)


class ShortlistIn(_In):
    offering_id: str


class ReportIn(_In):
    entity_type: Literal["university", "campus", "programme", "offering"]
    entity_id: str
    field: str | None = Field(default=None, max_length=60)
    message: str = Field(min_length=5, max_length=2000)


class ResultModeIn(_In):
    mode: Literal["extended", "strict_pdf"]


class RuleCheckIn(_In):
    rule_type: str
    params: dict
