"""Single source of truth for the schema. Schema changes go through Alembic migrations only."""
import uuid
from datetime import date, datetime
from typing import Optional
from sqlalchemy import REAL, String, Date, DateTime, Text, Integer, BigInteger, ForeignKey, CheckConstraint, UniqueConstraint, Index, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Contract(Base):
    __tablename__ = "contracts"
    contract_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(20))                 # pdf | docx | txt
    file_path: Mapped[str] = mapped_column(String(500))                # key returned by shared.storage.save_file
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(20), server_default="Active")             # updated by daily job
    ingestion_status: Mapped[str] = mapped_column(String(20), server_default="pending")  # set by RAG ingestion
    start_date: Mapped[Optional[date]] = mapped_column(Date)           # filled by Contract Information Tool
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    __table_args__ = (
        CheckConstraint("status IN ('Active','Expiring Soon','Expired')", name="ck_contract_status"),
        CheckConstraint("ingestion_status IN ('pending','processing','ready','failed')", name="ck_ingestion_status"),
        Index("ix_contracts_name", "name"), Index("ix_contracts_end_date", "end_date"),
    )

class ContractChunk(Base):
    __tablename__ = "contract_chunks"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    contract_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("contracts.contract_id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    page: Mapped[Optional[int]] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(ARRAY(REAL))  # plain Postgres array, no extension
    __table_args__ = (UniqueConstraint("contract_id", "chunk_index", name="uq_chunk_position"),)


class ChatMessage(Base):
    """Conversation memory for the agent chat (one session = one conversation about one contract)."""
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64))
    contract_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("contracts.contract_id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(10))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (CheckConstraint("role IN ('user','assistant')", name="ck_chat_role"),
                      Index("ix_chat_session", "session_id", "id"))
