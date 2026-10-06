import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.notifications import repository
from app.modules.notifications.models import Notification


def list_my_notifications(db: Session, user_id: uuid.UUID) -> list[Notification]:
    return repository.list_by_user(db, user_id)


def mark_notification_read(db: Session, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification:
    notification = repository.get_by_id(db, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    if notification.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this notification")

    if notification.read_at:
        return notification

    return repository.mark_as_read(db, notification)


def notify(db: Session, user_id: uuid.UUID, notification_type: str, title: str, body: str | None = None, commit: bool = True) -> Notification:
    """Convenience function for other modules to create notifications."""
    return repository.create_notification(db, user_id, notification_type, title, body, commit=commit)
