"""Marketplace features: brand approval, moderation, reviews, reports, finance.

Revision ID: 002
Revises: 001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # --- New enum types (create_type=False so column ops don't re-create them) ---
    brandstatus = postgresql.ENUM("pending", "approved", "rejected", name="brandstatus", create_type=False)
    brandstatus.create(bind)
    reportstatus = postgresql.ENUM("open", "resolved", "dismissed", name="reportstatus", create_type=False)
    reportstatus.create(bind)
    substatus = postgresql.ENUM("active", "cancelled", name="subscriptionstatus", create_type=False)
    substatus.create(bind)

    # --- User moderation columns ---
    op.add_column("users", sa.Column("blocked_until", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("block_reason", sa.String(500), nullable=True))

    # --- Brand approval columns (existing brands grandfathered to approved) ---
    op.add_column(
        "brands",
        sa.Column("status", brandstatus, nullable=False, server_default="approved"),
    )
    op.add_column("brands", sa.Column("rejection_reason", sa.String(500), nullable=True))

    # --- reviews ---
    op.create_table(
        "reviews",
        sa.Column("review_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(2000), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.product_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.brand_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("review_id"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_reviews_user_product"),
    )
    op.create_index("idx_reviews_product_id", "reviews", ["product_id"])
    op.create_index("idx_reviews_brand_id", "reviews", ["brand_id"])

    # --- issue_reports ---
    op.create_table(
        "issue_reports",
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reporter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reporter_role", sa.String(20), nullable=False),
        sa.Column("target_type", sa.String(30), nullable=False, server_default="other"),
        sa.Column("target_id", sa.String(64), nullable=True),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("message", sa.String(2000), nullable=False),
        sa.Column("status", reportstatus, nullable=False, server_default="open"),
        sa.Column("admin_note", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("report_id"),
    )
    op.create_index("idx_issue_reports_status", "issue_reports", ["status"])
    op.create_index("idx_issue_reports_reporter", "issue_reports", ["reporter_id"])

    # --- platform_settings (singleton) ---
    op.create_table(
        "platform_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("commission_percent", sa.Float(), nullable=False, server_default="10.0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- payouts ---
    op.create_table(
        "payouts",
        sa.Column("payout_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.brand_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("payout_id"),
    )
    op.create_index("idx_payouts_brand_id", "payouts", ["brand_id"])

    # --- subscription_plans ---
    op.create_table(
        "subscription_plans",
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("interval", sa.String(20), nullable=False, server_default="month"),
        sa.Column("features", sa.String(1000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("plan_id"),
    )

    # --- subscriptions ---
    op.create_table(
        "subscriptions",
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", substatus, nullable=False, server_default="active"),
        sa.Column("price_at_subscription", sa.Float(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("current_period_end", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.plan_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("subscription_id"),
    )
    op.create_index("idx_subscriptions_user_id", "subscriptions", ["user_id"])


def downgrade() -> None:
    op.drop_table("subscriptions")
    op.drop_table("subscription_plans")
    op.drop_table("payouts")
    op.drop_table("platform_settings")
    op.drop_table("issue_reports")
    op.drop_table("reviews")
    op.drop_column("brands", "rejection_reason")
    op.drop_column("brands", "status")
    op.drop_column("users", "block_reason")
    op.drop_column("users", "blocked_until")

    bind = op.get_bind()
    for name in ("subscriptionstatus", "reportstatus", "brandstatus"):
        postgresql.ENUM(name=name).drop(bind)
