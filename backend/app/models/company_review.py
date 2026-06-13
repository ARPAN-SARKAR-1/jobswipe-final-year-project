from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ReviewModerationStatus
from app.models.mixins import TimestampMixin


class CompanyReview(TimestampMixin, Base):
    __tablename__ = "company_reviews"
    __table_args__ = (
        UniqueConstraint("company_id", "reviewer_user_id", name="uq_company_reviews_company_reviewer"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_company_reviews_rating_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    review_text: Mapped[str] = mapped_column(Text, nullable=False)
    work_culture_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interview_process_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    growth_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    moderation_status: Mapped[str] = mapped_column(String(30), default=ReviewModerationStatus.VISIBLE.value, nullable=False)

    company = relationship("CompanyProfile", back_populates="reviews")
    reviewer = relationship("User", back_populates="company_reviews")
    application = relationship("Application")
