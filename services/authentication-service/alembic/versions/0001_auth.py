from alembic import op
import sqlalchemy as sa

revision = "0001_auth"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("account_type", sa.String(30), nullable=False, server_default="individual"),
        sa.Column("role", sa.String(50), nullable=False, server_default="individual_user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "external_identities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("provider_subject", sa.String(255), nullable=False),
        sa.Column("provider_email", sa.String(255), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("linked_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("provider", "provider_subject", name="uq_external_provider_subject"),
        sa.UniqueConstraint("provider", "user_id", name="uq_external_provider_user"),
    )
    op.create_index("ix_external_provider", "external_identities", ["provider"])
    op.create_index("ix_external_subject", "external_identities", ["provider_subject"])

    op.create_table(
        "mfa_configurations",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("method", sa.String(30), nullable=False, server_default="email"),
        sa.Column("secret_encrypted", sa.String(500), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "oauth_states",
        sa.Column("state_hash", sa.String(64), primary_key=True),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_oauth_states_expires_at", "oauth_states", ["expires_at"])


def downgrade():
    op.drop_table("oauth_states")
    op.drop_table("mfa_configurations")
    op.drop_table("external_identities")
    op.drop_table("users")
