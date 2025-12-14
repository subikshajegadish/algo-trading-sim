"""
Health check endpoint.
"""
from fastapi import APIRouter
from datetime import datetime
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    
    Returns:
        dict: Status information including timestamp and environment
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
    }
