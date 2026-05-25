from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class CompanyReview(TimestampMixin, Base):
    __tablename__ = "company_reviews"
    __table_args__ = (
        UniqueConstraint("company_id", "job_seeker_id", name="uq_company_review_company_job_seeker"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_company_reviews_rating_range"),
        CheckConstraint("overall_rating >= 1 AND overall_rating <= 5", name="ck_company_reviews_overall_rating_range"),
        CheckConstraint("work_culture_rating >= 1 AND work_culture_rating <= 5", name="ck_company_reviews_work_culture_rating_range"),
        CheckConstraint("interview_process_rating >= 1 AND interview_process_rating <= 5", name="ck_company_reviews_interview_process_rating_range"),
        CheckConstraint("salary_transparency_rating >= 1 AND salary_transparency_rating <= 5", name="ck_company_reviews_salary_transparency_rating_range"),
        CheckConstraint("growth_opportunity_rating >= 1 AND growth_opportunity_rating <= 5", name="ck_company_reviews_growth_opportunity_rating_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    job_seeker_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_rating: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    work_culture_rating: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    interview_process_rating: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    salary_transparency_rating: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    growth_opportunity_rating: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    review_title: Mapped[str | None] = mapped_column(String(160), nullable=True)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    pros: Mapped[str | None] = mapped_column(Text, nullable=True)
    cons: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    moderation_status: Mapped[str] = mapped_column(String(30), default="VISIBLE", nullable=False)

    company = relationship("Company", back_populates="reviews")
    job_seeker = relationship("User", back_populates="company_reviews")
    application = relationship("Application")
