from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config import PORTFOLIO_AGENT_API_KEY
from app.models import (
    HealthData,
    PortfolioData,
    PortfolioRequest,
    StandardAgentResponse,
)
from app.service import PortfolioSnapshotValidationError, analyze_portfolio
from app.system_contract import router as system_contract_router


app = FastAPI(
    title="Portfolio Agent",
    description="Portfolio exposure and rebalance advisory service for the multi-agent trading system.",
    version="0.1.0",
)
app.include_router(system_contract_router)

PUBLIC_PATHS = {
    "/health",
    "/ready",
    "/version",
    "/docs",
    "/redoc",
    "/openapi.json",
}

CorrelationIdHeader = Annotated[str | None, Header(alias="X-Correlation-ID")]


def _error_response(*, status_code: int, message: str, correlation_id: str | None) -> JSONResponse:
    payload = StandardAgentResponse[None](
        status="error",
        correlation_id=correlation_id,
        error={"code": f"HTTP_{status_code}", "message": message},
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    api_key = request.headers.get("X-API-KEY")
    if not api_key or not hmac.compare_digest(api_key, PORTFOLIO_AGENT_API_KEY):
        return _error_response(
            status_code=401,
            message="Invalid or missing API key",
            correlation_id=request.headers.get("X-Correlation-ID"),
        )

    return await call_next(request)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return _error_response(
        status_code=exc.status_code,
        message=str(exc.detail),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )


def _analyze(request: PortfolioRequest) -> PortfolioData:
    try:
        return analyze_portfolio(request)
    except PortfolioSnapshotValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/health", response_model=StandardAgentResponse[HealthData])
def health(x_correlation_id: CorrelationIdHeader = None) -> StandardAgentResponse[HealthData]:
    return StandardAgentResponse(status="success", correlation_id=x_correlation_id, data=HealthData())


@app.post("/portfolio/exposure", response_model=StandardAgentResponse[PortfolioData])
def portfolio_exposure(
    request: PortfolioRequest,
    x_correlation_id: CorrelationIdHeader = None,
) -> StandardAgentResponse[PortfolioData]:
    data = _analyze(request)
    return StandardAgentResponse(status="success", correlation_id=x_correlation_id, data=data)


@app.post("/portfolio/allocation", response_model=StandardAgentResponse[PortfolioData])
def portfolio_allocation(
    request: PortfolioRequest,
    x_correlation_id: CorrelationIdHeader = None,
) -> StandardAgentResponse[PortfolioData]:
    data = _analyze(request)
    return StandardAgentResponse(status="success", correlation_id=x_correlation_id, data=data)


@app.post("/portfolio/rebalance", response_model=StandardAgentResponse[PortfolioData])
def portfolio_rebalance(
    request: PortfolioRequest,
    x_correlation_id: CorrelationIdHeader = None,
) -> StandardAgentResponse[PortfolioData]:
    data = _analyze(request)
    return StandardAgentResponse(status="success", correlation_id=x_correlation_id, data=data)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"message": "Portfolio Agent is running"}
