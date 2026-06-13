from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import DocumentVerificationStatus
from app.models.mixins import TimestampMixin


class UserDocument(TimestampMixin, Base):
    __tablename__ = "user_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    document_type: Mapped[str] = mapped_column(String(60), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    visibility: Mapped[str] = mapped_column(String(30), default="PRIVATE", nullable=False)
    verification_status: Mapped[str] = mapped_column(String(30), default=DocumentVerificationStatus.PENDING.value, nullable=False)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner = relationship("User", foreign_keys=[owner_user_id], back_populates="documents")
    reviewer = relationship("User", foreign_keys=[reviewed_by], back_populates="reviewed_documents")
