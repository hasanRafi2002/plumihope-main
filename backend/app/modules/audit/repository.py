import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog


def create_log(
    db: Session,
    actor_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    before: dict | None = None,
    after: dict | None = None,
    metadata: dict | None = None,
    commit: bool = True,
) -> AuditLog:
    log = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before=before,
        after=after,
        event_metadata=metadata,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    if commit:
        db.commit()
    else:
        db.flush()
    return log
