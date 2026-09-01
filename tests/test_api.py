"""Integration tests against the FastAPI app via TestClient."""
from fastapi.testclient import TestClient


def test_root(client: TestClient):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["service"] == "cert-tracker"


def test_create_and_get_certification(client: TestClient):
    resp = client.post("/certs", json={"name": "AZ-900", "target_hours": 15})
    assert resp.status_code == 201
    cert_id = resp.json()["id"]

    resp = client.get(f"/certs/{cert_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "AZ-900"


def test_create_duplicate_certification_conflicts(client: TestClient):
    client.post("/certs", json={"name": "DP-900"})
    resp = client.post("/certs", json={"name": "DP-900"})
    assert resp.status_code == 409


def test_log_session_by_cert_name_auto_creates_cert(client: TestClient):
    resp = client.post(
        "/sessions",
        json={"cert_name": "AZ-900", "hours": 3, "topic": "core services", "confidence": 3},
    )
    assert resp.status_code == 201
    assert resp.json()["cert_id"] is not None


def test_next_up_with_no_certs_404s(client: TestClient):
    resp = client.get("/next")
    assert resp.status_code == 404


def test_next_up_picks_lowest_readiness(client: TestClient):
    strong = client.post("/certs", json={"name": "AZ-900", "target_hours": 10}).json()["id"]
    weak = client.post("/certs", json={"name": "DP-900", "target_hours": 10}).json()["id"]

    client.post("/sessions", json={"cert_id": strong, "hours": 10, "topic": "a", "confidence": 5})
    client.post("/sessions", json={"cert_id": weak, "hours": 1, "topic": "b", "confidence": 1})

    resp = client.get("/next")
    assert resp.status_code == 200
    assert resp.json()["cert"]["cert_name"] == "DP-900"