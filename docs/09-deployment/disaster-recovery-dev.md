# PlumiHope — Dev Environment Disaster Recovery

Run this full sequence after any Docker volume wipe (e.g. reclaiming disk
space via Docker Desktop, `docker volume prune`, or similar).

## Step 1 — Bring up fresh containers
```bash
docker compose up -d
```

## Step 2 — Wait for Postgres
```bash
docker compose exec postgres pg_isready -U plumihope
```

## Step 3 — Run migrations
```bash
docker compose exec api alembic upgrade head
```

## Step 4 — Verify tables (expect 26)
```bash
docker compose exec postgres psql -U plumihope -d plumihope -c "\dt"
```

## Step 5 — Create the MinIO bucket
MinIO's container coming up does NOT recreate buckets — they live inside
the wiped volume. Without this step, all file/photo uploads fail with
`NoSuchBucket`.
```bash
docker compose exec minio mc alias set local http://localhost:9000 plumihope plumihope123
docker compose exec minio mc mb local/plumihope
docker compose exec minio mc ls local
```
(confirm `plumihope/` is listed)

## Step 6 — Seed roles, permissions, categories
```bash
docker compose exec api python scripts/seed_rbac.py
```

## Step 7 — Verify seed
```bash
docker compose exec postgres psql -U plumihope -d plumihope -c "SELECT name FROM roles ORDER BY name;"
docker compose exec postgres psql -U plumihope -d plumihope -c "SELECT r.name AS role, count(*) FROM role_permissions rp JOIN roles r ON r.id = rp.role_id GROUP BY r.name ORDER BY r.name;"
docker compose exec postgres psql -U plumihope -d plumihope -c "SELECT name FROM campaign_categories ORDER BY name;"
```
Expect: 4 roles; USER=8, AGENT=12, MODERATOR=12, ADMIN=29 permissions; 8 categories.

## Step 8 — Register test accounts
```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register -H "Content-Type: application/json" -d '{"full_name": "Rafi", "email": "rafi@gmail.com", "password": "rafi.1234"}' | python3 -m json.tool
curl -s -X POST http://localhost:8000/api/v1/auth/register -H "Content-Type: application/json" -d '{"full_name": "Agent One", "email": "agent@gmail.com", "password": "agent.1234"}' | python3 -m json.tool
curl -s -X POST http://localhost:8000/api/v1/auth/register -H "Content-Type: application/json" -d '{"full_name": "Agent Two", "email": "agent1@gmail.com", "password": "agent.1234"}' | python3 -m json.tool
curl -s -X POST http://localhost:8000/api/v1/auth/register -H "Content-Type: application/json" -d '{"full_name": "Moderator", "email": "moderator@gmail.com", "password": "moderator.1234"}' | python3 -m json.tool
curl -s -X POST http://localhost:8000/api/v1/auth/register -H "Content-Type: application/json" -d '{"full_name": "Admin", "email": "admin@gmail.com", "password": "admin.1234"}' | python3 -m json.tool
```
(USER role is auto-assigned by `create_user()` — confirmed fixed as of commit f485cf3)

## Step 9 — Grant ADMIN role
```bash
docker compose exec postgres psql -U plumihope -d plumihope -c "
INSERT INTO user_roles (id, user_id, role_id, created_at, updated_at)
SELECT gen_random_uuid(), u.id, r.id, now(), now()
FROM users u, roles r
WHERE u.email = 'admin@gmail.com' AND r.name = 'ADMIN';
"
```

## Step 10 — Grant MODERATOR role
```bash
docker compose exec postgres psql -U plumihope -d plumihope -c "
INSERT INTO user_roles (id, user_id, role_id, created_at, updated_at)
SELECT gen_random_uuid(), u.id, r.id, now(), now()
FROM users u, roles r
WHERE u.email = 'moderator@gmail.com' AND r.name = 'MODERATOR';
"
```

## Step 11 — Make agent accounts VERIFIED
```bash
docker compose exec postgres psql -U plumihope -d plumihope -c "
INSERT INTO agent_profiles (id, user_id, status, full_name, created_at, updated_at)
SELECT gen_random_uuid(), u.id, 'VERIFIED', u.full_name, now(), now()
FROM users u
WHERE u.email IN ('agent@gmail.com', 'agent1@gmail.com');
"
```

## Step 12 — Final verification
```bash
docker compose exec postgres psql -U plumihope -d plumihope -c "
SELECT u.email, r.name AS role FROM users u
JOIN user_roles ur ON ur.user_id = u.id
JOIN roles r ON r.id = ur.role_id
ORDER BY u.email, r.name;
"
docker compose exec postgres psql -U plumihope -d plumihope -c "
SELECT u.email, ap.status FROM users u
JOIN agent_profiles ap ON ap.user_id = u.id
ORDER BY u.email;
"
```

## What this does NOT restore
Any campaigns, help requests, donations, or uploaded evidence/proof photos
created during testing are gone — this runbook restores structure and
accounts only. Re-create test workflow data by walking through the app
(submit help request → claim → investigate → create campaign → donate →
etc.) same as originally.
