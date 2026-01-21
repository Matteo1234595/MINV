from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models import OrgMembership, Organization, Session as UserSession, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET is not set")
    return secret


def _jwt_issuer() -> str:
    return os.getenv("JWT_ISSUER", "aion")


def _access_ttl() -> timedelta:
    return timedelta(minutes=int(os.getenv("ACCESS_TTL_MIN", "15")))


def _refresh_ttl() -> timedelta:
    return timedelta(days=int(os.getenv("REFRESH_TTL_DAYS", "30")))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_user(
    db: Session, *, organization_id: uuid.UUID, email: str, password: str, full_name: str | None
) -> User:
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if organization is None:
        raise ValueError("Organization not found")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError("Email already registered")

    user = User(
        organization_id=organization_id,
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.flush()

    membership = OrgMembership(
        organization_id=organization_id,
        user_id=user.id,
        role="member",
    )
    db.add(membership)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, *, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def _encode_token(payload: dict[str, object], expires_at: datetime) -> str:
    payload = {**payload, "exp": expires_at, "iss": _jwt_issuer()}
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def issue_tokens(db: Session, user: User) -> TokenPair:
    now = datetime.utcnow()
    access_expires_at = now + _access_ttl()
    refresh_expires_at = now + _refresh_ttl()

    session = UserSession(
        user_id=user.id,
        expires_at=refresh_expires_at,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    access_payload = {
        "sub": str(user.id),
        "type": "access",
        "org_id": str(user.organization_id),
    }
    refresh_payload = {
        "sub": str(user.id),
        "type": "refresh",
        "sid": str(session.id),
    }

    return TokenPair(
        access_token=_encode_token(access_payload, access_expires_at),
        refresh_token=_encode_token(refresh_payload, refresh_expires_at),
        access_expires_at=access_expires_at,
        refresh_expires_at=refresh_expires_at,
    )


def decode_token(token: str) -> dict[str, object]:
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=["HS256"], issuer=_jwt_issuer())
    except JWTError as exc:
        raise ValueError("Invalid token") from exc


def refresh_session(db: Session, refresh_token: str) -> TokenPair:
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise ValueError("Invalid refresh token")

    session_id = payload.get("sid")
    if not session_id:
        raise ValueError("Refresh session missing")

    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if session is None or session.revoked_at is not None:
        raise ValueError("Refresh session revoked")

    if session.expires_at < datetime.utcnow():
        raise ValueError("Refresh session expired")

    session.revoked_at = datetime.utcnow()
    db.add(session)
    db.commit()

    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if user is None:
        raise ValueError("User not found")

    return issue_tokens(db, user)


def revoke_refresh_token(db: Session, refresh_token: str) -> None:
    payload = decode_token(refresh_token)
    session_id = payload.get("sid")
    if session_id is None:
        raise ValueError("Refresh session missing")

    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if session is None:
        return
    session.revoked_at = datetime.utcnow()
    db.add(session)
    db.commit()


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def has_org_access(db: Session, user_id: uuid.UUID, organization_id: uuid.UUID) -> bool:
    membership = (
        db.query(OrgMembership)
        .filter(
            OrgMembership.user_id == user_id,
            OrgMembership.organization_id == organization_id,
        )
        .first()
    )
    return membership is not None
