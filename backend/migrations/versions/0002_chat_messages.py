"""chat_messages: conversation memory for the agent"""
revision = "0002"
down_revision = "0001"
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

def upgrade():
    op.create_table("chat_messages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.String(64), nullable=False),
        sa.Column("contract_id", UUID(as_uuid=False), sa.ForeignKey("contracts.contract_id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('user','assistant')", name="ck_chat_role"))
    op.create_index("ix_chat_session", "chat_messages", ["session_id", "id"])

def downgrade():
    op.drop_table("chat_messages")
