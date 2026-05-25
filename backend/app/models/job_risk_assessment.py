from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class JobRiskAssessment(TimestampMixin, Base):
    __tablename__ = "job_risk_assessments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(30), default="LOW", nullable=False)
    reasons: Mapped[str | None] = mapped_column(Text, nullable=True)
    auto_action: Mapped[str] = mapped_column(String(30), default="NONE", nullable=False)
    reviewed_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    job = relationship("Job", back_populates="risk_assessment")
    reviewed_by_admin = relationship("User", foreign_keys=[reviewed_by_admin_id])
