import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.notifications.models import Notification


def create_notification(db: Session, user_id: uuid.UUID, notification_type: str, title: str, body: str | None = None, commit: bool = True) -> Notification:
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        body=body,
    )
    db.add(notification)
    if commit:
        db.commit()
    else:
        db.flush()
    db.refresh(notification)
    return notification


def list_by_user(db: Session, user_id: uuid.UUID) -> list[Notification]:
    return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()


def get_by_id(db: Session, notification_id: uuid.UUID) -> Notification | None:
    return db.query(Notification).filter(Notification.id == notification_id).first()


def mark_as_read(db: Session, notification: Notification) -> Notification:
    notification.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notification)
    return notification
