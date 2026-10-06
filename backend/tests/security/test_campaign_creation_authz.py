# BR-01, BR-02, BR-08, BR-09, blueprint sec. 17, 88:
# only AGENT + VERIFIED may create a campaign; every other actor/status is rejected,
# and a rejected attempt must not convert the help request.
import pytest

from app.modules.campaigns.models import Campaign
from app.modules.help_requests.models import HelpRequest

BLOCKED_AGENT_STATUSES = ["PENDING", "UNDER_REVIEW", "REJECTED", "RESTRICTED", "SUSPENDED", "REVOKED"]


def _payload(help_request, category_id):
    return {
        "help_request_id": str(help_request.id),
        "category_id": str(category_id),
        "title": "Authz test campaign",
        "description": "authz test",
        "target_amount": "1000.00",
    }


def _assert_untouched(db, help_request):
    db.expire_all()
    assert db.get(HelpRequest, help_request.id).status == "ELIGIBLE"
    assert db.query(Campaign).filter(Campaign.help_request_id == help_request.id).count() == 0


def test_unauthenticated_rejected(client, db, eligible_help_request, category_id):
    r = client.post("/api/v1/campaigns", json=_payload(eligible_help_request, category_id))
    assert r.status_code in (401, 403)
    _assert_untouched(db, eligible_help_request)


def test_normal_user_cannot_create_campaign(client, db, make_user, eligible_help_request, category_id):  # BR-01
    _, headers = make_user(roles=("USER",))
    r = client.post("/api/v1/campaigns", json=_payload(eligible_help_request, category_id), headers=headers)
    assert r.status_code == 403
    _assert_untouched(db, eligible_help_request)


@pytest.mark.parametrize("agent_status", BLOCKED_AGENT_STATUSES)
def test_non_verified_agent_cannot_create_campaign(client, db, make_user, eligible_help_request, category_id, agent_status):
    _, headers = make_user(roles=("USER", "AGENT"), agent_status=agent_status)
    r = client.post("/api/v1/campaigns", json=_payload(eligible_help_request, category_id), headers=headers)
    assert r.status_code == 403, f"agent status {agent_status} was allowed to create a campaign"
    _assert_untouched(db, eligible_help_request)


@pytest.mark.parametrize("roles", [("USER", "MODERATOR"), ("USER", "ADMIN")])
def test_moderator_and_admin_without_agent_profile_cannot_create(client, db, make_user, eligible_help_request, category_id, roles):
    _, headers = make_user(roles=roles)
    r = client.post("/api/v1/campaigns", json=_payload(eligible_help_request, category_id), headers=headers)
    assert r.status_code == 403
    _assert_untouched(db, eligible_help_request)


def test_verified_agent_can_create_campaign(client, db, make_user, eligible_help_request, category_id):  # positive control
    _, headers = make_user(roles=("USER", "AGENT"), agent_status="VERIFIED")
    r = client.post("/api/v1/campaigns", json=_payload(eligible_help_request, category_id), headers=headers)
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "DRAFT"
    db.expire_all()
    assert db.get(HelpRequest, eligible_help_request.id).status == "CONVERTED_TO_CAMPAIGN"
