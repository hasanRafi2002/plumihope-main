import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.help_requests.models import HelpRequest, HelpRequestAgent, HelpRequestEvent


def create_help_request(db: Session, user_id: uuid.UUID, data: dict) -> HelpRequest:
    help_request = HelpRequest(user_id=user_id, status="SUBMITTED", **data)
    db.add(help_request)
    db.commit()
    db.refresh(help_request)
    return help_request


def list_help_requests(db: Session, status: str | None = None) -> list[HelpRequest]:
    query = db.query(HelpRequest)
    if status:
        query = query.filter(HelpRequest.status == status)
    return query.order_by(HelpRequest.created_at.desc()).all()


def list_by_user(db: Session, user_id: uuid.UUID, status: str | None = None) -> list[HelpRequest]:
    query = db.query(HelpRequest).filter(HelpRequest.user_id == user_id)
    if status:
        query = query.filter(HelpRequest.status == status)
    return query.order_by(HelpRequest.created_at.desc()).all()


def get_help_request(db: Session, help_request_id: uuid.UUID) -> HelpRequest | None:
    return db.query(HelpRequest).filter(HelpRequest.id == help_request_id).first()


def update_status(db: Session, help_request: HelpRequest, new_status: str) -> HelpRequest:
    help_request.status = new_status
    db.commit()
    db.refresh(help_request)
    return help_request


def create_claim(db: Session, help_request_id: uuid.UUID, agent_profile_id: uuid.UUID) -> HelpRequestAgent:
    claim = HelpRequestAgent(
        help_request_id=help_request_id, agent_profile_id=agent_profile_id, role="CLAIMANT"
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


def get_active_claim(db: Session, help_request_id: uuid.UUID) -> HelpRequestAgent | None:
    return (
        db.query(HelpRequestAgent)
        .filter(HelpRequestAgent.help_request_id == help_request_id)
        .first()
    )


def list_claimed_by_agent(db: Session, agent_profile_id: uuid.UUID) -> list[HelpRequest]:
    return (
        db.query(HelpRequest)
        .join(HelpRequestAgent, HelpRequestAgent.help_request_id == HelpRequest.id)
        .filter(HelpRequestAgent.agent_profile_id == agent_profile_id)
        .order_by(HelpRequest.created_at.desc())
        .all()
    )


def create_event(db: Session, help_request_id: uuid.UUID, actor_id: uuid.UUID | None, event_type: str, notes: str | None = None) -> HelpRequestEvent:
    event = HelpRequestEvent(
        help_request_id=help_request_id,
        actor_id=actor_id,
        event_type=event_type,
        notes=notes,
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
