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


def test_any_logged_in_user_can_read_public_media(client, make_user, make_media):
    owner, _ = make_user()
    _, headers = make_user()
    assert _get(client, make_media(owner, visibility="PUBLIC"), headers).status_code == 200


def test_unauthenticated_cannot_read_public_media(client, make_user, make_media):
    owner, _ = make_user()
    assert _get(client, make_media(owner, visibility="PUBLIC"), {}).status_code in UNAUTH


def test_restricted_denial_does_not_leak_object_key(client, make_user, make_media):
    owner, _ = make_user()
    _, headers = make_user()
    media = make_media(owner)
    r = _get(client, media, headers)
    assert media.object_key not in r.text


@pytest.mark.xfail(strict=True, reason="KNOWN GAP: PUBLIC media is readable even when its campaign is not public yet. "
                                       "Fix check_media_view_access to require campaign ACTIVE or later, then remove this xfail.")
def test_public_media_of_draft_campaign_not_readable_by_strangers(client, db, make_user, make_media, make_campaign):
    agent, _ = make_user(roles=("USER", "AGENT"), agent_status="VERIFIED")
    camp = make_campaign(agent, status="DRAFT")
    media = make_media(agent, visibility="PUBLIC")
    db.add(CampaignEvidence(campaign_id=camp.id, uploader_id=agent.id, evidence_type="RECIPIENT_PHOTO",
                            media_id=media.id, visibility="PUBLIC"))
    db.flush()
    _, stranger = make_user()
    assert _get(client, media, stranger).status_code == 403
