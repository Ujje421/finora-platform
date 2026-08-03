"""
Financial Intelligence Platform — Pydantic Schemas

Request/response schemas for the API.
These are separate from ORM models — they define the API contract.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────
# Company Schemas
# ─────────────────────────────────────────────

class CompanyBase(BaseModel):
    """Base company fields."""
    name: str
    ticker: str | None = None
    exchange: str | None = None
    market: str
    sector_id: str | None = None
    industry: str | None = None
    country: str | None = None


class CompanyCreate(CompanyBase):
    """Fields required to create a company."""
    company_id: str
    cik: str | None = None
    isin: str | None = None
    legal_name: str | None = None


class CompanyResponse(CompanyBase):
    """Company response with all computed fields."""
    model_config = ConfigDict(from_attributes=True)

    company_id: str
    legal_name: str | None = None
    cik: str | None = None
    isin: str | None = None
    website: str | None = None
    description: str | None = None
    market_cap: int | None = None
    employees: int | None = None
    source_tier: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class CompanyAliasResponse(BaseModel):
    """Company alias for entity resolution."""
    model_config = ConfigDict(from_attributes=True)

    alias_id: uuid.UUID
    company_id: str
    alias: str
    alias_type: str
    is_primary: bool


class CompanyWithAliases(CompanyResponse):
    """Company with all known aliases."""
    aliases: list[CompanyAliasResponse] = []


# ─────────────────────────────────────────────
# Financial Metric Schemas
# ─────────────────────────────────────────────

class FinancialMetricResponse(BaseModel):
    """Financial metric with provenance."""
    model_config = ConfigDict(from_attributes=True)

    metric_id: uuid.UUID
    company_id: str
    metric_name: str
    value: Decimal
    currency: str
    unit: str
    period_type: str
    period_year: int
    period_end_date: date
    source_tier: int
    is_verified: bool
    provenance_id: uuid.UUID


# ─────────────────────────────────────────────
# Event Schemas
# ─────────────────────────────────────────────

class EventResponse(BaseModel):
    """Event with claim status and market impact."""
    model_config = ConfigDict(from_attributes=True)

    event_id: uuid.UUID
    event_type: str
    company_id: str | None
    event_date: datetime
    event_title: str
    event_description: str
    source_id: str
    source_tier: int
    claim_status: str
    market_impact_observed: bool
    price_reaction_pct: Decimal | None
    sector_tags: list[str] | None
    is_cascade: bool
    created_at: datetime
    last_verified_at: datetime | None


# ─────────────────────────────────────────────
# Market Price Schemas
# ─────────────────────────────────────────────

class MarketPriceResponse(BaseModel):
    """Daily OHLCV price."""
    model_config = ConfigDict(from_attributes=True)

    company_id: str
    price_date: date
    open_price: Decimal | None
    high_price: Decimal | None
    low_price: Decimal | None
    close_price: Decimal
    adj_close: Decimal | None
    volume: int | None
    currency: str
    source_tier: int


# ─────────────────────────────────────────────
# News Schemas
# ─────────────────────────────────────────────

class NewsItemResponse(BaseModel):
    """News article with entity links and credibility."""
    model_config = ConfigDict(from_attributes=True)

    news_id: uuid.UUID
    headline: str
    summary: str | None
    source_id: str
    source_name: str | None
    source_tier: int
    source_url: str | None
    published_at: datetime
    company_ids: list[str] | None
    event_types: list[str] | None
    sentiment_score: Decimal | None
    relevance_score: Decimal | None


# ─────────────────────────────────────────────
# Person Schemas
# ─────────────────────────────────────────────

class PersonResponse(BaseModel):
    """Person with influence scores."""
    model_config = ConfigDict(from_attributes=True)

    person_id: uuid.UUID
    name: str
    current_role: str | None
    company_id: str | None
    influence_score: Decimal
    topic_scores: dict
    credibility_tier: int
    historical_impact_count: int
    historical_impact_median: Decimal | None


# ─────────────────────────────────────────────
# Agent / Query Schemas
# ─────────────────────────────────────────────

class AgentQueryRequest(BaseModel):
    """User query to the research agent."""
    query: str = Field(..., min_length=3, max_length=2000)
    company_id: str | None = None
    date_range_days: int = Field(default=30, ge=1, le=365)


class ClaimVerification(BaseModel):
    """Verification result for a single claim."""
    claim_text: str
    status: str  # verified | mismatch | unverifiable
    ai_value: Decimal | None = None
    fact_value: Decimal | None = None
    source: str | None = None


class EvidenceItem(BaseModel):
    """A single piece of evidence supporting or contradicting a conclusion."""
    text: str
    source: str
    source_tier: int
    timestamp: datetime
    verified: bool = False


class AgentQueryResponse(BaseModel):
    """Research agent response with full evidence and citations."""
    main_conclusion: str
    confidence_score: int = Field(..., ge=0, le=100)
    supporting_evidence: list[EvidenceItem] = []
    contradicting_evidence: list[EvidenceItem] = []
    alternative_explanations: list[str] = []
    data_gaps: list[str] = []
    numerical_claims_verified: int = 0
    numerical_claims_total: int = 0
    claims: list[ClaimVerification] = []
    trace_id: str
    last_verified_at: datetime


# ─────────────────────────────────────────────
# BYOM Settings Schemas
# ─────────────────────────────────────────────

class ApiKeyCreate(BaseModel):
    """Request to add/update a BYOM API key."""
    provider: str = Field(..., pattern="^(gemini|openai|anthropic|groq|ollama)$")
    api_key: str = Field(..., min_length=5)
    model_preference: str | None = None


class ApiKeyResponse(BaseModel):
    """API key info (NEVER includes the actual key)."""
    model_config = ConfigDict(from_attributes=True)

    key_id: uuid.UUID
    provider: str
    key_suffix: str  # Last 4 chars only
    model_preference: str | None
    is_active: bool
    last_used_at: datetime | None


# ─────────────────────────────────────────────
# Provenance Schema
# ─────────────────────────────────────────────

class ProvenanceResponse(BaseModel):
    """Provenance record — immutable source tracking."""
    model_config = ConfigDict(from_attributes=True)

    provenance_id: uuid.UUID
    source_id: str
    source_name: str
    source_tier: int
    source_url: str | None
    retrieved_at: datetime
    published_at: datetime | None
    confidence_initial: Decimal


# ─────────────────────────────────────────────
# Entity Resolution Schema
# ─────────────────────────────────────────────

class EntityResolutionResult(BaseModel):
    """Result of resolving an entity mention to a canonical ID."""
    input_text: str
    resolved_company_id: str | None = None
    resolved_name: str | None = None
    match_type: str  # exact | ticker | cik | fuzzy | embedding | none
    confidence: float = Field(..., ge=0.0, le=1.0)
    alternatives: list[dict] = []
