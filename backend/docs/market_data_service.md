# Market Data Service Documentation

## Overview

The market data service provides robust functionality for fetching historical OHLCV (Open, High, Low, Close, Volume) data from Yahoo Finance using the `yfinance` library. It includes comprehensive error handling, data validation, and is designed to be production-ready for the algorithmic trading simulator.

## Features

✅ **Fetch daily OHLCV data** for any valid ticker symbol  
✅ **Date range validation** (prevents future dates, inverted ranges)  
✅ **Ticker validation** (distinguishes invalid tickers from missing data)  
✅ **Data quality checks** (OHLC relationships, positive prices, valid volume)  
✅ **Multi-ticker support** with batch fetching  
✅ **Automatic data cleaning** (forward-fill missing values, remove invalid rows)  
✅ **Comprehensive error handling** with custom exceptions  
✅ **Pandas DataFrame output** ready for technical indicators  
✅ **Full test coverage** (19 unit tests, all passing)  

---

## Installation

The required dependencies are already in `requirements.txt`:

```bash
pip install yfinance pandas numpy
```

---

## Quick Start

### Basic Usage

```python
from app.services.market_data import fetch_ohlcv_data

# Fetch data for a single ticker
df = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-12-31')

print(df.head())
#                 Open    High     Low   Close      Volume
# Date                                                  
# 2023-01-03  130.28  130.90  124.17  125.07  112117500
# 2023-01-04  126.89  128.66  125.08  126.36   89113600
```

### Using Datetime Objects

```python
from datetime import datetime

start = datetime(2023, 1, 1)
end = datetime(2023, 12, 31)

df = fetch_ohlcv_data('MSFT', start, end)
```

### Fetching Multiple Tickers

```python
from app.services.market_data import fetch_multiple_tickers

tickers = ['AAPL', 'MSFT', 'GOOGL']
data = fetch_multiple_tickers(tickers, '2023-01-01', '2023-12-31')

for ticker, df in data.items():
    print(f"{ticker}: {len(df)} rows")
```

### Validating Tickers

```python
from app.services.market_data import validate_ticker

if validate_ticker('AAPL'):
    print("Valid ticker!")
else:
    print("Invalid ticker!")
```

---

## API Reference

### `fetch_ohlcv_data()`

Fetch daily OHLCV data for a single ticker.

**Signature:**
```python
def fetch_ohlcv_data(
    ticker: str,
    start_date: str | datetime,
    end_date: str | datetime,
    validate_data: bool = True
) -> pd.DataFrame
```

**Parameters:**
- `ticker` (str): Stock ticker symbol (e.g., 'AAPL', 'MSFT')
- `start_date` (str | datetime): Start date as 'YYYY-MM-DD' or datetime object
- `end_date` (str | datetime): End date as 'YYYY-MM-DD' or datetime object
- `validate_data` (bool): If True, perform validation checks (default: True)

**Returns:**
- `pd.DataFrame`: DataFrame with columns `['Open', 'High', 'Low', 'Close', 'Volume']`
  - Index: DatetimeIndex (timezone-naive)
  - All prices are float64
  - Volume is int64

**Raises:**
- `InvalidTickerError`: Ticker symbol is invalid or not found
- `NoDataError`: No data available for the given date range
- `ValueError`: Invalid date parameters
- `MarketDataError`: Other data fetching errors

**Example:**
```python
df = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-12-31')
```

---

### `fetch_multiple_tickers()`

Fetch OHLCV data for multiple tickers in batch.

**Signature:**
```python
def fetch_multiple_tickers(
    tickers: list[str],
    start_date: str | datetime,
    end_date: str | datetime,
    validate_data: bool = True,
    raise_on_error: bool = False
) -> dict[str, pd.DataFrame]
```

**Parameters:**
- `tickers` (list[str]): List of ticker symbols
- `start_date` (str | datetime): Start date
- `end_date` (str | datetime): End date
- `validate_data` (bool): Perform validation checks (default: True)
- `raise_on_error` (bool): If True, raise on first error. If False, skip failed tickers (default: False)

**Returns:**
- `dict[str, pd.DataFrame]`: Dictionary mapping ticker symbols to DataFrames
  - Only successful fetches are included

**Example:**
```python
data = fetch_multiple_tickers(['AAPL', 'MSFT'], '2023-01-01', '2023-12-31')
```

---

### `validate_ticker()`

Check if a ticker symbol is valid.

**Signature:**
```python
def validate_ticker(ticker: str) -> bool
```

**Parameters:**
- `ticker` (str): Stock ticker symbol

**Returns:**
- `bool`: True if valid, False otherwise

**Example:**
```python
is_valid = validate_ticker('AAPL')  # Returns True
```

---

## Error Handling

### Custom Exceptions

The service defines three custom exceptions:

```python
class MarketDataError(Exception):
    """Base exception for market data errors."""
    pass

class InvalidTickerError(MarketDataError):
    """Raised when ticker symbol is invalid."""
    pass

class NoDataError(MarketDataError):
    """Raised when no data is available."""
    pass
```

### Error Handling Examples

```python
from app.services.market_data import (
    fetch_ohlcv_data,
    InvalidTickerError,
    NoDataError
)

try:
    df = fetch_ohlcv_data('INVALID_XYZ', '2023-01-01', '2023-12-31')
except InvalidTickerError as e:
    print(f"Invalid ticker: {e}")
except NoDataError as e:
    print(f"No data available: {e}")
except ValueError as e:
    print(f"Invalid parameters: {e}")
```

---

## Data Validation

When `validate_data=True` (default), the service performs the following checks:

### 1. Missing Values
- Forward-fill missing values
- Backward-fill if needed
- Drop rows with remaining NaN values

### 2. OHLC Relationship Validation
- High >= Low
- High >= Open
- High >= Close
- Low <= Open
- Low <= Close

### 3. Price Validation
- All prices must be positive (> 0)
- Removes rows with zero or negative prices

### 4. Volume Validation
- Volume must be non-negative (>= 0)
- Sets negative volumes to 0

### 5. Data Sufficiency
- Raises `NoDataError` if no valid data remains after cleaning
- Warns if >50% of data is removed during validation

---

## DataFrame Output Format

The returned DataFrame has the following structure:

```python
                 Open    High     Low   Close      Volume
Date                                                  
2023-01-03  130.28  130.90  124.17  125.07  112117500
2023-01-04  126.89  128.66  125.08  126.36   89113600
2023-01-05  127.13  127.77  124.76  125.02   80962700
```

**Properties:**
- Index: `DatetimeIndex` (timezone-naive, sorted ascending)
- Columns: `['Open', 'High', 'Low', 'Close', 'Volume']`
- Data types: float64 for prices, int64 for volume
- No missing values (NaN)
- All OHLC relationships validated

---

## Using Data for Technical Indicators

The DataFrame is ready for calculating technical indicators:

```python
import pandas as pd
from app.services.market_data import fetch_ohlcv_data

# Fetch data
df = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-12-31')

# Simple Moving Averages
df['SMA_20'] = df['Close'].rolling(window=20).mean()
df['SMA_50'] = df['Close'].rolling(window=50).mean()

# Exponential Moving Average
df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()

# Daily Returns
df['Returns'] = df['Close'].pct_change()

# Volatility (20-day rolling standard deviation)
df['Volatility'] = df['Returns'].rolling(window=20).std()

# RSI (Relative Strength Index)
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

df['RSI'] = calculate_rsi(df['Close'])

print(df[['Close', 'SMA_20', 'SMA_50', 'RSI']].tail())
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/test_market_data.py -v

# Run specific test class
pytest tests/test_market_data.py::TestFetchOHLCVData -v

# Run with coverage
pytest tests/test_market_data.py --cov=app.services.market_data
```

### Test Coverage

The test suite includes 19 tests covering:

✅ Valid ticker fetching  
✅ Invalid ticker handling  
✅ Date validation (future dates, inverted ranges, invalid formats)  
✅ Data validation (OHLC relationships, positive prices)  
✅ Multi-ticker fetching  
✅ Ticker validation  
✅ Case-insensitivity  
✅ Datetime object support  
✅ Real data quality checks  

**Test Results:**
```
19 passed in 3.77s
```

---

## Performance Considerations

### Caching
- yfinance automatically caches data locally
- Subsequent requests for the same ticker/date range are faster

### Rate Limiting
- Yahoo Finance has rate limits
- For production, consider implementing request throttling
- Use `fetch_multiple_tickers()` for batch requests

### Data Size
- Daily data for 1 year ≈ 252 rows (trading days)
- Daily data for 5 years ≈ 1,260 rows
- Memory usage is minimal for typical backtests

---

## Best Practices

### 1. Always Use Try-Except Blocks

```python
try:
    df = fetch_ohlcv_data(ticker, start, end)
except InvalidTickerError:
    # Handle invalid ticker
    pass
except NoDataError:
    # Handle missing data
    pass
```

### 2. Validate Tickers Before Batch Fetching

```python
valid_tickers = [t for t in tickers if validate_ticker(t)]
data = fetch_multiple_tickers(valid_tickers, start, end)
```

### 3. Use Appropriate Date Ranges

```python
# Ensure at least 30 days of data for meaningful analysis
min_days = 30
date_diff = (end_date - start_date).days
if date_diff < min_days:
    raise ValueError(f"Date range must be at least {min_days} days")
```

### 4. Handle Market Holidays

```python
# The service automatically skips non-trading days
# No special handling needed
df = fetch_ohlcv_data('AAPL', '2023-12-23', '2023-12-26')
# Returns only trading days (Dec 26 is a trading day, Dec 25 is skipped)
```

---

## Logging

The service uses Python's built-in logging:

```python
import logging

# Configure logging level
logging.basicConfig(level=logging.INFO)

# Logs include:
# - INFO: Successful data fetches with row counts
# - WARNING: Data quality issues, missing values
# - ERROR: Failed fetches, unexpected errors
```

**Example log output:**
```
INFO:app.services.market_data:Fetching data for AAPL from 2023-01-01 to 2023-12-31
INFO:app.services.market_data:Successfully fetched 250 rows of data for AAPL from 2023-01-03 to 2023-12-29
```

---

## Integration with Backtest Engine

The market data service is designed to integrate seamlessly with the backtest engine:

```python
from app.services.market_data import fetch_ohlcv_data

def run_backtest(ticker, start_date, end_date, strategy):
    # Fetch historical data
    df = fetch_ohlcv_data(ticker, start_date, end_date)
    
    # Add technical indicators
    df = strategy.add_indicators(df)
    
    # Run backtest
    results = strategy.execute(df)
    
    return results
```

---

## Troubleshooting

### Issue: "Invalid ticker symbol"
**Cause:** Ticker doesn't exist or is misspelled  
**Solution:** Verify ticker on Yahoo Finance, use `validate_ticker()` first

### Issue: "No data available for date range"
**Cause:** Stock wasn't trading during that period (IPO, delisting)  
**Solution:** Check stock's trading history, adjust date range

### Issue: "end_date cannot be in the future"
**Cause:** End date is set to a future date  
**Solution:** Use current date or earlier

### Issue: Rate limiting errors
**Cause:** Too many requests to Yahoo Finance  
**Solution:** Add delays between requests, use caching

---

## Future Enhancements

Potential improvements for future versions:

- [ ] Support for intraday data (minute, hourly)
- [ ] Cryptocurrency and forex support
- [ ] Custom data source integration
- [ ] Advanced caching with Redis
- [ ] Parallel fetching for multiple tickers
- [ ] Adjusted prices option (split/dividend adjusted)
- [ ] Volume-weighted average price (VWAP)

---

## License

MIT License - See project root for details

---

## Support

For issues or questions:
1. Check the examples in `examples/fetch_data_example.py`
2. Review the test suite in `tests/test_market_data.py`
3. Check logs for detailed error messages
4. Consult yfinance documentation: https://github.com/ranaroussi/yfinance

---

**Last Updated:** 2025-12-14  
**Version:** 1.0.0
