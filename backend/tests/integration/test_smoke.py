# Infrastructure smoke tests: isolated test DB, migrations apply, app boots, auth is enforced.
from sqlalchemy import text


def test_uses_isolated_test_database(db):
    name = db.execute(text("select current_database()")).scalar()
    assert name.endswith("_test")


def test_migrations_created_core_tables(db):
    tables = {r[0] for r in db.execute(text("select table_name from information_schema.tables where table_schema='public'"))}
    for t in ("users", "campaigns", "campaign_evidence", "donations", "payments", "payouts", "audit_logs", "media"):
        assert t in tables


def test_openapi_available(client):
    assert client.get("/openapi.json").status_code == 200


def test_protected_endpoint_requires_auth(client):
    assert client.get("/api/v1/users/me").status_code in (401, 403)
