# Backtest API Endpoint Documentation

## Overview

The `/api/v1/backtest` endpoint allows you to run backtests for trading strategies on historical stock data and compare them against a buy-and-hold baseline.

---

## Endpoint

```
POST /api/v1/backtest
```

---

## Request Format

### Headers
```
Content-Type: application/json
```

### Request Body

```json
{
  "ticker": "AAPL",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_capital": 10000,
  "strategy_name": "sma_crossover",
  "strategy_params": {
    "short_window": 50,
    "long_window": 200
  }
}
```

### Parameters

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `ticker` | string | Yes | Stock ticker symbol | 1-10 characters, uppercase |
| `start_date` | string | Yes | Start date | Format: YYYY-MM-DD |
| `end_date` | string | Yes | End date | Format: YYYY-MM-DD |
| `initial_capital` | number | No | Initial capital in USD | Default: 10000, Min: 100, Max: 10,000,000 |
| `strategy_name` | string | Yes | Strategy to use | `sma_crossover` or `rsi_mean_reversion` |
| `strategy_params` | object | Yes | Strategy parameters | See below |

### Strategy Parameters

#### SMA Crossover (`sma_crossover`)
```json
{
  "short_window": 50,
  "long_window": 200
}
```

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| `short_window` | integer | Yes | Short-term MA period | 1-500 |
| `long_window` | integer | Yes | Long-term MA period | 2-1000, must be > short_window |

#### RSI Mean Reversion (`rsi_mean_reversion`)
```json
{
  "period": 14,
  "buy_threshold": 30,
  "sell_threshold": 70
}
```

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| `period` | integer | Yes | RSI calculation period | 2-100 |
| `buy_threshold` | number | Yes | RSI buy level (oversold) | 0-100, must be < sell_threshold |
| `sell_threshold` | number | Yes | RSI sell level (overbought) | 0-100, must be > buy_threshold |

---

## Response Format

### Success Response (200 OK)

```json
{
  "request": {
    "ticker": "AAPL",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 10000.0,
    "strategy_name": "sma_crossover",
    "strategy_params": {
      "short_window": 50,
      "long_window": 200
    }
  },
  "strategy_metrics": {
    "total_return": 0.0949,
    "total_return_pct": "9.49%",
    "cagr": 0.0964,
    "cagr_pct": "9.64%",
    "sharpe_ratio": 1.31,
    "max_drawdown": -0.0509,
    "max_drawdown_pct": "-5.09%",
    "initial_capital": 10000.0,
    "final_value": 10949.16,
    "num_trades": 2,
    "days_in_market": 51,
    "total_days": 250
  },
  "baseline_metrics": {
    "total_return": 0.5394,
    "total_return_pct": "53.94%",
    "cagr": 0.5491,
    "cagr_pct": "54.91%",
    "sharpe_ratio": 2.29,
    "max_drawdown": -0.1505,
    "max_drawdown_pct": "-15.05%",
    "initial_capital": 10000.0,
    "final_value": 15393.78,
    "num_trades": 1,
    "days_in_market": 250,
    "total_days": 250
  },
  "comparison": {
    "excess_return": -0.4445,
    "excess_return_pct": "-44.45%",
    "excess_cagr": -0.4527,
    "sharpe_difference": -0.98,
    "outperformed": false
  },
  "equity_curve": {
    "dates": ["2023-01-03", "2023-01-04", ...],
    "values": [10000.0, 10050.2, ...]
  },
  "baseline_curve": {
    "dates": ["2023-01-03", "2023-01-04", ...],
    "values": [10000.0, 10109.6, ...]
  },
  "success": true,
  "message": "Backtest completed successfully for AAPL"
}
```

### Error Responses

#### 400 Bad Request - Invalid Parameters
```json
{
  "detail": {
    "error": "InvalidParameters",
    "message": "short_window is required for SMA crossover strategy"
  }
}
```

#### 404 Not Found - Invalid Ticker
```json
{
  "detail": {
    "error": "InvalidTicker",
    "message": "Invalid ticker symbol: XYZ123. Please verify the ticker exists and is correctly spelled.",
    "ticker": "XYZ123"
  }
}
```

#### 404 Not Found - No Data Available
```json
{
  "detail": {
    "error": "NoDataAvailable",
    "message": "No data available for AAPL in the date range 1970-01-01 to 1970-12-31",
    "ticker": "AAPL",
    "date_range": "1970-01-01 to 1970-12-31"
  }
}
```

#### 400 Bad Request - Insufficient Data
```json
{
  "detail": {
    "error": "InsufficientData",
    "message": "Insufficient data: need at least 200 rows, but got 50 rows",
    "suggestion": "Try a shorter date range or smaller strategy parameters"
  }
}
```

---

## Examples

### Example 1: SMA Crossover Strategy

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 10000,
    "strategy_name": "sma_crossover",
    "strategy_params": {
      "short_window": 50,
      "long_window": 200
    }
  }'
```

**Response:** See success response above

---

### Example 2: RSI Mean Reversion Strategy

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "MSFT",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 50000,
    "strategy_name": "rsi_mean_reversion",
    "strategy_params": {
      "period": 14,
      "buy_threshold": 30,
      "sell_threshold": 70
    }
  }'
```

---

### Example 3: Using Python Requests

```python
import requests
import json

url = "http://localhost:8000/api/v1/backtest"

payload = {
    "ticker": "GOOGL",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 25000,
    "strategy_name": "sma_crossover",
    "strategy_params": {
        "short_window": 20,
        "long_window": 50
    }
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    data = response.json()
    print(f"Strategy Return: {data['strategy_metrics']['total_return_pct']}")
    print(f"Baseline Return: {data['baseline_metrics']['total_return_pct']}")
    print(f"Outperformed: {data['comparison']['outperformed']}")
else:
    print(f"Error: {response.json()}")
```

---

### Example 4: Using JavaScript/Fetch

```javascript
const url = 'http://localhost:8000/api/v1/backtest';

const payload = {
  ticker: 'AAPL',
  start_date: '2023-01-01',
  end_date: '2023-12-31',
  initial_capital: 10000,
  strategy_name: 'sma_crossover',
  strategy_params: {
    short_window: 50,
    long_window: 200
  }
};

fetch(url, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(payload)
})
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log('Strategy Return:', data.strategy_metrics.total_return_pct);
      console.log('Sharpe Ratio:', data.strategy_metrics.sharpe_ratio);
      
      // Plot equity curves
      const dates = data.equity_curve.dates;
      const strategyValues = data.equity_curve.values;
      const baselineValues = data.baseline_curve.values;
      
      // Use your charting library here
    } else {
      console.error('Backtest failed:', data.message);
    }
  })
  .catch(error => console.error('Error:', error));
```

---

## Response Fields Explained

### Metrics

| Field | Description | Example |
|-------|-------------|---------|
| `total_return` | Total return as decimal | 0.0949 = 9.49% |
| `cagr` | Compound Annual Growth Rate | 0.0964 = 9.64% annual |
| `sharpe_ratio` | Risk-adjusted return (higher is better) | 1.31 (good) |
| `max_drawdown` | Maximum peak-to-trough decline | -0.0509 = -5.09% |
| `final_value` | Ending portfolio value | $10,949.16 |
| `num_trades` | Number of position changes | 2 |
| `days_in_market` | Days with long position | 51 out of 250 |

### Comparison

| Field | Description |
|-------|-------------|
| `excess_return` | Strategy return - baseline return |
| `outperformed` | True if strategy beat buy-and-hold |

### Equity Curves

The `equity_curve` and `baseline_curve` contain parallel arrays of dates and portfolio values, perfect for charting:

```javascript
// Chart.js example
new Chart(ctx, {
  type: 'line',
  data: {
    labels: data.equity_curve.dates,
    datasets: [
      {
        label: 'Strategy',
        data: data.equity_curve.values,
        borderColor: 'blue'
      },
      {
        label: 'Buy & Hold',
        data: data.baseline_curve.values,
        borderColor: 'green'
      }
    ]
  }
});
```

---

## Error Handling

### Common Errors

1. **Invalid Ticker**: Ticker doesn't exist or is misspelled
   - Status: 404
   - Solution: Verify ticker symbol on Yahoo Finance

2. **No Data Available**: No historical data for date range
   - Status: 404
   - Solution: Adjust date range or try different ticker

3. **Insufficient Data**: Not enough data for strategy parameters
   - Status: 400
   - Solution: Use shorter MA windows or longer date range

4. **Invalid Parameters**: Missing or invalid strategy parameters
   - Status: 400
   - Solution: Check required parameters for your strategy

5. **Invalid Date Format**: Date not in YYYY-MM-DD format
   - Status: 422 (Validation Error)
   - Solution: Use correct date format

---

## Rate Limiting

Currently no rate limiting is implemented. For production use, consider:
- Implementing rate limiting (e.g., 10 requests/minute)
- Caching results for identical requests
- Using background tasks for long-running backtests

---

## Interactive Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation where you can:
- Try the API directly in your browser
- See all request/response schemas
- View example requests and responses

---

## Best Practices

1. **Start with short date ranges** for testing (e.g., 3-6 months)
2. **Use reasonable parameters** (e.g., SMA 50/200, RSI 30/70)
3. **Check the comparison** to see if strategy beats buy-and-hold
4. **Monitor Sharpe ratio** for risk-adjusted performance
5. **Consider max drawdown** for risk assessment

---

## Next Steps

- Add more strategies (MACD, Bollinger Bands)
- Implement multi-ticker portfolio backtests
- Add transaction costs (commissions, slippage)
- Support intraday data (hourly, minute)
- Add parameter optimization endpoints
