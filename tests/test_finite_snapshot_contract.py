import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models import PortfolioRequest, PositionInput


@pytest.mark.parametrize("value", [float("inf"), float("nan")])
def test_nonfinite_snapshot_is_rejected_before_reconciliation(value):
    with pytest.raises(ValidationError):
        PortfolioRequest(equity=value, cash=value)
    with pytest.raises(ValidationError):
        PositionInput(symbol="TEST", market_value=value)


def test_nonfinite_target_weight_has_a_contract_error_over_http():
    response = TestClient(app).post("/portfolio/allocation", headers={
        "X-API-KEY": "dev_portfolio_key", "X-Correlation-ID": "nonfinite-portfolio-contract"},
        json={"equity": 100000, "cash": 100000,
              "target_bucket_weights": {"core_dividend": "Infinity"}})
    assert response.status_code == 422
    assert response.json()["correlation_id"] == "nonfinite-portfolio-contract"
