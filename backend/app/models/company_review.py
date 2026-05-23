from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class CompanyReview(TimestampMixin, Base):
    __tablename__ = "company_reviews"
    __table_args__ = (
        UniqueConstraint("company_id", "job_seeker_id", name="uq_company_review_company_job_seeker"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_company_reviews_rating_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    job_seeker_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    company = relationship("Company", back_populates="reviews")
    job_seeker = relationship("User", back_populates="company_reviews")
