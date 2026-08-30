from fastapi.testclient import TestClient

from app.models import Severity, Status


def test_default_pagination(client: TestClient) -> None:
    """Verify default pagination parameters and response headers."""
    response = client.get("/api/v1/findings")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2500
    assert len(data["items"]) == 20
    assert data["limit"] == 20
    assert data["offset"] == 0
    assert data["has_more"] is True

    # Verify custom headers
    assert response.headers["X-Total-Count"] == "2500"
    assert response.headers["X-Page-Size"] == "20"
    assert response.headers["X-Offset"] == "0"
    assert response.headers["X-Limit"] == "20"


def test_custom_limit_and_offset(client: TestClient) -> None:
    """Verify custom offset and limit parameters."""
    response = client.get("/api/v1/findings?offset=50&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["offset"] == 50
    assert data["limit"] == 10
    assert data["has_more"] is True


def test_pagination_last_page(client: TestClient) -> None:
    """Verify pagination behavior on the boundary / last page."""
    response = client.get("/api/v1/findings?offset=2490&limit=20")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["has_more"] is False


def test_pagination_offset_beyond_dataset(client: TestClient) -> None:
    """Verify offset beyond total count returns empty items with has_more=False."""
    response = client.get("/api/v1/findings?offset=5000&limit=20")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0
    assert data["has_more"] is False


def test_pagination_invalid_parameters(client: TestClient) -> None:
    """Verify 422 error when limit or offset exceed defined constraints."""
    # Negative offset
    assert client.get("/api/v1/findings?offset=-1").status_code == 422

    # Limit = 0 (minimum is 1)
    assert client.get("/api/v1/findings?limit=0").status_code == 422

    # Limit > 100 (maximum allowed is 100)
    assert client.get("/api/v1/findings?limit=101").status_code == 422


def test_filter_by_severity(client: TestClient) -> None:
    """Verify filtering findings by severity enum."""
    response = client.get("/api/v1/findings?severity=CRITICAL&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for item in data["items"]:
        assert item["severity"] == Severity.CRITICAL


def test_filter_by_status(client: TestClient) -> None:
    """Verify filtering findings by status enum."""
    response = client.get("/api/v1/findings?status=RESOLVED&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for item in data["items"]:
        assert item["status"] == Status.RESOLVED


def test_search_filter(client: TestClient) -> None:
    """Verify search filter across title, asset, and CVE."""
    # Create specific searchable record
    client.post(
        "/api/v1/findings",
        json={
            "title": "Unique Searchable Vulnerability Ingress Test",
            "severity": Severity.MEDIUM,
            "asset_name": "unique-search-asset",
            "cve_id": "CVE-2024-8888",
        },
    )

    response = client.get("/api/v1/findings?search=unique-search-asset")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(item["asset_name"] == "unique-search-asset" for item in data["items"])
