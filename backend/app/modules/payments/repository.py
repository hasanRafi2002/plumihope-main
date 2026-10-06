import uuid

from sqlalchemy.orm import Session

from app.modules.payments.models import Payment


def create_payment(db: Session, donation_id: uuid.UUID, provider: str, provider_reference: str, amount) -> Payment:
    payment = Payment(
        donation_id=donation_id,
        provider=provider,
        provider_reference=provider_reference,
        amount=amount,
        status="INITIATED",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def get_by_donation_id(db: Session, donation_id: uuid.UUID) -> Payment | None:
    return db.query(Payment).filter(Payment.donation_id == donation_id).first()


def get_by_provider_reference(db: Session, provider_reference: str) -> Payment | None:
    return db.query(Payment).filter(Payment.provider_reference == provider_reference).first()


def update_status(db: Session, payment: Payment, new_status: str, commit: bool = True) -> Payment:
    payment.status = new_status
    if commit:
        db.commit()
    else:
        db.flush()
    db.refresh(payment)
    return payment


def get_by_provider_reference_for_update(db: Session, provider_reference: str) -> Payment | None:
    return (
        db.query(Payment)
        .filter(Payment.provider_reference == provider_reference)
        .with_for_update()
        .first()
    )
