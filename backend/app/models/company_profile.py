from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import CompanyType, CompanyVerificationStatus
from app.models.mixins import TimestampMixin


class CompanyProfile(TimestampMixin, Base):
    __tablename__ = "company_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_company_id: Mapped[str | None] = mapped_column(String(12), unique=True, index=True, nullable=True)
    slug: Mapped[str | None] = mapped_column(String(90), unique=True, index=True, nullable=True)
    recruiter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    company_logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    company_type: Mapped[str] = mapped_column(String(30), default=CompanyType.OTHER.value, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(160), nullable=True)
    official_email_domain: Mapped[str | None] = mapped_column(String(160), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(30), default=CompanyVerificationStatus.PENDING.value, nullable=False)
    recruiter_verification_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    verification_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verified_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rating_average: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    recruiter = relationship("User", foreign_keys=[recruiter_id], back_populates="company_profile")
    verified_by_admin = relationship("User", foreign_keys=[verified_by_admin_id])
    members = relationship("RecruiterCompanyMember", back_populates="company", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="company")
    reviews = relationship("CompanyReview", back_populates="company", cascade="all, delete-orphan")

    @property
    def name(self) -> str | None:
        return self.company_name

    @property
    def logo_url(self) -> str | None:
        return self.company_logo_url
