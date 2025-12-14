"""
Unit tests for backtesting engine.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.services.backtest import (
    run_backtest,
    run_buy_and_hold,
    compare_to_baseline,
    calculate_portfolio_stats,
    BacktestResults,
    BacktestError,
    InvalidPositionsError,
    _calculate_cagr,
    _calculate_sharpe_ratio,
    _calculate_max_drawdown,
    _count_trades
)


@pytest.fixture
def sample_prices():
    """Generate sample price data."""
    dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
    # Upward trending prices
    prices = pd.Series(
        100 + np.cumsum(np.random.randn(252) * 0.5),
        index=dates,
        name='Close'
    )
    return prices


@pytest.fixture
def sample_positions():
    """Generate sample position signals."""
    dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
    # Alternate between long and flat
    positions = pd.Series(
        [1 if i % 20 < 10 else 0 for i in range(252)],
        index=dates,
        dtype=int
    )
    return positions


@pytest.fixture
def constant_prices():
    """Generate constant price data (no change)."""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    prices = pd.Series(100.0, index=dates, name='Close')
    return prices


@pytest.fixture
def always_long_positions():
    """Generate positions that are always long."""
    dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
    return pd.Series(1, index=dates, dtype=int)


class TestRunBacktest:
    """Tests for run_backtest function."""
    
    def test_basic_backtest(self, sample_prices, sample_positions):
        """Test basic backtest execution."""
        results = run_backtest(sample_prices, sample_positions, initial_capital=10000)
        
        assert isinstance(results, BacktestResults)
        assert len(results.portfolio_value) == len(sample_prices)
        assert results.initial_capital == 10000
        assert results.final_value > 0
        assert results.total_days == 252
    
    def test_portfolio_value_starts_at_initial_capital(self, sample_prices, sample_positions):
        """Test that portfolio value starts at initial capital."""
        initial_capital = 10000
        results = run_backtest(sample_prices, sample_positions, initial_capital)
        
        # First day should be close to initial capital (may have small return)
        assert abs(results.portfolio_value.iloc[0] - initial_capital) < initial_capital * 0.1
    
    def test_buy_and_hold_always_invested(self, sample_prices):
        """Test buy-and-hold strategy."""
        results = run_buy_and_hold(sample_prices, initial_capital=10000)
        
        assert results.days_in_market == len(sample_prices)
        assert results.num_trades == 1  # Only initial buy
    
    def test_metrics_calculated(self, sample_prices, sample_positions):
        """Test that all metrics are calculated."""
        results = run_backtest(sample_prices, sample_positions)
        
        assert isinstance(results.total_return, float)
        assert isinstance(results.cagr, float)
        assert isinstance(results.sharpe_ratio, float)
        assert isinstance(results.max_drawdown, float)
        assert isinstance(results.num_trades, int)
    
    def test_invalid_positions_raises_error(self, sample_prices):
        """Test that invalid position values raise error."""
        dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
        invalid_positions = pd.Series([0, 1, 2, 1, 0], index=dates[:5])  # Contains 2
        
        with pytest.raises(InvalidPositionsError):
            run_backtest(sample_prices[:5], invalid_positions)
    
    def test_empty_data_raises_error(self):
        """Test that empty data raises error."""
        empty_prices = pd.Series([], dtype=float)
        empty_positions = pd.Series([], dtype=int)
        
        with pytest.raises(ValueError):
            run_backtest(empty_prices, empty_positions)
    
    def test_negative_capital_raises_error(self, sample_prices, sample_positions):
        """Test that negative initial capital raises error."""
        with pytest.raises(ValueError, match="initial_capital must be positive"):
            run_backtest(sample_prices, sample_positions, initial_capital=-1000)
    
    def test_nan_prices_raises_error(self, sample_positions):
        """Test that NaN prices raise error."""
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        prices_with_nan = pd.Series([100, 101, np.nan, 103, 104], index=dates[:5])
        
        with pytest.raises(ValueError, match="prices contains NaN"):
            run_backtest(prices_with_nan, sample_positions[:5])
    
    def test_constant_prices_zero_return(self, constant_prices, always_long_positions):
        """Test that constant prices result in zero return."""
        results = run_backtest(constant_prices, always_long_positions[:100])
        
        assert abs(results.total_return) < 0.001  # Near zero
        assert abs(results.cagr) < 0.001
    
    def test_no_positions_zero_return(self, sample_prices):
        """Test that no positions (always flat) results in zero return."""
        flat_positions = pd.Series(0, index=sample_prices.index, dtype=int)
        results = run_backtest(sample_prices, flat_positions)
        
        assert abs(results.total_return) < 0.001
        assert results.days_in_market == 0
    
    def test_results_to_dict(self, sample_prices, sample_positions):
        """Test converting results to dictionary."""
        results = run_backtest(sample_prices, sample_positions)
        result_dict = results.to_dict()
        
        assert 'metrics' in result_dict
        assert 'time_series' in result_dict
        assert 'total_return' in result_dict['metrics']
        assert 'portfolio_value' in result_dict['time_series']


class TestCalculateCAGR:
    """Tests for CAGR calculation."""
    
    def test_cagr_positive_return(self):
        """Test CAGR with positive returns."""
        dates = pd.date_range(start='2020-01-01', end='2023-01-01', freq='D')
        # Double the money over 3 years
        portfolio_value = pd.Series(
            np.linspace(10000, 20000, len(dates)),
            index=dates
        )
        
        cagr = _calculate_cagr(portfolio_value, 10000)
        
        # CAGR should be around 26% for doubling in 3 years
        assert 0.20 < cagr < 0.30
    
    def test_cagr_negative_return(self):
        """Test CAGR with negative returns."""
        dates = pd.date_range(start='2020-01-01', end='2023-01-01', freq='D')
        # Lose half the money over 3 years
        portfolio_value = pd.Series(
            np.linspace(10000, 5000, len(dates)),
            index=dates
        )
        
        cagr = _calculate_cagr(portfolio_value, 10000)
        
        assert cagr < 0  # Negative CAGR
    
    def test_cagr_zero_return(self):
        """Test CAGR with zero return."""
        dates = pd.date_range(start='2020-01-01', end='2023-01-01', freq='D')
        portfolio_value = pd.Series(10000, index=dates)
        
        cagr = _calculate_cagr(portfolio_value, 10000)
        
        assert abs(cagr) < 0.001  # Near zero


class TestCalculateSharpeRatio:
    """Tests for Sharpe ratio calculation."""
    
    def test_sharpe_positive_returns(self):
        """Test Sharpe with positive returns."""
        # Variable positive returns (need volatility for Sharpe)
        np.random.seed(42)
        returns = pd.Series(0.01 + np.random.randn(252) * 0.005)
        sharpe = _calculate_sharpe_ratio(returns)
        
        assert sharpe > 0
    
    def test_sharpe_negative_returns(self):
        """Test Sharpe with negative returns."""
        # Variable negative returns
        np.random.seed(42)
        returns = pd.Series(-0.01 + np.random.randn(252) * 0.005)
        sharpe = _calculate_sharpe_ratio(returns)
        
        assert sharpe < 0
    
    def test_sharpe_zero_volatility(self):
        """Test Sharpe with zero volatility."""
        # No volatility (constant returns)
        returns = pd.Series([0.01] * 252)
        sharpe = _calculate_sharpe_ratio(returns)
        
        # With zero volatility, Sharpe is undefined, we return 0
        assert sharpe == 0.0
    
    def test_sharpe_with_risk_free_rate(self):
        """Test Sharpe with non-zero risk-free rate."""
        np.random.seed(42)
        returns = pd.Series(0.01 + np.random.randn(252) * 0.005)
        sharpe_no_rf = _calculate_sharpe_ratio(returns, risk_free_rate=0.0)
        sharpe_with_rf = _calculate_sharpe_ratio(returns, risk_free_rate=0.05)
        
        # Sharpe should be lower with risk-free rate
        assert sharpe_with_rf < sharpe_no_rf


class TestCalculateMaxDrawdown:
    """Tests for max drawdown calculation."""
    
    def test_max_drawdown_declining_portfolio(self):
        """Test max drawdown with declining portfolio."""
        # Portfolio drops from 10000 to 5000
        portfolio_value = pd.Series([10000, 9000, 8000, 7000, 6000, 5000])
        max_dd = _calculate_max_drawdown(portfolio_value)
        
        assert max_dd == -0.5  # 50% drawdown
    
    def test_max_drawdown_peak_trough_recovery(self):
        """Test max drawdown with peak, trough, and recovery."""
        # Peak at 10000, trough at 7000, recover to 9000
        portfolio_value = pd.Series([10000, 9000, 8000, 7000, 8000, 9000])
        max_dd = _calculate_max_drawdown(portfolio_value)
        
        assert max_dd == -0.3  # 30% drawdown
    
    def test_max_drawdown_always_increasing(self):
        """Test max drawdown with always increasing portfolio."""
        portfolio_value = pd.Series([10000, 11000, 12000, 13000, 14000])
        max_dd = _calculate_max_drawdown(portfolio_value)
        
        assert max_dd == 0.0  # No drawdown


class TestCountTrades:
    """Tests for trade counting."""
    
    def test_count_trades_alternating(self):
        """Test counting trades with alternating positions."""
        # 0, 1, 0, 1, 0, 1
        positions = pd.Series([0, 1, 0, 1, 0, 1])
        num_trades = _count_trades(positions)
        
        # First position counts, then 5 changes = 6 total
        assert num_trades == 6
    
    def test_count_trades_always_long(self):
        """Test counting trades when always long."""
        positions = pd.Series([1, 1, 1, 1, 1])
        num_trades = _count_trades(positions)
        
        assert num_trades == 1  # Only initial position
    
    def test_count_trades_always_flat(self):
        """Test counting trades when always flat."""
        positions = pd.Series([0, 0, 0, 0, 0])
        num_trades = _count_trades(positions)
        
        # First position (flat) counts as 1
        assert num_trades == 1


class TestCompareToBaseline:
    """Tests for baseline comparison."""
    
    def test_compare_to_baseline(self, sample_prices, sample_positions):
        """Test comparing strategy to baseline."""
        strategy_results = run_backtest(sample_prices, sample_positions)
        baseline_results = run_buy_and_hold(sample_prices)
        
        comparison = compare_to_baseline(strategy_results, baseline_results)
        
        assert 'excess_return' in comparison
        assert 'excess_cagr' in comparison
        assert 'sharpe_difference' in comparison
        assert isinstance(comparison['excess_return'], float)


class TestCalculatePortfolioStats:
    """Tests for portfolio statistics calculation."""
    
    def test_calculate_stats(self, sample_prices, sample_positions):
        """Test calculating portfolio statistics."""
        results = run_backtest(sample_prices, sample_positions)
        stats = calculate_portfolio_stats(results)
        
        assert isinstance(stats, pd.DataFrame)
        assert 'Total Return' in stats.index
        assert 'Sharpe Ratio' in stats.index
        assert 'Max Drawdown' in stats.index


class TestBacktestResults:
    """Tests for BacktestResults dataclass."""
    
    def test_results_repr(self, sample_prices, sample_positions):
        """Test string representation of results."""
        results = run_backtest(sample_prices, sample_positions)
        repr_str = repr(results)
        
        assert 'BacktestResults' in repr_str
        assert 'Total Return' in repr_str
        assert 'Sharpe Ratio' in repr_str


class TestIntegration:
    """Integration tests with real-world scenarios."""
    
    def test_full_backtest_workflow(self):
        """Test complete backtest workflow."""
        # Create realistic price data
        dates = pd.date_range(start='2022-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        prices = pd.Series(
            100 * (1 + np.random.randn(len(dates)).cumsum() * 0.01),
            index=dates
        )
        
        # Create simple strategy: long when price > 100
        positions = (prices > 100).astype(int)
        
        # Run backtest
        results = run_backtest(prices, positions, initial_capital=10000)
        
        # Run baseline
        baseline = run_buy_and_hold(prices, initial_capital=10000)
        
        # Compare
        comparison = compare_to_baseline(results, baseline)
        
        # Verify results are reasonable
        assert -1.0 < results.total_return < 10.0  # Between -100% and 1000%
        assert -1.0 < results.max_drawdown <= 0.0  # Drawdown is negative or zero
        assert results.num_trades >= 0
        assert len(results.portfolio_value) == len(prices)
        
        # Verify comparison
        assert isinstance(comparison['excess_return'], float)
