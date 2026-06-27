# Portfolio Agent

Portfolio Agent analyzes portfolio exposure and returns rebalance advice for the multi-agent trading system.

It does **not** place orders. It returns advisory portfolio metadata for `Manager_Agent`, `Risk_Agent`, and `Execution_Agent`.

## Responsibilities

- Calculate cash and invested weights
- Calculate strategy bucket exposure
- Detect `unassigned` strategy buckets
- Detect oversized positions
- Recommend rebalance actions
- Adjust cash expectations based on operating mode: `normal`, `defensive`, or `cash_heavy`

## API

### Health

```bash
curl http://localhost:8012/health
```

### Portfolio Exposure

```bash
curl -X POST http://localhost:8012/portfolio/exposure \
  -H 'Content-Type: application/json' \
  -d '{
    "equity": 100000,
    "cash": 20000,
    "mode": "normal",
    "positions": [
      {"symbol": "ACGL", "market_value": 10000, "strategy_bucket": "value_rebound"},
      {"symbol": "ADBE", "market_value": 8000, "strategy_bucket": "core_dividend"}
    ]
  }'
```

Example response fields:

```json
{
  "rebalance_required": true,
  "cash_weight": 0.20,
  "invested_weight": 0.18,
  "recommended_cash_weight": 0.05,
  "bucket_exposure": [],
  "position_exposure": [],
  "warnings": []
}
```

## Endpoints

```text
GET  /health
POST /portfolio/exposure
POST /portfolio/allocation
POST /portfolio/rebalance
```

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8012
```

## Tests

```bash
ruff check app tests
pytest -q
```

## Docker

```bash
docker build -t portfolio-agent .
docker run --rm -p 8012:8012 portfolio-agent
```

## Integration rule

`Portfolio_Agent` is advisory only. It should never call `Execution_Agent` directly.

Recommended flow:

```text
Market_Regime_Agent
  -> Manager_Agent
  -> Portfolio_Agent
  -> Risk_Agent
  -> Execution_Agent
```
