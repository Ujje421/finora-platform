"""
Financial Intelligence Platform — Financial Metrics Model

Stores structured financial data with full provenance.
Rule: LLMs NEVER calculate these. Deterministic Python/SQL only.
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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FinancialMetric(Base):
    """
    A single financial metric for a company in a specific period.

    Examples: revenue Q3 2026, EPS FY2025, total_debt Q2 2026.
    Every record has provenance — you can always trace it to its source.
    """

    __tablename__ = "financial_metrics"

    metric_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("companies.company_id"), nullable=False
    )
    metric_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="'revenue', 'net_income', 'eps', 'ebitda', 'total_debt', etc."
    )
    value: Mapped[float] = mapped_column(
        DECIMAL(20, 4), nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(5), nullable=False, default="USD"
    )
    unit: Mapped[str] = mapped_column(
        String(20), nullable=False, default="absolute",
        comment="'absolute', 'thousands', 'millions', 'billions'"
    )
    period_type: Mapped[str] = mapped_column(
        String(10), nullable=False,
        comment="'Q1', 'Q2', 'Q3', 'Q4', 'FY', 'TTM'"
    )
    period_year: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    period_end_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )
    source_tier: Mapped[int] = mapped_column(
        SmallInteger, nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    provenance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("provenance_records.provenance_id"), nullable=False
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
        UniqueConstraint(
            "company_id", "metric_name", "period_type", "period_year", "source_tier",
            name="uq_metric_company_period_source"
        ),
        Index("idx_metrics_company", "company_id"),
        Index("idx_metrics_period", "period_year", "period_type"),
        Index("idx_metrics_metric", "metric_name"),
    )

    def __repr__(self) -> str:
        return f"<Metric {self.company_id} {self.metric_name}={self.value} {self.period_type}{self.period_year}>"
