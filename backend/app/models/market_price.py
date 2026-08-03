"""
Financial Intelligence Platform — Market Prices Model

Daily OHLCV data. For V1 we store daily candles, not tick-level.
Tick-level moves to ClickHouse when volume justifies it.
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    DECIMAL,
    ForeignKey,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MarketPrice(Base):
    """Daily OHLCV price data for a company."""

    __tablename__ = "market_prices"

    price_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("companies.company_id"), nullable=False
    )
    price_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )
    open_price: Mapped[float | None] = mapped_column(
        DECIMAL(16, 4), nullable=True
    )
    high_price: Mapped[float | None] = mapped_column(
        DECIMAL(16, 4), nullable=True
    )
    low_price: Mapped[float | None] = mapped_column(
        DECIMAL(16, 4), nullable=True
    )
    close_price: Mapped[float] = mapped_column(
        DECIMAL(16, 4), nullable=False
    )
    adj_close: Mapped[float | None] = mapped_column(
        DECIMAL(16, 4), nullable=True, comment="Adjusted close for splits/dividends"
    )
    volume: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    currency: Mapped[str] = mapped_column(
        String(5), nullable=False, default="USD"
    )
    source_tier: Mapped[int] = mapped_column(
        SmallInteger, nullable=False
    )
    provenance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("provenance_records.provenance_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id", "price_date", "source_tier",
            name="uq_price_company_date_source"
        ),
        # Composite index for the most common query: latest prices for a company
        {"comment": "Daily OHLCV. Migrate to ClickHouse when 10M+ rows cause latency."},
    )

    def __repr__(self) -> str:
        return f"<Price {self.company_id} {self.price_date} close={self.close_price}>"
