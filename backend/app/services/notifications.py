from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.notification import Notification
from app.models.user import User


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
    link_url: str | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        link_url=link_url,
    )
    db.add(notification)
    return notification


def notify_admins(
    db: Session,
    title: str,
    message: str,
    notification_type: str,
    link_url: str | None = "/admin/dashboard",
) -> None:
    admin_ids = db.scalars(select(User.id).where(User.role.in_([UserRole.OWNER.value, UserRole.ADMIN.value]))).all()
    for admin_id in admin_ids:
        create_notification(db, admin_id, title, message, notification_type, link_url)
