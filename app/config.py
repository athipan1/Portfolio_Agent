from __future__ import annotations

import os


def _non_negative_float(name: str, default: str) -> float:
    value = float(os.getenv(name, default))
    if value < 0:
        raise RuntimeError(f"{name} must be non-negative")
    return value


PORTFOLIO_AGENT_API_KEY = os.getenv(
    "PORTFOLIO_AGENT_API_KEY",
    "dev_portfolio_key",
).strip()
if not PORTFOLIO_AGENT_API_KEY:
    raise RuntimeError("PORTFOLIO_AGENT_API_KEY must not be empty")

PORTFOLIO_EQUITY_ABS_TOLERANCE = _non_negative_float(
    "PORTFOLIO_EQUITY_ABS_TOLERANCE",
    "0.01",
)
PORTFOLIO_EQUITY_REL_TOLERANCE = _non_negative_float(
    "PORTFOLIO_EQUITY_REL_TOLERANCE",
    "0.000001",
)
