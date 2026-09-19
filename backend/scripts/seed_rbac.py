"""
Idempotent seed script for roles, permissions, role_permissions, and
campaign_categories. Safe to re-run any time (e.g. after a Docker volume
wipe) — uses get-or-create for every row.

Run inside the api container:
    docker compose exec api python scripts/seed_rbac.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.modules.users.models import Role, Permission, RolePermission
from app.modules.campaigns.models import CampaignCategory

ROLES = ["USER", "AGENT", "MODERATOR", "ADMIN"]

PERMISSIONS = [
    "campaign:view", "campaign:create", "campaign:update_own", "campaign:submit",
    "campaign:review", "campaign:approve", "campaign:reject",
    "agent:apply", "agent:review", "agent:verify", "agent:suspend",
    "help_request:create", "help_request:claim",
    "donation:create", "donation:view_own",
    "finance:view", "finance:manage",
    "report:create", "report:review", "report:resolve",
    "dispute:resolve",
    "user:update_own", "user:view", "user:suspend",
    "follow:manage",
    "moderator:create", "moderator:manage",
    "system:manage",
    "audit:view",
]

# Blueprint §19 permission matrix.
USER_PERMISSIONS = {
    "campaign:view", "donation:create", "donation:view_own",
    "help_request:create", "agent:apply", "report:create",
    "follow:manage", "user:update_own",
}

AGENT_PERMISSIONS = USER_PERMISSIONS | {
    "campaign:create", "campaign:update_own", "campaign:submit", "help_request:claim",
}

# Moderator permissions are individually configurable per blueprint §4.3 —
# this seeds a reasonable default set covering typical moderation duties.
# Adjust per-moderator via admin tooling once that exists.
MODERATOR_PERMISSIONS = {
    "campaign:view", "campaign:review", "campaign:approve", "campaign:reject",
    "agent:review", "agent:verify", "agent:suspend",
    "report:review", "report:resolve",
    "dispute:resolve",
    "finance:view",
    "audit:view",
}

ADMIN_PERMISSIONS = set(PERMISSIONS)  # Admin gets everything.

ROLE_PERMISSION_MAP = {
    "USER": USER_PERMISSIONS,
    "AGENT": AGENT_PERMISSIONS,
    "MODERATOR": MODERATOR_PERMISSIONS,
    "ADMIN": ADMIN_PERMISSIONS,
}

CATEGORIES = ["MEDICAL", "EDUCATION", "EMERGENCY", "LIVELIHOOD", "FOOD", "HOUSING", "DISABILITY", "COMMUNITY_SUPPORT"]


def get_or_create_role(db, name: str) -> Role:
    role = db.query(Role).filter(Role.name == name).first()
    if not role:
        role = Role(name=name)
        db.add(role)
        db.commit()
        db.refresh(role)
        print(f"  created role: {name}")
    return role


def get_or_create_permission(db, code: str) -> Permission:
    perm = db.query(Permission).filter(Permission.code == code).first()
    if not perm:
        perm = Permission(code=code)
        db.add(perm)
        db.commit()
        db.refresh(perm)
        print(f"  created permission: {code}")
    return perm


def get_or_create_role_permission(db, role_id, permission_id) -> None:
    existing = (
        db.query(RolePermission)
        .filter(RolePermission.role_id == role_id, RolePermission.permission_id == permission_id)
        .first()
    )
    if not existing:
        db.add(RolePermission(role_id=role_id, permission_id=permission_id))
        db.commit()


def get_or_create_category(db, name: str) -> CampaignCategory:
    cat = db.query(CampaignCategory).filter(CampaignCategory.name == name).first()
    if not cat:
        cat = CampaignCategory(name=name)
        db.add(cat)
        db.commit()
        db.refresh(cat)
        print(f"  created category: {name}")
    return cat


def main():
    db = SessionLocal()
    try:
        print("Seeding roles...")
        roles = {name: get_or_create_role(db, name) for name in ROLES}

        print("Seeding permissions...")
        permissions = {code: get_or_create_permission(db, code) for code in PERMISSIONS}

        print("Wiring role_permissions...")
        for role_name, perm_codes in ROLE_PERMISSION_MAP.items():
            role = roles[role_name]
            for code in perm_codes:
                get_or_create_role_permission(db, role.id, permissions[code].id)

        print("Seeding campaign categories...")
        for name in CATEGORIES:
            get_or_create_category(db, name)

        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
