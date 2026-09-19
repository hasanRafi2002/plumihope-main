import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from pydantic import BaseModel

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.help_requests import service
from app.modules.help_requests.schemas import (
    HelpRequestCreate,
    HelpRequestPublic,
    HelpRequestDetail,
    HelpRequestEventPublic,
    InvestigationNoteCreate,
    InvestigationEvidenceCreate,
)
from app.modules.users.models import User


class EligibilityDecision(BaseModel):
    eligible: bool
    notes: str | None = None

router = APIRouter(prefix="/help-requests", tags=["help-requests"])


@router.post("", response_model=HelpRequestDetail, status_code=201)
def create_help_request(
    payload: HelpRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.create_help_request(db, current_user.id, payload)


@router.get("", response_model=list[HelpRequestPublic])
def list_help_requests(
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.list_help_requests(db, status)


@router.get("/me", response_model=list[HelpRequestDetail])
def list_my_help_requests(
    status: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.list_my_help_requests(db, current_user.id, status)


@router.get("/agent/cases", response_model=list[HelpRequestDetail])
def list_my_cases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.list_my_cases(db, current_user.id)


@router.get("/{help_request_id}", response_model=HelpRequestDetail)
def get_help_request(help_request_id: uuid.UUID, db: Session = Depends(get_db)):
    return service.get_help_request_or_404(db, help_request_id)


@router.post("/{help_request_id}/claim", response_model=HelpRequestDetail)
def claim_help_request(
    help_request_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.claim_help_request(db, help_request_id, current_user.id)


@router.post("/{help_request_id}/start-investigation", response_model=HelpRequestDetail)
def start_investigation(
    help_request_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.start_investigation(db, help_request_id, current_user.id)


@router.post("/{help_request_id}/eligibility", response_model=HelpRequestDetail)
def submit_eligibility_decision(
    help_request_id: uuid.UUID,
    payload: EligibilityDecision,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.submit_eligibility_decision(db, help_request_id, current_user.id, payload.eligible, payload.notes)


@router.post("/{help_request_id}/cancel", response_model=HelpRequestDetail)
def cancel_help_request(
    help_request_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.cancel_help_request(db, help_request_id, current_user.id)


@router.post("/{help_request_id}/notes", response_model=HelpRequestDetail)
def add_investigation_note(
    help_request_id: uuid.UUID,
    payload: InvestigationNoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.add_investigation_note(db, help_request_id, current_user.id, payload.notes)


@router.post("/{help_request_id}/evidence", response_model=HelpRequestDetail)
def log_evidence_uploaded(
    help_request_id: uuid.UUID,
    payload: InvestigationEvidenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.log_evidence_uploaded(db, help_request_id, current_user.id, payload.media_id, payload.evidence_type)


@router.get("/{help_request_id}/events", response_model=list[HelpRequestEventPublic])
def list_events(
    help_request_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    return service.list_events(db, help_request_id)
