import uuid

from sqlalchemy.orm import Session

from app.modules.campaigns.models import Campaign, CampaignEvidence, CampaignCategory


def list_categories(db: Session) -> list[CampaignCategory]:
    return db.query(CampaignCategory).order_by(CampaignCategory.name).all()


def create_campaign(db: Session, agent_profile_id: uuid.UUID, data: dict) -> Campaign:
    campaign = Campaign(agent_profile_id=agent_profile_id, status="DRAFT", **data)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def get_by_id(db: Session, campaign_id: uuid.UUID) -> Campaign | None:
    return db.query(Campaign).filter(Campaign.id == campaign_id).first()


def get_by_help_request(db: Session, help_request_id: uuid.UUID) -> Campaign | None:
    return db.query(Campaign).filter(Campaign.help_request_id == help_request_id).first()


def list_campaigns(db: Session, status: str | None = None) -> list[Campaign]:
    query = db.query(Campaign)
    if status:
        query = query.filter(Campaign.status == status)
    return query.order_by(Campaign.created_at.desc()).all()


def update_fields(db: Session, campaign: Campaign, updates: dict) -> Campaign:
    for key, value in updates.items():
        setattr(campaign, key, value)
    db.commit()
    db.refresh(campaign)
    return campaign


def update_status(db: Session, campaign: Campaign, new_status: str) -> Campaign:
    campaign.status = new_status
    db.commit()
    db.refresh(campaign)
    return campaign


def count_evidence(db: Session, campaign_id: uuid.UUID) -> int:
    return db.query(CampaignEvidence).filter(CampaignEvidence.campaign_id == campaign_id).count()


def add_evidence(db: Session, campaign_id: uuid.UUID, uploader_id: uuid.UUID, data: dict) -> CampaignEvidence:
    evidence = CampaignEvidence(
        campaign_id=campaign_id,
        uploader_id=uploader_id,
        verification_status="UPLOADED",
        **data,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def list_evidence(db: Session, campaign_id: uuid.UUID) -> list[CampaignEvidence]:
    return db.query(CampaignEvidence).filter(CampaignEvidence.campaign_id == campaign_id).all()


def search_public_campaigns(
    db: Session,
    category_id: uuid.UUID | None = None,
    status_filter: str | None = None,
    search_text: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Campaign], int]:
    query = db.query(Campaign)

    if status_filter:
        query = query.filter(Campaign.status == status_filter)
    else:
        query = query.filter(Campaign.status.in_([
            "ACTIVE", "TARGET_REACHED", "PAYOUT_PENDING",
            "ASSISTANCE_PENDING", "ASSISTANCE_DELIVERED",
            "FINAL_REVIEW", "SUCCESSFUL",
        ]))

    if category_id:
        query = query.filter(Campaign.category_id == category_id)

    if search_text:
        like_pattern = f"%{search_text}%"
        query = query.filter(
            Campaign.title.ilike(like_pattern) | Campaign.description.ilike(like_pattern)
        )

    total = query.count()
    items = (
        query.order_by(Campaign.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def increment_raised_amount(db: Session, campaign_id: uuid.UUID, amount) -> Campaign:
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).with_for_update().first()
    campaign.raised_amount = campaign.raised_amount + amount
    db.commit()
    db.refresh(campaign)
    return campaign
