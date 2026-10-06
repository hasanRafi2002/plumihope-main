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


@pytest.fixture
def db(_schema):
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
