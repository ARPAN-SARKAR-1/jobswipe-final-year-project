from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import JobCareerLinkStatus, JobSourceType
from app.models.mixins import TimestampMixin


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_public_id: Mapped[str | None] = mapped_column(String(12), unique=True, index=True, nullable=True)
    recruiter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("company_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    company_name: Mapped[str] = mapped_column(String(160), nullable=False)
    company_logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    location: Mapped[str] = mapped_column(String(160), nullable=False)
    job_type: Mapped[str] = mapped_column(String(40), nullable=False)
    work_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    salary: Mapped[str | None] = mapped_column(String(120), nullable=True)
    required_skills: Mapped[str] = mapped_column(Text, nullable=False)
    required_experience_level: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    eligibility: Mapped[str | None] = mapped_column(Text, nullable=True)
    career_page_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    official_apply_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_type: Mapped[str] = mapped_column(String(40), default=JobSourceType.COMPANY_PORTAL.value, nullable=False)
    career_link_status: Mapped[str] = mapped_column(String(40), default=JobCareerLinkStatus.LINK_NOT_CHECKED.value, nullable=False)
    career_link_warning: Mapped[str | None] = mapped_column(Text, nullable=True)
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    has_bond: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bond_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    bond_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    moderation_status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    moderation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    risk_flags: Mapped[str | None] = mapped_column(Text, nullable=True)

    recruiter = relationship("User", back_populates="jobs")
    company = relationship("CompanyProfile", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    swipes = relationship("Swipe", back_populates="job", cascade="all, delete-orphan")
    chat_threads = relationship("ChatThread", back_populates="job", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="job")
