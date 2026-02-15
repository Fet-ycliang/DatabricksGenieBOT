from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging
from app.core.config import DefaultConfig
from app.core.exceptions import BotException
from app.core.logging_middleware import RequestLoggingMiddleware, get_request_id
from app.api.bot import router as bot_router
from app.api.genie import router as genie_router
from app.api.health import router as health_router

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命週期管理

    負責啟動和關閉應用程式資源：
    - SessionManager: 自動清理過期 sessions
    - GenieService: HTTP 連接池管理
    """
    # Import here to avoid circular dependency
    from app.bot_instance import SESSION_MANAGER, GENIE_SERVICE

    logger.info("========================================")
    logger.info("應用程式啟動中...")
    logger.info("========================================")

    # 啟動 SessionManager
    try:
        await SESSION_MANAGER.start()
        logger.info("✅ SessionManager 已啟動")
    except Exception as e:
        logger.error(f"❌ SessionManager 啟動失敗: {e}")

    logger.info("========================================")
    logger.info("應用程式已就緒")
    logger.info("========================================")

    yield  # 應用程式運行中

    # 關閉資源
    logger.info("========================================")
    logger.info("應用程式關閉中...")
    logger.info("========================================")

    # 停止 SessionManager
    try:
        await SESSION_MANAGER.stop()
        logger.info("✅ SessionManager 已停止")
    except Exception as e:
        logger.error(f"❌ SessionManager 停止失敗: {e}")

    # 關閉 GenieService HTTP Session
    try:
        await GENIE_SERVICE.close()
        logger.info("✅ GenieService HTTP Session 已關閉")
    except Exception as e:
        logger.error(f"❌ GenieService 關閉失敗: {e}")

    logger.info("========================================")
    logger.info("應用程式已關閉")
    logger.info("========================================")


app = FastAPI(
    title="Databricks Genie Bot API",
    description="API for accessing Genie Service and Bot Framework integration with Microsoft 365 Agent Framework.",
    version="1.0.0",
    lifespan=lifespan,
)


# ==================== 全域異常處理器 ====================


@app.exception_handler(BotException)
async def bot_exception_handler(request: Request, exc: BotException):
    """處理應用程式自定義異常"""
    request_id = get_request_id(request)

    logger.error(
        f"[{request_id}] BotException: {exc.code.value} - {exc.message} | "
        f"Path: {request.url.path} | "
        f"Details: {exc.details}"
    )

    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.code.value,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path,
            "request_id": request_id,
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """處理 HTTP 異常（包含 FastAPI HTTPException）"""
    request_id = get_request_id(request)

    logger.warning(
        f"[{request_id}] HTTPException: {exc.status_code} - {exc.detail} | "
        f"Path: {request.url.path}"
    )

    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": f"HTTP_{exc.status_code}",
            "message": exc.detail if isinstance(exc.detail, str) else "HTTP錯誤",
            "details": {},
            "path": request.url.path,
            "request_id": request_id,
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """處理請求驗證錯誤（Pydantic 驗證）"""
    request_id = get_request_id(request)

    logger.warning(
        f"[{request_id}] ValidationError: {exc.errors()} | "
        f"Path: {request.url.path}"
    )

    response = JSONResponse(
        status_code=400,
        content={
            "error_code": "INPUT_001",
            "message": "請求驗證失敗",
            "details": {
                "errors": exc.errors(),
            },
            "path": request.url.path,
            "request_id": request_id,
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """處理所有未捕獲的異常"""
    request_id = get_request_id(request)

    logger.error(
        f"[{request_id}] UnhandledException: {type(exc).__name__} - {str(exc)} | "
        f"Path: {request.url.path}",
        exc_info=True,
    )

    # 不洩漏內部錯誤細節
    response = JSONResponse(
        status_code=500,
        content={
            "error_code": "SYSTEM_001",
            "message": "系統內部錯誤，請稍後再試",
            "details": {},
            "path": request.url.path,
            "request_id": request_id,
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


# ==================== 中介軟體 ====================

# 加入請求日誌中介軟體（包含 request_id 追蹤）
app.add_middleware(RequestLoggingMiddleware)

# Include Routers
app.include_router(health_router, prefix="", tags=["health"])
app.include_router(bot_router, prefix="/api", tags=["bot"])
app.include_router(genie_router, prefix="/api/genie", tags=["genie"])


@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "Databricks Genie Bot",
        "docs": "/docs"
    }
