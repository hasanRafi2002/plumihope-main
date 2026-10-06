# SM-CAMPAIGN: exhaustive positive/negative transition tests
# Verifies blueprint sec. 20, 23, 87 (every defined transition passes, every undefined one is rejected)
import pytest
from fastapi import HTTPException

from app.modules.campaigns.state_machine import ALLOWED_TRANSITIONS, validate_transition

EXPECTED = {
    "DRAFT": {"SUBMITTED", "CANCELLED"},
    "SUBMITTED": {"UNDER_REVIEW", "CANCELLED"},
    "UNDER_REVIEW": {"APPROVED", "REJECTED"},
    "REJECTED": set(),
    "APPROVED": {"ACTIVE"},
    "ACTIVE": {"TARGET_REACHED", "EXPIRED", "SUSPENDED", "CANCELLED", "DISPUTED"},
    "TARGET_REACHED": {"PAYOUT_PENDING", "DISPUTED"},
    "PAYOUT_PENDING": {"ASSISTANCE_PENDING", "DISPUTED"},
    "ASSISTANCE_PENDING": {"ASSISTANCE_DELIVERED", "DISPUTED"},
    "ASSISTANCE_DELIVERED": {"FINAL_REVIEW", "DISPUTED"},
    "FINAL_REVIEW": {"SUCCESSFUL", "DISPUTED"},
    "SUCCESSFUL": {"CLOSED"},
    "EXPIRED": {"CLOSED"},
    "SUSPENDED": {"ACTIVE", "CANCELLED", "FRAUDULENT"},
    "DISPUTED": {"ACTIVE", "SUSPENDED", "CANCELLED", "FRAUDULENT"},
    "CANCELLED": set(),
    "FRAUDULENT": set(),
    "CLOSED": set(),
}

ALL_STATES = set(EXPECTED) | {t for ts in EXPECTED.values() for t in ts}
ALLOWED = sorted((s, t) for s, ts in EXPECTED.items() for t in ts)
FORBIDDEN = sorted((s, t) for s in ALL_STATES for t in ALL_STATES if t not in EXPECTED.get(s, set()))


def test_table_matches_expected():
    assert ALLOWED_TRANSITIONS == EXPECTED


def test_every_target_is_a_known_state():
    assert ALL_STATES == set(ALLOWED_TRANSITIONS)


@pytest.mark.parametrize("current,target", ALLOWED)
def test_allowed_transition(current, target):
    validate_transition(current, target)  # must not raise


@pytest.mark.parametrize("current,target", FORBIDDEN)
def test_forbidden_transition(current, target):
    with pytest.raises(HTTPException) as exc:
        validate_transition(current, target)
    assert exc.value.status_code == 409


@pytest.mark.parametrize("current,target", [
    ("DRAFT", "ACTIVE"),
    ("SUBMITTED", "ACTIVE"),
    ("UNDER_REVIEW", "ACTIVE"),
    ("ACTIVE", "SUCCESSFUL"),
    ("TARGET_REACHED", "SUCCESSFUL"),   # money raised != assistance delivered
    ("PAYOUT_PENDING", "SUCCESSFUL"),
    ("ASSISTANCE_DELIVERED", "SUCCESSFUL"),  # needs FINAL_REVIEW
])
def test_blueprint_shortcuts_rejected(current, target):
    with pytest.raises(HTTPException):
        validate_transition(current, target)


@pytest.mark.parametrize("terminal", ["REJECTED", "CANCELLED", "FRAUDULENT", "CLOSED"])
def test_terminal_states_have_no_exits(terminal):
    assert ALLOWED_TRANSITIONS[terminal] == set()


def test_unknown_state_rejected():
    with pytest.raises(HTTPException):
        validate_transition("NOT_A_STATE", "ACTIVE")
