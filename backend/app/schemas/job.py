from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from app.models.enums import JobModerationStatus
from app.utils.skills import normalize_skills, split_skills


class JobBase(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    company_name: str = Field(min_length=2, max_length=160)
    company_logo_url: str | None = Field(default=None, max_length=500)
    location: str = Field(min_length=2, max_length=160)
    job_type: str = Field(min_length=2, max_length=40)
    work_mode: str = Field(min_length=2, max_length=40)
    salary: str | None = Field(default=None, max_length=120)
    required_skills: str = Field(min_length=2)
    required_experience_level: str = Field(min_length=2, max_length=40)
    description: str = Field(min_length=10)
    eligibility: str | None = None
    deadline: date
    is_active: bool = True
    has_bond: bool = False
    bond_years: float | None = Field(default=None, ge=0)
    bond_details: str | None = None

    @field_validator("required_skills", mode="before")
    @classmethod
    def normalize_required_skills(cls, value: Any) -> str:
        return normalize_skills(value)

    @model_validator(mode="after")
    def validate_bond(self) -> "JobBase":
        if self.has_bond and self.bond_years is None:
            raise ValueError("Bond period in years is required when a job has a bond")
        if not self.has_bond:
            self.bond_years = None
            self.bond_details = None
        return self

    @computed_field
    @property
    def required_skills_list(self) -> list[str]:
        return split_skills(self.required_skills)


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=180)
    company_name: str | None = Field(default=None, min_length=2, max_length=160)
    company_logo_url: str | None = Field(default=None, max_length=500)
    location: str | None = Field(default=None, min_length=2, max_length=160)
    job_type: str | None = Field(default=None, min_length=2, max_length=40)
    work_mode: str | None = Field(default=None, min_length=2, max_length=40)
    salary: str | None = Field(default=None, max_length=120)
    required_skills: str | None = Field(default=None, min_length=2)
    required_experience_level: str | None = Field(default=None, min_length=2, max_length=40)
    description: str | None = Field(default=None, min_length=10)
    eligibility: str | None = None
    deadline: date | None = None
    is_active: bool | None = None
    has_bond: bool | None = None
    bond_years: float | None = Field(default=None, ge=0)
    bond_details: str | None = None

    @field_validator("required_skills", mode="before")
    @classmethod
    def normalize_required_skills(cls, value: Any) -> str | None:
        if value is None:
            return None
        return normalize_skills(value)

    @model_validator(mode="after")
    def validate_bond(self) -> "JobUpdate":
        if self.has_bond is True and self.bond_years is None:
            raise ValueError("Bond period in years is required when a job has a bond")
        if self.has_bond is False:
            self.bond_years = None
            self.bond_details = None
        return self


class JobRead(JobBase):
    id: int
    recruiter_id: int
    moderation_status: JobModerationStatus = JobModerationStatus.ACTIVE
    moderation_reason: str | None = None
    match_score: int | None = None
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    match_note: str | None = None
    existing_application_status: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
