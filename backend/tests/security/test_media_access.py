# File security (blueprint sec. 14, 75, 82; UI/UX "Restricted evidence UX"):
# RESTRICTED media must only be readable by owner or authorized reviewers.
import pytest

from app.modules.campaigns.models import CampaignEvidence

UNAUTH = (401, 403)


def _get(client, media, headers):
    return client.get(f"/api/v1/media/{media.id}", headers=headers)


def test_unauthenticated_cannot_read_restricted(client, make_user, make_media):
    owner, _ = make_user()
    assert _get(client, make_media(owner), {}).status_code in UNAUTH


def test_owner_can_read_own_restricted(client, make_user, make_media):
    owner, headers = make_user()
    assert _get(client, make_media(owner), headers).status_code == 200


@pytest.mark.parametrize("roles,agent_status", [
    (("USER",), None),
    (("USER", "AGENT"), "VERIFIED"),
    (("USER", "AGENT"), "SUSPENDED"),
])
def test_other_users_cannot_read_restricted(client, make_user, make_media, roles, agent_status):
    owner, _ = make_user()
    _, headers = make_user(roles=roles, agent_status=agent_status)
    assert _get(client, make_media(owner), headers).status_code == 403


@pytest.mark.parametrize("role", ["MODERATOR", "ADMIN"])
def test_reviewers_can_read_restricted(client, make_user, make_media, role):
    owner, _ = make_user()
    _, headers = make_user(roles=("USER", role))
    assert _get(client, make_media(owner), headers).status_code == 200


PUBLIC_STATUSES = ["ACTIVE", "TARGET_REACHED", "PAYOUT_PENDING", "ASSISTANCE_PENDING",
                   "ASSISTANCE_DELIVERED", "FINAL_REVIEW", "SUCCESSFUL"]
NON_PUBLIC_STATUSES = ["DRAFT", "SUBMITTED", "UNDER_REVIEW", "APPROVED", "REJECTED", "EXPIRED",
                       "SUSPENDED", "DISPUTED", "CANCELLED", "FRAUDULENT", "CLOSED"]


def _public_media_on_campaign(db, make_user, make_media, make_campaign, status, evidence_visibility="PUBLIC"):
    agent, agent_headers = make_user(roles=("USER", "AGENT"), agent_status="VERIFIED")
    camp = make_campaign(agent, status=status)
    media = make_media(agent, visibility="PUBLIC")
    db.add(CampaignEvidence(campaign_id=camp.id, uploader_id=agent.id, evidence_type="RECIPIENT_PHOTO",
                            media_id=media.id, visibility=evidence_visibility))
    db.flush()
    return media, agent_headers


@pytest.mark.parametrize("status", PUBLIC_STATUSES)
def test_stranger_can_read_public_media_of_public_campaign(client, db, make_user, make_media, make_campaign, status):
    media, _ = _public_media_on_campaign(db, make_user, make_media, make_campaign, status)
    _, stranger = make_user()
    assert _get(client, media, stranger).status_code == 200


@pytest.mark.parametrize("status", NON_PUBLIC_STATUSES)
def test_stranger_cannot_read_public_media_of_non_public_campaign(client, db, make_user, make_media, make_campaign, status):
    media, _ = _public_media_on_campaign(db, make_user, make_media, make_campaign, status)
    _, stranger = make_user()
    assert _get(client, media, stranger).status_code == 403


def test_stranger_cannot_read_orphan_public_media(client, make_user, make_media):
    owner, _ = make_user()
    _, stranger = make_user()
    assert _get(client, make_media(owner, visibility="PUBLIC"), stranger).status_code == 403


def test_public_media_via_restricted_evidence_not_readable_by_strangers(client, db, make_user, make_media, make_campaign):
    media, _ = _public_media_on_campaign(db, make_user, make_media, make_campaign, "ACTIVE", evidence_visibility="RESTRICTED")
    _, stranger = make_user()
    assert _get(client, media, stranger).status_code == 403


def test_owner_can_read_own_public_media_of_draft_campaign(client, db, make_user, make_media, make_campaign):
    media, owner_headers = _public_media_on_campaign(db, make_user, make_media, make_campaign, "DRAFT")
    assert _get(client, media, owner_headers).status_code == 200


def test_moderator_can_read_public_media_of_draft_campaign(client, db, make_user, make_media, make_campaign):
    media, _ = _public_media_on_campaign(db, make_user, make_media, make_campaign, "UNDER_REVIEW")
    _, mod = make_user(roles=("USER", "MODERATOR"))
    assert _get(client, media, mod).status_code == 200


def test_unauthenticated_cannot_read_public_media(client, make_user, make_media):
    owner, _ = make_user()
    assert _get(client, make_media(owner, visibility="PUBLIC"), {}).status_code in UNAUTH


def test_restricted_denial_does_not_leak_object_key(client, make_user, make_media):
    owner, _ = make_user()
    _, headers = make_user()
    media = make_media(owner)
    r = _get(client, media, headers)
    assert media.object_key not in r.text


def test_public_media_of_draft_campaign_not_readable_by_strangers(client, db, make_user, make_media, make_campaign):
    agent, _ = make_user(roles=("USER", "AGENT"), agent_status="VERIFIED")
    camp = make_campaign(agent, status="DRAFT")
    media = make_media(agent, visibility="PUBLIC")
    db.add(CampaignEvidence(campaign_id=camp.id, uploader_id=agent.id, evidence_type="RECIPIENT_PHOTO",
                            media_id=media.id, visibility="PUBLIC"))
    db.flush()
    _, stranger = make_user()
    assert _get(client, media, stranger).status_code == 403
