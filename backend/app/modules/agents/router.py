import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_permission, require_role
from app.modules.auth.dependencies import get_current_user
from app.modules.agents import service
from app.modules.agents.schemas import AgentApplicationCreate, AgentProfilePublic, AgentProfileDetail, AgentReviewDecision
from app.modules.users.models import User

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/apply", response_model=AgentProfileDetail, status_code=201)
def apply_as_agent(
    payload: AgentApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.apply_as_agent(db, current_user.id, payload)


@router.get("", response_model=list[AgentProfilePublic])
def list_agents(
    status: str | None = Query(default=None),
    current_user: User = Depends(require_permission("agent:review")),
    db: Session = Depends(get_db),
):
    return service.list_agents(db, status)


@router.get("/me", response_model=AgentProfileDetail | None)
def get_my_agent_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.get_my_agent_profile(db, current_user.id)


@router.get("/{agent_profile_id}", response_model=AgentProfileDetail)
def get_agent(agent_profile_id: uuid.UUID, db: Session = Depends(get_db)):
    return service.get_agent_or_404(db, agent_profile_id)


@router.post("/{agent_profile_id}/start-review", response_model=AgentProfileDetail)
def start_review(
    agent_profile_id: uuid.UUID,
    current_user: User = Depends(require_permission("agent:review")),
    db: Session = Depends(get_db),
):
    return service.start_review(db, agent_profile_id)


@router.post("/{agent_profile_id}/decision", response_model=AgentProfileDetail)
def review_decision(
    agent_profile_id: uuid.UUID,
    payload: AgentReviewDecision,
    current_user: User = Depends(require_permission("agent:verify")),
    db: Session = Depends(get_db),
):
    return service.review_decision(db, agent_profile_id, current_user.id, payload.decision, payload.notes)


@router.post("/{agent_profile_id}/suspend", response_model=AgentProfileDetail)
def suspend_agent(
    agent_profile_id: uuid.UUID,
    notes: str | None = None,
    current_user: User = Depends(require_permission("agent:suspend")),
    db: Session = Depends(get_db),
):
    return service.suspend_agent(db, agent_profile_id, current_user.id, notes)


@router.post("/{agent_profile_id}/revoke", response_model=AgentProfileDetail)
def revoke_agent(
    agent_profile_id: uuid.UUID,
    notes: str | None = None,
    current_user: User = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    return service.revoke_agent(db, agent_profile_id, current_user.id, notes)
