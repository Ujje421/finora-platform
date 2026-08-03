"""
Financial Intelligence Platform — Test Configuration
"""

import pytest


@pytest.fixture
def sample_company():
    """Sample company data for testing."""
    return {
        "company_id": "AAPL_US",
        "name": "Apple Inc.",
        "ticker": "AAPL",
        "exchange": "NASDAQ",
        "cik": "0000320193",
        "market": "US",
        "sector_id": "technology",
        "industry": "Consumer Electronics",
        "country": "US",
        "source_tier": 1,
        "is_verified": True,
    }


@pytest.fixture
def sample_provenance():
    """Sample provenance record for testing."""
    return {
        "source_id": "sec_edgar",
        "source_name": "SEC EDGAR",
        "source_tier": 1,
        "source_url": "https://www.sec.gov/cgi-bin/browse-edgar",
        "raw_hash": "a" * 64,
        "confidence_initial": 1.0,
    }


@pytest.fixture
def sample_financial_metric():
    """Sample financial metric for testing."""
    return {
        "company_id": "AAPL_US",
        "metric_name": "revenue",
        "value": 94836000000,
        "currency": "USD",
        "unit": "absolute",
        "period_type": "Q3",
        "period_year": 2026,
        "period_end_date": "2026-06-28",
        "source_tier": 1,
        "is_verified": True,
    }
