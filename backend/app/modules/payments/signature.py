import hashlib
import hmac
from typing import Optional

from fastapi import HTTPException

from app.core.config import settings

SIGNATURE_HEADER = "X-PlumiHope-Signature"


def compute_signature(secret: str, raw_body: bytes) -> str:
    return hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()


def _unsigned_sandbox_allowed(provider: str) -> bool:
    # Server-side config only; never derived from anything the caller sends.
    return (
        provider == "sandbox"
        and settings.payment_webhook_allow_unsigned_sandbox
        and settings.app_env != "production"
    )


def verify_webhook_signature(provider: str, raw_body: bytes, signature: Optional[str]) -> None:
    if _unsigned_sandbox_allowed(provider):
        return
    secret = settings.payment_webhook_secret
    if not secret or not signature:  # fail closed
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    expected = compute_signature(secret, raw_body)
    if not hmac.compare_digest(expected, signature.strip().lower()):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
