# PlumiHope handoff (update at the end of each session; repo + terminal output stay authoritative)

## State
- Backend MVP complete (phases 0-18). iOS: auth, discover, campaign detail + public cover photo, donation flow, help requests, profile, notifications, agent workspace (apply, cases, investigation, 4-step create campaign, manage). Web: scaffold folders only.
- Backend tests (run in docker): `docker compose exec api python -m pytest tests -q` -> ~752 passed, 2 xfailed.
  Uses isolated DB `plumihope_test` (alembic-migrated by tests/conftest.py); dev DB is never touched.
  Layout: tests/unit/state_machines (all 8 machines exhaustive), tests/security (authz, IDOR, media, webhook, donation), tests/integration (smoke).
  Fixtures in conftest: make_user(roles, agent_status), make_campaign, make_media, make_donation, make_payment.
  NOTE: a request that raises triggers db.rollback() inside process_webhook; tests must db.commit() fixtures first.
- Webhook now runs as ONE transaction (helpers take commit=False; process_webhook commits once / rolls back on error). Provider failure marks donation FAILED.
- Dev data: moderator and agent test accounts exist in the dev DB (credentials kept out of the repo).

## Known gaps (tracked as strict xfail tests or open items)
1. POST /payments/webhooks/{provider} has no signature validation (xfail test_unsigned_webhook_is_rejected). iOS dev button calls /payments/webhooks/sandbox unauthenticated (DonationService.swift ~L120): require HMAC except sandbox+development.
2. PUBLIC media readable by any logged-in user even if campaign not public (xfail in test_media_access.py). Fix check_media_view_access: require campaign ACTIVE or later.
3. DISPUTED -> REFUNDED transition and refund path missing (dispute REFUND/PARTIAL_REFUND outcomes cannot refund).
4. Overfunding policy undefined (webhook keeps incrementing raised_amount after TARGET_REACHED).
5. Empty modules: verification, admin; follows has models only; audit has no router.
6. No CI (.github/workflows missing). Docs not updated for cover_media_id / PUBLIC-media rule.
7. No iOS screens for: report campaign, post update, assistance proof, payouts, follow/saved.
8. No moderator/admin UI (moderation done via curl); web portals not started.

## Next (in order)
webhook HMAC -> media access fix -> GitHub Actions CI -> refund path -> iOS report/updates/assistance proof -> moderator/admin web UI -> docs refresh.

## Working rules
Terminal-only workflow per docs/PlumiHope — Master Terminal-Based Development Prompt.md. Patch via python3 heredoc with exact-string asserts; verify all anchors before writing; small commits.
