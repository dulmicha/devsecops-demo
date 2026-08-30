from fastapi.testclient import TestClient

from app.models import Severity, Status


def test_healthcheck(client: TestClient) -> None:
    """Verify healthcheck endpoint returns healthy status and record count."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["records_loaded"] == 2500
    assert data["app_name"] == "devsecops-demo"


def test_root_endpoint(client: TestClient) -> None:
    """Verify root endpoint returns API links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "docs_url" in data
    assert "health_url" in data


def test_create_finding_success(client: TestClient) -> None:
    """Verify creating a valid finding returns 201 and persists record."""
    payload = {
        "title": "Unauthenticated Prometheus Metrics Endpoint",
        "severity": Severity.HIGH,
        "asset_name": "k8s-ingress",
        "cve_id": "CVE-2024-9999",
        "status": Status.OPEN,
        "description": "Metrics endpoint exposed to public internet.",
    }
    response = client.post("/api/v1/findings", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["severity"] == Severity.HIGH
    assert data["asset_name"] == payload["asset_name"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

    # Verify retrieval
    get_res = client.get(f"/api/v1/findings/{data['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == data["id"]


def test_create_finding_validation_error(client: TestClient) -> None:
    """Verify validation error when title is too short or invalid severity."""
    # Title too short (< 3 chars)
    payload = {
        "title": "x",
        "severity": "INVALID_SEVERITY",
        "asset_name": "api",
    }
    response = client.post("/api/v1/findings", json=payload)
    assert response.status_code == 422


def test_get_finding_not_found(client: TestClient) -> None:
    """Verify 404 is returned for non-existent finding ID."""
    response = client.get("/api/v1/findings/non-existent-uuid-1234")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_finding_success(client: TestClient) -> None:
    """Verify partial update on existing finding."""
    # List first finding to get an ID
    list_res = client.get("/api/v1/findings?limit=1")
    finding_id = list_res.json()["items"][0]["id"]

    update_payload = {
        "title": "Updated Finding Title After Triage",
        "severity": Severity.CRITICAL,
        "status": Status.IN_TRIAGE,
    }
    response = client.put(f"/api/v1/findings/{finding_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_payload["title"]
    assert data["severity"] == Severity.CRITICAL
    assert data["status"] == Status.IN_TRIAGE


def test_update_finding_not_found(client: TestClient) -> None:
    """Verify 404 on update for non-existent finding ID."""
    response = client.put(
        "/api/v1/findings/non-existent-id",
        json={"title": "Updated Title Here"},
    )
    assert response.status_code == 404


def test_delete_finding_success(client: TestClient) -> None:
    """Verify deleting an existing finding returns 204 and removes record."""
    # Create a finding to delete
    create_res = client.post(
        "/api/v1/findings",
        json={
            "title": "Temporary Finding for Deletion",
            "severity": Severity.LOW,
            "asset_name": "test-asset",
        },
    )
    finding_id = create_res.json()["id"]

    # Delete
    del_res = client.delete(f"/api/v1/findings/{finding_id}")
    assert del_res.status_code == 204

    # Verify no longer exists
    get_res = client.get(f"/api/v1/findings/{finding_id}")
    assert get_res.status_code == 404


def test_delete_finding_not_found(client: TestClient) -> None:
    """Verify 404 when attempting to delete non-existent finding."""
    response = client.delete("/api/v1/findings/non-existent-uuid")
    assert response.status_code == 404


def test_get_metrics_summary(client: TestClient) -> None:
    """Verify metrics summary endpoint calculates correct aggregate distributions."""
    response = client.get("/api/v1/findings/metrics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert data["total"] == 2500
    assert "by_severity" in data
    assert "by_status" in data
    assert Severity.CRITICAL.value in data["by_severity"]
    assert Status.OPEN.value in data["by_status"]
