from fastapi import APIRouter
from app.core.config import DefaultConfig
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
config = DefaultConfig()


@router.get("/health")
async def health_check():
    """
    Health Check Endpoint.

    檢查應用程式核心元件的運行狀態。
    """
    from app.bot_instance import GENIE_SERVICE

    checks = {"app": "up"}

    # 檢查 Databricks 連線（GenieService 是否已初始化）
    try:
        if GENIE_SERVICE and GENIE_SERVICE._workspace_client:
            checks["databricks"] = "up"
        else:
            checks["databricks"] = "not_initialized"
    except Exception as e:
        logger.warning(f"Databricks health check failed: {e}")
        checks["databricks"] = "down"

    # 檢查必要配置
    checks["config"] = "ok" if config.DATABRICKS_TOKEN and config.DATABRICKS_HOST else "missing"

    overall = "healthy" if all(
        v in ("up", "ok") for v in checks.values()
    ) else "degraded"

    return {
        "status": overall,
        "checks": checks,
    }


@router.get("/ready")
async def ready_check():
    """
    Readiness Check Endpoint.

    確認應用程式是否準備好接受流量。
    """
    required = {
        "databricks_token": bool(config.DATABRICKS_TOKEN),
        "databricks_host": bool(config.DATABRICKS_HOST),
        "databricks_space_id": bool(config.DATABRICKS_SPACE_ID),
    }

    ready = all(required.values())
    return {
        "status": "ready" if ready else "not_ready",
        "checks": required,
    }
