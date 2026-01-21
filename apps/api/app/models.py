from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utc_now() -> datetime:
    return datetime.utcnow()


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    users: Mapped[list[User]] = relationship(back_populates="organization")
    memberships: Mapped[list[OrgMembership]] = relationship(back_populates="organization")
    uploads: Mapped[list[Upload]] = relationship(back_populates="organization")
    bank_transactions: Mapped[list[BankTransaction]] = relationship(back_populates="organization")
    invoices: Mapped[list[Invoice]] = relationship(back_populates="organization")
    kpi_snapshots: Mapped[list[KpiSnapshot]] = relationship(back_populates="organization")
    health_scores: Mapped[list[HealthScore]] = relationship(back_populates="organization")
    insights: Mapped[list[Insight]] = relationship(back_populates="organization")
    actions: Mapped[list[Action]] = relationship(back_populates="organization")
    strategy_briefs: Mapped[list[StrategyBrief]] = relationship(back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(100), default="member")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    organization: Mapped[Organization] = relationship(back_populates="users")
    memberships: Mapped[list[OrgMembership]] = relationship(back_populates="user")
    sessions: Mapped[list[Session]] = relationship(back_populates="user")
    uploads: Mapped[list[Upload]] = relationship(back_populates="uploader")


class Upload(Base):
    __tablename__ = "uploads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="received")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    organization: Mapped[Organization] = relationship(back_populates="uploads")
    uploader: Mapped[User | None] = relationship(back_populates="uploads")
    bank_transactions: Mapped[list[BankTransaction]] = relationship(back_populates="upload")
    invoices: Mapped[list[Invoice]] = relationship(back_populates="upload")


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    upload_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("uploads.id"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    description: Mapped[str | None] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    organization: Mapped[Organization] = relationship(back_populates="bank_transactions")
    upload: Mapped[Upload | None] = relationship(back_populates="bank_transactions")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    upload_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("uploads.id"))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[str] = mapped_column(String(50), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    organization: Mapped[Organization] = relationship(back_populates="invoices")
    upload: Mapped[Upload | None] = relationship(back_populates="invoices")


class KpiSnapshot(Base):
    __tablename__ = "kpi_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metric: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    organization: Mapped[Organization] = relationship(back_populates="kpi_snapshots")


class HealthScore(Base):
    __tablename__ = "health_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    score: Mapped[int] = mapped_column(nullable=False)
    components: Mapped[dict[str, float | dict[str, float]]] = mapped_column(JSONB, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    organization: Mapped[Organization] = relationship(back_populates="health_scores")


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text(), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default="info")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    organization: Mapped[Organization] = relationship(back_populates="insights")
    actions: Mapped[list[Action]] = relationship(back_populates="insight")


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    insight_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("insights.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="open")
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    organization: Mapped[Organization] = relationship(back_populates="actions")
    insight: Mapped[Insight | None] = relationship(back_populates="actions")


class StrategyBrief(Base):
    __tablename__ = "strategy_briefs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text(), nullable=False)
    context: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    organization: Mapped[Organization] = relationship(back_populates="strategy_briefs")


class OrgMembership(Base):
    __tablename__ = "org_memberships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(100), default="member")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    organization: Mapped[Organization] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    user: Mapped[User] = relationship(back_populates="sessions")
