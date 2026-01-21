"""add health scores table

Revision ID: 0002_add_health_scores
Revises: 0001_create_aion_tables
Create Date: 2026-01-21 14:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0002_add_health_scores"
down_revision = "0001_create_aion_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "health_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("components", postgresql.JSONB(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("organization_id", "computed_at", name="uq_health_scores_org_time"),
    )


def downgrade() -> None:
    op.drop_table("health_scores")
