from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Dict

from fastapi import APIRouter, Header

PORTFOLIO_AGENT_TYPE = "portfolio-agent"
PORTFOLIO_AGENT_VERSION = "0.1.0"
SCHEMA_VERSION = "1.0"

router = APIRouter()

CorrelationIdHeader = Annotated[str | None, Header(alias="X-Correlation-ID")]


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def contract_response(
    *,
    status: str,
    correlation_id: str | None = None,
    data: Dict[str, Any] | None = None,
    metadata: Dict[str, Any] | None = None,
    error: Dict[str, Any] | None = None,
    confidence_score: float | None = None,
) -> Dict[str, Any]:
    return {
        "status": status,
        "agent_type": PORTFOLIO_AGENT_TYPE,
        "version": PORTFOLIO_AGENT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "timestamp": utc_timestamp(),
        "correlation_id": correlation_id,
        "data": data,
        "metadata": metadata or {},
        "error": error,
        "confidence_score": confidence_score,
    }


@router.get("/version")
def version(x_correlation_id: CorrelationIdHeader = None) -> Dict[str, Any]:
    return contract_response(
        status="success",
        correlation_id=x_correlation_id,
        data={
            "agent_type": PORTFOLIO_AGENT_TYPE,
            "version": PORTFOLIO_AGENT_VERSION,
            "schema_version": SCHEMA_VERSION,
            "api_contract": "multi-agent-trading-api-contract",
        },
        metadata={
            "required_operational_endpoints": ["/health", "/ready", "/version"],
        },
    )


@router.get("/ready")
def ready(x_correlation_id: CorrelationIdHeader = None) -> Dict[str, Any]:
    return contract_response(
        status="success",
        correlation_id=x_correlation_id,
        data={
            "ready": True,
            "exposure_endpoint": "/portfolio/exposure",
            "allocation_endpoint": "/portfolio/allocation",
            "rebalance_endpoint": "/portfolio/rebalance",
            "supported_modes": ["normal", "defensive", "cash_heavy"],
        },
        metadata={
            "contract_source": "portfolio-agent-runtime-contract",
        },
        confidence_score=1.0,
    )
