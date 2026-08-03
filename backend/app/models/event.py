"""
Financial Intelligence Platform — Event Model

The event engine is your proprietary moat. Everything else can be
replicated. A deep, structured, verifiable event graph built over
years cannot.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    DECIMAL,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Event(Base):
    """
    A financial event — earnings, M&A, management change, regulatory action, etc.

    Every event has claim_status tracking (verified → contradicted),
    market impact observation, and cascade detection.
    """

    __tablename__ = "events"

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="earnings_release, guidance_update, management_change, merger_acquisition, etc."
    )
    company_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("companies.company_id"), nullable=True
    )
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("people.person_id"), nullable=True
    )
    event_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    event_title: Mapped[str] = mapped_column(
        String(500), nullable=False
    )
    event_description: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    source_id: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    source_tier: Mapped[int] = mapped_column(
        SmallInteger, nullable=False
    )
    claim_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unconfirmed",
        comment="verified|corroborated|plausible|unconfirmed|contradicted"
    )
    market_impact_observed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    price_reaction_pct: Mapped[float | None] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="Observed price reaction percentage"
    )
    reaction_window_hrs: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Hours after event when reaction was measured"
    )
    related_event_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=True
    )
    sector_tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(50)), nullable=True
    )
    geography_tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(10)), nullable=True
    )
    # Information cascade detection
    is_cascade: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="True if this is a downstream repetition, not an original signal"
    )
    origin_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.event_id"), nullable=True,
        comment="If is_cascade=True, points to the originating event"
    )
    mention_velocity: Mapped[float | None] = mapped_column(
        DECIMAL(10, 2), nullable=True, comment="Mentions per hour at detection time"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "claim_status IN ('verified', 'corroborated', 'plausible', 'unconfirmed', 'contradicted')",
            name="valid_claim_status"
        ),
        Index("idx_events_company", "company_id"),
        Index("idx_events_type", "event_type"),
        Index("idx_events_date", "event_date"),
        Index("idx_events_claim", "claim_status"),
        Index("idx_events_cascade", "is_cascade", postgresql_where="is_cascade = true"),
    )

    def __repr__(self) -> str:
        return f"<Event {self.event_type} company={self.company_id} status={self.claim_status}>"
