import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import PortfolioMode, PortfolioRequest, PositionInput, RebalanceAction
from app.service import PortfolioSnapshotValidationError, analyze_portfolio


client = TestClient(app)
AUTH_HEADERS = {
    "X-API-KEY": "dev_portfolio_key",
    "X-Correlation-ID": "portfolio-test-correlation",
}


def test_root_status_endpoint_remains_public():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Portfolio Agent is running"}


def test_health_endpoint_is_public():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["status"] == "healthy"


def test_portfolio_endpoint_requires_api_key():
    response = client.post(
        "/portfolio/exposure",
        headers={"X-Correlation-ID": "missing-key-correlation"},
        json={"equity": 100_000, "cash": 100_000, "positions": []},
    )

    assert response.status_code == 401
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["correlation_id"] == "missing-key-correlation"
    assert payload["error"]["code"] == "HTTP_401"


def test_unassigned_bucket_requires_review():
    result = analyze_portfolio(
        PortfolioRequest(
            equity=38_000,
            cash=20_000,
            positions=[
                PositionInput(symbol="ACGL", market_value=10_000, strategy_bucket="unassigned"),
                PositionInput(symbol="ADBE", market_value=8_000, strategy_bucket="core_dividend"),
            ],
        )
    )
    assert result.rebalance_required is True
    assert any("ACGL" in warning for warning in result.warnings)
    assert any(item.bucket == "unassigned" and item.action == RebalanceAction.REVIEW for item in result.bucket_exposure)


def test_oversized_position_requires_reduce():
    result = analyze_portfolio(
        PortfolioRequest(
            equity=30_000,
            cash=10_000,
            positions=[PositionInput(symbol="AAPL", market_value=20_000, strategy_bucket="core_dividend")],
            max_symbol_weight=0.10,
        )
    )
    apple = next(item for item in result.position_exposure if item.symbol == "AAPL")
    assert apple.action == RebalanceAction.REDUCE
    assert result.rebalance_required is True


def test_cash_heavy_mode_warns_when_cash_is_low():
    result = analyze_portfolio(
        PortfolioRequest(
            equity=100_000,
            cash=5_000,
            mode=PortfolioMode.CASH_HEAVY,
            positions=[PositionInput(symbol="MSFT", market_value=95_000, strategy_bucket="core_dividend")],
        )
    )
    assert result.recommended_cash_weight == 0.30
    assert result.rebalance_required is True
    assert any("Cash weight" in warning for warning in result.warnings)


def test_inconsistent_snapshot_is_rejected_before_weight_calculation():
    with pytest.raises(PortfolioSnapshotValidationError, match="does not reconcile"):
        analyze_portfolio(
            PortfolioRequest(
                equity=100_000,
                cash=20_000,
                positions=[PositionInput(symbol="AAPL", market_value=10_000, strategy_bucket="core_dividend")],
            )
        )


def test_portfolio_exposure_endpoint_rejects_inconsistent_snapshot():
    response = client.post(
        "/portfolio/exposure",
        headers=AUTH_HEADERS,
        json={
            "equity": 100_000,
            "cash": 20_000,
            "positions": [
                {"symbol": "AAPL", "market_value": 10_000, "strategy_bucket": "core_dividend"},
            ],
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["correlation_id"] == "portfolio-test-correlation"
    assert payload["error"]["code"] == "HTTP_422"
    assert "does not reconcile" in payload["error"]["message"]


def test_portfolio_exposure_endpoint():
    response = client.post(
        "/portfolio/exposure",
        headers=AUTH_HEADERS,
        json={
            "equity": 100_000,
            "cash": 20_000,
            "mode": "normal",
            "positions": [
                {"symbol": "ACGL", "market_value": 10_000, "strategy_bucket": "value_rebound"},
                {"symbol": "ADBE", "market_value": 8_000, "strategy_bucket": "core_dividend"},
                {"symbol": "SPY", "market_value": 62_000, "strategy_bucket": "core_dividend"},
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["correlation_id"] == "portfolio-test-correlation"
    assert payload["data"]["equity"] == 100_000
    assert payload["data"]["cash_weight"] == 0.2
    assert payload["data"]["invested_weight"] == 0.8
    assert payload["data"]["metadata"]["snapshot_value"] == 100_000
