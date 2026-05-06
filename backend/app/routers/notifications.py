from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationActionRead, NotificationRead, UnreadCountRead

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationRead])
def notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[Notification]:
    return list(
        db.scalars(
            select(Notification)
            .where(Notification.user_id == current_user.id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(80)
        ).all()
    )


@router.get("/unread-count", response_model=UnreadCountRead)
def unread_count(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UnreadCountRead:
    count = (
        db.scalar(
            select(func.count(Notification.id))
            .where(Notification.user_id == current_user.id)
            .where(Notification.is_read.is_(False))
        )
        or 0
    )
    return UnreadCountRead(unread_count=count)


@router.put("/read-all", response_model=NotificationActionRead)
def mark_all_read(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> NotificationActionRead:
    notifications_to_update = db.scalars(
        select(Notification).where(Notification.user_id == current_user.id).where(Notification.is_read.is_(False))
    ).all()
    for notification in notifications_to_update:
        notification.is_read = True
    db.commit()
    return NotificationActionRead(message="All notifications marked as read")


@router.put("/{notification_id}/read", response_model=NotificationRead)
def mark_read(
    notification_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Notification:
    notification = db.scalar(
        select(Notification).where(Notification.id == notification_id).where(Notification.user_id == current_user.id)
    )
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
