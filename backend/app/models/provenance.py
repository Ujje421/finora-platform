"""
Financial Intelligence Platform — Provenance Records Model

Every financial fact in the system has a provenance record.
This is the audit trail — you can always answer:
"Where did this number come from?"

These records are IMMUTABLE once created. The calculation layer
can add derived confidence but cannot modify original provenance.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DECIMAL,
    DateTime,
    Index,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProvenanceRecord(Base):
    """
    Source tracking for every financial fact in the system.

    Immutable after creation. Never update these records.
    """

    __tablename__ = "provenance_records"

    provenance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="e.g., 'sec_edgar', 'yahoo_finance'"
    )
    source_name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Human-readable source name"
    )
    source_tier: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, comment="1=Primary, 2=Licensed, 3=Secondary, 4=Social, 5=Unverified"
    )
    source_url: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="URL where the data was retrieved from"
    )
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="When we fetched it"
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When the source published it"
    )
    raw_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="SHA-256 hash of the raw input"
    )
    raw_object_key: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Path in object storage (R2/S3)"
    )
    confidence_initial: Mapped[float] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=1.0, comment="Initial confidence score 0.0-1.0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_provenance_source", "source_id"),
        Index("idx_provenance_retrieved", "retrieved_at"),
        {"comment": "Immutable provenance records — never update after creation"},
    )

    def __repr__(self) -> str:
        return f"<Provenance {self.source_id} tier={self.source_tier} at={self.retrieved_at}>"
