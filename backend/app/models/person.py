"""
Financial Intelligence Platform — Person Influence Graph Model

Not just a celebrity list. A database of people who move markets.
Influence is computed deterministically from historical market reactions,
not from follower count alone.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    DECIMAL,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Person(Base):
    """
    A market-moving individual in the person influence graph.

    Categories: executives, government officials, finance professionals,
    industry leaders, media/journalists.

    influence_score is deterministic:
    = audience_reach * 0.20
    + financial_relevance * 0.25
    + historical_market_impact * 0.35
    + source_credibility * 0.15
    + topic_specificity * 0.05
    """

    __tablename__ = "people"

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(300), nullable=False
    )
    aliases: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(300)), nullable=True
    )
    current_role: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="e.g., 'CEO', 'CFO', 'Minister of Finance'"
    )
    company_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("companies.company_id"), nullable=True
    )
    influence_score: Mapped[float] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=0,
        comment="Deterministic score 0.0-1.0"
    )
    topic_scores: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment='{"Q3 earnings": 0.95, "geopolitics": 0.2}'
    )
    credibility_tier: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=4, comment="1-5 tier"
    )
    follower_counts: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment='{"twitter": 20000000, "linkedin": 500000}'
    )
    source_platform_ids: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment='{"twitter": "@handle", "linkedin": "profile_url"}'
    )
    historical_impact_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Number of past statements that caused measurable market reaction"
    )
    historical_impact_median: Mapped[float | None] = mapped_column(
        DECIMAL(8, 4), nullable=True,
        comment="Median price reaction percentage from past statements"
    )
    bio: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_people_company", "company_id"),
        Index("idx_people_influence", "influence_score"),
        Index("idx_people_name", "name"),
    )

    def __repr__(self) -> str:
        return f"<Person {self.name} influence={self.influence_score}>"
