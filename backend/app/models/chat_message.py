from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class ChatMessage(TimestampMixin, Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("chat_threads.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_for_sender: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_for_receiver: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    thread = relationship("ChatThread", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="chat_messages")

    @property
    def sender_name(self) -> str | None:
        return self.sender.name if self.sender else None

    @property
    def sender_role(self) -> str | None:
        return self.sender.role if self.sender else None
