from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.payments import service
from app.modules.payments.schemas import PaymentInitiateRequest, PaymentInitiateResponse, WebhookPayload
from app.modules.payments.signature import SIGNATURE_HEADER, verify_webhook_signature
from app.modules.users.models import User

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/initiate", response_model=PaymentInitiateResponse, status_code=201)
def initiate_payment(
    payload: PaymentInitiateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.initiate_payment(db, payload.donation_id, current_user.id)


async def _raw_body(request: Request) -> bytes:
    return await request.body()


@router.post("/webhooks/{provider}")
def payment_webhook(
    provider: str,
    raw_body: bytes = Depends(_raw_body),
    signature: Optional[str] = Header(default=None, alias=SIGNATURE_HEADER),
    db: Session = Depends(get_db),
):
    # Blueprint sec. 110 step 1: validate signature over the RAW body before parsing/DB work.
    verify_webhook_signature(provider, raw_body, signature)
    try:
        payload = WebhookPayload.model_validate_json(raw_body)
    except ValidationError:
        raise HTTPException(status_code=422, detail="Invalid webhook payload")
    return service.process_webhook(db, payload.provider_reference)
