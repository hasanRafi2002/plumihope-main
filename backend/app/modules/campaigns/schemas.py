import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    help_request_id: uuid.UUID
    category_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    target_amount: Decimal = Field(gt=0)
    currency: str = Field(default="BDT", max_length=8)
    start_date: date | None = None
    end_date: date | None = None
    recipient_name: str | None = Field(default=None, max_length=255)
    recipient_relationship: str | None = Field(default=None, max_length=128)


class CampaignUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    target_amount: Decimal | None = Field(default=None, gt=0)
    end_date: date | None = None
    recipient_name: str | None = Field(default=None, max_length=255)
    recipient_relationship: str | None = Field(default=None, max_length=128)
    payout_destination_ref: str | None = Field(default=None, max_length=255)


class CampaignCategoryPublic(BaseModel):
    id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class CampaignPublic(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    category_id: uuid.UUID
    target_amount: Decimal
    raised_amount: Decimal
    currency: str
    status: str
    verification_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignDetail(CampaignPublic):
    help_request_id: uuid.UUID
    agent_profile_id: uuid.UUID
    start_date: date | None
    end_date: date | None
    recipient_name: str | None
    recipient_relationship: str | None
    updated_at: datetime


class RejectRequest(BaseModel):
    notes: str = Field(min_length=1)


class CampaignEvidenceCreate(BaseModel):
    media_id: uuid.UUID
    evidence_type: str = Field(min_length=1, max_length=64)
    visibility: str = Field(default="RESTRICTED", pattern="^(PUBLIC|RESTRICTED)$")


class CampaignEvidencePublic(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    evidence_type: str
    visibility: str
    verification_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WhyVerifiedResponse(BaseModel):
    agent_identity_reviewed: bool
    case_investigated: bool
    evidence_reviewed: bool
    campaign_moderator_approved: bool
    last_reviewed_at: datetime | None
    disclaimer: str = (
        "Verified means the listed checks were completed and reviewed. "
        "It is not a guarantee of absolute certainty."
    )


class AssistanceProofSubmit(BaseModel):
    media_id: uuid.UUID
    delivery_date: date
    amount_delivered: Decimal = Field(gt=0)
    notes: str | None = None
