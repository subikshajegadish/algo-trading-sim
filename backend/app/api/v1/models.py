"""
Pydantic models for API request/response validation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Any
from datetime import datetime


class StrategyParams(BaseModel):
    """Parameters for trading strategies."""
    
    # SMA Crossover parameters
    short_window: Optional[int] = Field(None, ge=1, le=500, description="Short-term MA window")
    long_window: Optional[int] = Field(None, ge=2, le=1000, description="Long-term MA window")
    
    # RSI Mean Reversion parameters
    period: Optional[int] = Field(None, ge=2, le=100, description="RSI period")
    buy_threshold: Optional[float] = Field(None, ge=0, le=100, description="RSI buy threshold")
    sell_threshold: Optional[float] = Field(None, ge=0, le=100, description="RSI sell threshold")
    
    class Config:
        json_schema_extra = {
            "example": {
                "short_window": 50,
                "long_window": 200
            }
        }


class BacktestRequest(BaseModel):
    """Request model for backtest endpoint."""
    
    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    initial_capital: float = Field(default=10000.0, ge=100, le=10000000, description="Initial capital in dollars")
    strategy_name: str = Field(..., description="Strategy name: 'sma_crossover' or 'rsi_mean_reversion'")
    strategy_params: StrategyParams = Field(default_factory=StrategyParams, description="Strategy parameters")
    
    @field_validator('ticker')
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Validate and normalize ticker."""
        return v.strip().upper()
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format."""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD")
    
    @field_validator('strategy_name')
    @classmethod
    def validate_strategy_name(cls, v: str) -> str:
        """Validate strategy name."""
        valid_strategies = ['sma_crossover', 'rsi_mean_reversion']
        if v not in valid_strategies:
            raise ValueError(
                f"Invalid strategy: {v}. Must be one of {valid_strategies}"
            )
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
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
        }


class MetricsResponse(BaseModel):
    """Performance metrics response."""
    
    total_return: float = Field(..., description="Total return as decimal")
    total_return_pct: str = Field(..., description="Total return as percentage string")
    cagr: float = Field(..., description="Compound Annual Growth Rate")
    cagr_pct: str = Field(..., description="CAGR as percentage string")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown as decimal")
    max_drawdown_pct: str = Field(..., description="Max drawdown as percentage string")
    initial_capital: float = Field(..., description="Initial capital")
    final_value: float = Field(..., description="Final portfolio value")
    num_trades: int = Field(..., description="Number of trades")
    days_in_market: int = Field(..., description="Days with long position")
    total_days: int = Field(..., description="Total trading days")


class TimeSeriesData(BaseModel):
    """Time series data for equity curves."""
    
    dates: List[str] = Field(..., description="List of dates in YYYY-MM-DD format")
    values: List[float] = Field(..., description="List of portfolio values")


class ComparisonResponse(BaseModel):
    """Comparison metrics between strategy and baseline."""
    
    excess_return: float = Field(..., description="Strategy return - baseline return")
    excess_return_pct: str = Field(..., description="Excess return as percentage")
    excess_cagr: float = Field(..., description="Strategy CAGR - baseline CAGR")
    sharpe_difference: float = Field(..., description="Strategy Sharpe - baseline Sharpe")
    outperformed: bool = Field(..., description="True if strategy beat baseline")


class BacktestResponse(BaseModel):
    """Complete backtest response."""
    
    request: Dict[str, Any] = Field(..., description="Original request parameters")
    strategy_metrics: MetricsResponse = Field(..., description="Strategy performance metrics")
    baseline_metrics: MetricsResponse = Field(..., description="Buy-and-hold baseline metrics")
    comparison: ComparisonResponse = Field(..., description="Strategy vs baseline comparison")
    equity_curve: TimeSeriesData = Field(..., description="Strategy equity curve")
    baseline_curve: TimeSeriesData = Field(..., description="Baseline equity curve")
    success: bool = Field(default=True, description="Whether backtest succeeded")
    message: str = Field(default="Backtest completed successfully", description="Status message")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Detailed error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
