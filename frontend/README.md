# Algorithmic Trading Backtester - Frontend

A minimal React + Vite frontend for backtesting trading strategies.

## Features

✅ **Single Page Application**
- Clean, modern UI with dark theme
- Responsive design for mobile and desktop

✅ **Form Inputs**
- Stock ticker input
- Date range selection (start/end dates)
- Initial capital input
- Strategy dropdown (SMA Crossover, RSI Mean Reversion)
- Dynamic strategy parameters based on selection

✅ **API Integration**
- Connects to FastAPI backend at `http://localhost:8000`
- Handles loading states
- Displays error messages
- Shows comprehensive results

✅ **Results Display**
- Strategy performance metrics
- Buy-and-hold baseline comparison
- Excess return calculation
- Visual metric cards

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend server running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

## Usage

1. **Enter Stock Ticker**: e.g., AAPL, MSFT, GOOGL
2. **Select Date Range**: Choose start and end dates
3. **Set Initial Capital**: Default is $10,000
4. **Choose Strategy**:
   - **SMA Crossover**: Requires short_window and long_window
   - **RSI Mean Reversion**: Requires period, buy_threshold, sell_threshold
5. **Click "Run Backtest"**: Wait for results
6. **View Results**: See strategy vs baseline performance

## Strategy Parameters

### SMA Crossover
- **Short Window**: 1-500 (default: 50)
- **Long Window**: 2-1000 (default: 200)
- Common configurations: 50/200 (standard), 20/50 (fast)

### RSI Mean Reversion
- **Period**: 2-100 (default: 14)
- **Buy Threshold**: 0-100 (default: 30)
- **Sell Threshold**: 0-100 (default: 70)
- Common configurations: 30/70 (standard), 20/80 (aggressive)

## API Endpoint

The frontend connects to:
```
POST http://localhost:8000/api/v1/backtest
```

### Request Format
```json
{
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
```

### Response Format
```json
{
  "strategy_metrics": {
    "total_return_pct": "9.49%",
    "cagr_pct": "9.64%",
    "sharpe_ratio": 1.31,
    "max_drawdown_pct": "-5.09%",
    "final_value": 10949.16,
    "num_trades": 2
  },
  "baseline_metrics": { ... },
  "comparison": {
    "excess_return_pct": "-44.45%",
    "outperformed": false
  },
  "equity_curve": {
    "dates": [...],
    "values": [...]
  }
}
```

## Project Structure

```
frontend/
├── src/
│   ├── App.jsx          # Main component with form and results
│   ├── App.css          # Component styles
│   ├── index.css        # Global styles
│   └── main.jsx         # Entry point
├── index.html           # HTML template
├── package.json         # Dependencies
└── vite.config.js       # Vite configuration
```

## Technologies

- **React 18**: UI library
- **Vite**: Build tool and dev server
- **Vanilla CSS**: Styling (no framework needed)
- **Fetch API**: HTTP requests

## Future Enhancements

- 📈 Add Chart.js or Recharts for equity curve visualization
- 💾 Save backtest results to local storage
- 📊 Compare multiple strategies side-by-side
- 🎨 Add light/dark theme toggle
- 📱 Improve mobile responsiveness
- ⚡ Add parameter optimization interface
- 📥 Export results as CSV/PDF

## Troubleshooting

### CORS Errors
Make sure the backend has CORS enabled for `http://localhost:5173`:
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Backend Not Running
Ensure the FastAPI backend is running:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Port Already in Use
If port 5173 is in use, Vite will automatically use the next available port.

## License

MIT
