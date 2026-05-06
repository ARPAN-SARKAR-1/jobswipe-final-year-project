from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    recruiter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
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
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    has_bond: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bond_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    bond_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    moderation_status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    moderation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    recruiter = relationship("User", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    swipes = relationship("Swipe", back_populates="job", cascade="all, delete-orphan")
    chat_threads = relationship("ChatThread", back_populates="job", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="job")
