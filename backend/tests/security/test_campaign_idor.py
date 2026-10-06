# IDOR / object-level authorization on campaign mutations (blueprint sec. 17, 41, 81, 89;
# UI/UX "Object Ownership UX": Agent B must not edit Agent A's campaign).
import pytest

from app.modules.campaigns.models import Campaign, CampaignEvidence, CampaignUpdate


def _agent(make_user):
    return make_user(roles=("USER", "AGENT"), agent_status="VERIFIED")


@pytest.fixture
def owner_and_campaign(make_user, make_campaign):
    owner, owner_headers = _agent(make_user)
    return owner, owner_headers, make_campaign(owner)


def _attackers(make_user):
    other_agent = _agent(make_user)[1]
    plain_user = make_user()[1]
    return {"other_verified_agent": other_agent, "plain_user": plain_user, "unauthenticated": {}}


@pytest.mark.parametrize("who", ["other_verified_agent", "plain_user", "unauthenticated"])
def test_cannot_patch_someone_elses_campaign(client, db, make_user, owner_and_campaign, who):
    _, _, camp = owner_and_campaign
    r = client.patch(f"/api/v1/campaigns/{camp.id}", json={"title": "HACKED"}, headers=_attackers(make_user)[who])
    assert r.status_code in (401, 403, 404)
    db.expire_all()
    assert db.get(Campaign, camp.id).title == "Original title"


@pytest.mark.parametrize("who", ["other_verified_agent", "plain_user", "unauthenticated"])
def test_cannot_submit_someone_elses_campaign(client, db, make_user, make_media, owner_and_campaign, who):
    owner, _, camp = owner_and_campaign
    db.add(CampaignEvidence(campaign_id=camp.id, uploader_id=owner.id, evidence_type="COST_ESTIMATE",
                            media_id=make_media(owner).id, visibility="RESTRICTED"))
    db.flush()  # submit would otherwise be blocked only by the evidence gate, not by ownership
    r = client.post(f"/api/v1/campaigns/{camp.id}/submit", headers=_attackers(make_user)[who])
    assert r.status_code in (401, 403, 404)
    db.expire_all()
    assert db.get(Campaign, camp.id).status == "DRAFT"


@pytest.mark.parametrize("who", ["other_verified_agent", "plain_user", "unauthenticated"])
def test_cannot_add_evidence_to_someone_elses_campaign(client, db, make_user, make_media, owner_and_campaign, who):
    _, _, camp = owner_and_campaign
    attacker_user, attacker_headers = _agent(make_user)
    headers = {"other_verified_agent": attacker_headers, "plain_user": make_user()[1], "unauthenticated": {}}[who]
    media = make_media(attacker_user)
    r = client.post(
        f"/api/v1/campaigns/{camp.id}/evidence",
        json={"media_id": str(media.id), "evidence_type": "COST_ESTIMATE", "visibility": "RESTRICTED"},
        headers=headers,
    )
    assert r.status_code in (401, 403, 404)
    db.expire_all()
    assert db.query(CampaignEvidence).filter(CampaignEvidence.campaign_id == camp.id).count() == 0


@pytest.mark.parametrize("who", ["other_verified_agent", "plain_user", "unauthenticated"])
def test_cannot_post_update_on_someone_elses_campaign(client, db, make_user, owner_and_campaign, who):
    _, _, camp = owner_and_campaign
    r = client.post(f"/api/v1/campaigns/{camp.id}/updates", json={"content": "fake update"}, headers=_attackers(make_user)[who])
    assert r.status_code in (401, 403, 404)
    db.expire_all()
    assert db.query(CampaignUpdate).filter(CampaignUpdate.campaign_id == camp.id).count() == 0


# ---- positive controls + state rules ----
def test_owner_can_patch_draft(client, db, owner_and_campaign):
    _, headers, camp = owner_and_campaign
    r = client.patch(f"/api/v1/campaigns/{camp.id}", json={"title": "New title"}, headers=headers)
    assert r.status_code == 200, r.text
    db.expire_all()
    assert db.get(Campaign, camp.id).title == "New title"


@pytest.mark.parametrize("status", ["SUBMITTED", "UNDER_REVIEW", "APPROVED", "ACTIVE"])
def test_owner_cannot_freely_edit_after_draft(client, db, make_user, make_campaign, status):
    owner, headers = _agent(make_user)
    camp = make_campaign(owner, status=status)
    r = client.patch(f"/api/v1/campaigns/{camp.id}", json={"title": "late edit"}, headers=headers)
    assert r.status_code == 409
    db.expire_all()
    assert db.get(Campaign, camp.id).title == "Original title"


def test_submit_requires_evidence(client, db, owner_and_campaign):  # BR-04
    _, headers, camp = owner_and_campaign
    r = client.post(f"/api/v1/campaigns/{camp.id}/submit", headers=headers)
    assert r.status_code == 409
    db.expire_all()
    assert db.get(Campaign, camp.id).status == "DRAFT"


def test_cannot_attach_someone_elses_media_as_evidence(client, db, make_user, make_media, owner_and_campaign):
    owner, headers, camp = owner_and_campaign
    victim, _ = make_user()
    stolen = make_media(victim)
    r = client.post(
        f"/api/v1/campaigns/{camp.id}/evidence",
        json={"media_id": str(stolen.id), "evidence_type": "COST_ESTIMATE", "visibility": "RESTRICTED"},
        headers=headers,
    )
    assert r.status_code == 403
