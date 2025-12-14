"""
Complete example: Fetch data, apply strategy, run backtest, compare to baseline.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.market_data import fetch_ohlcv_data
from app.services.strategies import sma_crossover_strategy, rsi_mean_reversion_strategy
from app.services.backtest import (
    run_backtest,
    run_buy_and_hold,
    compare_to_baseline,
    calculate_portfolio_stats
)

print("=" * 80)
print("COMPLETE BACKTESTING EXAMPLE")
print("=" * 80)

# Step 1: Fetch historical data
print("\n📊 Step 1: Fetching AAPL data for 2023...")
df = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-12-31')
print(f"✅ Fetched {len(df)} days of data")
print(f"   Price range: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")

# Step 2: Apply SMA Crossover Strategy
print("\n" + "-" * 80)
print("📈 Step 2: Applying SMA Crossover Strategy (50/200)")
print("-" * 80)

sma_positions = sma_crossover_strategy(df, short_window=50, long_window=200)
print(f"✅ Generated {len(sma_positions)} position signals")
print(f"   Long positions: {sma_positions.sum()} days ({sma_positions.sum()/len(df)*100:.1f}%)")

# Step 3: Run backtest
print("\n💰 Step 3: Running backtest with $10,000 initial capital...")

sma_results = run_backtest(
    prices=df['Close'],
    positions=sma_positions,
    initial_capital=10000
)

print("\n📊 SMA Crossover Results:")
print(sma_results)

# Step 4: Run buy-and-hold baseline
print("\n" + "-" * 80)
print("📊 Step 4: Running Buy-and-Hold Baseline")
print("-" * 80)

baseline_results = run_buy_and_hold(
    prices=df['Close'],
    initial_capital=10000
)

print("\n📊 Buy-and-Hold Results:")
print(baseline_results)

# Step 5: Compare to baseline
print("\n" + "-" * 80)
print("🔄 Step 5: Comparing Strategy to Baseline")
print("-" * 80)

comparison = compare_to_baseline(sma_results, baseline_results)

print(f"\n📈 Performance Comparison:")
print(f"   Strategy Return:  {comparison['strategy_total_return']:>8.2%}")
print(f"   Baseline Return:  {comparison['baseline_total_return']:>8.2%}")
print(f"   Excess Return:    {comparison['excess_return']:>8.2%}")
print(f"")
print(f"   Strategy Sharpe:  {comparison['strategy_sharpe']:>8.2f}")
print(f"   Baseline Sharpe:  {comparison['baseline_sharpe']:>8.2f}")
print(f"   Sharpe Diff:      {comparison['sharpe_difference']:>8.2f}")

if comparison['excess_return'] > 0:
    print(f"\n✅ Strategy OUTPERFORMED baseline by {comparison['excess_return']:.2%}")
else:
    print(f"\n❌ Strategy UNDERPERFORMED baseline by {abs(comparison['excess_return']):.2%}")

# Step 6: Detailed statistics
print("\n" + "-" * 80)
print("📊 Step 6: Detailed Portfolio Statistics")
print("-" * 80)

stats = calculate_portfolio_stats(sma_results)
print("\n" + str(stats))

# Step 7: Try RSI strategy
print("\n" + "=" * 80)
print("🔄 BONUS: RSI Mean Reversion Strategy")
print("=" * 80)

rsi_positions = rsi_mean_reversion_strategy(df, period=14, buy_threshold=30, sell_threshold=70)
rsi_results = run_backtest(df['Close'], rsi_positions, initial_capital=10000)

print("\n📊 RSI Strategy Results:")
print(rsi_results)

rsi_comparison = compare_to_baseline(rsi_results, baseline_results)

print(f"\n📈 RSI vs Baseline:")
print(f"   Strategy Return:  {rsi_comparison['strategy_total_return']:>8.2%}")
print(f"   Baseline Return:  {rsi_comparison['baseline_total_return']:>8.2%}")
print(f"   Excess Return:    {rsi_comparison['excess_return']:>8.2%}")

# Step 8: Compare both strategies
print("\n" + "=" * 80)
print("🏆 Strategy Comparison Summary")
print("=" * 80)

print(f"\n{'Metric':<20} {'SMA Crossover':>15} {'RSI Mean Rev':>15} {'Buy & Hold':>15}")
print("-" * 68)
print(f"{'Total Return':<20} {sma_results.total_return:>14.2%} {rsi_results.total_return:>14.2%} {baseline_results.total_return:>14.2%}")
print(f"{'CAGR':<20} {sma_results.cagr:>14.2%} {rsi_results.cagr:>14.2%} {baseline_results.cagr:>14.2%}")
print(f"{'Sharpe Ratio':<20} {sma_results.sharpe_ratio:>14.2f} {rsi_results.sharpe_ratio:>14.2f} {baseline_results.sharpe_ratio:>14.2f}")
print(f"{'Max Drawdown':<20} {sma_results.max_drawdown:>14.2%} {rsi_results.max_drawdown:>14.2%} {baseline_results.max_drawdown:>14.2%}")
print(f"{'Final Value':<20} ${sma_results.final_value:>13,.2f} ${rsi_results.final_value:>13,.2f} ${baseline_results.final_value:>13,.2f}")
print(f"{'Num Trades':<20} {sma_results.num_trades:>14} {rsi_results.num_trades:>14} {baseline_results.num_trades:>14}")

# Determine winner
strategies = [
    ('SMA Crossover', sma_results.total_return),
    ('RSI Mean Reversion', rsi_results.total_return),
    ('Buy & Hold', baseline_results.total_return)
]
winner = max(strategies, key=lambda x: x[1])

print(f"\n🏆 Best Strategy: {winner[0]} with {winner[1]:.2%} return")

print("\n" + "=" * 80)
print("✅ Complete Backtest Example Finished!")
print("=" * 80)
