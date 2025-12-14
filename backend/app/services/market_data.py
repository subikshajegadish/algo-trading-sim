"""
Market data fetching service using yfinance.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketDataError(Exception):
    """Custom exception for market data errors."""
    pass


class InvalidTickerError(MarketDataError):
    """Raised when ticker symbol is invalid."""
    pass


class NoDataError(MarketDataError):
    """Raised when no data is available for the given parameters."""
    pass


def fetch_ohlcv_data(
    ticker: str,
    start_date: str | datetime,
    end_date: str | datetime,
    validate_data: bool = True
) -> pd.DataFrame:
    """
    Fetch daily OHLCV (Open, High, Low, Close, Volume) data for a given ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        start_date: Start date as string 'YYYY-MM-DD' or datetime object
        end_date: End date as string 'YYYY-MM-DD' or datetime object
        validate_data: If True, perform validation checks on the data
    
    Returns:
        pd.DataFrame: DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
                     Index is DatetimeIndex with timezone-naive dates
    
    Raises:
        InvalidTickerError: If ticker symbol is invalid or not found
        NoDataError: If no data is available for the given date range
        MarketDataError: For other data fetching errors
        ValueError: If date parameters are invalid
    
    Example:
        >>> df = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-12-31')
        >>> print(df.head())
                      Open    High     Low   Close      Volume
        Date                                                  
        2023-01-03  130.28  130.90  124.17  125.07  112117500
        2023-01-04  126.89  128.66  125.08  126.36   89113600
    """
    # Validate and normalize ticker
    if not ticker or not isinstance(ticker, str):
        raise ValueError("Ticker must be a non-empty string")
    
    ticker = ticker.strip().upper()
    
    # Convert dates to string format if datetime objects
    if isinstance(start_date, datetime):
        start_date = start_date.strftime('%Y-%m-%d')
    if isinstance(end_date, datetime):
        end_date = end_date.strftime('%Y-%m-%d')
    
    # Validate date format
    try:
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
    except Exception as e:
        raise ValueError(f"Invalid date format. Use 'YYYY-MM-DD'. Error: {str(e)}")
    
    # Validate date range
    if start_dt >= end_dt:
        raise ValueError("start_date must be before end_date")
    
    if end_dt > pd.Timestamp.now():
        raise ValueError("end_date cannot be in the future")
    
    logger.info(f"Fetching data for {ticker} from {start_date} to {end_date}")
    
    try:
        # Create ticker object
        ticker_obj = yf.Ticker(ticker)
        
        # Fetch historical data
        df = ticker_obj.history(
            start=start_date,
            end=end_date,
            interval='1d',
            auto_adjust=False,  # Keep raw OHLC data
            actions=False  # Don't include dividends/splits
        )
        
        # Check if ticker is valid by examining the response
        if df.empty:
            # Try to get ticker info to distinguish between invalid ticker and no data
            try:
                info = ticker_obj.info
                # If we can get info but no data, it's a date range issue
                if info and 'symbol' in info:
                    raise NoDataError(
                        f"No data available for {ticker} in the date range "
                        f"{start_date} to {end_date}. The ticker may be newly listed "
                        f"or delisted during this period."
                    )
            except Exception:
                pass
            
            # If we can't get info, it's likely an invalid ticker
            raise InvalidTickerError(
                f"Invalid ticker symbol: {ticker}. "
                f"Please verify the ticker exists and is correctly spelled."
            )
        
        # Remove timezone information from index for consistency
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # Select only OHLCV columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # Check if all required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise MarketDataError(
                f"Missing required columns: {missing_columns}. "
                f"Available columns: {df.columns.tolist()}"
            )
        
        df = df[required_columns].copy()
        
        # Perform data validation if requested
        if validate_data:
            df = _validate_and_clean_data(df, ticker)
        
        logger.info(
            f"Successfully fetched {len(df)} rows of data for {ticker} "
            f"from {df.index[0].date()} to {df.index[-1].date()}"
        )
        
        return df
        
    except (InvalidTickerError, NoDataError, ValueError):
        # Re-raise our custom exceptions and ValueError
        raise
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error fetching data for {ticker}: {str(e)}")
        raise MarketDataError(
            f"Failed to fetch data for {ticker}: {str(e)}"
        ) from e


def _validate_and_clean_data(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Validate and clean OHLCV data.
    
    Args:
        df: DataFrame with OHLCV data
        ticker: Ticker symbol (for logging)
    
    Returns:
        pd.DataFrame: Cleaned DataFrame
    
    Raises:
        NoDataError: If data is insufficient after cleaning
    """
    original_len = len(df)
    
    # Check for missing values
    missing_counts = df.isnull().sum()
    if missing_counts.any():
        logger.warning(
            f"Found missing values in {ticker} data: {missing_counts[missing_counts > 0].to_dict()}"
        )
        
        # Forward fill missing values (common for market data)
        df = df.fillna(method='ffill')
        
        # If still have NaN (e.g., first rows), backward fill
        df = df.fillna(method='bfill')
        
        # Drop any remaining rows with NaN
        df = df.dropna()
    
    # Validate OHLC relationships (High >= Low, High >= Open/Close, Low <= Open/Close)
    invalid_ohlc = (
        (df['High'] < df['Low']) |
        (df['High'] < df['Open']) |
        (df['High'] < df['Close']) |
        (df['Low'] > df['Open']) |
        (df['Low'] > df['Close'])
    )
    
    if invalid_ohlc.any():
        invalid_count = invalid_ohlc.sum()
        logger.warning(
            f"Found {invalid_count} rows with invalid OHLC relationships in {ticker} data. "
            f"Removing these rows."
        )
        df = df[~invalid_ohlc]
    
    # Check for negative or zero prices
    price_columns = ['Open', 'High', 'Low', 'Close']
    invalid_prices = (df[price_columns] <= 0).any(axis=1)
    
    if invalid_prices.any():
        invalid_count = invalid_prices.sum()
        logger.warning(
            f"Found {invalid_count} rows with non-positive prices in {ticker} data. "
            f"Removing these rows."
        )
        df = df[~invalid_prices]
    
    # Check for negative volume
    invalid_volume = df['Volume'] < 0
    if invalid_volume.any():
        invalid_count = invalid_volume.sum()
        logger.warning(
            f"Found {invalid_count} rows with negative volume in {ticker} data. "
            f"Setting to 0."
        )
        df.loc[invalid_volume, 'Volume'] = 0
    
    # Check if we have sufficient data after cleaning
    if len(df) == 0:
        raise NoDataError(
            f"No valid data remaining for {ticker} after cleaning. "
            f"Original data had {original_len} rows."
        )
    
    if len(df) < original_len * 0.5:
        logger.warning(
            f"Significant data loss for {ticker}: {original_len} -> {len(df)} rows "
            f"({(1 - len(df)/original_len)*100:.1f}% removed)"
        )
    
    # Ensure data is sorted by date
    df = df.sort_index()
    
    return df


def fetch_multiple_tickers(
    tickers: list[str],
    start_date: str | datetime,
    end_date: str | datetime,
    validate_data: bool = True,
    raise_on_error: bool = False
) -> dict[str, pd.DataFrame]:
    """
    Fetch OHLCV data for multiple tickers.
    
    Args:
        tickers: List of ticker symbols
        start_date: Start date as string 'YYYY-MM-DD' or datetime object
        end_date: End date as string 'YYYY-MM-DD' or datetime object
        validate_data: If True, perform validation checks on the data
        raise_on_error: If True, raise exception on first error. If False, skip failed tickers.
    
    Returns:
        dict: Dictionary mapping ticker symbols to DataFrames
              Only successful fetches are included
    
    Example:
        >>> data = fetch_multiple_tickers(['AAPL', 'MSFT'], '2023-01-01', '2023-12-31')
        >>> print(data.keys())
        dict_keys(['AAPL', 'MSFT'])
    """
    results = {}
    errors = {}
    
    for ticker in tickers:
        try:
            df = fetch_ohlcv_data(ticker, start_date, end_date, validate_data)
            results[ticker] = df
        except Exception as e:
            errors[ticker] = str(e)
            logger.error(f"Failed to fetch data for {ticker}: {str(e)}")
            
            if raise_on_error:
                raise
    
    if errors:
        logger.warning(
            f"Failed to fetch data for {len(errors)} ticker(s): {list(errors.keys())}"
        )
    
    logger.info(
        f"Successfully fetched data for {len(results)}/{len(tickers)} tickers"
    )
    
    return results


def validate_ticker(ticker: str) -> bool:
    """
    Validate if a ticker symbol exists and has data available.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        bool: True if ticker is valid, False otherwise
    
    Example:
        >>> validate_ticker('AAPL')
        True
        >>> validate_ticker('INVALID123')
        False
    """
    try:
        ticker = ticker.strip().upper()
        ticker_obj = yf.Ticker(ticker)
        
        # Try to get basic info
        info = ticker_obj.info
        
        # Check if we got meaningful data
        if info and 'symbol' in info:
            return True
        
        return False
    except Exception:
        return False
