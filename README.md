# Koko Finance Python SDK

Python SDK for the [Koko Finance](https://kokofinance.net) credit card intelligence API.

Analyze credit card portfolios, compare cards side-by-side, get spending-based recommendations, and check whether a card is worth renewing — all with a few lines of Python.

## Installation

```bash
pip install koko-finance
```

## Quick Start

```python
from koko_finance import KokoClient

client = KokoClient(api_key="koko_your_api_key")

# Analyze your credit card portfolio
analysis = client.analyze_portfolio(
    cards=[
        {"card_name": "Chase Sapphire Preferred", "annual_fee": 95},
        {"card_name": "American Express Gold Card", "annual_fee": 250},
        {"card_name": "Citi Double Cash", "annual_fee": 0},
    ],
    spending={"dining": 500, "travel": 300, "groceries": 600, "gas": 150},
    primary_goal="travel",
)
print(analysis)
```

## API Reference

### `KokoClient(api_key, base_url, timeout)`

| Parameter  | Type | Default | Description |
|------------|------|---------|-------------|
| `api_key`  | str  | required | Your Koko API key (format: `koko_xxxxx`) |
| `base_url` | str  | `https://kokofinance.net` | API base URL |
| `timeout`  | int  | `30` | Request timeout in seconds |

### `analyze_portfolio(cards, spending, primary_goal, credit_tier, issuer_preferences, benefit_selections, verbose)`

Analyze 1-10 credit cards for total value, per-card verdicts (KEEP/OPTIMIZE/CANCEL), and break-even analysis.

```python
# Fast (default, <100ms) — deterministic calculations
analysis = client.analyze_portfolio(
    cards=[
        {"card_name": "Chase Sapphire Preferred", "annual_fee": 95},
        {"card_name": "American Express Gold Card", "annual_fee": 250},
    ],
    spending={"dining": 500, "travel": 300, "groceries": 400},
    primary_goal="travel",
)

# With benefit selections (only selected benefits count at 100%)
analysis = client.analyze_portfolio(
    cards=[
        {"card_name": "American Express Platinum Card", "annual_fee": 695},
    ],
    spending={"dining": 500, "travel": 300},
    benefit_selections=["uber", "airline_fee", "digital_entertainment", "saks"],
)

# Verbose (3-5s) — adds AI-generated narrative
analysis = client.analyze_portfolio(
    cards=[...],
    spending={"dining": 500, "travel": 300},
    verbose=True,
)
```

### `compare_cards(cards, spending, primary_goal, issuer_preferences, verbose)`

Compare 2-3 credit cards side-by-side with fees, rewards, net value, and break-even.

```python
# Fast (default, <100ms) — structured data, no AI winner
comparison = client.compare_cards(
    cards=[
        {"card_name": "Chase Sapphire Preferred", "annual_fee": 95},
        {"card_name": "Capital One Venture X", "annual_fee": 395},
    ],
    spending={"dining": 400, "travel": 500},
    primary_goal="travel",
)

# Verbose (3-5s) — adds AI-generated winner and pros/cons
comparison = client.compare_cards(cards=[...], verbose=True)
```

### `recommend_card(category, spending, primary_goal, credit_tier, portfolio_card_names, issuer_preferences, verbose)`

Get the best card recommendations for a spending category.

```python
# From the full market (always fast)
recs = client.recommend_card(
    category="dining",
    spending={"dining": 600},
    credit_tier="excellent",
)

# From your existing portfolio (fast, <100ms)
recs = client.recommend_card(
    category="dining",
    portfolio_card_names=["Chase Sapphire Preferred", "Citi Double Cash"],
)

# From portfolio with AI narrative (verbose, 2-4s)
recs = client.recommend_card(
    category="dining",
    portfolio_card_names=["Chase Sapphire Preferred", "Citi Double Cash"],
    verbose=True,
)
```

### `check_renewal(card, spending, primary_goal, issuer_preferences, benefit_selections)`

Check if a card is worth keeping at annual fee renewal time.

```python
renewal = client.check_renewal(
    card={"card_name": "Chase Sapphire Preferred", "annual_fee": 95},
    spending={"dining": 400, "travel": 300},
)
# renewal["verdict"] is "RENEW", "DOWNGRADE", or "CANCEL_AND_REPLACE"

# With benefit selections (only selected benefits count at 100%)
renewal = client.check_renewal(
    card={"card_name": "Amex Platinum"},
    spending={"dining": 400, "travel": 300, "groceries": 500},
    benefit_selections=["uber", "airline_fee", "digital_entertainment"],
)
```

### `get_benefit_categories()`

Get all valid benefit keys grouped by category (no authentication required). Use the returned keys with `benefit_selections` in `analyze_portfolio()` and `check_renewal()`.

```python
categories = client.get_benefit_categories()
print(categories["all_keys"])  # ['admirals_club', 'airline_fee', 'dining', ...]

# Use in portfolio analysis
analysis = client.analyze_portfolio(
    cards=[...],
    benefit_selections=["uber", "dining", "admirals_club"],
)
```

### `health()`

Check API health status (no authentication required).

```python
status = client.health()
```

## Error Handling

The SDK raises typed exceptions for API errors:

```python
from koko_finance import KokoClient, RateLimitError, AuthenticationError

client = KokoClient(api_key="koko_your_api_key")

try:
    result = client.analyze_portfolio(cards=[...])
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds.")
```

| Exception | HTTP Status | When |
|-----------|-------------|------|
| `AuthenticationError` | 401 | Invalid or missing API key |
| `RateLimitError` | 429 | Rate limit exceeded (60 req/min) |
| `ValidationError` | 400, 422 | Invalid request parameters |
| `ServerError` | 500 | API server error |
| `KokoError` | other | Base exception for all API errors |

## Spending Categories

The `spending` parameter accepts monthly dollar amounts for these categories:

| Category | Key | Example |
|----------|-----|---------|
| Groceries | `groceries` | `600` |
| Dining | `dining` | `400` |
| Travel | `travel` | `200` |
| Gas | `gas` | `150` |
| Streaming | `streaming` | `45` |
| Shopping | `shopping` | `300` |
| Other | `other` | `200` |

## Links

- [Developer Docs](https://kokofinance.net/developers)
- [Interactive API Docs (Swagger)](https://kokofinance.net/api/v1/docs)
- [GitHub](https://github.com/KokoFinance/koko-finance-python)

## License

MIT
