"""
Vectorized backtesting engine for trading strategies.

This module provides a clean, efficient backtesting engine that calculates
portfolio performance metrics from price data and position signals.
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class BacktestError(Exception):
    """Base exception for backtesting errors."""
    pass


class InvalidPositionsError(BacktestError):
    """Raised when position signals are invalid."""
    pass


@dataclass
class BacktestResults:
    """Container for backtest results."""
    
    # Time series data
    portfolio_value: pd.Series
    positions: pd.Series
    returns: pd.Series
    
    # Performance metrics
    total_return: float
    cagr: float
    sharpe_ratio: float
    max_drawdown: float
    
    # Additional info
    initial_capital: float
    final_value: float
    num_trades: int
    days_in_market: int
    total_days: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary."""
        return {
            'metrics': {
                'total_return': self.total_return,
                'cagr': self.cagr,
                'sharpe_ratio': self.sharpe_ratio,
                'max_drawdown': self.max_drawdown,
                'initial_capital': self.initial_capital,
                'final_value': self.final_value,
                'num_trades': self.num_trades,
                'days_in_market': self.days_in_market,
                'total_days': self.total_days,
            },
            'time_series': {
                'portfolio_value': self.portfolio_value.to_dict(),
                'returns': self.returns.to_dict(),
                'positions': self.positions.to_dict(),
            }
        }
    
    def __repr__(self) -> str:
        """String representation of results."""
        return (
            f"BacktestResults(\n"
            f"  Total Return: {self.total_return:.2%}\n"
            f"  CAGR: {self.cagr:.2%}\n"
            f"  Sharpe Ratio: {self.sharpe_ratio:.2f}\n"
            f"  Max Drawdown: {self.max_drawdown:.2%}\n"
            f"  Trades: {self.num_trades}\n"
            f"  Final Value: ${self.final_value:,.2f}\n"
            f")"
        )


def run_backtest(
    prices: pd.Series,
    positions: pd.Series,
    initial_capital: float = 10000.0,
    risk_free_rate: float = 0.0
) -> BacktestResults:
    """
    Run a vectorized backtest on price data with position signals.
    
    This function calculates portfolio value over time and computes key
    performance metrics including total return, CAGR, Sharpe ratio, and
    maximum drawdown.
    
    Args:
        prices: Series of prices (typically Close prices) with DatetimeIndex
        positions: Series of position signals (1 = long, 0 = flat) with same index as prices
        initial_capital: Starting capital in dollars (default: 10000)
        risk_free_rate: Annual risk-free rate for Sharpe calculation (default: 0.0)
    
    Returns:
        BacktestResults: Object containing portfolio values and performance metrics
    
    Raises:
        ValueError: If inputs are invalid
        InvalidPositionsError: If position signals are invalid
    
    Example:
        >>> prices = df['Close']
        >>> positions = sma_crossover_strategy(df)
        >>> results = run_backtest(prices, positions, initial_capital=10000)
        >>> print(f"Total Return: {results.total_return:.2%}")
        >>> print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
    """
    # Validate inputs
    _validate_backtest_inputs(prices, positions, initial_capital)
    
    # Align prices and positions
    prices, positions = _align_series(prices, positions)
    
    logger.info(
        f"Running backtest: {len(prices)} days, "
        f"initial capital ${initial_capital:,.2f}"
    )
    
    # Calculate daily returns
    returns = prices.pct_change()
    
    # Calculate strategy returns (position from previous day * today's return)
    # We use shift(1) because we can only trade on today's close for tomorrow
    strategy_returns = returns * positions.shift(1)
    
    # Handle first day (no position yet)
    strategy_returns.iloc[0] = 0.0
    
    # Calculate portfolio value over time
    portfolio_value = initial_capital * (1 + strategy_returns).cumprod()
    
    # Calculate performance metrics
    total_return = (portfolio_value.iloc[-1] / initial_capital) - 1
    cagr = _calculate_cagr(portfolio_value, initial_capital)
    sharpe_ratio = _calculate_sharpe_ratio(strategy_returns, risk_free_rate)
    max_drawdown = _calculate_max_drawdown(portfolio_value)
    
    # Calculate trading statistics
    num_trades = _count_trades(positions)
    days_in_market = positions.sum()
    total_days = len(positions)
    
    logger.info(
        f"Backtest complete: Total Return {total_return:.2%}, "
        f"Sharpe {sharpe_ratio:.2f}, Max DD {max_drawdown:.2%}"
    )
    
    return BacktestResults(
        portfolio_value=portfolio_value,
        positions=positions,
        returns=strategy_returns,
        total_return=total_return,
        cagr=cagr,
        sharpe_ratio=sharpe_ratio,
        max_drawdown=max_drawdown,
        initial_capital=initial_capital,
        final_value=portfolio_value.iloc[-1],
        num_trades=num_trades,
        days_in_market=int(days_in_market),
        total_days=total_days
    )


def run_buy_and_hold(
    prices: pd.Series,
    initial_capital: float = 10000.0,
    risk_free_rate: float = 0.0
) -> BacktestResults:
    """
    Run a buy-and-hold baseline backtest.
    
    This creates a simple baseline where the strategy buys on day 1 and
    holds until the end. Useful for comparing active strategies against
    passive investing.
    
    Args:
        prices: Series of prices (typically Close prices) with DatetimeIndex
        initial_capital: Starting capital in dollars (default: 10000)
        risk_free_rate: Annual risk-free rate for Sharpe calculation (default: 0.0)
    
    Returns:
        BacktestResults: Object containing portfolio values and performance metrics
    
    Example:
        >>> prices = df['Close']
        >>> baseline = run_buy_and_hold(prices, initial_capital=10000)
        >>> print(f"Buy & Hold Return: {baseline.total_return:.2%}")
    """
    # Create positions series: always long (1)
    positions = pd.Series(1, index=prices.index, dtype=int)
    
    logger.info("Running buy-and-hold baseline")
    
    return run_backtest(prices, positions, initial_capital, risk_free_rate)


def compare_to_baseline(
    strategy_results: BacktestResults,
    baseline_results: BacktestResults
) -> Dict[str, float]:
    """
    Compare strategy results to buy-and-hold baseline.
    
    Args:
        strategy_results: Results from active strategy
        baseline_results: Results from buy-and-hold baseline
    
    Returns:
        dict: Comparison metrics including excess returns and ratios
    
    Example:
        >>> strategy = run_backtest(prices, positions)
        >>> baseline = run_buy_and_hold(prices)
        >>> comparison = compare_to_baseline(strategy, baseline)
        >>> print(f"Excess Return: {comparison['excess_return']:.2%}")
    """
    return {
        'excess_return': strategy_results.total_return - baseline_results.total_return,
        'excess_cagr': strategy_results.cagr - baseline_results.cagr,
        'sharpe_difference': strategy_results.sharpe_ratio - baseline_results.sharpe_ratio,
        'drawdown_difference': strategy_results.max_drawdown - baseline_results.max_drawdown,
        'strategy_total_return': strategy_results.total_return,
        'baseline_total_return': baseline_results.total_return,
        'strategy_sharpe': strategy_results.sharpe_ratio,
        'baseline_sharpe': baseline_results.sharpe_ratio,
    }


# Helper functions for calculations

def _validate_backtest_inputs(
    prices: pd.Series,
    positions: pd.Series,
    initial_capital: float
) -> None:
    """Validate backtest inputs."""
    if not isinstance(prices, pd.Series):
        raise ValueError("prices must be a pandas Series")
    
    if not isinstance(positions, pd.Series):
        raise ValueError("positions must be a pandas Series")
    
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValueError("prices must have a DatetimeIndex")
    
    if len(prices) == 0:
        raise ValueError("prices cannot be empty")
    
    if len(positions) == 0:
        raise ValueError("positions cannot be empty")
    
    if initial_capital <= 0:
        raise ValueError("initial_capital must be positive")
    
    # Validate position values
    unique_positions = positions.unique()
    if not set(unique_positions).issubset({0, 1}):
        raise InvalidPositionsError(
            f"positions must only contain 0 or 1, found: {unique_positions}"
        )
    
    # Check for NaN values
    if prices.isna().any():
        raise ValueError("prices contains NaN values")
    
    if positions.isna().any():
        raise ValueError("positions contains NaN values")


def _align_series(prices: pd.Series, positions: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Align prices and positions to same index."""
    if not prices.index.equals(positions.index):
        logger.warning("Prices and positions have different indices, aligning...")
        # Use inner join to keep only common dates
        aligned = pd.DataFrame({'prices': prices, 'positions': positions}).dropna()
        return aligned['prices'], aligned['positions']
    
    return prices, positions


def _calculate_cagr(portfolio_value: pd.Series, initial_capital: float) -> float:
    """
    Calculate Compound Annual Growth Rate.
    
    CAGR = (Final Value / Initial Value)^(1 / Years) - 1
    """
    final_value = portfolio_value.iloc[-1]
    
    # Calculate number of years
    start_date = portfolio_value.index[0]
    end_date = portfolio_value.index[-1]
    days = (end_date - start_date).days
    years = days / 365.25
    
    if years <= 0:
        return 0.0
    
    cagr = (final_value / initial_capital) ** (1 / years) - 1
    
    return cagr


def _calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """
    Calculate annualized Sharpe Ratio.
    
    Sharpe = (Mean Return - Risk Free Rate) / Std Dev of Returns * sqrt(periods)
    
    Args:
        returns: Series of daily returns
        risk_free_rate: Annual risk-free rate (default: 0.0)
        periods_per_year: Trading days per year (default: 252)
    """
    if len(returns) < 2:
        return 0.0
    
    # Calculate excess returns
    daily_rf_rate = risk_free_rate / periods_per_year
    excess_returns = returns - daily_rf_rate
    
    # Calculate mean and std of excess returns
    mean_excess_return = excess_returns.mean()
    std_excess_return = excess_returns.std()
    
    if std_excess_return == 0:
        return 0.0
    
    # Annualize
    sharpe = (mean_excess_return / std_excess_return) * np.sqrt(periods_per_year)
    
    return sharpe


def _calculate_max_drawdown(portfolio_value: pd.Series) -> float:
    """
    Calculate maximum drawdown.
    
    Max Drawdown = (Trough Value - Peak Value) / Peak Value
    
    This is the largest peak-to-trough decline in portfolio value.
    """
    # Calculate running maximum
    running_max = portfolio_value.cummax()
    
    # Calculate drawdown at each point
    drawdown = (portfolio_value - running_max) / running_max
    
    # Maximum drawdown is the minimum value (most negative)
    max_drawdown = drawdown.min()
    
    return max_drawdown


def _count_trades(positions: pd.Series) -> int:
    """
    Count number of trades (position changes).
    
    A trade occurs when position changes from 0 to 1 or 1 to 0.
    """
    # Calculate position changes
    position_changes = positions.diff()
    
    # Count non-zero changes (excluding first day)
    num_trades = (position_changes != 0).sum()
    
    return int(num_trades)


def calculate_portfolio_stats(results: BacktestResults) -> pd.DataFrame:
    """
    Calculate additional portfolio statistics.
    
    Args:
        results: BacktestResults object
    
    Returns:
        pd.DataFrame: Summary statistics
    """
    returns = results.returns
    
    stats = {
        'Total Return': f"{results.total_return:.2%}",
        'CAGR': f"{results.cagr:.2%}",
        'Sharpe Ratio': f"{results.sharpe_ratio:.2f}",
        'Max Drawdown': f"{results.max_drawdown:.2%}",
        'Initial Capital': f"${results.initial_capital:,.2f}",
        'Final Value': f"${results.final_value:,.2f}",
        'Number of Trades': results.num_trades,
        'Days in Market': f"{results.days_in_market} ({results.days_in_market/results.total_days*100:.1f}%)",
        'Total Days': results.total_days,
        'Mean Daily Return': f"{returns.mean():.4%}",
        'Std Daily Return': f"{returns.std():.4%}",
        'Best Day': f"{returns.max():.2%}",
        'Worst Day': f"{returns.min():.2%}",
        'Positive Days': f"{(returns > 0).sum()} ({(returns > 0).sum()/len(returns)*100:.1f}%)",
        'Negative Days': f"{(returns < 0).sum()} ({(returns < 0).sum()/len(returns)*100:.1f}%)",
    }
    
    return pd.DataFrame.from_dict(stats, orient='index', columns=['Value'])
