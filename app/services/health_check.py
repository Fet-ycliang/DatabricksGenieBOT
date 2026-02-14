"""
Azure Web App Health Check Configuration

此模組提供應用程式健康檢查和就緒狀態檢查的配置。
用於 Azure App Service 監控和自動復原。

參考：
https://learn.microsoft.com/azure/app-service/monitor-instances-health-check
https://docs.microsoft.com/azure/architecture/patterns/health-endpoint-monitoring
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import Request
from fastapi.responses import JSONResponse

from app.services.genie import GenieService
from app.services.graph import GraphService
# from app.core.adapter import ADAPTER # If needed


class HealthCheckStatus:
    """應用程式健康狀態的列舉值"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class ComponentStatus:
    """元件狀態的列舉值"""
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"
    NOT_CHECKED = "not_checked"
    NOT_CONFIGURED = "not_configured"


class HealthCheckResponse:
    """健康檢查回應的資料模型"""
    
    def __init__(self, status: str, timestamp: Optional[datetime] = None):
        self.status = status
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.checks: Dict[str, Dict[str, Any]] = {}
        self.error: Optional[str] = None
    
    def add_check(self, name: str, component_status: str, details: Optional[Dict] = None):
        """添加單一檢查結果"""
        self.checks[name] = {
            "status": component_status,
            "details": details or {}
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "checks": self.checks,
            "error": self.error
        }


class ReadyCheckResponse:
    """就緒狀態檢查回應的資料模型"""
    
    def __init__(self, ready: bool, timestamp: Optional[datetime] = None):
        self.ready = ready
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.checks: Dict[str, bool] = {}
        self.error: Optional[str] = None
    
    def add_check(self, name: str, is_ready: bool):
        """添加單一就緒狀態檢查"""
        self.checks[name] = is_ready
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ready": self.ready,
            "timestamp": self.timestamp.isoformat(),
            "configuration_checks": self.checks,
            "error": self.error
        }


def create_health_check_handler(
    dependencies: Optional[Dict[str, Any]] = None
):
    """
    創建健康檢查處理程式工廠
    
    參數：
        dependencies: 包含要檢查的依賴項的字典
            - genie_service: GenieService 實例
            - graph_service: GraphService 實例
            - adapter: BotFrameworkAdapter 實例
    
    返回：
        健康檢查的處理程式函數
    """
    dependencies = dependencies or {}
    
    async def health_check(req: Request) -> web.Response:
        """
        健康檢查端點
        
        用於 Azure App Service 監控應用程式的健康狀態。
        Azure 會根據此端點的回應決定是否重啟實例。
        
        返回：
        - 200: 應用程式運行正常
        - 503: 應用程式異常
        """
        try:
            response = HealthCheckResponse(HealthCheckStatus.HEALTHY)
            
            # 應用程式基本狀態
            response.add_check("app", ComponentStatus.UP, {"message": "application running"})
            
            # 檢查 Databricks 連接
            genie_service = dependencies.get("genie_service")
            try:
                if genie_service and hasattr(genie_service, 'client') and genie_service.client:
                    response.add_check("databricks", ComponentStatus.UP, {
                        "message": "Databricks client initialized",
                        "space_id": genie_service.space_id if hasattr(genie_service, 'space_id') else "unknown"
                    })
                else:
                    response.add_check("databricks", ComponentStatus.UNKNOWN, {
                        "message": "Databricks client not fully initialized"
                    })
            except Exception as e:
                logger.warning(f"Databricks health check failed: {str(e)}")
                response.add_check("databricks", ComponentStatus.DOWN, {
                    "error": str(e)
                })
            
            # 檢查 Graph API 連接
            graph_service = dependencies.get("graph_service")
            try:
                if graph_service and hasattr(graph_service, 'client_id') and graph_service.client_id:
                    response.add_check("graph_api", ComponentStatus.UP, {
                        "message": "Graph API configured",
                        "client_id": graph_service.client_id[:8] + "..." if graph_service.client_id else "unknown"
                    })
                else:
                    response.add_check("graph_api", ComponentStatus.NOT_CONFIGURED, {
                        "message": "Graph API not configured"
                    })
            except Exception as e:
                logger.warning(f"Graph API health check failed: {str(e)}")
                response.add_check("graph_api", ComponentStatus.DOWN, {
                    "error": str(e)
                })
            
            # 檢查 BotFrameworkAdapter
            adapter = dependencies.get("adapter")
            try:
                if adapter:
                    response.add_check("bot_adapter", ComponentStatus.UP, {
                        "message": "BotFrameworkAdapter initialized"
                    })
                else:
                    response.add_check("bot_adapter", ComponentStatus.DOWN, {
                        "message": "BotFrameworkAdapter not initialized"
                    })
            except Exception as e:
                logger.warning(f"Bot adapter health check failed: {str(e)}")
                response.add_check("bot_adapter", ComponentStatus.DOWN, {
                    "error": str(e)
                })
            
            # 如果有任何服務異常，標記為降級
            down_services = [
                check for check, details in response.checks.items()
                if details.get("status") == ComponentStatus.DOWN
            ]
            if down_services:
                response.status = HealthCheckStatus.DEGRADED
            
            status_code = 200 if response.status != HealthCheckStatus.UNHEALTHY else 503
            return json_response(data=response.to_dict(), status=status_code)
            
        except Exception as e:
            logger.error(f"Health check failed with exception: {str(e)}")
            error_response = HealthCheckResponse(HealthCheckStatus.UNHEALTHY)
            error_response.error = str(e)
            return json_response(data=error_response.to_dict(), status=503)
    
    return health_check


def create_ready_check_handler(
    config: Optional[Any] = None,
    dependencies: Optional[Dict[str, Any]] = None
):
    """
    創建就緒狀態檢查處理程式工廠
    
    參數：
        config: 應用程式配置物件
        dependencies: 包含要檢查的依賴項的字典
    
    返回：
        就緒狀態檢查的處理程式函數
    """
    config = config or {}
    dependencies = dependencies or {}
    
    async def ready_check(req: Request) -> web.Response:
        """
        應用程式就緒狀態檢查端點
        
        檢查應用程式是否準備好接收流量。
        在應用程式啟動階段調用。
        
        返回：
        - 200: 應用程式已就緒
        - 503: 應用程式尚未就緒
        """
        try:
            response = ReadyCheckResponse(ready=True)
            
            # 檢查必要的環境配置
            required_checks = {
                "app_id": bool(getattr(config, 'APP_ID', None)),
                "databricks_token": bool(getattr(config, 'DATABRICKS_TOKEN', None)),
                "databricks_host": bool(getattr(config, 'DATABRICKS_HOST', None)),
                "databricks_space_id": bool(getattr(config, 'DATABRICKS_SPACE_ID', None)),
                "app_password": bool(getattr(config, 'APP_PASSWORD', None)),
            }
            
            for check_name, is_ready in required_checks.items():
                response.add_check(check_name, is_ready)
            
            response.ready = all(required_checks.values())
            
            # 檢查重要依賴項是否初始化
            if response.ready:
                genie_service = dependencies.get("genie_service")
                if genie_service and hasattr(genie_service, 'client') and not genie_service.client:
                    response.ready = False
            
            status_code = 200 if response.ready else 503
            return json_response(data=response.to_dict(), status=status_code)
            
        except Exception as e:
            logger.error(f"Ready check failed with exception: {str(e)}")
            response = ReadyCheckResponse(ready=False)
            response.error = str(e)
            return JSONResponse(response.to_dict(), status_code=503)
    
    return ready_check


def register_health_check_routes(app, handlers: Dict[str, Any]):
    """
    向應用程式註冊健康檢查路由
    
    參數：
        app: FastAPI 應用程式實例
        handlers: 包含 'health_check' 和 'ready_check' 處理程式的字典
    """
    if "health_check" in handlers:
        app.add_route("/health", handlers["health_check"], methods=["GET"])
        logger.info("Registered health check route: GET /health")
    
    if "ready_check" in handlers:
        app.add_route("/ready", handlers["ready_check"], methods=["GET"])
        logger.info("Registered ready check route: GET /ready")
    
    # 也可以添加到根路徑作為心跳檢查
    async def heartbeat(req: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})
    
    app.add_route("/", heartbeat, methods=["GET"])
