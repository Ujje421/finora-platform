"""
Financial Intelligence Platform — News Items Model

News articles with entity linking, source tier tracking,
and provenance. The raw article is stored in object storage;
the structured event we derive from it is the real value.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    DECIMAL,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NewsItem(Base):
    """
    A processed news article linked to companies and events.

    The raw article is preserved in object storage (raw_object_key).
    The structured extraction (entities, events, sentiment) is what
    the research agent and users interact with.
    """

    __tablename__ = "news_items"

    news_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    headline: Mapped[str] = mapped_column(
        String(1000), nullable=False
    )
    summary: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    full_text_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="SHA-256 of full text in object storage"
    )
    source_id: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    source_name: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    source_tier: Mapped[int] = mapped_column(
        SmallInteger, nullable=False
    )
    source_url: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    company_ids: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(50)), nullable=True, comment="Linked company IDs"
    )
    person_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=True
    )
    event_types: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(50)), nullable=True
    )
    sentiment_score: Mapped[float | None] = mapped_column(
        DECIMAL(5, 4), nullable=True, comment="-1.0 (negative) to 1.0 (positive)"
    )
    relevance_score: Mapped[float | None] = mapped_column(
        DECIMAL(5, 4), nullable=True, comment="0.0 to 1.0"
    )
    provenance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("provenance_records.provenance_id"), nullable=False
    )
    raw_object_key: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Full article in object storage"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_news_published", "published_at"),
        Index("idx_news_companies", "company_ids", postgresql_using="gin"),
        Index("idx_news_source", "source_id"),
    )

    def __repr__(self) -> str:
        return f"<News '{self.headline[:50]}...' tier={self.source_tier}>"
