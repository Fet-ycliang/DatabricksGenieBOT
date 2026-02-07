from fastapi import APIRouter, Depends
from app.core.config import DefaultConfig
from app.services.genie import GenieService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
config = DefaultConfig()

@router.get("/health")
async def health_check():
    """
    Health Check Endpoint.
    """
    return {
        "status": "healthy",
        "checks": {
            "app": "up",
            "database": "unknown" # Implement actual check
        }
    }

@router.get("/ready")
async def ready_check():
    """
    Readiness Check Endpoint.
    """
    return {"status": "ready"}
