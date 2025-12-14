"""
Quick demo of both strategies.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.market_data import fetch_ohlcv_data
from app.services.strategies import sma_crossover_strategy, rsi_mean_reversion_strategy

print("=" * 70)
print("TRADING STRATEGIES DEMO")
print("=" * 70)

# Fetch data
print("\n📊 Fetching AAPL data for 2023...")
df = fetch_ohlcv_data('AAPL', '2023-01-01', '2023-12-31')
print(f"✅ Fetched {len(df)} days of data")

# Strategy 1: SMA Crossover
print("\n" + "-" * 70)
print("Strategy 1: SMA Crossover (50/200)")
print("-" * 70)

sma_positions = sma_crossover_strategy(df, short_window=50, long_window=200)

print(f"\n📈 Results:")
print(f"   Long positions: {sma_positions.sum()} days ({sma_positions.sum()/len(df)*100:.1f}%)")
print(f"   Flat positions: {(sma_positions==0).sum()} days ({(sma_positions==0).sum()/len(df)*100:.1f}%)")
print(f"   Total trades: {(sma_positions.diff() != 0).sum()}")

# Strategy 2: RSI Mean Reversion
print("\n" + "-" * 70)
print("Strategy 2: RSI Mean Reversion (14, 30/70)")
print("-" * 70)

rsi_positions = rsi_mean_reversion_strategy(df, period=14, buy_threshold=30, sell_threshold=70)

print(f"\n📉 Results:")
print(f"   Long positions: {rsi_positions.sum()} days ({rsi_positions.sum()/len(df)*100:.1f}%)")
print(f"   Flat positions: {(rsi_positions==0).sum()} days ({(rsi_positions==0).sum()/len(df)*100:.1f}%)")
print(f"   Total trades: {(rsi_positions.diff() != 0).sum()}")

# Comparison
print("\n" + "-" * 70)
print("Strategy Comparison")
print("-" * 70)

both_long = ((sma_positions == 1) & (rsi_positions == 1)).sum()
both_flat = ((sma_positions == 0) & (rsi_positions == 0)).sum()
agreement = both_long + both_flat

print(f"\n🔄 Agreement:")
print(f"   Both long: {both_long} days")
print(f"   Both flat: {both_flat} days")
print(f"   Total agreement: {agreement}/{len(df)} days ({agreement/len(df)*100:.1f}%)")

# Sample output
print("\n" + "-" * 70)
print("Sample Positions (Last 5 Days)")
print("-" * 70)

comparison = df[['Close']].copy()
comparison['SMA_Pos'] = sma_positions
comparison['RSI_Pos'] = rsi_positions
print(f"\n{comparison.tail()}")

print("\n" + "=" * 70)
print("✅ Demo Complete!")
print("=" * 70)
