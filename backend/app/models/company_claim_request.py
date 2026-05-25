from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class CompanyClaimRequest(TimestampMixin, Base):
    __tablename__ = "company_claim_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    requested_company_name: Mapped[str] = mapped_column(String(160), nullable=False)
    requested_domain: Mapped[str] = mapped_column(String(160), nullable=False)
    requester_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    official_email: Mapped[str] = mapped_column(String(255), nullable=False)
    claim_status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    verification_token_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reviewed_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(30), default="LOW", nullable=False)
    requires_admin_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    risk_reasons: Mapped[str | None] = mapped_column(Text, nullable=True)

    company = relationship("Company", back_populates="claim_requests")
    requester = relationship("User", foreign_keys=[requester_user_id], back_populates="company_claim_requests")
    reviewed_by_admin = relationship("User", foreign_keys=[reviewed_by_admin_id])
