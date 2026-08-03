"""
Financial Intelligence Platform — ORM Models

All 12 tables in the system, imported here for Alembic
auto-detection and convenient access.
"""

# Core entities
from app.models.company import Company, CompanyAlias
from app.models.person import Person
from app.models.provenance import ProvenanceRecord

# Financial data
from app.models.financial_metric import FinancialMetric
from app.models.market_price import MarketPrice

# Intelligence layer
from app.models.event import Event
from app.models.news import NewsItem

# Supporting tables
from app.models.supporting import (
    AgentToolLog,
    Embedding,
    Quarantine,
    Relationship,
    User,
    UserApiKey,
)

__all__ = [
    # Core
    "Company",
    "CompanyAlias",
    "Person",
    "ProvenanceRecord",
    # Financial
    "FinancialMetric",
    "MarketPrice",
    # Intelligence
    "Event",
    "NewsItem",
    # Supporting
    "AgentToolLog",
    "Embedding",
    "Quarantine",
    "Relationship",
    "User",
    "UserApiKey",
]
