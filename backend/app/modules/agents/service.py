import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.agents import repository
from app.modules.agents.models import AgentProfile
from app.modules.agents.schemas import AgentApplicationCreate
from app.modules.agents.state_machine import validate_transition


def apply_as_agent(db: Session, user_id: uuid.UUID, payload: AgentApplicationCreate) -> AgentProfile:
    existing = repository.get_by_user_id(db, user_id)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agent application already exists")

    profile = repository.create_profile(db, user_id, payload.model_dump())
    return profile


def list_agents(db: Session, status: str | None = None) -> list[AgentProfile]:
    return repository.list_by_status(db, status)


def get_my_agent_profile(db: Session, user_id: uuid.UUID) -> AgentProfile | None:
    return repository.get_by_user_id(db, user_id)


def get_agent_or_404(db: Session, agent_profile_id: uuid.UUID) -> AgentProfile:
    profile = repository.get_by_id(db, agent_profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent profile not found")
    return profile


def start_review(db: Session, agent_profile_id: uuid.UUID) -> AgentProfile:
    profile = get_agent_or_404(db, agent_profile_id)
    validate_transition(profile.status, "UNDER_REVIEW")
    return repository.update_status(db, profile, "UNDER_REVIEW")


def review_decision(
    db: Session, agent_profile_id: uuid.UUID, reviewer_id: uuid.UUID, decision: str, notes: str | None
) -> AgentProfile:
    profile = get_agent_or_404(db, agent_profile_id)
    validate_transition(profile.status, decision)

    repository.create_verification_record(db, agent_profile_id, reviewer_id, decision, notes)
    profile = repository.update_status(db, profile, decision)

    from app.modules.notifications.service import notify
    if decision == "VERIFIED":
        notify(db, profile.user_id, "AGENT_VERIFIED", "Agent application approved", "You are now a verified Agent.")
    elif decision == "REJECTED":
        notify(db, profile.user_id, "AGENT_REJECTED", "Agent application rejected", notes or "Your application was not approved.")

    return profile


def suspend_agent(db: Session, agent_profile_id: uuid.UUID, reviewer_id: uuid.UUID, notes: str | None) -> AgentProfile:
    profile = get_agent_or_404(db, agent_profile_id)
    validate_transition(profile.status, "SUSPENDED")

    repository.create_verification_record(db, agent_profile_id, reviewer_id, "SUSPENDED", notes)
    return repository.update_status(db, profile, "SUSPENDED")


def revoke_agent(db: Session, agent_profile_id: uuid.UUID, reviewer_id: uuid.UUID, notes: str | None) -> AgentProfile:
    profile = get_agent_or_404(db, agent_profile_id)
    validate_transition(profile.status, "REVOKED")

    repository.create_verification_record(db, agent_profile_id, reviewer_id, "REVOKED", notes)
    return repository.update_status(db, profile, "REVOKED")
