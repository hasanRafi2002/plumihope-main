import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class HelpRequestCreate(BaseModel):
    category: str = Field(min_length=1, max_length=64)
    subcategory: str | None = Field(default=None, max_length=64)
    description: str = Field(min_length=1)
    location: str | None = Field(default=None, max_length=255)
    contact_info: str | None = Field(default=None, max_length=255)


class HelpRequestPublic(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category: str
    subcategory: str | None
    description: str
    location: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class HelpRequestDetail(HelpRequestPublic):
    contact_info: str | None
    updated_at: datetime


class HelpRequestEventPublic(BaseModel):
    id: uuid.UUID
    actor_id: uuid.UUID | None
    event_type: str
    notes: str | None
    occurred_at: datetime

    model_config = {"from_attributes": True}


class InvestigationNoteCreate(BaseModel):
    notes: str = Field(min_length=1)


class InvestigationEvidenceCreate(BaseModel):
    media_id: uuid.UUID
    evidence_type: str = Field(min_length=1, max_length=64)
