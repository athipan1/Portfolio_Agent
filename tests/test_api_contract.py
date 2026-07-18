from fastapi.testclient import TestClient

from app.main import app


REQUIRED_CONTRACT_FIELDS = {
    "status",
    "agent_type",
    "version",
    "schema_version",
    "timestamp",
    "correlation_id",
    "data",
    "metadata",
    "error",
    "confidence_score",
}


def assert_contract_response(payload):
    assert REQUIRED_CONTRACT_FIELDS.issubset(payload.keys())
    assert payload["agent_type"] == "portfolio-agent"
    assert payload["version"] == "0.1.0"
    assert payload["schema_version"] == "1.0"


def test_version_endpoint_uses_contract_response_and_echoes_correlation_id():
    client = TestClient(app)
    response = client.get("/version", headers={"X-Correlation-ID": "version-correlation"})

    assert response.status_code == 200
    payload = response.json()
    assert_contract_response(payload)
    assert payload["correlation_id"] == "version-correlation"
    assert payload["data"]["api_contract"] == "multi-agent-trading-api-contract"
    assert payload["data"]["schema_version"] == "1.0"


def test_ready_endpoint_uses_contract_response_and_echoes_correlation_id():
    client = TestClient(app)
    response = client.get("/ready", headers={"X-Correlation-ID": "ready-correlation"})

    assert response.status_code == 200
    payload = response.json()
    assert_contract_response(payload)
    assert payload["correlation_id"] == "ready-correlation"
    assert payload["data"]["ready"] is True
    assert payload["metadata"]["contract_source"] == "portfolio-agent-runtime-contract"


def test_existing_health_endpoint_still_works_and_echoes_correlation_id():
    client = TestClient(app)
    response = client.get("/health", headers={"X-Correlation-ID": "health-correlation"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["agent_type"] == "portfolio-agent"
    assert payload["version"] == "0.1.0"
    assert payload["correlation_id"] == "health-correlation"
    assert payload["data"]["status"] == "healthy"
