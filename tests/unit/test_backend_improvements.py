"""
測試後端 Code Review 改善項目

驗證 Phase 1-3 的所有修復是否正確：
- Config 修復 (A2, A3)
- Import 清理 (A4)
- Card version 一致性 (A5)
- 安全性修復 (B1, B2)
- JWKS client 快取 (B3)
- HTTP session race condition 保護 (C2)
- 死碼移除 (A1, D1)
- Suggested questions 提取 (D2)
- AuthenticationError 移除 (D3)
- Health check 改善 (E1)
"""

import ast
import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))


# ── A2: Config 重複 APP_TYPE 已移除 ──

def test_config_no_duplicate_app_type():
    """APP_TYPE 不應重複定義"""
    config_path = os.path.join(os.path.dirname(__file__), "../../app/core/config.py")
    with open(config_path, encoding="utf-8") as f:
        content = f.read()
    count = content.count("APP_TYPE = os.getenv")
    assert count == 1, f"APP_TYPE 定義了 {count} 次，應該只有 1 次"


# ── A3: ENABLE_GRAPH_API_AUTO_LOGIN 存在於 config ──

def test_config_has_enable_graph_api_auto_login():
    """ENABLE_GRAPH_API_AUTO_LOGIN 應在 DefaultConfig 中定義"""
    from app.core.config import DefaultConfig
    config = DefaultConfig()
    assert hasattr(config, "ENABLE_GRAPH_API_AUTO_LOGIN")
    assert isinstance(config.ENABLE_GRAPH_API_AUTO_LOGIN, bool)


# ── A4: genie.py 不含未使用的 import ──

def test_genie_no_unused_imports():
    """genie.py 不應包含 io、base64 或重複的 import"""
    genie_path = os.path.join(os.path.dirname(__file__), "../../app/services/genie.py")
    with open(genie_path, encoding="utf-8") as f:
        content = f.read()
    assert "import io" not in content
    assert "import base64" not in content
    # 確認 WorkspaceClient 只 import 一次
    assert content.count("from databricks.sdk import WorkspaceClient") == 1


# ── A5: Graph service card version 使用常數 ──

def test_graph_card_version_uses_constant():
    """GraphService.create_user_profile_card 應使用 ADAPTIVE_CARD_VERSION"""
    from app.services.graph import GraphService
    from bot.cards.constants import ADAPTIVE_CARD_VERSION
    card = GraphService.create_user_profile_card({"displayName": "Test"})
    assert card["version"] == ADAPTIVE_CARD_VERSION


# ── B1: ChatRequest 不再含 space_id ──

def test_chat_request_no_space_id():
    """ChatRequest 不應有 space_id 欄位"""
    from app.api.genie import ChatRequest
    fields = ChatRequest.model_fields
    assert "space_id" not in fields


# ── B3: PyJWKClient 快取 ──

def test_jwks_client_is_cached():
    """同一個 tenant_id 應返回同一個 PyJWKClient 實例"""
    from app.core.auth_middleware import _get_jwks_client, _jwks_client_cache
    _jwks_client_cache.clear()  # 清理測試狀態
    client1 = _get_jwks_client("test-tenant-123")
    client2 = _get_jwks_client("test-tenant-123")
    assert client1 is client2
    _jwks_client_cache.clear()  # 清理


# ── C2: HTTP session 有 asyncio.Lock 保護 ──

def test_genie_service_has_http_session_lock():
    """GenieService 應有 _http_session_lock"""
    import asyncio
    genie_path = os.path.join(os.path.dirname(__file__), "../../app/services/genie.py")
    with open(genie_path, encoding="utf-8") as f:
        content = f.read()
    assert "_http_session_lock = asyncio.Lock()" in content


# ── D1: process_query_results 已移除 ──

def test_no_process_query_results():
    """process_query_results 不應存在於 genie.py"""
    genie_path = os.path.join(os.path.dirname(__file__), "../../app/services/genie.py")
    with open(genie_path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    func_names = [
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    assert "process_query_results" not in func_names


# ── D2: _extract_suggested_questions helper 存在 ──

def test_extract_suggested_questions_exists():
    """GenieService 應有 _extract_suggested_questions 靜態方法"""
    from app.services.genie import GenieService
    assert hasattr(GenieService, "_extract_suggested_questions")
    assert callable(GenieService._extract_suggested_questions)


def test_extract_suggested_questions_returns_empty_for_none():
    """_extract_suggested_questions 在無內容時應返回空列表"""
    from app.services.genie import GenieService
    result = GenieService._extract_suggested_questions(None)
    assert result == []


# ── D3: auth_middleware 不再定義本地 AuthenticationError ──

def test_no_local_authentication_error_in_middleware():
    """auth_middleware 不應定義自己的 AuthenticationError"""
    middleware_path = os.path.join(
        os.path.dirname(__file__), "../../app/core/auth_middleware.py"
    )
    with open(middleware_path, encoding="utf-8") as f:
        content = f.read()
    assert "class AuthenticationError" not in content


# ── A1: health_check.py 已刪除 ──

def test_health_check_service_deleted():
    """app/services/health_check.py 應已被刪除"""
    path = os.path.join(os.path.dirname(__file__), "../../app/services/health_check.py")
    assert not os.path.exists(path)


# ── E1: health check 回傳 databricks 檢查 ──

def test_health_check_returns_databricks_status():
    """health check 應包含 databricks 狀態"""
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "checks" in data
    assert "databricks" in data["checks"]
    assert "status" in data


def test_ready_check_returns_config_checks():
    """ready check 應包含配置檢查"""
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    response = client.get("/ready")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "checks" in data
    assert "databricks_token" in data["checks"]


# ── GraphService.close() 存在 ──

def test_graph_service_has_close():
    """GraphService 應有 close() 方法"""
    from app.services.graph import GraphService
    assert hasattr(GraphService, "close")


# ── bot_instance exports GRAPH_SERVICE ──

def test_bot_instance_has_graph_service():
    """bot_instance 應 export GRAPH_SERVICE"""
    from app.bot_instance import GRAPH_SERVICE
    from app.services.graph import GraphService
    assert isinstance(GRAPH_SERVICE, GraphService)
