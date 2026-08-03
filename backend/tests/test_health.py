"""
Tests for the health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    """Basic health check returns 200 with service info."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "financial-terminal"
    assert "version" in data


def test_health_check_has_trace_id():
    """Health check response includes X-Trace-ID header."""
    response = client.get("/health")
    assert "X-Trace-ID" in response.headers
    assert len(response.headers["X-Trace-ID"]) > 0


def test_health_check_propagates_trace_id():
    """If a trace ID is provided, it is propagated in the response."""
    response = client.get("/health", headers={"X-Trace-ID": "test-123"})
    assert response.headers["X-Trace-ID"] == "test-123"


def test_response_time_header():
    """Response includes X-Response-Time-MS header."""
    response = client.get("/health")
    assert "X-Response-Time-MS" in response.headers
    assert int(response.headers["X-Response-Time-MS"]) >= 0
