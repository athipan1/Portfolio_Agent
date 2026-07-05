from __future__ import annotations

from fastapi import FastAPI

from app.models import (
    HealthData,
    PortfolioData,
    PortfolioRequest,
    StandardAgentResponse,
)
from app.service import analyze_portfolio
from app.system_contract import router as system_contract_router


app = FastAPI(
    title="Portfolio Agent",
    description="Portfolio exposure and rebalance advisory service for the multi-agent trading system.",
    version="0.1.0",
)
app.include_router(system_contract_router)


@app.get("/health", response_model=StandardAgentResponse[HealthData])
def health() -> StandardAgentResponse[HealthData]:
    return StandardAgentResponse(status="success", data=HealthData())


@app.post("/portfolio/exposure", response_model=StandardAgentResponse[PortfolioData])
def portfolio_exposure(request: PortfolioRequest) -> StandardAgentResponse[PortfolioData]:
    data = analyze_portfolio(request)
    return StandardAgentResponse(status="success", data=data)


@app.post("/portfolio/allocation", response_model=StandardAgentResponse[PortfolioData])
def portfolio_allocation(request: PortfolioRequest) -> StandardAgentResponse[PortfolioData]:
    data = analyze_portfolio(request)
    return StandardAgentResponse(status="success", data=data)


@app.post("/portfolio/rebalance", response_model=StandardAgentResponse[PortfolioData])
def portfolio_rebalance(request: PortfolioRequest) -> StandardAgentResponse[PortfolioData]:
    data = analyze_portfolio(request)
    return StandardAgentResponse(status="success", data=data)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"message": "Portfolio Agent is running"}
