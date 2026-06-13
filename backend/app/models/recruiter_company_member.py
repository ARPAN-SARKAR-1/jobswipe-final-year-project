from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import CompanyJoinStatus, RecruiterVerificationStatus
from app.models.mixins import TimestampMixin


class RecruiterCompanyMember(TimestampMixin, Base):
    __tablename__ = "recruiter_company_members"
    __table_args__ = (
        UniqueConstraint("recruiter_id", name="uq_recruiter_company_members_recruiter_id"),
        UniqueConstraint("company_id", "recruiter_id", name="uq_recruiter_company_members_company_recruiter"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    recruiter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    designation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    work_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(30), default=RecruiterVerificationStatus.PENDING.value, nullable=False)
    company_join_status: Mapped[str] = mapped_column(String(30), default=CompanyJoinStatus.PENDING.value, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verified_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_by_company_owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    recruiter = relationship("User", foreign_keys=[recruiter_id], back_populates="company_memberships")
    company = relationship("CompanyProfile", back_populates="members")
    verified_by_admin = relationship("User", foreign_keys=[verified_by_admin_id])
    verified_by_company_owner = relationship("User", foreign_keys=[verified_by_company_owner_id])
