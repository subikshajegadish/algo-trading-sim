"""
Example usage of the market data service.
"""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.market_data import (
    fetch_ohlcv_data,
    fetch_multiple_tickers,
    validate_ticker,
    InvalidTickerError,
    NoDataError
)


def example_single_ticker():
    """Example: Fetch data for a single ticker."""
    print("=" * 60)
    print("Example 1: Fetch data for a single ticker (AAPL)")
    print("=" * 60)
    
    try:
        df = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-12-31')
        
        print(f"\nSuccessfully fetched {len(df)} rows of data")
        print(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")
        print(f"\nFirst 5 rows:")
        print(df.head())
        print(f"\nData statistics:")
        print(df.describe())
        
    except (InvalidTickerError, NoDataError) as e:
        print(f"Error: {e}")


def example_invalid_ticker():
    """Example: Handle invalid ticker gracefully."""
    print("\n" + "=" * 60)
    print("Example 2: Handle invalid ticker")
    print("=" * 60)
    
    try:
        df = fetch_ohlcv_data('INVALID_XYZ123', '2023-01-01', '2023-12-31')
    except InvalidTickerError as e:
        print(f"\nCaught InvalidTickerError: {e}")


def example_no_data():
    """Example: Handle date range with no data."""
    print("\n" + "=" * 60)
    print("Example 3: Handle date range with no data")
    print("=" * 60)
    
    try:
        # Try to fetch very old data for a modern stock
        df = fetch_ohlcv_data('AAPL', '1970-01-01', '1970-01-31')
    except (NoDataError, InvalidTickerError) as e:
        print(f"\nCaught error: {e}")


def example_multiple_tickers():
    """Example: Fetch data for multiple tickers."""
    print("\n" + "=" * 60)
    print("Example 4: Fetch data for multiple tickers")
    print("=" * 60)
    
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'INVALID_XYZ']
    
    data = fetch_multiple_tickers(
        tickers,
        '2023-01-01',
        '2023-01-31',
        raise_on_error=False
    )
    
    print(f"\nSuccessfully fetched data for {len(data)}/{len(tickers)} tickers")
    
    for ticker, df in data.items():
        print(f"\n{ticker}: {len(df)} rows, "
              f"Close range: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")


def example_validate_tickers():
    """Example: Validate ticker symbols before fetching."""
    print("\n" + "=" * 60)
    print("Example 5: Validate ticker symbols")
    print("=" * 60)
    
    tickers_to_check = ['AAPL', 'MSFT', 'INVALID123', 'GOOGL']
    
    print("\nValidating tickers...")
    for ticker in tickers_to_check:
        is_valid = validate_ticker(ticker)
        status = "✓ Valid" if is_valid else "✗ Invalid"
        print(f"{ticker:15} {status}")


def example_data_for_indicators():
    """Example: Prepare data for technical indicators."""
    print("\n" + "=" * 60)
    print("Example 6: Data ready for technical indicators")
    print("=" * 60)
    
    df = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-12-31')
    
    # Calculate a simple moving average (example indicator)
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    print(f"\nData with indicators (last 5 rows):")
    print(df[['Close', 'SMA_20', 'SMA_50']].tail())
    
    # Calculate daily returns
    df['Returns'] = df['Close'].pct_change()
    
    print(f"\nDaily returns statistics:")
    print(df['Returns'].describe())


if __name__ == '__main__':
    # Run all examples
    example_single_ticker()
    example_invalid_ticker()
    example_no_data()
    example_multiple_tickers()
    example_validate_tickers()
    example_data_for_indicators()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
