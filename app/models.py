from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class PortfolioMode(str, Enum):
    NORMAL = "normal"
    DEFENSIVE = "defensive"
    CASH_HEAVY = "cash_heavy"


class RebalanceAction(str, Enum):
    HOLD = "hold"
    INCREASE = "increase"
    REDUCE = "reduce"
    REVIEW = "review"


class PositionInput(BaseModel):
    symbol: str
    market_value: float = Field(ge=0)
    quantity: Optional[float] = Field(default=None, ge=0)
    strategy_bucket: Optional[str] = Field(default=None, description="core_dividend, value_rebound, news_momentum, or unassigned")
    sector: Optional[str] = None
    unrealized_pl_pct: Optional[float] = None


class PortfolioRequest(BaseModel):
    equity: float = Field(gt=0)
    cash: float = Field(ge=0)
    positions: List[PositionInput] = Field(default_factory=list)
    mode: PortfolioMode = PortfolioMode.NORMAL
    target_bucket_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "core_dividend": 0.50,
            "value_rebound": 0.30,
            "news_momentum": 0.20,
        }
    )
    max_symbol_weight: float = Field(default=0.10, gt=0, le=1)
    rebalance_tolerance: float = Field(default=0.03, ge=0, le=1)


class BucketExposure(BaseModel):
    bucket: str
    market_value: float
    current_weight: float
    target_weight: float
    drift: float
    action: RebalanceAction


class PositionExposure(BaseModel):
    symbol: str
    strategy_bucket: str
    market_value: float
    current_weight: float
    action: RebalanceAction
    reason: str


class PortfolioData(BaseModel):
    equity: float
    cash: float
    cash_weight: float
    invested_weight: float
    mode: PortfolioMode
    rebalance_required: bool
    bucket_exposure: List[BucketExposure]
    position_exposure: List[PositionExposure]
    warnings: List[str]
    recommended_cash_weight: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthData(BaseModel):
    status: str = "healthy"
    service: str = "portfolio-agent"


class StandardAgentResponse(BaseModel, Generic[T]):
    status: str
    agent_type: str = "portfolio-agent"
    version: str = "0.1.0"
    schema_version: str = "1.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None
    data: Optional[T] = None
    error: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: Optional[float] = None
