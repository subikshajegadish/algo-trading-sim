"""
Example usage of trading strategies.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.market_data import fetch_ohlcv_data
from app.services.strategies import (
    sma_crossover_strategy,
    rsi_mean_reversion_strategy,
    get_strategy_info,
    list_available_strategies,
    _calculate_rsi
)
import pandas as pd


def example_sma_crossover():
    """Example: SMA Crossover Strategy."""
    print("=" * 70)
    print("Example 1: SMA Crossover Strategy")
    print("=" * 70)
    
    # Fetch historical data
    print("\nFetching AAPL data for 2023...")
    df = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-12-31')
    
    # Apply SMA crossover strategy
    print("\nApplying SMA Crossover (50/200)...")
    positions = sma_crossover_strategy(
        df,
        short_window=50,
        long_window=200
    )
    
    # Calculate SMAs for visualization
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    df['Position'] = positions
    
    # Statistics
    total_days = len(positions)
    long_days = positions.sum()
    flat_days = total_days - long_days
    
    print(f"\nStrategy Statistics:")
    print(f"  Total trading days: {total_days}")
    print(f"  Long position days: {long_days} ({long_days/total_days*100:.1f}%)")
    print(f"  Flat position days: {flat_days} ({flat_days/total_days*100:.1f}%)")
    
    # Show position changes (signals)
    position_changes = positions.diff()
    buy_signals = (position_changes == 1).sum()
    sell_signals = (position_changes == -1).sum()
    
    print(f"\nTrading Signals:")
    print(f"  Buy signals (enter long): {buy_signals}")
    print(f"  Sell signals (exit long): {sell_signals}")
    
    # Show sample data
    print(f"\nSample data (last 10 days):")
    print(df[['Close', 'SMA_50', 'SMA_200', 'Position']].tail(10))
    
    return df


def example_rsi_mean_reversion():
    """Example: RSI Mean Reversion Strategy."""
    print("\n" + "=" * 70)
    print("Example 2: RSI Mean Reversion Strategy")
    print("=" * 70)
    
    # Fetch historical data
    print("\nFetching MSFT data for 2023...")
    df = fetch_ohlcv_data('MSFT', '2023-01-01', '2023-12-31')
    
    # Apply RSI mean reversion strategy
    print("\nApplying RSI Mean Reversion (period=14, buy=30, sell=70)...")
    positions = rsi_mean_reversion_strategy(
        df,
        period=14,
        buy_threshold=30,
        sell_threshold=70
    )
    
    # Calculate RSI for visualization
    df['RSI'] = _calculate_rsi(df['Close'], period=14)
    df['Position'] = positions
    
    # Statistics
    total_days = len(positions)
    long_days = positions.sum()
    flat_days = total_days - long_days
    
    print(f"\nStrategy Statistics:")
    print(f"  Total trading days: {total_days}")
    print(f"  Long position days: {long_days} ({long_days/total_days*100:.1f}%)")
    print(f"  Flat position days: {flat_days} ({flat_days/total_days*100:.1f}%)")
    
    # Show position changes (signals)
    position_changes = positions.diff()
    buy_signals = (position_changes == 1).sum()
    sell_signals = (position_changes == -1).sum()
    
    print(f"\nTrading Signals:")
    print(f"  Buy signals (RSI < 30): {buy_signals}")
    print(f"  Sell signals (RSI >= 70): {sell_signals}")
    
    # RSI statistics
    print(f"\nRSI Statistics:")
    print(f"  Mean RSI: {df['RSI'].mean():.2f}")
    print(f"  Min RSI: {df['RSI'].min():.2f}")
    print(f"  Max RSI: {df['RSI'].max():.2f}")
    print(f"  Days oversold (RSI < 30): {(df['RSI'] < 30).sum()}")
    print(f"  Days overbought (RSI > 70): {(df['RSI'] > 70).sum()}")
    
    # Show sample data
    print(f"\nSample data (last 10 days):")
    print(df[['Close', 'RSI', 'Position']].tail(10))
    
    return df


def example_strategy_comparison():
    """Example: Compare both strategies on same data."""
    print("\n" + "=" * 70)
    print("Example 3: Strategy Comparison")
    print("=" * 70)
    
    # Fetch historical data
    print("\nFetching GOOGL data for 2023...")
    df = fetch_ohlcv_data('GOOGL', '2023-01-01', '2023-12-31')
    
    # Apply both strategies
    print("\nApplying both strategies...")
    sma_positions = sma_crossover_strategy(df, short_window=50, long_window=200)
    rsi_positions = rsi_mean_reversion_strategy(df, period=14)
    
    df['SMA_Position'] = sma_positions
    df['RSI_Position'] = rsi_positions
    
    # Compare statistics
    print(f"\nComparison:")
    print(f"  SMA Crossover - Long: {sma_positions.sum()} days ({sma_positions.sum()/len(df)*100:.1f}%)")
    print(f"  RSI Mean Rev  - Long: {rsi_positions.sum()} days ({rsi_positions.sum()/len(df)*100:.1f}%)")
    
    # Agreement analysis
    both_long = ((sma_positions == 1) & (rsi_positions == 1)).sum()
    both_flat = ((sma_positions == 0) & (rsi_positions == 0)).sum()
    agreement = both_long + both_flat
    
    print(f"\nAgreement Analysis:")
    print(f"  Both long: {both_long} days")
    print(f"  Both flat: {both_flat} days")
    print(f"  Agreement: {agreement}/{len(df)} days ({agreement/len(df)*100:.1f}%)")
    print(f"  Disagreement: {len(df) - agreement} days ({(len(df) - agreement)/len(df)*100:.1f}%)")
    
    return df


def example_custom_parameters():
    """Example: Using custom strategy parameters."""
    print("\n" + "=" * 70)
    print("Example 4: Custom Strategy Parameters")
    print("=" * 70)
    
    # Fetch historical data
    df = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-12-31')
    
    # Test different SMA windows
    print("\nTesting different SMA windows:")
    
    configs = [
        (20, 50, "Fast (20/50)"),
        (50, 200, "Standard (50/200)"),
        (100, 300, "Slow (100/300) - will fail due to insufficient data")
    ]
    
    for short, long, label in configs:
        try:
            positions = sma_crossover_strategy(df, short_window=short, long_window=long)
            long_pct = positions.sum() / len(positions) * 100
            print(f"  {label}: {positions.sum()} long days ({long_pct:.1f}%)")
        except Exception as e:
            print(f"  {label}: Error - {e}")
    
    # Test different RSI thresholds
    print("\nTesting different RSI thresholds:")
    
    rsi_configs = [
        (20, 80, "Aggressive (20/80)"),
        (30, 70, "Standard (30/70)"),
        (40, 60, "Conservative (40/60)")
    ]
    
    for buy, sell, label in rsi_configs:
        positions = rsi_mean_reversion_strategy(
            df,
            period=14,
            buy_threshold=buy,
            sell_threshold=sell
        )
        long_pct = positions.sum() / len(positions) * 100
        signals = (positions.diff() == 1).sum()
        print(f"  {label}: {positions.sum()} long days ({long_pct:.1f}%), {signals} trades")


def example_strategy_info():
    """Example: Get strategy information."""
    print("\n" + "=" * 70)
    print("Example 5: Strategy Information")
    print("=" * 70)
    
    # List available strategies
    strategies = list_available_strategies()
    print(f"\nAvailable strategies: {strategies}")
    
    # Get detailed info for each strategy
    for strategy_name in strategies:
        info = get_strategy_info(strategy_name)
        
        print(f"\n{'-' * 70}")
        print(f"Strategy: {info['name']}")
        print(f"Type: {info['type']}")
        print(f"Description: {info['description']}")
        print(f"Best for: {info['best_for']}")
        print(f"\nParameters:")
        
        for param_name, param_info in info['parameters'].items():
            print(f"  - {param_name} ({param_info['type']}): {param_info['description']}")
            print(f"    Default: {param_info['default']}")


def example_visualization():
    """Example: Visualize strategy signals (requires matplotlib)."""
    print("\n" + "=" * 70)
    print("Example 6: Strategy Visualization")
    print("=" * 70)
    
    try:
        import matplotlib.pyplot as plt
        
        # Fetch data
        print("\nFetching data and generating signals...")
        df = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-12-31')
        
        # Apply SMA strategy
        positions = sma_crossover_strategy(df, short_window=50, long_window=200)
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['Position'] = positions
        
        # Create visualization
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
        
        # Plot 1: Price and SMAs
        ax1.plot(df.index, df['Close'], label='Close Price', linewidth=1.5)
        ax1.plot(df.index, df['SMA_50'], label='SMA 50', linewidth=1, alpha=0.7)
        ax1.plot(df.index, df['SMA_200'], label='SMA 200', linewidth=1, alpha=0.7)
        
        # Highlight long positions
        long_periods = df[df['Position'] == 1].index
        for date in long_periods:
            ax1.axvspan(date, date, alpha=0.1, color='green')
        
        ax1.set_ylabel('Price ($)')
        ax1.set_title('AAPL - SMA Crossover Strategy (50/200)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Position signals
        ax2.fill_between(df.index, 0, df['Position'], alpha=0.3, color='green', label='Long Position')
        ax2.set_ylabel('Position')
        ax2.set_xlabel('Date')
        ax2.set_ylim(-0.1, 1.1)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        output_file = 'strategy_visualization.png'
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"\nVisualization saved to: {output_file}")
        
        # Don't display in non-interactive mode
        # plt.show()
        
    except ImportError:
        print("\nMatplotlib not installed. Skipping visualization.")
    except Exception as e:
        print(f"\nError creating visualization: {e}")


if __name__ == '__main__':
    # Run all examples
    example_sma_crossover()
    example_rsi_mean_reversion()
    example_strategy_comparison()
    example_custom_parameters()
    example_strategy_info()
    example_visualization()
    
    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)
