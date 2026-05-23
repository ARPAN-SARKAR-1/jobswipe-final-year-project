from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_name: Mapped[str] = mapped_column(String(160), nullable=False)
    company_logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    company_type: Mapped[str] = mapped_column(String(80), default="Other", nullable=False)
    industry: Mapped[str | None] = mapped_column(String(160), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    official_email_domain: Mapped[str | None] = mapped_column(String(160), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    headquarters_location: Mapped[str | None] = mapped_column(String(160), nullable=True)
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(80), nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    verification_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    average_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    verified_by_admin = relationship("User", foreign_keys=[verified_by_admin_id])
    recruiters = relationship("RecruiterProfile", back_populates="company")
    jobs = relationship("Job", back_populates="company")
    reviews = relationship("CompanyReview", back_populates="company", cascade="all, delete-orphan")
