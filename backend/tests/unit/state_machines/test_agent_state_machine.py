# SM-AGENT: exhaustive positive/negative transition tests
# Verifies blueprint sec. 20 and 87 (every defined transition passes, every undefined one is rejected)
import pytest
from fastapi import HTTPException

from app.modules.agents.state_machine import ALLOWED_TRANSITIONS, validate_transition

EXPECTED = {
    "PENDING": {"UNDER_REVIEW"},
    "UNDER_REVIEW": {"REJECTED", "VERIFIED"},
    "VERIFIED": {"RESTRICTED", "REVOKED", "SUSPENDED"},
    "RESTRICTED": {"REVOKED", "SUSPENDED", "VERIFIED"},
    "SUSPENDED": {"REVOKED", "VERIFIED"},
    "REJECTED": set(),
    "REVOKED": set(),
}

ALL_STATES = set(EXPECTED) | {t for ts in EXPECTED.values() for t in ts}
ALLOWED = sorted((s, t) for s, ts in EXPECTED.items() for t in ts)
FORBIDDEN = sorted((s, t) for s in ALL_STATES for t in ALL_STATES if t not in EXPECTED.get(s, set()))
SHORTCUTS = [('PENDING', 'VERIFIED'), ('PENDING', 'REVOKED'), ('UNDER_REVIEW', 'REVOKED'), ('REJECTED', 'VERIFIED'), ('REVOKED', 'VERIFIED')]
TERMINALS = ['REJECTED', 'REVOKED']


def test_table_matches_expected():
    assert ALLOWED_TRANSITIONS == EXPECTED


def test_every_target_is_a_known_state():
    assert ALL_STATES == set(ALLOWED_TRANSITIONS)


@pytest.mark.parametrize("current,target", ALLOWED)
def test_allowed_transition(current, target):
    validate_transition(current, target)


@pytest.mark.parametrize("current,target", FORBIDDEN)
def test_forbidden_transition(current, target):
    with pytest.raises(HTTPException) as exc:
        validate_transition(current, target)
    assert exc.value.status_code == 409


@pytest.mark.parametrize("current,target", SHORTCUTS)
def test_blueprint_shortcuts_rejected(current, target):
    assert target not in ALLOWED_TRANSITIONS[current]
    with pytest.raises(HTTPException):
        validate_transition(current, target)


@pytest.mark.parametrize("terminal", TERMINALS)
def test_terminal_states_have_no_exits(terminal):
    assert ALLOWED_TRANSITIONS[terminal] == set()


def test_unknown_state_rejected():
    with pytest.raises(HTTPException):
        validate_transition("NOT_A_STATE", next(iter(ALL_STATES)))


def test_revoke_is_admin_only_target():
    from app.modules.agents.state_machine import ADMIN_ONLY_TARGET_STATES
    assert ADMIN_ONLY_TARGET_STATES == {"REVOKED"}
