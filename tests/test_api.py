"""Tests for the PAR Scrape API endpoints."""

import pytest
from fastapi.testclient import TestClient
from par_scrape.api import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "endpoints" in data
    assert "scrape" in data["endpoints"]
    assert "health" in data["endpoints"]


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


def test_scrape_invalid_url():
    """Test scraping with an invalid URL returns 400."""
    response = client.post("/scrape", json={"url": "invalid-url"})
    assert response.status_code == 400
    assert "Invalid URL" in response.json()["detail"]


def test_scrape_missing_url():
    """Test scraping without URL returns 422 validation error."""
    response = client.post("/scrape", json={})
    assert response.status_code == 422  # Validation error


def test_scrape_no_scheme():
    """Test scraping with URL missing scheme returns 400."""
    response = client.post("/scrape", json={"url": "www.example.com"})
    assert response.status_code == 400


def test_scrape_wait_selector_required():
    """Test that wait_selector is required when wait_type is 'selector'."""
    response = client.post(
        "/scrape", json={"url": "https://example.com", "wait_type": "selector", "wait_selector": None}
    )
    assert response.status_code == 400
    assert "wait_selector is required" in response.json()["detail"]


def test_scrape_request_defaults():
    """Test that request model has proper defaults."""
    from par_scrape.api import ScrapeRequest

    request = ScrapeRequest(url="https://example.com")
    assert request.fetch_using == "playwright"
    assert request.sleep_time == 2
    assert request.timeout == 10
    assert request.headless is True
    assert request.wait_type == "sleep"


def test_scrape_request_validation():
    """Test request validation with invalid values."""
    from pydantic import ValidationError

    from par_scrape.api import ScrapeRequest

    # Test sleep_time too high
    with pytest.raises(ValidationError):
        ScrapeRequest(url="https://example.com", sleep_time=100)

    # Test timeout too low
    with pytest.raises(ValidationError):
        ScrapeRequest(url="https://example.com", timeout=0)


def test_validate_url_function():
    """Test the validate_url helper function."""
    from par_scrape.api import InvalidURLError, validate_url

    # Valid URLs should not raise
    validate_url("https://example.com")
    validate_url("http://example.com")

    # Invalid URLs should raise
    with pytest.raises(InvalidURLError):
        validate_url("ftp://example.com")

    with pytest.raises(InvalidURLError):
        validate_url("example.com")

    with pytest.raises(InvalidURLError):
        validate_url("")


def test_map_wait_type_function():
    """Test the map_wait_type helper function."""
    from par_ai_core.web_tools import ScraperWaitType
    from par_scrape.api import map_wait_type

    assert map_wait_type("sleep") == ScraperWaitType.SLEEP
    assert map_wait_type("idle") == ScraperWaitType.IDLE
    assert map_wait_type("none") == ScraperWaitType.NONE
    assert map_wait_type("selector") == ScraperWaitType.SELECTOR
    assert map_wait_type("text") == ScraperWaitType.TEXT
    assert map_wait_type("invalid") == ScraperWaitType.SLEEP  # Default


def test_openapi_schema():
    """Test that OpenAPI schema is generated correctly."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    assert "/" in schema["paths"]
    assert "/health" in schema["paths"]
    assert "/scrape" in schema["paths"]


def test_scrape_response_format():
    """Test that scrape response has correct format with urls and text fields."""
    from par_scrape.api import ScrapeResponse

    # Test response model structure
    response = ScrapeResponse(
        url="https://example.com",
        urls=["https://example.com/link1", "https://example.com/link2"],
        text="This is visible text content",
        fetch_using="playwright",
        processing_time=1.5,
    )

    assert response.url == "https://example.com"
    assert isinstance(response.urls, list)
    assert len(response.urls) == 2
    assert isinstance(response.text, str)
    assert response.fetch_using == "playwright"
    assert response.processing_time == 1.5


def test_scrape_response_json_serialization():
    """Test that response can be properly serialized to JSON."""
    from par_scrape.api import ScrapeResponse

    response = ScrapeResponse(
        url="https://example.com",
        urls=["https://link.com"],
        text="Sample text",
        fetch_using="playwright",
        processing_time=1.0,
    )

    json_data = response.model_dump()
    assert "urls" in json_data
    assert "text" in json_data
    assert "markdown" not in json_data  # Ensure old field is gone
