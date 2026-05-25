from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    recruiter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
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
    eligible_academic_status: Mapped[str] = mapped_column(String(30), default="BOTH", nullable=False)
    eligible_streams: Mapped[str | None] = mapped_column(Text, nullable=True)
    minimum_cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    eligible_graduation_years: Mapped[str | None] = mapped_column(String(255), nullable=True)
    internship_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    recruiter = relationship("User", back_populates="jobs")
    company = relationship("Company", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    swipes = relationship("Swipe", back_populates="job", cascade="all, delete-orphan")
    chat_threads = relationship("ChatThread", back_populates="job", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="job")
    risk_assessment = relationship("JobRiskAssessment", back_populates="job", uselist=False, cascade="all, delete-orphan")

    @property
    def company_verification_status(self) -> str | None:
        return self.company.verification_status if self.company else None

    @property
    def recruiter_verification_status(self) -> str | None:
        profile = self.recruiter.recruiter_profile if self.recruiter else None
        return profile.recruiter_verification_status if profile else None

    @property
    def company_average_rating(self) -> float | None:
        return self.company.average_rating if self.company else None

    @property
    def company_total_reviews(self) -> int | None:
        return self.company.total_reviews if self.company else None

    @property
    def trusted_job(self) -> bool:
        profile = self.recruiter.recruiter_profile if self.recruiter else None
        return bool(
            self.company
            and profile
            and self.company.verification_status == "VERIFIED"
            and profile.recruiter_verification_status == "VERIFIED"
            and profile.company_id == self.company_id
            and self.recruiter.account_status == "ACTIVE"
        )
