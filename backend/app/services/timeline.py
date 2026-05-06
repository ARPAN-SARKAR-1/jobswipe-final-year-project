from sqlalchemy.orm import Session

from app.models.application_timeline import ApplicationTimeline


def add_timeline_event(
    db: Session,
    application_id: int,
    action: str,
    old_status: str | None = None,
    new_status: str | None = None,
    note: str | None = None,
    created_by_user_id: int | None = None,
) -> ApplicationTimeline:
    event = ApplicationTimeline(
        application_id=application_id,
        action=action,
        old_status=old_status,
        new_status=new_status,
        note=note,
        created_by_user_id=created_by_user_id,
    )
    db.add(event)
    return event
