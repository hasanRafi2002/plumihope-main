import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

# --- Point the whole app at a dedicated test database BEFORE any app import ---
_dev_url = make_url(os.environ["DATABASE_URL"])
_test_db_name = _dev_url.database if _dev_url.database.endswith("_test") else f"{_dev_url.database}_test"
_admin_url = _dev_url.set(database="postgres")
_test_url = _dev_url.set(database=_test_db_name)
os.environ["DATABASE_URL"] = _test_url.render_as_string(hide_password=False)

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402


@pytest.fixture(scope="session")
def _schema():
    assert _test_db_name.endswith("_test"), "refusing to touch a non-test database"
    admin = create_engine(_admin_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(
            text("select pg_terminate_backend(pid) from pg_stat_activity where datname = :n and pid <> pg_backend_pid()"),
            {"n": _test_db_name},
        )
        conn.execute(text(f'DROP DATABASE IF EXISTS "{_test_db_name}"'))
        conn.execute(text(f'CREATE DATABASE "{_test_db_name}"'))
    admin.dispose()

    command.upgrade(Config("alembic.ini"), "head")
    yield

    from app.core.database import engine
    engine.dispose()


@pytest.fixture(scope="session")
def _seeded(_schema):
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
    import seed_rbac
    seed_rbac.main()


@pytest.fixture
def db(_seeded):
    """Per-test session inside an outer transaction that is always rolled back."""
    from app.core.database import engine

    assert engine.url.database.endswith("_test")
    conn = engine.connect()
    outer = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        outer.rollback()
        conn.close()


@pytest.fixture
def client(db):
    from app.core.database import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


# ---------------- factories ----------------
import itertools  # noqa: E402
import uuid  # noqa: E402

_counter = itertools.count(1)


@pytest.fixture
def make_user(db):
    """make_user(roles=("USER",), agent_status=None) -> (user, auth_headers)."""
    from app.core.security import create_access_token, hash_password
    from app.modules.agents.models import AgentProfile
    from app.modules.users.models import Role, User, UserRole

    pw_hash = hash_password("Test-pass-123")

    def _make(roles=("USER",), agent_status=None):
        n = next(_counter)
        user = User(email=f"user{n}-{uuid.uuid4().hex[:6]}@example.test", password_hash=pw_hash, full_name=f"Test User {n}", status="ACTIVE")
        db.add(user)
        db.flush()
        for name in roles:
            role = db.query(Role).filter(Role.name == name).one()
            db.add(UserRole(user_id=user.id, role_id=role.id))
        if agent_status:
            db.add(AgentProfile(user_id=user.id, status=agent_status, full_name=user.full_name))
        db.flush()
        return user, {"Authorization": f"Bearer {create_access_token(user.id)}"}

    return _make


@pytest.fixture
def eligible_help_request(db, make_user):
    from app.modules.help_requests.models import HelpRequest

    owner, _ = make_user()
    hr = HelpRequest(user_id=owner.id, category="MEDICAL", description="test case", status="ELIGIBLE")
    db.add(hr)
    db.flush()
    return hr


@pytest.fixture
def category_id(db):
    from app.modules.campaigns.models import CampaignCategory

    return db.query(CampaignCategory).first().id


@pytest.fixture
def make_media(db):
    from app.modules.media.models import Media

    def _make(owner, visibility="RESTRICTED"):
        m = Media(
            owner_id=owner.id,
            object_key=f"test/{uuid.uuid4().hex}.jpg",
            mime_type="image/jpeg",
            size_bytes=10,
            visibility=visibility,
        )
        db.add(m)
        db.flush()
        return m

    return _make


@pytest.fixture
def make_campaign(db, category_id):
    """make_campaign(agent_user, status="DRAFT") -> Campaign owned by that agent."""
    from app.modules.agents.models import AgentProfile
    from app.modules.campaigns.models import Campaign
    from app.modules.help_requests.models import HelpRequest

    def _make(agent_user, status="DRAFT"):
        profile = db.query(AgentProfile).filter(AgentProfile.user_id == agent_user.id).one()
        hr = HelpRequest(user_id=agent_user.id, category="MEDICAL", description="idor test", status="CONVERTED_TO_CAMPAIGN")
        db.add(hr)
        db.flush()
        camp = Campaign(
            help_request_id=hr.id,
            agent_profile_id=profile.id,
            category_id=category_id,
            title="Original title",
            description="orig",
            target_amount=1000,
            status=status,
        )
        db.add(camp)
        db.flush()
        return camp

    return _make
