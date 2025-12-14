"""
Unit tests for market data service.
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from app.services.market_data import (
    fetch_ohlcv_data,
    fetch_multiple_tickers,
    validate_ticker,
    InvalidTickerError,
    NoDataError,
    MarketDataError
)


class TestFetchOHLCVData:
    """Tests for fetch_ohlcv_data function."""
    
    def test_fetch_valid_ticker(self):
        """Test fetching data for a valid ticker."""
        df = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-01-31')
        
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert list(df.columns) == ['Open', 'High', 'Low', 'Close', 'Volume']
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index.tz is None  # Should be timezone-naive
        
    def test_fetch_with_datetime_objects(self):
        """Test fetching data with datetime objects instead of strings."""
        start = datetime(2023, 1, 1)
        end = datetime(2023, 1, 31)
        
        df = fetch_ohlcv_data('MSFT', start, end)
        
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        
    def test_invalid_ticker(self):
        """Test that invalid ticker raises InvalidTickerError."""
        with pytest.raises(InvalidTickerError):
            fetch_ohlcv_data('INVALID_TICKER_XYZ123', '2023-01-01', '2023-01-31')
    
    def test_empty_ticker(self):
        """Test that empty ticker raises ValueError."""
        with pytest.raises(ValueError, match="Ticker must be a non-empty string"):
            fetch_ohlcv_data('', '2023-01-01', '2023-01-31')
    
    def test_future_date(self):
        """Test that future end date raises ValueError."""
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        
        with pytest.raises(ValueError, match="cannot be in the future"):
            fetch_ohlcv_data('AAPL', '2023-01-01', future_date)
    
    def test_inverted_date_range(self):
        """Test that start_date after end_date raises ValueError."""
        with pytest.raises(ValueError, match="start_date must be before end_date"):
            fetch_ohlcv_data('AAPL', '2023-12-31', '2023-01-01')
    
    def test_invalid_date_format(self):
        """Test that invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date format"):
            fetch_ohlcv_data('AAPL', 'invalid-date', '2023-01-31')
    
    def test_ticker_case_insensitive(self):
        """Test that ticker symbols are case-insensitive."""
        df1 = fetch_ohlcv_data('aapl', '2023-01-01', '2023-01-31')
        df2 = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-01-31')
        
        pd.testing.assert_frame_equal(df1, df2)
    
    def test_data_validation(self):
        """Test that data validation works correctly."""
        df = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-01-31', validate_data=True)
        
        # Check OHLC relationships
        assert (df['High'] >= df['Low']).all()
        assert (df['High'] >= df['Open']).all()
        assert (df['High'] >= df['Close']).all()
        assert (df['Low'] <= df['Open']).all()
        assert (df['Low'] <= df['Close']).all()
        
        # Check for positive prices
        assert (df['Open'] > 0).all()
        assert (df['High'] > 0).all()
        assert (df['Low'] > 0).all()
        assert (df['Close'] > 0).all()
        
        # Check for non-negative volume
        assert (df['Volume'] >= 0).all()
    
    def test_data_sorted_by_date(self):
        """Test that returned data is sorted by date."""
        df = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-03-31')
        
        assert df.index.is_monotonic_increasing
    
    def test_no_data_for_date_range(self):
        """Test handling of date range with no data (e.g., future IPO)."""
        # Use a very old date range where modern stocks didn't exist
        with pytest.raises((NoDataError, InvalidTickerError)):
            fetch_ohlcv_data('AAPL', '1970-01-01', '1970-01-31')


class TestFetchMultipleTickers:
    """Tests for fetch_multiple_tickers function."""
    
    def test_fetch_multiple_valid_tickers(self):
        """Test fetching data for multiple valid tickers."""
        tickers = ['AAPL', 'MSFT', 'GOOGL']
        data = fetch_multiple_tickers(tickers, '2023-01-01', '2023-01-31')
        
        assert isinstance(data, dict)
        assert len(data) == 3
        assert all(ticker in data for ticker in tickers)
        assert all(isinstance(df, pd.DataFrame) for df in data.values())
    
    def test_fetch_with_invalid_ticker_no_raise(self):
        """Test that invalid tickers are skipped when raise_on_error=False."""
        tickers = ['AAPL', 'INVALID_XYZ123', 'MSFT']
        data = fetch_multiple_tickers(
            tickers, '2023-01-01', '2023-01-31', raise_on_error=False
        )
        
        assert len(data) == 2
        assert 'AAPL' in data
        assert 'MSFT' in data
        assert 'INVALID_XYZ123' not in data
    
    def test_fetch_with_invalid_ticker_raise(self):
        """Test that invalid tickers raise exception when raise_on_error=True."""
        tickers = ['AAPL', 'INVALID_XYZ123', 'MSFT']
        
        with pytest.raises(InvalidTickerError):
            fetch_multiple_tickers(
                tickers, '2023-01-01', '2023-01-31', raise_on_error=True
            )


class TestValidateTicker:
    """Tests for validate_ticker function."""
    
    def test_validate_valid_ticker(self):
        """Test validation of valid ticker."""
        assert validate_ticker('AAPL') is True
        assert validate_ticker('MSFT') is True
    
    def test_validate_invalid_ticker(self):
        """Test validation of invalid ticker."""
        assert validate_ticker('INVALID_XYZ123') is False
    
    def test_validate_case_insensitive(self):
        """Test that validation is case-insensitive."""
        assert validate_ticker('aapl') is True
        assert validate_ticker('AAPL') is True
    
    def test_validate_with_whitespace(self):
        """Test that validation handles whitespace."""
        assert validate_ticker(' AAPL ') is True


# Integration test (optional, can be slow)
@pytest.mark.slow
class TestIntegration:
    """Integration tests that make real API calls."""
    
    def test_real_data_quality(self):
        """Test that real data from yfinance meets quality standards."""
        df = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-12-31')
        
        # Should have approximately 252 trading days (allowing for holidays)
        assert 240 <= len(df) <= 260
        
        # Should have no missing values
        assert not df.isnull().any().any()
        
        # All prices should be reasonable (not zero or negative)
        assert (df[['Open', 'High', 'Low', 'Close']] > 0).all().all()
