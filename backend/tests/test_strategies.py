"""
Unit tests for trading strategies.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.services.strategies import (
    sma_crossover_strategy,
    rsi_mean_reversion_strategy,
    get_strategy_info,
    list_available_strategies,
    StrategyError,
    InsufficientDataError,
    _calculate_rsi
)


@pytest.fixture
def sample_price_data():
    """Generate sample price data for testing."""
    dates = pd.date_range(start='2023-01-01', periods=300, freq='D')
    
    # Create synthetic price data with a trend
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(300) * 2)
    
    df = pd.DataFrame({
        'Open': prices + np.random.randn(300) * 0.5,
        'High': prices + np.abs(np.random.randn(300) * 1),
        'Low': prices - np.abs(np.random.randn(300) * 1),
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, 300)
    }, index=dates)
    
    return df


@pytest.fixture
def trending_data():
    """Generate trending price data."""
    dates = pd.date_range(start='2023-01-01', periods=300, freq='D')
    prices = 100 + np.arange(300) * 0.5  # Upward trend
    
    df = pd.DataFrame({
        'Open': prices,
        'High': prices + 1,
        'Low': prices - 1,
        'Close': prices,
        'Volume': 1000000
    }, index=dates)
    
    return df


@pytest.fixture
def oscillating_data():
    """Generate oscillating price data for mean reversion."""
    dates = pd.date_range(start='2023-01-01', periods=300, freq='D')
    prices = 100 + 10 * np.sin(np.arange(300) * 0.1)  # Oscillating pattern
    
    df = pd.DataFrame({
        'Open': prices,
        'High': prices + 1,
        'Low': prices - 1,
        'Close': prices,
        'Volume': 1000000
    }, index=dates)
    
    return df


class TestSMACrossoverStrategy:
    """Tests for SMA Crossover Strategy."""
    
    def test_basic_functionality(self, sample_price_data):
        """Test basic strategy execution."""
        positions = sma_crossover_strategy(
            sample_price_data,
            short_window=20,
            long_window=50
        )
        
        assert isinstance(positions, pd.Series)
        assert len(positions) == len(sample_price_data)
        assert set(positions.unique()).issubset({0, 1})
        assert positions.index.equals(sample_price_data.index)
    
    def test_default_parameters(self, sample_price_data):
        """Test strategy with default parameters."""
        positions = sma_crossover_strategy(sample_price_data)
        
        assert isinstance(positions, pd.Series)
        assert len(positions) == len(sample_price_data)
    
    def test_trending_market(self, trending_data):
        """Test strategy in trending market."""
        positions = sma_crossover_strategy(
            trending_data,
            short_window=20,
            long_window=50
        )
        
        # In uptrend, should eventually be long
        assert positions.iloc[-50:].sum() > 0
    
    def test_invalid_windows(self, sample_price_data):
        """Test that invalid window parameters raise errors."""
        # Short window >= long window
        with pytest.raises(ValueError, match="short_window.*must be less than"):
            sma_crossover_strategy(sample_price_data, short_window=100, long_window=50)
        
        # Negative window
        with pytest.raises(ValueError, match="must be positive"):
            sma_crossover_strategy(sample_price_data, short_window=-10, long_window=50)
        
        # Zero window
        with pytest.raises(ValueError, match="must be positive"):
            sma_crossover_strategy(sample_price_data, short_window=0, long_window=50)
    
    def test_insufficient_data(self):
        """Test that insufficient data raises error."""
        # Create data with only 50 rows
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        df = pd.DataFrame({
            'Close': np.random.randn(50) + 100
        }, index=dates)
        
        with pytest.raises(InsufficientDataError):
            sma_crossover_strategy(df, short_window=50, long_window=200)
    
    def test_missing_price_column(self, sample_price_data):
        """Test that missing price column raises error."""
        with pytest.raises(KeyError, match="Column 'Price' not found"):
            sma_crossover_strategy(sample_price_data, price_column='Price')
    
    def test_custom_price_column(self, sample_price_data):
        """Test using custom price column."""
        positions = sma_crossover_strategy(
            sample_price_data,
            short_window=20,
            long_window=50,
            price_column='Open'
        )
        
        assert isinstance(positions, pd.Series)
        assert len(positions) == len(sample_price_data)
    
    def test_position_values(self, sample_price_data):
        """Test that positions are only 0 or 1."""
        positions = sma_crossover_strategy(
            sample_price_data,
            short_window=20,
            long_window=50
        )
        
        assert positions.min() >= 0
        assert positions.max() <= 1
        assert positions.dtype == int


class TestRSIMeanReversionStrategy:
    """Tests for RSI Mean Reversion Strategy."""
    
    def test_basic_functionality(self, sample_price_data):
        """Test basic strategy execution."""
        positions = rsi_mean_reversion_strategy(
            sample_price_data,
            period=14,
            buy_threshold=30,
            sell_threshold=70
        )
        
        assert isinstance(positions, pd.Series)
        assert len(positions) == len(sample_price_data)
        assert set(positions.unique()).issubset({0, 1})
        assert positions.index.equals(sample_price_data.index)
    
    def test_default_parameters(self, sample_price_data):
        """Test strategy with default parameters."""
        positions = rsi_mean_reversion_strategy(sample_price_data)
        
        assert isinstance(positions, pd.Series)
        assert len(positions) == len(sample_price_data)
    
    def test_oscillating_market(self, oscillating_data):
        """Test strategy in oscillating market."""
        positions = rsi_mean_reversion_strategy(
            oscillating_data,
            period=14,
            buy_threshold=30,
            sell_threshold=70
        )
        
        # Should have some long positions in oscillating market
        assert positions.sum() > 0
        assert positions.sum() < len(positions)  # Not always long
    
    def test_invalid_period(self, sample_price_data):
        """Test that invalid period raises error."""
        with pytest.raises(ValueError, match="Period must be a positive"):
            rsi_mean_reversion_strategy(sample_price_data, period=-1)
        
        with pytest.raises(ValueError, match="Period must be a positive"):
            rsi_mean_reversion_strategy(sample_price_data, period=0)
    
    def test_invalid_thresholds(self, sample_price_data):
        """Test that invalid thresholds raise errors."""
        # buy_threshold >= sell_threshold
        with pytest.raises(ValueError, match="buy_threshold.*must be less than"):
            rsi_mean_reversion_strategy(
                sample_price_data,
                buy_threshold=70,
                sell_threshold=30
            )
        
        # Threshold out of range
        with pytest.raises(ValueError, match="must be between 0 and 100"):
            rsi_mean_reversion_strategy(sample_price_data, buy_threshold=-10)
        
        with pytest.raises(ValueError, match="must be between 0 and 100"):
            rsi_mean_reversion_strategy(sample_price_data, sell_threshold=150)
    
    def test_insufficient_data(self):
        """Test that insufficient data raises error."""
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        df = pd.DataFrame({
            'Close': np.random.randn(10) + 100
        }, index=dates)
        
        with pytest.raises(InsufficientDataError):
            rsi_mean_reversion_strategy(df, period=14)
    
    def test_missing_price_column(self, sample_price_data):
        """Test that missing price column raises error."""
        with pytest.raises(KeyError, match="Column 'Price' not found"):
            rsi_mean_reversion_strategy(sample_price_data, price_column='Price')
    
    def test_custom_price_column(self, sample_price_data):
        """Test using custom price column."""
        positions = rsi_mean_reversion_strategy(
            sample_price_data,
            period=14,
            price_column='Open'
        )
        
        assert isinstance(positions, pd.Series)
        assert len(positions) == len(sample_price_data)
    
    def test_position_values(self, sample_price_data):
        """Test that positions are only 0 or 1."""
        positions = rsi_mean_reversion_strategy(sample_price_data)
        
        assert positions.min() >= 0
        assert positions.max() <= 1
        assert positions.dtype == int


class TestCalculateRSI:
    """Tests for RSI calculation helper function."""
    
    def test_rsi_range(self, sample_price_data):
        """Test that RSI values are in valid range."""
        rsi = _calculate_rsi(sample_price_data['Close'], period=14)
        
        # RSI should be between 0 and 100
        assert rsi.min() >= 0
        assert rsi.max() <= 100
    
    def test_rsi_extreme_values(self):
        """Test RSI with extreme price movements."""
        # All prices increasing
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        increasing_prices = pd.Series(range(100, 150), index=dates)
        rsi = _calculate_rsi(increasing_prices, period=14)
        
        # RSI should be high (near 100) for consistently increasing prices
        assert rsi.iloc[-10:].mean() > 70
        
        # All prices decreasing
        decreasing_prices = pd.Series(range(150, 100, -1), index=dates)
        rsi = _calculate_rsi(decreasing_prices, period=14)
        
        # RSI should be low (near 0) for consistently decreasing prices
        assert rsi.iloc[-10:].mean() < 30


class TestStrategyHelpers:
    """Tests for strategy helper functions."""
    
    def test_list_available_strategies(self):
        """Test listing available strategies."""
        strategies = list_available_strategies()
        
        assert isinstance(strategies, list)
        assert 'sma_crossover' in strategies
        assert 'rsi_mean_reversion' in strategies
        assert len(strategies) == 2
    
    def test_get_strategy_info_sma(self):
        """Test getting SMA crossover strategy info."""
        info = get_strategy_info('sma_crossover')
        
        assert info['name'] == 'SMA Crossover'
        assert 'description' in info
        assert 'parameters' in info
        assert 'short_window' in info['parameters']
        assert 'long_window' in info['parameters']
        assert info['type'] == 'trend_following'
    
    def test_get_strategy_info_rsi(self):
        """Test getting RSI strategy info."""
        info = get_strategy_info('rsi_mean_reversion')
        
        assert info['name'] == 'RSI Mean Reversion'
        assert 'description' in info
        assert 'parameters' in info
        assert 'period' in info['parameters']
        assert 'buy_threshold' in info['parameters']
        assert 'sell_threshold' in info['parameters']
        assert info['type'] == 'mean_reversion'
    
    def test_get_strategy_info_invalid(self):
        """Test getting info for invalid strategy."""
        with pytest.raises(ValueError, match="Unknown strategy"):
            get_strategy_info('invalid_strategy')


class TestStrategyComparison:
    """Integration tests comparing strategies."""
    
    def test_strategies_return_same_length(self, sample_price_data):
        """Test that both strategies return same length as input."""
        sma_positions = sma_crossover_strategy(
            sample_price_data,
            short_window=20,
            long_window=50
        )
        
        rsi_positions = rsi_mean_reversion_strategy(
            sample_price_data,
            period=14
        )
        
        assert len(sma_positions) == len(sample_price_data)
        assert len(rsi_positions) == len(sample_price_data)
        assert len(sma_positions) == len(rsi_positions)
    
    def test_strategies_different_signals(self, sample_price_data):
        """Test that different strategies produce different signals."""
        sma_positions = sma_crossover_strategy(
            sample_price_data,
            short_window=20,
            long_window=50
        )
        
        rsi_positions = rsi_mean_reversion_strategy(
            sample_price_data,
            period=14
        )
        
        # Strategies should produce different signals
        # (not always, but usually for random data)
        assert not sma_positions.equals(rsi_positions)
