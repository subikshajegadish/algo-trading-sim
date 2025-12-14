# Algo Trading Simulator - Backend API

FastAPI backend for the Algorithmic Trading Strategy Simulator.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip

### Installation

1. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run the development server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Configuration management
│   └── api/
│       ├── __init__.py
│       └── v1/
│           ├── __init__.py
│           ├── router.py       # API v1 router
│           └── endpoints/
│               ├── __init__.py
│               └── health.py   # Health check endpoint
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🔌 API Endpoints

### Health Check
- **GET** `/api/v1/health`
  - Returns API health status, timestamp, and version

### Root
- **GET** `/`
  - Returns welcome message and API information

## 🛠️ Development

### Running Tests
```bash
# Install test dependencies first
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Formatting
```bash
# Install formatting tools
pip install black isort

# Format code
black app/
isort app/
```

## 🔧 Configuration

Configuration is managed through environment variables. See `.env.example` for available options:

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `ENVIRONMENT`: Environment name (development/production)
- `CORS_ORIGINS`: Comma-separated list of allowed origins
- `API_V1_PREFIX`: API v1 prefix (default: /api/v1)

## 📝 Next Steps

Future endpoints to implement (per MVP requirements):
- `POST /api/v1/backtest` - Run backtest with strategy and parameters
- `GET /api/v1/strategies` - List available trading strategies

## 🤝 Contributing

Follow these best practices:
- Keep code simple and readable
- Add docstrings to all functions
- Use type hints
- Follow PEP 8 style guide
- Write tests for new features

## 📄 License

MIT
