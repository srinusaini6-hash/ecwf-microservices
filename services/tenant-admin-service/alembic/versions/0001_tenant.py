from alembic import op
import sqlalchemy as sa

revision = "0001_tenant"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("legal_name", sa.String(220), nullable=True),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("primary_domain", sa.String(255), nullable=True),
        sa.Column("organization_type", sa.String(50), nullable=False, server_default="enterprise"),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("website", sa.String(300), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"])
    op.create_index("ix_tenants_owner", "tenants", ["owner_user_id"])

    op.create_table(
        "tenant_settings",
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="Asia/Kolkata"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="INR"),
        sa.Column("data_region", sa.String(50), nullable=False, server_default="India"),
        sa.Column("storage_plan", sa.String(50), nullable=False, server_default="standard"),
        sa.Column("user_limit", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("security_policy", sa.String(50), nullable=False, server_default="standard"),
        sa.Column("require_mfa", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("session_timeout_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("max_concurrent_sessions", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("allowed_domains", sa.JSON(), nullable=False),
    )

    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("head_membership_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_department_tenant_code"),
    )
    op.create_index("ix_departments_tenant", "departments", ["tenant_id"])
    op.create_index("ix_departments_parent", "departments", ["parent_id"])

    op.create_table(
        "memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("role_code", sa.String(80), nullable=False, server_default="tenant_user"),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_membership_tenant_user"),
    )
    op.create_index("ix_memberships_tenant", "memberships", ["tenant_id"])
    op.create_index("ix_memberships_user", "memberships", ["user_id"])
    op.create_index("ix_memberships_department", "memberships", ["department_id"])

    op.create_table(
        "invitations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("role_code", sa.String(80), nullable=False, server_default="tenant_user"),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_sent_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("rejected_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("accepted_by_user_id", sa.Integer(), nullable=True),
        sa.Column("resend_count", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("token_hash", name="uq_invitation_token_hash"),
    )
    op.create_index("ix_invitations_tenant", "invitations", ["tenant_id"])
    op.create_index("ix_invitations_email", "invitations", ["email"])
    op.create_index("ix_invitations_status", "invitations", ["status"])


def downgrade():
    for table in ["invitations", "memberships", "departments", "tenant_settings", "tenants"]:
        op.drop_table(table)
