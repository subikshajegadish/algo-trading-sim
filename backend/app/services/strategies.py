"""
Trading strategy implementations.

This module provides vectorized implementations of common trading strategies
that generate position signals (1 = long, 0 = flat) based on technical indicators.
"""
import pandas as pd
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class StrategyError(Exception):
    """Base exception for strategy errors."""
    pass


class InsufficientDataError(StrategyError):
    """Raised when there is insufficient data for strategy calculation."""
    pass


def sma_crossover_strategy(
    data: pd.DataFrame,
    short_window: int = 50,
    long_window: int = 200,
    price_column: str = 'Close'
) -> pd.Series:
    """
    Simple Moving Average (SMA) Crossover Strategy.
    
    Generates buy signals when short-term SMA crosses above long-term SMA,
    and sell signals when short-term SMA crosses below long-term SMA.
    
    Strategy Logic:
    - Position = 1 (long) when SMA_short > SMA_long
    - Position = 0 (flat) when SMA_short <= SMA_long
    
    Args:
        data: DataFrame with OHLCV data (must have price_column)
        short_window: Period for short-term moving average (default: 50)
        long_window: Period for long-term moving average (default: 200)
        price_column: Column name to use for price (default: 'Close')
    
    Returns:
        pd.Series: Position signals (1 = long, 0 = flat) with same index as data
    
    Raises:
        ValueError: If parameters are invalid
        InsufficientDataError: If data is too short for the strategy
        KeyError: If price_column doesn't exist in data
    
    Example:
        >>> df = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-12-31')
        >>> positions = sma_crossover_strategy(df, short_window=50, long_window=200)
        >>> print(positions.value_counts())
        0    150
        1    100
    """
    # Validate inputs
    if short_window <= 0 or long_window <= 0:
        raise ValueError("Window periods must be positive integers")
    
    if short_window >= long_window:
        raise ValueError(
            f"short_window ({short_window}) must be less than "
            f"long_window ({long_window})"
        )
    
    if price_column not in data.columns:
        raise KeyError(
            f"Column '{price_column}' not found in data. "
            f"Available columns: {data.columns.tolist()}"
        )
    
    if len(data) < long_window:
        raise InsufficientDataError(
            f"Insufficient data: need at least {long_window} rows, "
            f"but got {len(data)} rows"
        )
    
    logger.info(
        f"Calculating SMA crossover strategy with windows: "
        f"short={short_window}, long={long_window}"
    )
    
    # Calculate moving averages (vectorized)
    sma_short = data[price_column].rolling(window=short_window).mean()
    sma_long = data[price_column].rolling(window=long_window).mean()
    
    # Generate position signals
    # Position = 1 when short MA > long MA, else 0
    positions = (sma_short > sma_long).astype(int)
    
    # Log strategy statistics
    total_signals = len(positions)
    long_signals = positions.sum()
    flat_signals = total_signals - long_signals
    
    logger.info(
        f"SMA Crossover signals generated: "
        f"{long_signals} long ({long_signals/total_signals*100:.1f}%), "
        f"{flat_signals} flat ({flat_signals/total_signals*100:.1f}%)"
    )
    
    return positions


def rsi_mean_reversion_strategy(
    data: pd.DataFrame,
    period: int = 14,
    buy_threshold: float = 30.0,
    sell_threshold: float = 70.0,
    price_column: str = 'Close'
) -> pd.Series:
    """
    Relative Strength Index (RSI) Mean Reversion Strategy.
    
    Generates buy signals when RSI is oversold (below buy_threshold),
    and sell signals when RSI is overbought (above sell_threshold).
    
    Strategy Logic:
    - Position = 1 (long) when RSI < buy_threshold (oversold, expect bounce)
    - Position = 0 (flat) when RSI >= sell_threshold (overbought, exit)
    - Position = previous position when buy_threshold <= RSI < sell_threshold
    
    Args:
        data: DataFrame with OHLCV data (must have price_column)
        period: RSI calculation period (default: 14)
        buy_threshold: RSI level to enter long position (default: 30)
        sell_threshold: RSI level to exit position (default: 70)
        price_column: Column name to use for price (default: 'Close')
    
    Returns:
        pd.Series: Position signals (1 = long, 0 = flat) with same index as data
    
    Raises:
        ValueError: If parameters are invalid
        InsufficientDataError: If data is too short for the strategy
        KeyError: If price_column doesn't exist in data
    
    Example:
        >>> df = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-12-31')
        >>> positions = rsi_mean_reversion_strategy(df, period=14, buy_threshold=30, sell_threshold=70)
        >>> print(positions.value_counts())
        0    180
        1     70
    """
    # Validate inputs
    if period <= 0:
        raise ValueError("Period must be a positive integer")
    
    if not (0 <= buy_threshold <= 100):
        raise ValueError("buy_threshold must be between 0 and 100")
    
    if not (0 <= sell_threshold <= 100):
        raise ValueError("sell_threshold must be between 0 and 100")
    
    if buy_threshold >= sell_threshold:
        raise ValueError(
            f"buy_threshold ({buy_threshold}) must be less than "
            f"sell_threshold ({sell_threshold})"
        )
    
    if price_column not in data.columns:
        raise KeyError(
            f"Column '{price_column}' not found in data. "
            f"Available columns: {data.columns.tolist()}"
        )
    
    if len(data) < period + 1:
        raise InsufficientDataError(
            f"Insufficient data: need at least {period + 1} rows, "
            f"but got {len(data)} rows"
        )
    
    logger.info(
        f"Calculating RSI mean reversion strategy with period={period}, "
        f"buy_threshold={buy_threshold}, sell_threshold={sell_threshold}"
    )
    
    # Calculate RSI (vectorized)
    rsi = _calculate_rsi(data[price_column], period)
    
    # Generate position signals using state machine logic
    positions = pd.Series(0, index=data.index, dtype=int)
    
    # Vectorized approach: use forward fill for state persistence
    # Mark buy signals (RSI < buy_threshold)
    buy_signals = (rsi < buy_threshold).astype(int)
    
    # Mark sell signals (RSI >= sell_threshold)
    sell_signals = (rsi >= sell_threshold).astype(int)
    
    # Create signal series: 1 for buy, -1 for sell, 0 for hold
    signals = buy_signals - sell_signals
    
    # Convert to positions using cumulative approach
    # Start with position 0, then apply signals
    position_changes = signals.copy()
    
    # Use a more efficient vectorized approach
    current_position = 0
    position_list = []
    
    for signal in signals:
        if signal == 1:  # Buy signal
            current_position = 1
        elif signal == -1:  # Sell signal
            current_position = 0
        # else: maintain current position
        position_list.append(current_position)
    
    positions = pd.Series(position_list, index=data.index, dtype=int)
    
    # Log strategy statistics
    total_signals = len(positions)
    long_signals = positions.sum()
    flat_signals = total_signals - long_signals
    
    logger.info(
        f"RSI Mean Reversion signals generated: "
        f"{long_signals} long ({long_signals/total_signals*100:.1f}%), "
        f"{flat_signals} flat ({flat_signals/total_signals*100:.1f}%)"
    )
    
    return positions


def _calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    
    RSI = 100 - (100 / (1 + RS))
    where RS = Average Gain / Average Loss over the period
    
    Args:
        prices: Series of prices
        period: RSI period (default: 14)
    
    Returns:
        pd.Series: RSI values (0-100)
    """
    # Calculate price changes
    delta = prices.diff()
    
    # Separate gains and losses
    gains = delta.where(delta > 0, 0.0)
    losses = -delta.where(delta < 0, 0.0)
    
    # Calculate exponential moving average of gains and losses
    # Using Wilder's smoothing method (equivalent to EWM with alpha=1/period)
    avg_gains = gains.ewm(com=period - 1, min_periods=period).mean()
    avg_losses = losses.ewm(com=period - 1, min_periods=period).mean()
    
    # Calculate RS and RSI
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    
    # Handle division by zero (when avg_losses = 0, RSI = 100)
    rsi = rsi.fillna(100)
    
    return rsi


def get_strategy_info(strategy_name: str) -> dict:
    """
    Get information about a specific strategy.
    
    Args:
        strategy_name: Name of the strategy ('sma_crossover' or 'rsi_mean_reversion')
    
    Returns:
        dict: Strategy information including name, description, parameters
    
    Example:
        >>> info = get_strategy_info('sma_crossover')
        >>> print(info['description'])
    """
    strategies = {
        'sma_crossover': {
            'name': 'SMA Crossover',
            'description': (
                'Trend-following strategy that buys when short-term moving average '
                'crosses above long-term moving average, and sells on the opposite cross.'
            ),
            'parameters': {
                'short_window': {
                    'type': 'int',
                    'default': 50,
                    'description': 'Period for short-term moving average',
                    'min': 1,
                    'max': None
                },
                'long_window': {
                    'type': 'int',
                    'default': 200,
                    'description': 'Period for long-term moving average',
                    'min': 2,
                    'max': None
                }
            },
            'type': 'trend_following',
            'best_for': 'Trending markets with clear directional moves'
        },
        'rsi_mean_reversion': {
            'name': 'RSI Mean Reversion',
            'description': (
                'Counter-trend strategy that buys when RSI indicates oversold conditions '
                'and sells when overbought, expecting price to revert to mean.'
            ),
            'parameters': {
                'period': {
                    'type': 'int',
                    'default': 14,
                    'description': 'RSI calculation period',
                    'min': 2,
                    'max': 100
                },
                'buy_threshold': {
                    'type': 'float',
                    'default': 30.0,
                    'description': 'RSI level to enter long position (oversold)',
                    'min': 0,
                    'max': 100
                },
                'sell_threshold': {
                    'type': 'float',
                    'default': 70.0,
                    'description': 'RSI level to exit position (overbought)',
                    'min': 0,
                    'max': 100
                }
            },
            'type': 'mean_reversion',
            'best_for': 'Range-bound markets with clear support/resistance levels'
        }
    }
    
    if strategy_name not in strategies:
        raise ValueError(
            f"Unknown strategy: {strategy_name}. "
            f"Available strategies: {list(strategies.keys())}"
        )
    
    return strategies[strategy_name]


def list_available_strategies() -> list[str]:
    """
    List all available trading strategies.
    
    Returns:
        list[str]: List of strategy names
    
    Example:
        >>> strategies = list_available_strategies()
        >>> print(strategies)
        ['sma_crossover', 'rsi_mean_reversion']
    """
    return ['sma_crossover', 'rsi_mean_reversion']
