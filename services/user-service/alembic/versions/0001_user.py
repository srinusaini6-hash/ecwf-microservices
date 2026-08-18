from alembic import op
import sqlalchemy as sa
revision="0001_user";down_revision=None;branch_labels=None;depends_on=None

def upgrade():
    op.create_table("user_profiles",sa.Column("user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="CASCADE"),primary_key=True),sa.Column("phone",sa.String(30)),sa.Column("job_title",sa.String(120)),sa.Column("bio",sa.Text()),sa.Column("profile_image_url",sa.String(500)),sa.Column("locale",sa.String(20),nullable=False,server_default="en-IN"),sa.Column("timezone",sa.String(60),nullable=False,server_default="Asia/Kolkata"),sa.Column("updated_at",sa.DateTime(),nullable=False))
    op.create_table("user_account_settings",sa.Column("user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="CASCADE"),primary_key=True),sa.Column("email_notifications",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("security_notifications",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("theme",sa.String(20),nullable=False,server_default="system"),sa.Column("updated_at",sa.DateTime(),nullable=False))

def downgrade():op.drop_table("user_account_settings");op.drop_table("user_profiles")
