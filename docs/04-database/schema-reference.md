# PlumiHope — Live Schema Reference

Generated from `information_schema` on the actual dev database.
Re-generate after any migration:

```bash
docker compose exec postgres psql -U plumihope -d plumihope -c "\dt"
```

26 tables, grouped by domain (matches blueprint §12).

---

## IDENTITY / ACCESS

### users
| column | type | nullable |
|---|---|---|
| id | uuid | NO |
| email | varchar | NO |
| phone | varchar | YES |
| password_hash | varchar | NO |
| full_name | varchar | NO |
| status | varchar | NO |
| created_at / updated_at | timestamptz | NO |

### roles
| column | type | nullable |
|---|---|---|
| id | uuid | NO |
| name | varchar | NO |

### permissions
| column | type | nullable |
|---|---|---|
| id | uuid | NO |
| code | varchar | NO |

### user_roles (junction: who has which role)
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| user_id | uuid | NO | users.id |
| role_id | uuid | NO | roles.id |

### role_permissions (junction: what each role can do)
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| role_id | uuid | NO | roles.id |
| permission_id | uuid | NO | permissions.id |

### refresh_tokens
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| user_id | uuid | NO | users.id |
| token_hash | varchar | NO | |
| expires_at | timestamptz | NO | |
| revoked | boolean | NO | |

**Note:** Permission checks (`require_permission`) walk `users → user_roles → roles → role_permissions → permissions`.
**Separately**, `require_agent_verified` checks ONLY `agent_profiles.status == 'VERIFIED'` — it does NOT check `user_roles`. These are two independent gates; don't assume one implies the other.

---

## HUMANITARIAN — AGENTS

### agent_profiles
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| user_id | uuid | NO | users.id |
| status | varchar | NO | (PENDING/UNDER_REVIEW/VERIFIED/REJECTED/RESTRICTED/SUSPENDED/REVOKED) |
| full_name | varchar | NO | |
| phone | varchar | YES | |
| location | varchar | YES | |
| experience | text | YES | |
| facebook_url / youtube_url / other_url | varchar | YES | |

### agent_verifications (audit trail of review decisions)
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| agent_profile_id | uuid | NO | agent_profiles.id |
| reviewer_id | uuid | YES | users.id |
| decision | varchar | NO | |
| notes | text | YES | |
| reviewed_at | timestamptz | YES | |

---

## HUMANITARIAN — HELP REQUESTS

### help_requests
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| user_id | uuid | NO | users.id |
| category | varchar | NO | |
| subcategory | varchar | YES | |
| description | text | NO | |
| location | varchar | YES | |
| contact_info | varchar | YES | |
| status | varchar | NO | (SUBMITTED/AVAILABLE/CLAIMED/INVESTIGATING/ELIGIBLE/NOT_ELIGIBLE/CONVERTED_TO_CAMPAIGN/CLOSED/CANCELLED) |

### help_request_agents (claim record — who is working the case)
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| help_request_id | uuid | NO | help_requests.id |
| agent_profile_id | uuid | NO | agent_profiles.id |
| role | varchar | NO | |

### help_request_events (audit trail)
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| help_request_id | uuid | NO | help_requests.id |
| actor_id | uuid | YES | users.id |
| event_type | varchar | NO | |
| notes | text | YES | |
| occurred_at | timestamptz | NO | |

---

## CAMPAIGN

### campaign_categories (self-referential tree)
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| name | varchar | NO | |
| parent_id | uuid | YES | campaign_categories.id |

### campaigns
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| help_request_id | uuid | NO | help_requests.id |
| agent_profile_id | uuid | NO | agent_profiles.id |
| category_id | uuid | NO | campaign_categories.id |
| title | varchar | NO | |
| description | text | NO | |
| target_amount | numeric | NO | |
| raised_amount | numeric | NO | |
| currency | varchar | NO | |
| start_date / end_date | date | YES | |
| status | varchar | NO | |
| verification_status | varchar | NO | |
| recipient_name | varchar | YES | |
| recipient_relationship | varchar | YES | |
| payout_destination_ref | varchar | YES | |

### campaign_evidence
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| campaign_id | uuid | NO | campaigns.id |
| uploader_id | uuid | NO | users.id |
| evidence_type | varchar | NO | |
| media_id | uuid | YES | media.id |
| visibility | varchar | NO | |
| verification_status | varchar | NO | |
| verified_by | uuid | YES | users.id |
| verified_at | timestamptz | YES | |

### campaign_updates
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| campaign_id | uuid | NO | campaigns.id |
| author_id | uuid | NO | users.id |
| content | text | NO | |

---

## FINANCIAL

### donations
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| campaign_id | uuid | NO | campaigns.id |
| user_id | uuid | NO | users.id |
| amount | numeric | NO | |
| currency | varchar | NO | |
| status | varchar | NO | |

### payments
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| donation_id | uuid | NO | donations.id |
| provider | varchar | NO | |
| provider_reference | varchar | NO | (UNIQUE) |
| amount | numeric | NO | |
| status | varchar | NO | |

### payouts
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| campaign_id | uuid | NO | campaigns.id |
| amount | numeric | NO | |
| status | varchar | NO | (PENDING/PROCESSING/COMPLETED/FAILED) |

---

## TRUST / ACCOUNTABILITY

### reports
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| reporter_id | uuid | NO | users.id |
| entity_type | varchar | NO | |
| entity_id | uuid | NO | (polymorphic — no FK constraint) |
| reason | varchar | NO | |
| description | text | YES | |
| status | varchar | NO | |
| resolution_notes | text | YES | |
| resolved_by | uuid | YES | users.id |
| resolved_at | timestamptz | YES | |

### reviews (generic moderator decision log)
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| reviewer_id | uuid | NO | users.id |
| entity_type | varchar | NO | |
| entity_id | uuid | NO | (polymorphic) |
| decision | varchar | NO | |
| notes | text | YES | |

### disputes
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| campaign_id | uuid | YES | campaigns.id |
| donation_id | uuid | YES | donations.id |
| raised_by | uuid | NO | users.id |
| issue | text | NO | |
| status | varchar | NO | |
| outcome | varchar | YES | |
| resolved_by | uuid | YES | users.id |
| resolved_at | timestamptz | YES | |

---

## ENGAGEMENT

### follows
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| user_id | uuid | NO | users.id |
| agent_profile_id | uuid | NO | agent_profiles.id |

### notifications
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| user_id | uuid | NO | users.id |
| notification_type | varchar | NO | |
| title | varchar | NO | |
| body | text | YES | |
| read_at | timestamptz | YES | |

### media
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| owner_id | uuid | NO | users.id |
| object_key | varchar | NO | |
| mime_type | varchar | NO | |
| size_bytes | bigint | NO | |
| visibility | varchar | NO | |

### audit_logs
| column | type | nullable | FK → |
|---|---|---|---|
| id | uuid | NO | |
| actor_id | uuid | YES | users.id (SET NULL) |
| action | varchar | NO | |
| entity_type | varchar | NO | |
| entity_id | uuid | NO | (polymorphic) |
| before / after | json | YES | |
| event_metadata | json | YES | |

---

## SYSTEM

### alembic_version
| column | type |
|---|---|
| version_num | varchar |

---

## Known gaps (as of this doc's generation)

- `follows` table exists but has NO router/service/repository — backend module incomplete.
- `apply_as_agent()` does not insert into `user_roles`. Dev seed users with `agent_profiles.status = VERIFIED` (test@example.com, agent2@example.com) do NOT necessarily hold the `AGENT` role in `user_roles`. Confirm before building any endpoint that uses `require_permission(...)` for Agent-only actions rather than `require_agent_verified`.
- `admin` and `verification` backend module folders are empty (no dedicated files yet).
