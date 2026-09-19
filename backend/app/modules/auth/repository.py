import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.users.models import User, Role, UserRole
from app.modules.auth.models import RefreshToken


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, full_name: str, email: str, password_hash: str) -> User:
    user = User(full_name=full_name, email=email, password_hash=password_hash, status="ACTIVE")
    db.add(user)
    db.commit()
    db.refresh(user)

    user_role = db.query(Role).filter(Role.name == "USER").first()
    if user_role:
        db.add(UserRole(user_id=user.id, role_id=user_role.id))
        db.commit()

    return user


def store_refresh_token(db: Session, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> RefreshToken:
    token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def get_refresh_token(db: Session, token_hash: str) -> RefreshToken | None:
    return db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()


def revoke_refresh_token(db: Session, token_hash: str) -> None:
    db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).update({"revoked": True})
    db.commit()
