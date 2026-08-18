from alembic import op
import sqlalchemy as sa
revision="0001_notification";down_revision=None;branch_labels=None;depends_on=None

def upgrade():op.create_table("delivery_logs",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("recipient",sa.String(255),nullable=False),sa.Column("actual_recipient",sa.String(255),nullable=False),sa.Column("template",sa.String(100),nullable=False),sa.Column("subject",sa.String(255),nullable=False),sa.Column("status",sa.String(30),nullable=False),sa.Column("error",sa.Text()),sa.Column("created_at",sa.DateTime(),nullable=False))
def downgrade():op.drop_table("delivery_logs")
