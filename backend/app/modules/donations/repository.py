import uuid

from sqlalchemy.orm import Session

from app.modules.donations.models import Donation


def create_donation(db: Session, user_id: uuid.UUID, campaign_id: uuid.UUID, amount, currency: str) -> Donation:
    donation = Donation(
        user_id=user_id,
        campaign_id=campaign_id,
        amount=amount,
        currency=currency,
        status="INITIATED",
    )
    db.add(donation)
    db.commit()
    db.refresh(donation)
    return donation


def get_by_id(db: Session, donation_id: uuid.UUID) -> Donation | None:
    return db.query(Donation).filter(Donation.id == donation_id).first()


def list_by_user(db: Session, user_id: uuid.UUID) -> list[Donation]:
    return db.query(Donation).filter(Donation.user_id == user_id).order_by(Donation.created_at.desc()).all()


def update_status(db: Session, donation: Donation, new_status: str, commit: bool = True) -> Donation:
    donation.status = new_status
    if commit:
        db.commit()
    else:
        db.flush()
    db.refresh(donation)
    return donation


def get_by_id_for_update(db: Session, donation_id: uuid.UUID) -> Donation | None:
    return db.query(Donation).filter(Donation.id == donation_id).with_for_update().first()
