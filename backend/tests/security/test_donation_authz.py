# Donation / payment initiation authorization (blueprint sec. 17, 29, 89; BR-05):
# ownership, campaign-state guard, and "client cannot claim payment success".
from decimal import Decimal

import pytest

from app.modules.campaigns.models import Campaign
from app.modules.donations.models import Donation
from app.modules.payments.models import Payment


@pytest.fixture
def active_campaign(make_user, make_campaign):
    agent, _ = make_user(roles=("USER", "AGENT"), agent_status="VERIFIED")
    return make_campaign(agent, status="ACTIVE")


def _donate(client, campaign, headers, **extra):
    body = {"campaign_id": str(campaign.id), "amount": "500.00", "currency": "BDT", **extra}
    return client.post("/api/v1/donations", json=body, headers=headers)


def test_unauthenticated_cannot_donate(client, active_campaign):
    assert _donate(client, active_campaign, {}).status_code in (401, 403)


def test_donor_can_create_donation_in_initiated_state(client, db, make_user, active_campaign):  # positive control
    donor, headers = make_user()
    r = _donate(client, active_campaign, headers)
    assert r.status_code == 201, r.text
    d = db.query(Donation).filter(Donation.user_id == donor.id).one()
    assert d.status == "INITIATED"


def test_client_cannot_force_confirmed_status_or_raise_total(client, db, make_user, active_campaign):
    donor, headers = make_user()
    r = _donate(client, active_campaign, headers, status="CONFIRMED", raised_amount="999999", payment="success")
    assert r.status_code in (201, 422)
    db.expire_all()
    for d in db.query(Donation).filter(Donation.user_id == donor.id).all():
        assert d.status == "INITIATED"
    assert db.get(Campaign, active_campaign.id).raised_amount == Decimal("0")


@pytest.mark.parametrize("status", ["DRAFT", "SUBMITTED", "UNDER_REVIEW", "SUSPENDED", "CANCELLED"])
def test_cannot_donate_to_non_active_campaign(client, db, make_user, make_campaign, status):
    agent, _ = make_user(roles=("USER", "AGENT"), agent_status="VERIFIED")
    camp = make_campaign(agent, status=status)
    donor, headers = make_user()
    r = _donate(client, camp, headers)
    assert r.status_code == 409
    assert db.query(Donation).filter(Donation.user_id == donor.id).count() == 0


# ---- payment initiation ownership ----
def _initiate(client, donation, headers):
    return client.post("/api/v1/payments/initiate", json={"donation_id": str(donation.id)}, headers=headers)


def test_owner_can_initiate_payment(client, db, make_user, make_donation, active_campaign):  # positive control
    donor, headers = make_user()
    donation = make_donation(donor, active_campaign)
    r = _initiate(client, donation, headers)
    assert r.status_code == 201, r.text
    assert r.json()["provider_reference"].startswith("SANDBOX-")
    db.expire_all()
    assert db.get(Donation, donation.id).status == "PENDING"


def test_cannot_initiate_payment_on_someone_elses_donation(client, db, make_user, make_donation, active_campaign):
    owner, _ = make_user()
    _, attacker = make_user()
    donation = make_donation(owner, active_campaign)
    r = _initiate(client, donation, attacker)
    assert r.status_code == 403
    assert db.query(Payment).filter(Payment.donation_id == donation.id).count() == 0
    db.expire_all()
    assert db.get(Donation, donation.id).status == "INITIATED"


def test_unauthenticated_cannot_initiate_payment(client, make_user, make_donation, active_campaign):
    owner, _ = make_user()
    assert _initiate(client, make_donation(owner, active_campaign), {}).status_code in (401, 403)


def test_second_initiation_is_rejected(client, db, make_user, make_donation, active_campaign):
    donor, headers = make_user()
    donation = make_donation(donor, active_campaign)
    assert _initiate(client, donation, headers).status_code == 201
    assert _initiate(client, donation, headers).status_code == 409
    assert db.query(Payment).filter(Payment.donation_id == donation.id).count() == 1
