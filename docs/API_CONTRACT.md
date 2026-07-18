# Portfolio_Agent API Contract

This document defines the baseline API contract for `Portfolio_Agent`.

`Portfolio_Agent` provides portfolio exposure, allocation, and rebalance advisory output for other agents.

## Standard Headers

```http
Content-Type: application/json
X-Correlation-ID: <uuid>
X-API-KEY: <portfolio-agent-api-key>
```

`X-API-KEY` is required for `/portfolio/exposure`, `/portfolio/allocation`, and `/portfolio/rebalance`. Operational endpoints and API documentation remain public for health orchestration.

## Standard Response Envelope

All runtime endpoints echo the received correlation ID in the response envelope:

```json
{
  "status": "success",
  "agent_type": "portfolio-agent",
  "version": "0.1.0",
  "schema_version": "1.0",
  "timestamp": "2026-07-04T00:00:00Z",
  "correlation_id": "b2c3d4e5-example",
  "data": {},
  "metadata": {},
  "error": null,
  "confidence_score": null
}
```

## Operational Endpoints

```http
GET /health
GET /ready
GET /version
```

## Portfolio Endpoints

```http
POST /portfolio/exposure
POST /portfolio/allocation
POST /portfolio/rebalance
```

Portfolio requests must reconcile:

```text
cash + sum(positions.market_value) == equity
```

A mismatch outside `PORTFOLIO_EQUITY_ABS_TOLERANCE` and `PORTFOLIO_EQUITY_REL_TOLERANCE` returns HTTP 422.

## Notes

1. This service provides portfolio context for other agents.
2. Runtime readiness is reported through `/ready`.
3. Version and schema metadata are reported through `/version`.
4. The service is advisory-only and never submits orders.
