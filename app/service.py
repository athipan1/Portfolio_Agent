from __future__ import annotations

from collections import defaultdict
from math import isclose
from typing import Dict, List

from app.config import (
    PORTFOLIO_EQUITY_ABS_TOLERANCE,
    PORTFOLIO_EQUITY_REL_TOLERANCE,
)
from app.models import (
    BucketExposure,
    PortfolioData,
    PortfolioMode,
    PortfolioRequest,
    PositionExposure,
    PositionInput,
    RebalanceAction,
)


DEFAULT_TARGETS = {
    "core_dividend": 0.50,
    "value_rebound": 0.30,
    "news_momentum": 0.20,
}

RECOMMENDED_CASH_BY_MODE = {
    PortfolioMode.NORMAL: 0.05,
    PortfolioMode.DEFENSIVE: 0.15,
    PortfolioMode.CASH_HEAVY: 0.30,
}


class PortfolioSnapshotValidationError(ValueError):
    """Raised when cash and position values do not reconcile to equity."""


def _normalize_bucket(position: PositionInput) -> str:
    bucket = (position.strategy_bucket or "unassigned").strip().lower()
    if not bucket:
        return "unassigned"
    return bucket


def _normalize_targets(targets: Dict[str, float]) -> Dict[str, float]:
    clean_targets = {key: max(0.0, value) for key, value in targets.items()}
    total = sum(clean_targets.values())
    if total <= 0:
        return DEFAULT_TARGETS.copy()
    return {key: round(value / total, 6) for key, value in clean_targets.items()}


def _bucket_action(drift: float, tolerance: float) -> RebalanceAction:
    if drift > tolerance:
        return RebalanceAction.REDUCE
    if drift < -tolerance:
        return RebalanceAction.INCREASE
    return RebalanceAction.HOLD


def _position_action(position_weight: float, max_symbol_weight: float, bucket: str) -> tuple[RebalanceAction, str]:
    if bucket == "unassigned":
        return RebalanceAction.REVIEW, "Position has no strategy_bucket assigned"
    if position_weight > max_symbol_weight:
        return RebalanceAction.REDUCE, "Position exceeds max symbol weight"
    return RebalanceAction.HOLD, "Position is within portfolio limits"


def _validate_equity_consistency(request: PortfolioRequest) -> tuple[float, float, float]:
    positions_market_value = sum(position.market_value for position in request.positions)
    snapshot_value = request.cash + positions_market_value
    difference = snapshot_value - request.equity
    tolerance = max(
        PORTFOLIO_EQUITY_ABS_TOLERANCE,
        abs(request.equity) * PORTFOLIO_EQUITY_REL_TOLERANCE,
    )

    if not isclose(
        snapshot_value,
        request.equity,
        rel_tol=PORTFOLIO_EQUITY_REL_TOLERANCE,
        abs_tol=PORTFOLIO_EQUITY_ABS_TOLERANCE,
    ):
        raise PortfolioSnapshotValidationError(
            "Portfolio snapshot does not reconcile: "
            f"cash ({request.cash:.2f}) + positions.market_value ({positions_market_value:.2f}) "
            f"= {snapshot_value:.2f}, equity = {request.equity:.2f}, "
            f"difference = {difference:.2f}, allowed tolerance = {tolerance:.2f}"
        )

    return snapshot_value, difference, tolerance


def analyze_portfolio(request: PortfolioRequest) -> PortfolioData:
    snapshot_value, equity_difference, equity_tolerance = _validate_equity_consistency(request)
    targets = _normalize_targets(request.target_bucket_weights)
    bucket_values: Dict[str, float] = defaultdict(float)
    warnings: List[str] = []

    for position in request.positions:
        bucket = _normalize_bucket(position)
        bucket_values[bucket] += position.market_value
        if bucket == "unassigned":
            warnings.append(f"{position.symbol.upper()} has unassigned strategy_bucket")

    bucket_exposures: List[BucketExposure] = []
    known_buckets = sorted(set(targets) | set(bucket_values))
    for bucket in known_buckets:
        market_value = bucket_values.get(bucket, 0.0)
        current_weight = market_value / request.equity
        target_weight = targets.get(bucket, 0.0)
        drift = current_weight - target_weight
        action = RebalanceAction.REVIEW if bucket == "unassigned" and market_value > 0 else _bucket_action(
            drift, request.rebalance_tolerance
        )
        bucket_exposures.append(
            BucketExposure(
                bucket=bucket,
                market_value=round(market_value, 2),
                current_weight=round(current_weight, 6),
                target_weight=round(target_weight, 6),
                drift=round(drift, 6),
                action=action,
            )
        )

    position_exposures: List[PositionExposure] = []
    for position in request.positions:
        bucket = _normalize_bucket(position)
        position_weight = position.market_value / request.equity
        action, reason = _position_action(position_weight, request.max_symbol_weight, bucket)
        position_exposures.append(
            PositionExposure(
                symbol=position.symbol.upper(),
                strategy_bucket=bucket,
                market_value=round(position.market_value, 2),
                current_weight=round(position_weight, 6),
                action=action,
                reason=reason,
            )
        )

    cash_weight = request.cash / request.equity
    invested_weight = sum(position.market_value for position in request.positions) / request.equity
    recommended_cash_weight = RECOMMENDED_CASH_BY_MODE[request.mode]

    if cash_weight < recommended_cash_weight:
        warnings.append(
            f"Cash weight {cash_weight:.2%} is below recommended {recommended_cash_weight:.2%} for {request.mode.value} mode"
        )

    rebalance_required = any(item.action != RebalanceAction.HOLD for item in bucket_exposures + position_exposures)
    rebalance_required = rebalance_required or cash_weight < recommended_cash_weight

    return PortfolioData(
        equity=round(request.equity, 2),
        cash=round(request.cash, 2),
        cash_weight=round(cash_weight, 6),
        invested_weight=round(invested_weight, 6),
        mode=request.mode,
        rebalance_required=rebalance_required,
        bucket_exposure=bucket_exposures,
        position_exposure=position_exposures,
        warnings=warnings,
        recommended_cash_weight=recommended_cash_weight,
        metadata={
            "max_symbol_weight": request.max_symbol_weight,
            "rebalance_tolerance": request.rebalance_tolerance,
            "target_bucket_weights": targets,
            "snapshot_value": round(snapshot_value, 2),
            "equity_difference": round(equity_difference, 6),
            "equity_reconciliation_tolerance": round(equity_tolerance, 6),
        },
    )
