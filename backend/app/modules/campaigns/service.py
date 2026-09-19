import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.campaigns import repository
from app.modules.campaigns.models import Campaign
from app.modules.campaigns.schemas import CampaignCreate, CampaignUpdateRequest
from app.modules.campaigns.state_machine import validate_transition
from app.modules.agents.models import AgentProfile
from app.modules.help_requests import repository as help_requests_repository
from app.modules.help_requests import service as help_requests_service


def _get_agent_profile_or_403(db: Session, user_id: uuid.UUID) -> AgentProfile:
    profile = db.query(AgentProfile).filter(AgentProfile.user_id == user_id).first()
    if not profile or profile.status != "VERIFIED":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requires verified Agent status")
    return profile


def list_categories(db: Session):
    return repository.list_categories(db)


def create_campaign(db: Session, user_id: uuid.UUID, payload: CampaignCreate) -> Campaign:
    agent_profile = _get_agent_profile_or_403(db, user_id)

    help_request = help_requests_service.get_help_request_or_404(db, payload.help_request_id)
    if help_request.status != "ELIGIBLE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Help request must be ELIGIBLE before a campaign can be created",
        )

    existing_campaign = repository.get_by_help_request(db, payload.help_request_id)
    if existing_campaign:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A campaign already exists for this help request",
        )

    data = payload.model_dump()
    campaign = repository.create_campaign(db, agent_profile.id, data)

    help_requests_repository.update_status(db, help_request, "CONVERTED_TO_CAMPAIGN")

    return campaign


def list_campaigns(db: Session, status: str | None = None) -> list[Campaign]:
    return repository.list_campaigns(db, status)


def get_campaign_or_404(db: Session, campaign_id: uuid.UUID) -> Campaign:
    campaign = repository.get_by_id(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


def _require_owner(db: Session, campaign: Campaign, user_id: uuid.UUID) -> None:
    agent_profile = db.query(AgentProfile).filter(AgentProfile.user_id == user_id).first()
    if not agent_profile or campaign.agent_profile_id != agent_profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this campaign")


def update_campaign(db: Session, campaign_id: uuid.UUID, user_id: uuid.UUID, payload: CampaignUpdateRequest) -> Campaign:
    campaign = get_campaign_or_404(db, campaign_id)
    _require_owner(db, campaign, user_id)

    if campaign.status != "DRAFT":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only DRAFT campaigns can be freely edited")

    updates = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not updates:
        return campaign
    return repository.update_fields(db, campaign, updates)


def submit_campaign(db: Session, campaign_id: uuid.UUID, user_id: uuid.UUID) -> Campaign:
    campaign = get_campaign_or_404(db, campaign_id)
    _require_owner(db, campaign, user_id)

    validate_transition(campaign.status, "SUBMITTED")

    evidence_count = repository.count_evidence(db, campaign_id)
    if evidence_count == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="At least one evidence item is required before submission",
        )

    return repository.update_status(db, campaign, "SUBMITTED")


def add_evidence(db: Session, campaign_id: uuid.UUID, user_id: uuid.UUID, payload) -> Campaign:
    campaign = get_campaign_or_404(db, campaign_id)
    _require_owner(db, campaign, user_id)

    if campaign.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Evidence can only be added while campaign is in DRAFT",
        )

    from app.modules.media.service import get_media_or_404
    media = get_media_or_404(db, payload.media_id)
    if media.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this media")

    data = payload.model_dump()
    return repository.add_evidence(db, campaign_id, user_id, data)


def list_evidence(db: Session, campaign_id: uuid.UUID):
    get_campaign_or_404(db, campaign_id)
    return repository.list_evidence(db, campaign_id)


def discover_campaigns(
    db: Session,
    category_id: uuid.UUID | None,
    status_filter: str | None,
    search_text: str | None,
    page: int,
    page_size: int,
):
    items, total = repository.search_public_campaigns(
        db, category_id, status_filter, search_text, page, page_size
    )
    has_next = (page * page_size) < total
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_next": has_next,
    }


def get_why_verified(db: Session, campaign_id: uuid.UUID) -> dict:
    campaign = get_campaign_or_404(db, campaign_id)

    from app.modules.agents.models import AgentProfile
    from app.modules.help_requests.models import HelpRequest
    from app.modules.reports.models import Review

    agent_profile = db.query(AgentProfile).filter(AgentProfile.id == campaign.agent_profile_id).first()
    agent_identity_reviewed = bool(agent_profile and agent_profile.status == "VERIFIED")

    help_request = db.query(HelpRequest).filter(HelpRequest.id == campaign.help_request_id).first()
    case_investigated = bool(help_request and help_request.status in {"ELIGIBLE", "CONVERTED_TO_CAMPAIGN"})

    evidence_count = repository.count_evidence(db, campaign_id)
    evidence_reviewed = evidence_count > 0

    latest_approval = (
        db.query(Review)
        .filter(Review.entity_type == "campaign", Review.entity_id == campaign_id, Review.decision == "APPROVED")
        .order_by(Review.created_at.desc())
        .first()
    )
    campaign_moderator_approved = latest_approval is not None
    last_reviewed_at = latest_approval.created_at if latest_approval else None

    return {
        "agent_identity_reviewed": agent_identity_reviewed,
        "case_investigated": case_investigated,
        "evidence_reviewed": evidence_reviewed,
        "campaign_moderator_approved": campaign_moderator_approved,
        "last_reviewed_at": last_reviewed_at,
    }


def confirm_assistance_delivered(db: Session, campaign_id: uuid.UUID, user_id: uuid.UUID) -> Campaign:
    campaign = get_campaign_or_404(db, campaign_id)
    _require_owner(db, campaign, user_id)

    validate_transition(campaign.status, "ASSISTANCE_DELIVERED")
    return repository.update_status(db, campaign, "ASSISTANCE_DELIVERED")


def submit_assistance_proof(db: Session, campaign_id: uuid.UUID, user_id: uuid.UUID, payload) -> Campaign:
    campaign = get_campaign_or_404(db, campaign_id)
    _require_owner(db, campaign, user_id)

    if campaign.status != "ASSISTANCE_DELIVERED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assistance must be confirmed delivered before proof can be submitted",
        )

    from app.modules.media.service import get_media_or_404
    media = get_media_or_404(db, payload.media_id)
    if media.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this media")

    from app.modules.campaigns.models import CampaignUpdate
    content = (
        f"Assistance proof submitted. Delivery date: {payload.delivery_date}. "
        f"Amount delivered: {payload.amount_delivered}."
    )
    if payload.notes:
        content += f" Notes: {payload.notes}"

    update = CampaignUpdate(campaign_id=campaign_id, author_id=user_id, content=content)
    db.add(update)
    db.commit()

    validate_transition(campaign.status, "FINAL_REVIEW")
    return repository.update_status(db, campaign, "FINAL_REVIEW")
