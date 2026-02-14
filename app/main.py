from fastapi import FastAPI, Request
import logging
from app.core.config import DefaultConfig
from app.api.bot import router as bot_router
from app.api.genie import router as genie_router
from app.api.health import router as health_router
from app.api.m365_agent import router as m365_router

# 初始化配置
CONFIG = DefaultConfig()

# 配置日誌
log_level = logging.DEBUG if CONFIG.VERBOSE_LOGGING else logging.INFO
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

logging.basicConfig(
    level=log_level,
    format=log_format,
    handlers=[
        logging.StreamHandler(),  # 控制台輸出
        logging.FileHandler(CONFIG.LOG_FILE, encoding='utf-8')  # 文件輸出
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"🔍 日誌級別設置為: {logging.getLevelName(log_level)}")
logger.info(f"📄 日誌文件: {CONFIG.LOG_FILE}")

app = FastAPI(
    title="Databricks Genie Bot API",
    description="API for accessing Genie Service and Bot Framework integration with Microsoft 365 Agent Framework.",
    version="1.0.0",
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("HTTP %s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("HTTP %s %s -> %s", request.method, request.url.path, response.status_code)
    return response

# Include Routers
app.include_router(health_router, prefix="", tags=["health"])
app.include_router(bot_router, prefix="/api", tags=["bot"])
app.include_router(genie_router, prefix="/api/genie", tags=["genie"])
app.include_router(m365_router, prefix="/api", tags=["m365-agent"])


@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "Databricks Genie Bot",
        "docs": "/docs"
    }
