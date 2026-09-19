import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.campaigns import service
from app.modules.campaigns.schemas import CampaignCreate, CampaignUpdateRequest, CampaignPublic, CampaignDetail, CampaignEvidenceCreate, CampaignEvidencePublic, WhyVerifiedResponse, AssistanceProofSubmit, CampaignCategoryPublic
from app.schemas.pagination import PaginatedResponse
from app.modules.users.models import User

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignDetail, status_code=201)
def create_campaign(
    payload: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.create_campaign(db, current_user.id, payload)


@router.get("", response_model=list[CampaignPublic])
def list_campaigns(
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.list_campaigns(db, status)


@router.get("/discover", response_model=PaginatedResponse[CampaignPublic])
def discover_campaigns(
    category_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return service.discover_campaigns(db, category_id, status, q, page, page_size)


@router.get("/categories", response_model=list[CampaignCategoryPublic])
def list_categories(db: Session = Depends(get_db)):
    return service.list_categories(db)


@router.get("/{campaign_id}", response_model=CampaignDetail)
def get_campaign(campaign_id: uuid.UUID, db: Session = Depends(get_db)):
    return service.get_campaign_or_404(db, campaign_id)


@router.patch("/{campaign_id}", response_model=CampaignDetail)
def update_campaign(
    campaign_id: uuid.UUID,
    payload: CampaignUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.update_campaign(db, campaign_id, current_user.id, payload)


@router.post("/{campaign_id}/submit", response_model=CampaignDetail)
def submit_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.submit_campaign(db, campaign_id, current_user.id)


@router.post("/{campaign_id}/evidence", response_model=CampaignEvidencePublic, status_code=201)
def add_evidence(
    campaign_id: uuid.UUID,
    payload: CampaignEvidenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.add_evidence(db, campaign_id, current_user.id, payload)


@router.get("/{campaign_id}/evidence", response_model=list[CampaignEvidencePublic])
def list_evidence(campaign_id: uuid.UUID, db: Session = Depends(get_db)):
    return service.list_evidence(db, campaign_id)


@router.get("/{campaign_id}/why-verified", response_model=WhyVerifiedResponse)
def get_why_verified(campaign_id: uuid.UUID, db: Session = Depends(get_db)):
    return service.get_why_verified(db, campaign_id)


@router.post("/{campaign_id}/assistance/confirm-delivered", response_model=CampaignDetail)
def confirm_assistance_delivered(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.confirm_assistance_delivered(db, campaign_id, current_user.id)


@router.post("/{campaign_id}/assistance/proof", response_model=CampaignDetail)
def submit_assistance_proof(
    campaign_id: uuid.UUID,
    payload: AssistanceProofSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.submit_assistance_proof(db, campaign_id, current_user.id, payload)
