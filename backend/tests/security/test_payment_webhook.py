# Payment verification security (blueprint sec. 29-32, 83, 89, 110; UI/UX "Payment UX rule"):
# only a server-side webhook may confirm a payment; duplicates/forgeries must not move money.
from decimal import Decimal

import pytest

from app.modules.audit.models import AuditLog
from app.modules.campaigns.models import Campaign
from app.modules.donations.models import Donation
from app.modules.notifications.models import Notification
from app.modules.payments.models import Payment

WEBHOOK = "/api/v1/payments/webhooks/sandbox"


@pytest.fixture
def scenario(db, make_user, make_campaign, make_donation, make_payment):
    agent, _ = make_user(roles=("USER", "AGENT"), agent_status="VERIFIED")
    campaign = make_campaign(agent, status="ACTIVE")
    campaign.target_amount = Decimal("1000.00")
    donor, _ = make_user()
    donation = make_donation(donor, campaign, status="PENDING", amount="500.00")
    payment = make_payment(donation, status="INITIATED")
    db.flush()
    return {"campaign": campaign, "donor": donor, "donation": donation, "payment": payment}


def _fire(client, ref):
    return client.post(WEBHOOK, json={"provider_reference": ref})


def _reload(db, *objs):
    db.expire_all()
    return [db.get(type(o), o.id) for o in objs]


def _audit_count(db, donation):
    return db.query(AuditLog).filter(AuditLog.action == "DONATION_CONFIRMED", AuditLog.entity_id == donation.id).count()


def _notif_count(db, user):
    return db.query(Notification).filter(Notification.user_id == user.id).count()


# ---------- forged / unknown ----------
def test_unknown_reference_rejected_and_changes_nothing(client, db, scenario):
    s = scenario
    r = _fire(client, "SANDBOX-does-not-exist")
    assert r.status_code == 404
    campaign, donation, payment = _reload(db, s["campaign"], s["donation"], s["payment"])
    assert campaign.raised_amount == Decimal("0")
    assert donation.status == "PENDING" and payment.status == "INITIATED"


# ---------- happy path ----------
def test_valid_webhook_confirms_payment_donation_and_campaign_total(client, db, scenario):
    s = scenario
    r = _fire(client, s["payment"].provider_reference)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "confirmed"
    campaign, donation, payment = _reload(db, s["campaign"], s["donation"], s["payment"])
    assert payment.status == "VERIFIED"
    assert donation.status == "CONFIRMED"
    assert campaign.raised_amount == Decimal("500.00")
    assert campaign.status == "ACTIVE"  # target not reached yet
    assert _audit_count(db, donation) == 1
    assert _notif_count(db, s["donor"]) == 1


def test_reaching_target_moves_campaign_to_target_reached(client, db, scenario, make_donation, make_payment):
    s = scenario
    s["campaign"].target_amount = Decimal("500.00")
    db.flush()
    _fire(client, s["payment"].provider_reference)
    campaign, = _reload(db, s["campaign"])
    assert campaign.raised_amount == Decimal("500.00")
    assert campaign.status == "TARGET_REACHED"  # NOT SUCCESSFUL: money raised != assistance delivered


# ---------- duplicate / replay ----------
def test_duplicate_webhook_does_not_double_count(client, db, scenario):
    s = scenario
    ref = s["payment"].provider_reference
    assert _fire(client, ref).json()["status"] == "confirmed"
    second = _fire(client, ref)
    assert second.status_code == 200
    assert second.json()["status"] == "already_processed"
    campaign, donation, payment = _reload(db, s["campaign"], s["donation"], s["payment"])
    assert campaign.raised_amount == Decimal("500.00")
    assert _audit_count(db, donation) == 1
    assert _notif_count(db, s["donor"]) == 1


def test_many_replays_still_counted_once(client, db, scenario):
    s = scenario
    for _ in range(5):
        _fire(client, s["payment"].provider_reference)
    campaign, = _reload(db, s["campaign"])
    assert campaign.raised_amount == Decimal("500.00")


# ---------- terminal payment states cannot be revived ----------
@pytest.mark.parametrize("pay_status,don_status", [("FAILED", "FAILED"), ("CANCELLED", "CANCELLED")])
def test_failed_or_cancelled_payment_cannot_be_verified(client, db, make_user, make_campaign, make_donation, make_payment, pay_status, don_status):
    agent, _ = make_user(roles=("USER", "AGENT"), agent_status="VERIFIED")
    campaign = make_campaign(agent, status="ACTIVE")
    donor, _ = make_user()
    donation = make_donation(donor, campaign, status=don_status)
    payment = make_payment(donation, status=pay_status)
    r = _fire(client, payment.provider_reference)
    assert r.status_code == 409
    campaign, donation, payment = _reload(db, campaign, donation, payment)
    assert payment.status == pay_status and donation.status == don_status
    assert campaign.raised_amount == Decimal("0")


# ---------- provider says not verified ----------
class _FailingProvider:
    def verify_payment(self, provider_reference):
        return {"status": "FAILED", "provider_reference": provider_reference}


@pytest.fixture
def provider_fails(monkeypatch):
    monkeypatch.setattr("app.modules.payments.service.get_payment_provider", lambda: _FailingProvider())


def test_provider_failure_marks_payment_failed_and_adds_no_money(client, db, scenario, provider_fails):
    s = scenario
    r = _fire(client, s["payment"].provider_reference)
    assert r.status_code == 200 and r.json()["status"] == "failed"
    campaign, payment = _reload(db, s["campaign"], s["payment"])
    assert payment.status == "FAILED"
    assert campaign.raised_amount == Decimal("0")


@pytest.mark.xfail(strict=True, reason="KNOWN GAP: provider failure leaves the donation stuck in PENDING (PENDING->FAILED is allowed "
                                       "but process_webhook never applies it). Fix, then remove this xfail.")
def test_provider_failure_marks_donation_failed(client, db, scenario, provider_fails):
    s = scenario
    _fire(client, s["payment"].provider_reference)
    donation, = _reload(db, s["donation"])
    assert donation.status == "FAILED"


# ---------- signature (blueprint sec. 110 step 1) ----------
@pytest.mark.xfail(strict=True, reason="KNOWN GAP: webhook has no signature validation; anyone with a provider_reference can confirm it. "
                                       "Add HMAC check, then update these webhook tests to send a valid signature.")
def test_unsigned_webhook_is_rejected(client, db, scenario):
    s = scenario
    r = _fire(client, s["payment"].provider_reference)
    assert r.status_code in (401, 403)
    payment, = _reload(db, s["payment"])
    assert payment.status == "INITIATED"
