"""init: contracts + contract_chunks"""
revision = "0001"
down_revision = None
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, ARRAY

def upgrade():
    op.create_table("contracts",
        sa.Column("contract_id", UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status", sa.String(20), server_default="Active", nullable=False),
        sa.Column("ingestion_status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("start_date", sa.Date()), sa.Column("end_date", sa.Date()),
        sa.CheckConstraint("status IN ('Active','Expiring Soon','Expired')", name="ck_contract_status"),
        sa.CheckConstraint("ingestion_status IN ('pending','processing','ready','failed')", name="ck_ingestion_status"))
    op.create_index("ix_contracts_name", "contracts", ["name"])
    op.create_index("ix_contracts_end_date", "contracts", ["end_date"])
    op.create_table("contract_chunks",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("contract_id", UUID(as_uuid=False), sa.ForeignKey("contracts.contract_id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page", sa.Integer()),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", ARRAY(sa.REAL()), nullable=False),
        sa.UniqueConstraint("contract_id", "chunk_index", name="uq_chunk_position"))
    op.create_index("ix_contract_chunks_contract_id", "contract_chunks", ["contract_id"])

def downgrade():
    op.drop_table("contract_chunks"); op.drop_table("contracts")
