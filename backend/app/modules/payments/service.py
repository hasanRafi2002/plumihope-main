import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.payments import repository
from app.modules.payments.models import Payment
from app.modules.payments.providers import get_payment_provider
from app.modules.donations import repository as donations_repository
from app.modules.donations.state_machine import validate_transition as validate_donation_transition


def initiate_payment(db: Session, donation_id: uuid.UUID, user_id: uuid.UUID) -> dict:
    donation = donations_repository.get_by_id(db, donation_id)
    if not donation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")

    if donation.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this donation")

    existing_payment = repository.get_by_donation_id(db, donation_id)
    if existing_payment:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment already initiated for this donation")

    validate_donation_transition(donation.status, "PENDING")

    provider = get_payment_provider()
    result = provider.initiate_payment(str(donation.id), donation.amount, donation.currency)

    payment = repository.create_payment(
        db, donation_id, settings.payment_provider, result["provider_reference"], donation.amount
    )

    donations_repository.update_status(db, donation, "PENDING")

    return {
        "payment_id": payment.id,
        "provider": payment.provider,
        "provider_reference": payment.provider_reference,
        "redirect_url": result["redirect_url"],
        "status": payment.status,
    }


def process_webhook(db: Session, provider_reference: str) -> dict:
    """Run the whole webhook as ONE transaction: commit once, roll back on any failure.
    The payment row lock taken inside is held until that single commit."""
    try:
        result = _process_webhook_inner(db, provider_reference)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise


def _process_webhook_inner(db: Session, provider_reference: str) -> dict:
    from app.modules.payments.state_machine import validate_transition as validate_payment_transition
    from app.modules.donations.state_machine import validate_transition as validate_donation_transition
    from app.modules.donations import repository as donations_repository
    from app.modules.campaigns import repository as campaigns_repository
    from app.modules.audit import repository as audit_repository

    # Step 1: Lock the payment record to prevent concurrent processing of
    # the same webhook (replay / duplicate webhook protection).
    payment = repository.get_by_provider_reference_for_update(db, provider_reference)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    # Idempotency: already verified, do nothing further.
    if payment.status == "VERIFIED":
        return {"status": "already_processed", "payment_id": str(payment.id)}

    # Step 2: Verify with the provider (authoritative check, never trust the
    # webhook payload's own claimed status without calling back to verify).
    provider = get_payment_provider()
    verification = provider.verify_payment(provider_reference)

    if verification["status"] != "VERIFIED":
        validate_payment_transition(payment.status, "FAILED")
        repository.update_status(db, payment, "FAILED", commit=False)
        failed_donation = donations_repository.get_by_id_for_update(db, payment.donation_id)
        if failed_donation.status == "PENDING":
            validate_donation_transition(failed_donation.status, "FAILED")
            donations_repository.update_status(db, failed_donation, "FAILED", commit=False)
        return {"status": "failed", "payment_id": str(payment.id)}

    # Step 3: Confirm payment.
    before_payment_status = payment.status
    validate_payment_transition(payment.status, "PROCESSING")
    payment = repository.update_status(db, payment, "PROCESSING", commit=False)
    validate_payment_transition(payment.status, "VERIFIED")
    payment = repository.update_status(db, payment, "VERIFIED", commit=False)

    # Step 4: Update donation -> CONFIRMED (locked to prevent races).
    donation = donations_repository.get_by_id_for_update(db, payment.donation_id)
    before_donation_status = donation.status
    validate_donation_transition(donation.status, "PAID")
    donation = donations_repository.update_status(db, donation, "PAID", commit=False)
    validate_donation_transition(donation.status, "CONFIRMED")
    donation = donations_repository.update_status(db, donation, "CONFIRMED", commit=False)

    # Step 5: Update campaign raised_amount atomically.
    campaign = campaigns_repository.increment_raised_amount(db, donation.campaign_id, donation.amount, commit=False)

    # Cross-entity rule: campaign -> TARGET_REACHED only from confirmed
    # donation total, never from a client-provided flag.
    if campaign.status == "ACTIVE" and campaign.raised_amount >= campaign.target_amount:
        from app.modules.campaigns.state_machine import validate_transition as validate_campaign_transition
        validate_campaign_transition(campaign.status, "TARGET_REACHED")
        campaigns_repository.update_status(db, campaign, "TARGET_REACHED", commit=False)

    # Step 6: Audit log.
    audit_repository.create_log(
        db,
        actor_id=None,
        action="DONATION_CONFIRMED",
        entity_type="donation",
        entity_id=donation.id,
        before={"payment_status": before_payment_status, "donation_status": before_donation_status},
        after={"payment_status": payment.status, "donation_status": donation.status},
        metadata={"provider_reference": provider_reference},
        commit=False,
    )

    from app.modules.notifications.service import notify
    notify(
        db, donation.user_id, "DONATION_CONFIRMED",
        "Donation confirmed",
        f"Your donation of {donation.amount} {donation.currency} was confirmed.",
        commit=False,
    )

    # Step 7: commit already happened via repository calls (each is its own
    # transaction here for simplicity; row locks held throughout this
    # function's session scope prevent concurrent double-processing).

    return {"status": "confirmed", "payment_id": str(payment.id), "donation_id": str(donation.id)}
