"""
Backtest endpoint for running trading strategy backtests.
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any

from app.api.v1.models import (
    BacktestRequest,
    BacktestResponse,
    MetricsResponse,
    TimeSeriesData,
    ComparisonResponse,
    ErrorResponse
)
from app.services.market_data import (
    fetch_ohlcv_data,
    InvalidTickerError,
    NoDataError,
    MarketDataError
)
from app.services.strategies import (
    sma_crossover_strategy,
    rsi_mean_reversion_strategy,
    InsufficientDataError,
    StrategyError
)
from app.services.backtest import (
    run_backtest,
    run_buy_and_hold,
    compare_to_baseline,
    BacktestError
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _create_metrics_response(results) -> MetricsResponse:
    """Convert BacktestResults to MetricsResponse."""
    return MetricsResponse(
        total_return=results.total_return,
        total_return_pct=f"{results.total_return:.2%}",
        cagr=results.cagr,
        cagr_pct=f"{results.cagr:.2%}",
        sharpe_ratio=results.sharpe_ratio,
        max_drawdown=results.max_drawdown,
        max_drawdown_pct=f"{results.max_drawdown:.2%}",
        initial_capital=results.initial_capital,
        final_value=results.final_value,
        num_trades=results.num_trades,
        days_in_market=results.days_in_market,
        total_days=results.total_days
    )


def _create_time_series_data(results) -> TimeSeriesData:
    """Convert portfolio value series to TimeSeriesData."""
    return TimeSeriesData(
        dates=[date.strftime('%Y-%m-%d') for date in results.portfolio_value.index],
        values=results.portfolio_value.tolist()
    )


def _create_comparison_response(comparison: Dict[str, float]) -> ComparisonResponse:
    """Convert comparison dict to ComparisonResponse."""
    return ComparisonResponse(
        excess_return=comparison['excess_return'],
        excess_return_pct=f"{comparison['excess_return']:.2%}",
        excess_cagr=comparison['excess_cagr'],
        sharpe_difference=comparison['sharpe_difference'],
        outperformed=comparison['excess_return'] > 0
    )


@router.post(
    "/backtest",
    response_model=BacktestResponse,
    status_code=status.HTTP_200_OK,
    summary="Run a trading strategy backtest",
    description="""
    Run a backtest for a trading strategy on historical stock data.
    
    Supported strategies:
    - **sma_crossover**: Simple Moving Average crossover (requires short_window, long_window)
    - **rsi_mean_reversion**: RSI-based mean reversion (requires period, buy_threshold, sell_threshold)
    
    Returns equity curves, performance metrics, and comparison to buy-and-hold baseline.
    """,
    responses={
        200: {"description": "Backtest completed successfully"},
        400: {"description": "Invalid request parameters", "model": ErrorResponse},
        404: {"description": "Ticker not found or no data available", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
async def run_backtest_endpoint(request: BacktestRequest) -> BacktestResponse:
    """
    Run a backtest for a trading strategy.
    
    Args:
        request: BacktestRequest containing ticker, dates, capital, strategy, and parameters
    
    Returns:
        BacktestResponse with equity curves, metrics, and comparison
    
    Raises:
        HTTPException: For various error conditions with appropriate status codes
    """
    try:
        logger.info(
            f"Backtest request: {request.ticker} "
            f"({request.start_date} to {request.end_date}), "
            f"strategy={request.strategy_name}, "
            f"capital=${request.initial_capital:,.2f}"
        )
        
        # Step 1: Fetch market data
        try:
            df = fetch_ohlcv_data(
                ticker=request.ticker,
                start_date=request.start_date,
                end_date=request.end_date,
                validate_data=True
            )
        except InvalidTickerError as e:
            logger.warning(f"Invalid ticker: {request.ticker}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "InvalidTicker",
                    "message": str(e),
                    "ticker": request.ticker
                }
            )
        except NoDataError as e:
            logger.warning(f"No data available: {request.ticker}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "NoDataAvailable",
                    "message": str(e),
                    "ticker": request.ticker,
                    "date_range": f"{request.start_date} to {request.end_date}"
                }
            )
        except MarketDataError as e:
            logger.error(f"Market data error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "MarketDataError",
                    "message": f"Failed to fetch market data: {str(e)}"
                }
            )
        
        # Step 2: Apply trading strategy
        try:
            if request.strategy_name == 'sma_crossover':
                # Validate required parameters
                if request.strategy_params.short_window is None:
                    raise ValueError("short_window is required for SMA crossover strategy")
                if request.strategy_params.long_window is None:
                    raise ValueError("long_window is required for SMA crossover strategy")
                
                positions = sma_crossover_strategy(
                    df,
                    short_window=request.strategy_params.short_window,
                    long_window=request.strategy_params.long_window
                )
                
            elif request.strategy_name == 'rsi_mean_reversion':
                # Validate required parameters
                if request.strategy_params.period is None:
                    raise ValueError("period is required for RSI mean reversion strategy")
                if request.strategy_params.buy_threshold is None:
                    raise ValueError("buy_threshold is required for RSI mean reversion strategy")
                if request.strategy_params.sell_threshold is None:
                    raise ValueError("sell_threshold is required for RSI mean reversion strategy")
                
                positions = rsi_mean_reversion_strategy(
                    df,
                    period=request.strategy_params.period,
                    buy_threshold=request.strategy_params.buy_threshold,
                    sell_threshold=request.strategy_params.sell_threshold
                )
            else:
                raise ValueError(f"Unknown strategy: {request.strategy_name}")
                
        except InsufficientDataError as e:
            logger.warning(f"Insufficient data for strategy: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InsufficientData",
                    "message": str(e),
                    "suggestion": "Try a shorter date range or smaller strategy parameters"
                }
            )
        except ValueError as e:
            logger.warning(f"Invalid strategy parameters: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidParameters",
                    "message": str(e)
                }
            )
        except StrategyError as e:
            logger.error(f"Strategy error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "StrategyError",
                    "message": f"Strategy execution failed: {str(e)}"
                }
            )
        
        # Step 3: Run backtest
        try:
            strategy_results = run_backtest(
                prices=df['Close'],
                positions=positions,
                initial_capital=request.initial_capital
            )
        except BacktestError as e:
            logger.error(f"Backtest error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "BacktestError",
                    "message": f"Backtest execution failed: {str(e)}"
                }
            )
        
        # Step 4: Run buy-and-hold baseline
        try:
            baseline_results = run_buy_and_hold(
                prices=df['Close'],
                initial_capital=request.initial_capital
            )
        except BacktestError as e:
            logger.error(f"Baseline backtest error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "BaselineError",
                    "message": f"Baseline backtest failed: {str(e)}"
                }
            )
        
        # Step 5: Compare to baseline
        comparison = compare_to_baseline(strategy_results, baseline_results)
        
        # Step 6: Build response
        response = BacktestResponse(
            request={
                "ticker": request.ticker,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "initial_capital": request.initial_capital,
                "strategy_name": request.strategy_name,
                "strategy_params": request.strategy_params.model_dump(exclude_none=True)
            },
            strategy_metrics=_create_metrics_response(strategy_results),
            baseline_metrics=_create_metrics_response(baseline_results),
            comparison=_create_comparison_response(comparison),
            equity_curve=_create_time_series_data(strategy_results),
            baseline_curve=_create_time_series_data(baseline_results),
            success=True,
            message=f"Backtest completed successfully for {request.ticker}"
        )
        
        logger.info(
            f"Backtest completed: {request.ticker}, "
            f"Strategy Return: {strategy_results.total_return:.2%}, "
            f"Baseline Return: {baseline_results.total_return:.2%}"
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch any unexpected errors
        logger.exception(f"Unexpected error in backtest endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "UnexpectedError",
                "message": "An unexpected error occurred during backtest execution",
                "details": str(e)
            }
        )
