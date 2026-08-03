"""
Financial Intelligence Platform — Relationship, Embedding, Quarantine,
User, UserApiKey, and AgentToolLog Models

These are the supporting tables that complete the 12-table schema.
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    DECIMAL,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ─────────────────────────────────────────────
# Relationship Graph
# ─────────────────────────────────────────────

class Relationship(Base):
    """
    Entity-to-entity relationships: supplier, customer, competitor,
    subsidiary, board_member, investor, etc.

    The knowledge graph is built in PostgreSQL first.
    Move to a graph database only if query patterns justify it.
    """

    __tablename__ = "relationships"

    relationship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    from_entity_id: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    from_entity_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="'company' or 'person'"
    )
    to_entity_id: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    to_entity_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="supplier, customer, competitor, subsidiary, board_member, investor"
    )
    strength: Mapped[float] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=0.5, comment="0.0 to 1.0"
    )
    source_tier: Mapped[int] = mapped_column(
        SmallInteger, nullable=False
    )
    provenance_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("provenance_records.provenance_id"), nullable=True
    )
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_rel_from", "from_entity_id"),
        Index("idx_rel_to", "to_entity_id"),
        Index("idx_rel_type", "relationship_type"),
    )

    def __repr__(self) -> str:
        return f"<Rel {self.from_entity_id} --{self.relationship_type}--> {self.to_entity_id}>"


# ─────────────────────────────────────────────
# Vector Embeddings
# ─────────────────────────────────────────────

class Embedding(Base):
    """
    Vector embeddings for semantic search.

    Rules:
    - Use a SINGLE consistent embedding model
    - NEVER mix embeddings from different models in the same index
    - When upgrading models, re-embed everything, keep old index until validated
    """

    __tablename__ = "embeddings"

    embedding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_id: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="event_id, news_id, filing_id, etc."
    )
    entity_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="'event', 'news', 'filing', 'social'"
    )
    content_text: Mapped[str] = mapped_column(
        Text, nullable=False, comment="The text that was embedded"
    )
    content_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="SHA-256 of content_text"
    )
    # NOTE: The vector column is created in the migration using raw SQL
    # because SQLAlchemy doesn't natively handle pgvector well in all cases.
    # Column: embedding vector(768)
    model_version: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="e.g., 'nomic-embed-text-v1.5'"
    )
    embedded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_embed_entity", "entity_id"),
    )

    def __repr__(self) -> str:
        return f"<Embedding {self.entity_type}:{self.entity_id}>"


# ─────────────────────────────────────────────
# Quarantine Queue
# ─────────────────────────────────────────────

class Quarantine(Base):
    """
    Records that fail validation but are not definitively wrong.

    A background job reviews quarantine daily and either:
    - Promotes (cross-source agreement appeared)
    - Discards (confirmed bad data)
    """

    __tablename__ = "quarantine"

    quarantine_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    record_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="'metric', 'price', 'event'"
    )
    raw_data: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )
    failure_reason: Mapped[str] = mapped_column(
        String(200), nullable=False
    )
    failure_details: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )
    source_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        comment="pending | promoted | discarded"
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_by: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_quarantine_status", "status", postgresql_where="status = 'pending'"),
    )

    def __repr__(self) -> str:
        return f"<Quarantine {self.record_type} status={self.status}>"


# ─────────────────────────────────────────────
# Users + BYOM API Keys
# ─────────────────────────────────────────────

class User(Base):
    """Application user."""

    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(320), nullable=False, unique=True
    )
    display_name: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    hashed_password: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Null if using OAuth"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class UserApiKey(Base):
    """
    Encrypted API keys for BYOM (Bring Your Own Model) architecture.

    Security rules:
    - encrypted_key is AES-256-GCM encrypted at rest
    - key_suffix (last 4 chars) is the ONLY part ever logged or displayed
    - Keys are decrypted ONLY in memory at the moment of API call
    - NEVER log the full key
    """

    __tablename__ = "user_api_keys"

    key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    provider: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="'gemini', 'openai', 'anthropic', 'groq', 'ollama'"
    )
    encrypted_key: Mapped[str] = mapped_column(
        Text, nullable=False, comment="AES-256-GCM encrypted"
    )
    key_suffix: Mapped[str] = mapped_column(
        String(4), nullable=False, comment="Last 4 chars for display only"
    )
    model_preference: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="e.g., 'gemini-2.0-flash'"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )

    def __repr__(self) -> str:
        return f"<ApiKey {self.provider} ...{self.key_suffix}>"


# ─────────────────────────────────────────────
# Agent Tool Audit Log
# ─────────────────────────────────────────────

class AgentToolLog(Base):
    """
    Audit trail for every tool invocation by the research agent.

    If you can't answer "why did the system produce this response?",
    the system has failed. This table ensures you always can.
    """

    __tablename__ = "agent_tool_logs"

    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trace_id: Mapped[str] = mapped_column(
        String(36), nullable=False, comment="Request trace ID for end-to-end tracing"
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    tool_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    parameters: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )
    response_time_ms: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    evidence_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    provider_used: Mapped[str | None] = mapped_column(
        String(30), nullable=True, comment="Which AI provider was called"
    )
    model_used: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    error: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_tool_logs_trace", "trace_id"),
        Index("idx_tool_logs_user", "user_id"),
        Index("idx_tool_logs_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ToolLog {self.tool_name} trace={self.trace_id}>"
