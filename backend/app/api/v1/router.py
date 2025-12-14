"""
API v1 router aggregating all endpoint routers.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import health, backtest

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(backtest.router, tags=["backtest"])
