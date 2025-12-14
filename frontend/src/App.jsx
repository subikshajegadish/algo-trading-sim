import { useState } from 'react';
import './App.css';

function App() {
  const [formData, setFormData] = useState({
    ticker: 'AAPL',
    start_date: '2023-01-01',
    end_date: '2023-12-31',
    initial_capital: 10000,
    strategy_name: 'sma_crossover',
    strategy_params: {
      short_window: 50,
      long_window: 200,
      period: 14,
      buy_threshold: 30,
      sell_threshold: 70,
    },
  });

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleParamChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      strategy_params: {
        ...prev.strategy_params,
        [name]: parseFloat(value) || parseInt(value),
      },
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      // Prepare request payload based on strategy
      const payload = {
        ticker: formData.ticker.toUpperCase(),
        start_date: formData.start_date,
        end_date: formData.end_date,
        initial_capital: parseFloat(formData.initial_capital),
        strategy_name: formData.strategy_name,
        strategy_params: {},
      };

      // Add relevant parameters based on strategy
      if (formData.strategy_name === 'sma_crossover') {
        payload.strategy_params = {
          short_window: parseInt(formData.strategy_params.short_window),
          long_window: parseInt(formData.strategy_params.long_window),
        };
      } else if (formData.strategy_name === 'rsi_mean_reversion') {
        payload.strategy_params = {
          period: parseInt(formData.strategy_params.period),
          buy_threshold: parseFloat(formData.strategy_params.buy_threshold),
          sell_threshold: parseFloat(formData.strategy_params.sell_threshold),
        };
      }

      const response = await fetch('http://localhost:8000/api/v1/backtest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail?.message || 'Backtest failed');
      }

      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const isSMA = formData.strategy_name === 'sma_crossover';
  const isRSI = formData.strategy_name === 'rsi_mean_reversion';

  return (
    <div className="app">
      <div className="container">
        <header>
          <h1>📈 Algorithmic Trading Backtester</h1>
          <p>Test your trading strategies with historical data</p>
        </header>

        <div className="content">
          <div className="form-section">
            <h2>Backtest Configuration</h2>
            <form onSubmit={handleSubmit}>
              {/* Basic Parameters */}
              <div className="form-group">
                <label htmlFor="ticker">Stock Ticker</label>
                <input
                  type="text"
                  id="ticker"
                  name="ticker"
                  value={formData.ticker}
                  onChange={handleInputChange}
                  placeholder="AAPL"
                  required
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="start_date">Start Date</label>
                  <input
                    type="date"
                    id="start_date"
                    name="start_date"
                    value={formData.start_date}
                    onChange={handleInputChange}
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="end_date">End Date</label>
                  <input
                    type="date"
                    id="end_date"
                    name="end_date"
                    value={formData.end_date}
                    onChange={handleInputChange}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="initial_capital">Initial Capital ($)</label>
                <input
                  type="number"
                  id="initial_capital"
                  name="initial_capital"
                  value={formData.initial_capital}
                  onChange={handleInputChange}
                  min="100"
                  max="10000000"
                  step="1000"
                  required
                />
              </div>

              {/* Strategy Selection */}
              <div className="form-group">
                <label htmlFor="strategy_name">Trading Strategy</label>
                <select
                  id="strategy_name"
                  name="strategy_name"
                  value={formData.strategy_name}
                  onChange={handleInputChange}
                  required
                >
                  <option value="sma_crossover">SMA Crossover</option>
                  <option value="rsi_mean_reversion">RSI Mean Reversion</option>
                </select>
              </div>

              {/* Strategy Parameters */}
              <div className="strategy-params">
                <h3>Strategy Parameters</h3>

                {isSMA && (
                  <>
                    <div className="form-row">
                      <div className="form-group">
                        <label htmlFor="short_window">Short Window</label>
                        <input
                          type="number"
                          id="short_window"
                          name="short_window"
                          value={formData.strategy_params.short_window}
                          onChange={handleParamChange}
                          min="1"
                          max="500"
                          required
                        />
                      </div>

                      <div className="form-group">
                        <label htmlFor="long_window">Long Window</label>
                        <input
                          type="number"
                          id="long_window"
                          name="long_window"
                          value={formData.strategy_params.long_window}
                          onChange={handleParamChange}
                          min="2"
                          max="1000"
                          required
                        />
                      </div>
                    </div>
                    <p className="param-hint">
                      Common: 50/200 (standard), 20/50 (fast)
                    </p>
                  </>
                )}

                {isRSI && (
                  <>
                    <div className="form-group">
                      <label htmlFor="period">RSI Period</label>
                      <input
                        type="number"
                        id="period"
                        name="period"
                        value={formData.strategy_params.period}
                        onChange={handleParamChange}
                        min="2"
                        max="100"
                        required
                      />
                    </div>

                    <div className="form-row">
                      <div className="form-group">
                        <label htmlFor="buy_threshold">Buy Threshold</label>
                        <input
                          type="number"
                          id="buy_threshold"
                          name="buy_threshold"
                          value={formData.strategy_params.buy_threshold}
                          onChange={handleParamChange}
                          min="0"
                          max="100"
                          step="5"
                          required
                        />
                      </div>

                      <div className="form-group">
                        <label htmlFor="sell_threshold">Sell Threshold</label>
                        <input
                          type="number"
                          id="sell_threshold"
                          name="sell_threshold"
                          value={formData.strategy_params.sell_threshold}
                          onChange={handleParamChange}
                          min="0"
                          max="100"
                          step="5"
                          required
                        />
                      </div>
                    </div>
                    <p className="param-hint">
                      Common: 30/70 (standard), 20/80 (aggressive)
                    </p>
                  </>
                )}
              </div>

              <button type="submit" className="submit-btn" disabled={loading}>
                {loading ? '⏳ Running Backtest...' : '🚀 Run Backtest'}
              </button>
            </form>
          </div>

          {/* Results Section */}
          {error && (
            <div className="results-section error">
              <h2>❌ Error</h2>
              <p>{error}</p>
            </div>
          )}

          {results && (
            <div className="results-section">
              <h2>📊 Backtest Results</h2>

              <div className="metrics-grid">
                <div className="metric-card">
                  <h3>Strategy Performance</h3>
                  <div className="metric">
                    <span className="label">Total Return</span>
                    <span className={`value ${results.strategy_metrics.total_return >= 0 ? 'positive' : 'negative'}`}>
                      {results.strategy_metrics.total_return_pct}
                    </span>
                  </div>
                  <div className="metric">
                    <span className="label">CAGR</span>
                    <span className="value">{results.strategy_metrics.cagr_pct}</span>
                  </div>
                  <div className="metric">
                    <span className="label">Sharpe Ratio</span>
                    <span className="value">{results.strategy_metrics.sharpe_ratio.toFixed(2)}</span>
                  </div>
                  <div className="metric">
                    <span className="label">Max Drawdown</span>
                    <span className="value negative">{results.strategy_metrics.max_drawdown_pct}</span>
                  </div>
                  <div className="metric">
                    <span className="label">Final Value</span>
                    <span className="value">${results.strategy_metrics.final_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                  </div>
                  <div className="metric">
                    <span className="label">Trades</span>
                    <span className="value">{results.strategy_metrics.num_trades}</span>
                  </div>
                </div>

                <div className="metric-card">
                  <h3>Buy & Hold Baseline</h3>
                  <div className="metric">
                    <span className="label">Total Return</span>
                    <span className={`value ${results.baseline_metrics.total_return >= 0 ? 'positive' : 'negative'}`}>
                      {results.baseline_metrics.total_return_pct}
                    </span>
                  </div>
                  <div className="metric">
                    <span className="label">CAGR</span>
                    <span className="value">{results.baseline_metrics.cagr_pct}</span>
                  </div>
                  <div className="metric">
                    <span className="label">Sharpe Ratio</span>
                    <span className="value">{results.baseline_metrics.sharpe_ratio.toFixed(2)}</span>
                  </div>
                  <div className="metric">
                    <span className="label">Max Drawdown</span>
                    <span className="value negative">{results.baseline_metrics.max_drawdown_pct}</span>
                  </div>
                  <div className="metric">
                    <span className="label">Final Value</span>
                    <span className="value">${results.baseline_metrics.final_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                  </div>
                </div>

                <div className="metric-card comparison">
                  <h3>Comparison</h3>
                  <div className="metric">
                    <span className="label">Excess Return</span>
                    <span className={`value ${results.comparison.excess_return >= 0 ? 'positive' : 'negative'}`}>
                      {results.comparison.excess_return_pct}
                    </span>
                  </div>
                  <div className="metric">
                    <span className="label">Outperformed</span>
                    <span className={`value ${results.comparison.outperformed ? 'positive' : 'negative'}`}>
                      {results.comparison.outperformed ? '✅ Yes' : '❌ No'}
                    </span>
                  </div>
                  <div className="metric">
                    <span className="label">Sharpe Difference</span>
                    <span className={`value ${results.comparison.sharpe_difference >= 0 ? 'positive' : 'negative'}`}>
                      {results.comparison.sharpe_difference.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="equity-curve-placeholder">
                <h3>📈 Equity Curves</h3>
                <p>
                  Strategy has {results.equity_curve.dates.length} data points from{' '}
                  {results.equity_curve.dates[0]} to{' '}
                  {results.equity_curve.dates[results.equity_curve.dates.length - 1]}
                </p>
                <p className="hint">
                  💡 Equity curve visualization can be added with Chart.js or Recharts
                </p>
              </div>
            </div>
          )}
        </div>

        <footer>
          <p>Built with React + Vite | Backend: FastAPI + Python</p>
        </footer>
      </div>
    </div>
  );
}

export default App;
