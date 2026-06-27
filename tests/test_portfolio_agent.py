from fastapi.testclient import TestClient

from app.main import app
from app.models import PortfolioMode, PortfolioRequest, PositionInput, RebalanceAction
from app.service import analyze_portfolio


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["status"] == "healthy"


def test_unassigned_bucket_requires_review():
    result = analyze_portfolio(
        PortfolioRequest(
            equity=100_000,
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
            equity=100_000,
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
            positions=[PositionInput(symbol="MSFT", market_value=5_000, strategy_bucket="core_dividend")],
        )
    )
    assert result.recommended_cash_weight == 0.30
    assert result.rebalance_required is True
    assert any("Cash weight" in warning for warning in result.warnings)


def test_portfolio_exposure_endpoint():
    response = client.post(
        "/portfolio/exposure",
        json={
            "equity": 100000,
            "cash": 20000,
            "mode": "normal",
            "positions": [
                {"symbol": "ACGL", "market_value": 10000, "strategy_bucket": "value_rebound"},
                {"symbol": "ADBE", "market_value": 8000, "strategy_bucket": "core_dividend"},
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["equity"] == 100000
    assert payload["data"]["cash_weight"] == 0.2
