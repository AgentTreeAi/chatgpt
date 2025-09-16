"""Initial database schema."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20240407_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    integration_kind = sa.Enum("slack", "calendar", "hris", name="integration_kind")
    integration_kind.create(op.get_bind(), checkfirst=True)

    plan_enum = sa.Enum("starter", "pro", "enterprise", name="plan")
    plan_enum.create(op.get_bind(), checkfirst=True)

    subscription_status = sa.Enum("trialing", "active", "past_due", "canceled", name="subscription_status")
    subscription_status.create(op.get_bind(), checkfirst=True)

    risk_level = sa.Enum("low", "moderate", "high", name="risk_level")
    risk_level.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "orgs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("allowed_domains", postgresql.ARRAY(sa.String()), server_default=sa.text("'{}'::text[]")),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="180"),
    )

    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_teams_org_id", "teams", ["org_id"])

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stripe_customer", sa.String(length=120)),
        sa.Column("stripe_subscription", sa.String(length=120)),
        sa.Column("plan", plan_enum, nullable=True),
        sa.Column("seats", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", subscription_status, nullable=True),
        sa.Column("trial_end", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_subscriptions_org_id", "subscriptions", ["org_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("target", sa.String(length=255)),
        sa.Column("ts", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("meta_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_audit_logs_org_id", "audit_logs", ["org_id"])

    op.create_table(
        "integrations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", integration_kind, nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="disconnected"),
        sa.Column("config_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_integrations_org_id", "integrations", ["org_id"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("anon_token_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("email", sa.String(length=255)),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="employee"),
    )
    op.create_index("ix_users_team_id", "users", ["team_id"])
    op.create_index("ix_users_anon_token_hash", "users", ["anon_token_hash"], unique=True)

    op.create_table(
        "calendar_stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("meeting_hours", sa.Float(), nullable=False),
        sa.Column("after_hours_events", sa.Integer(), nullable=False),
    )
    op.create_index("ix_calendar_stats_team_id", "calendar_stats", ["team_id"])

    op.create_table(
        "email_login_nonces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_email_login_nonces_org_id", "email_login_nonces", ["org_id"])
    op.create_index("ix_email_login_nonces_token", "email_login_nonces", ["token"], unique=True)

    op.create_table(
        "checkins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("checkin_date", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("mood", sa.Integer(), nullable=False),
        sa.Column("stress", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
    )
    op.create_index("ix_checkins_user_id", "checkins", ["user_id"])
    op.create_index("ix_checkins_team_id", "checkins", ["team_id"])

    op.create_table(
        "risk_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("risk_level", risk_level, nullable=False),
        sa.Column("avg_mood", sa.Float(), nullable=False),
        sa.Column("avg_stress", sa.Float(), nullable=False),
        sa.Column("checkin_count", sa.Integer(), nullable=False),
    )
    op.create_index("ix_risk_snapshots_team_id", "risk_snapshots", ["team_id"])


def downgrade() -> None:
    op.drop_index("ix_risk_snapshots_team_id", table_name="risk_snapshots")
    op.drop_table("risk_snapshots")

    op.drop_index("ix_checkins_team_id", table_name="checkins")
    op.drop_index("ix_checkins_user_id", table_name="checkins")
    op.drop_table("checkins")

    op.drop_index("ix_email_login_nonces_token", table_name="email_login_nonces")
    op.drop_index("ix_email_login_nonces_org_id", table_name="email_login_nonces")
    op.drop_table("email_login_nonces")

    op.drop_index("ix_calendar_stats_team_id", table_name="calendar_stats")
    op.drop_table("calendar_stats")

    op.drop_index("ix_users_anon_token_hash", table_name="users")
    op.drop_index("ix_users_team_id", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_integrations_org_id", table_name="integrations")
    op.drop_table("integrations")

    op.drop_index("ix_audit_logs_org_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_subscriptions_org_id", table_name="subscriptions")
    op.drop_table("subscriptions")

    op.drop_index("ix_teams_org_id", table_name="teams")
    op.drop_table("teams")

    op.drop_table("orgs")

    risk_level = sa.Enum(name="risk_level")
    subscription_status = sa.Enum(name="subscription_status")
    plan_enum = sa.Enum(name="plan")
    integration_kind = sa.Enum(name="integration_kind")

    risk_level.drop(op.get_bind(), checkfirst=True)
    subscription_status.drop(op.get_bind(), checkfirst=True)
    plan_enum.drop(op.get_bind(), checkfirst=True)
    integration_kind.drop(op.get_bind(), checkfirst=True)
