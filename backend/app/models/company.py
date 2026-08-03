"""
Financial Intelligence Platform — Company Models

The canonical company registry. Every company has ONE canonical ID.
All aliases resolve to that ID via the entity resolution service.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Company(Base):
    """
    Canonical company entity.

    Every company in the system has exactly one record here.
    All name variants (ticker, legal name, common name) are in company_aliases.
    """

    __tablename__ = "companies"

    company_id: Mapped[str] = mapped_column(
        String(50), primary_key=True, comment="Canonical ID, e.g., 'AAPL_US'"
    )
    name: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Primary display name"
    )
    legal_name: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Official legal entity name"
    )
    ticker: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Exchange ticker symbol"
    )
    exchange: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="NYSE, NASDAQ, BSE, NSE"
    )
    isin: Mapped[str | None] = mapped_column(
        String(12), nullable=True, comment="International Securities Identification Number"
    )
    cik: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="SEC Central Index Key"
    )
    market: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="'US' or 'IN'"
    )
    sector_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Sector classification"
    )
    industry: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Industry classification"
    )
    country: Mapped[str | None] = mapped_column(
        String(5), nullable=True, comment="ISO country code"
    )
    website: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Company description"
    )
    market_cap: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="Market capitalization in base currency"
    )
    employees: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    source_tier: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    provenance_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("provenance_records.provenance_id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Soft delete timestamp"
    )

    # Relationships
    aliases: Mapped[list["CompanyAlias"]] = relationship(
        back_populates="company", lazy="selectin"
    )

    __table_args__ = (
        Index("idx_companies_ticker", "ticker"),
        Index("idx_companies_cik", "cik"),
        Index("idx_companies_market", "market"),
        Index("idx_companies_sector", "sector_id"),
    )

    def __repr__(self) -> str:
        return f"<Company {self.company_id} ({self.ticker})>"


class CompanyAlias(Base):
    """
    All known name variants for a company.

    Used by the entity resolution service to map mentions
    like "Tata Motors Ltd" or "TATAMOTORS" to a canonical company_id.
    """

    __tablename__ = "company_aliases"

    alias_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("companies.company_id"), nullable=False
    )
    alias: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="The alias text"
    )
    alias_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="'ticker', 'legal', 'common', 'subsidiary', 'former'"
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="aliases")

    __table_args__ = (
        Index("idx_aliases_alias", "alias"),
        Index("idx_aliases_company", "company_id"),
    )

    def __repr__(self) -> str:
        return f"<Alias '{self.alias}' → {self.company_id}>"
