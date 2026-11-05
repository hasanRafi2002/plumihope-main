# PlumiHope handoff (update at the end of each session; repo + terminal output stay authoritative)

## State (HEAD 4c1dfca on main, CI green)
- Backend MVP complete (phases 0-18) and hardened. Tests: `docker compose exec api python -m pytest tests -q` -> 781 passed, 0 xfailed (isolated plumihope_test DB; dev DB untouched).
- Done this stretch: atomic webhook; webhook HMAC (X-PlumiHope-Signature, PAYMENT_WEBHOOK_SECRET; dev-only PAYMENT_WEBHOOK_ALLOW_UNSIGNED_SANDBOX, ignored in production, sandbox only); PUBLIC media readable by strangers only as PUBLIC evidence of a campaign in PUBLIC_CAMPAIGN_STATUSES (campaigns/repository.py, shared with discovery); Docker image includes pytest; .github/workflows/backend.yml (pytest on postgres service + docker build).
- iOS: auth, discover, campaign detail + cover photo, donation flow, help requests, profile, notifications, agent workspace. Web: scaffold folders only.
- Local .env holds real dev secrets and is gitignored; never paste it.

## Known gaps
1. Refund path: dispute REFUND/PARTIAL_REFUND do nothing; no DISPUTED -> REFUNDED, no refunded_amount column, no provider refund(); nothing moves a donation to DISPUTED. Needs policy decisions (raised_amount, campaign status after refund, partials).
2. Overfunding policy undefined (raised_amount keeps growing after TARGET_REACHED).
3. Verify authz on disputes/router.py (resolve must require dispute:resolve).
4. Empty modules: verification, admin; follows models only; audit has no router.
5. No moderator/admin UI (curl only); web portals not started.
6. iOS missing: report campaign, post update, assistance proof, payouts, follow/saved, email verification + forgot-password screens, SwiftData, APNs. iOS dev webhook button (DonationService.swift) must go before a real provider.
7. Real provider needs per-provider webhook secrets.
8. CI: only backend.yml; web/ios/e2e/security/release yml are empty; no lint/type checks; no branch protection.
9. Docs stale (cover_media_id, PUBLIC-media rule, webhook signing, env vars); some docs/05-state-machines files may be empty.

## Next (in order)
refund path -> iOS report/updates/assistance proof -> moderator/admin web UI -> docs refresh -> remaining CI.

## Working rules
Terminal-only workflow per docs/PlumiHope — Master Terminal-Based Development Prompt.md. No inline # comments in pasted commands (zsh). Patch via python3 heredoc with exact-string asserts; small commits.
