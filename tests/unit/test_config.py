"""
測試配置管理
"""

import pytest
import os
from unittest.mock import patch


def test_config_default_values():
    """測試配置預設值"""
    # 在乾淨的環境中測試
    with patch.dict(os.environ, {}, clear=False):
        # 動態導入以避免影響其他測試
        import importlib
        import app.core.config as config_module
        importlib.reload(config_module)

        from app.core.config import DefaultConfig

        # 測試預設值
        assert DefaultConfig.PORT == int(os.getenv("PORT", "3978"))
        assert DefaultConfig.APP_TYPE == "SingleTenant"
        assert DefaultConfig.CONNECTION_NAME == "MyTeamsSSOConnection"
        assert DefaultConfig.TIMEZONE == "Asia/Taipei"
        assert isinstance(DefaultConfig.ENABLE_FEEDBACK_CARDS, bool)
        assert isinstance(DefaultConfig.ENABLE_GENIE_FEEDBACK_API, bool)


def test_config_port_from_env():
    """測試從環境變數讀取 PORT"""
    with patch.dict(os.environ, {"PORT": "8000"}, clear=False):
        import importlib
        import app.core.config as config_module
        importlib.reload(config_module)

        from app.core.config import DefaultConfig

        assert DefaultConfig.PORT == 8000


def test_config_boolean_parsing():
    """測試布林值解析"""
    # 測試 True 值
    with patch.dict(os.environ, {
        "ENABLE_FEEDBACK_CARDS": "True",
        "ENABLE_GENIE_FEEDBACK_API": "true",
        "VERBOSE_LOGGING": "TRUE"
    }, clear=False):
        import importlib
        import app.core.config as config_module
        importlib.reload(config_module)

        from app.core.config import DefaultConfig

        # 應該全部為 True
        assert DefaultConfig.ENABLE_FEEDBACK_CARDS is True
        assert DefaultConfig.ENABLE_GENIE_FEEDBACK_API is True
        assert DefaultConfig.VERBOSE_LOGGING is True


def test_config_boolean_false_values():
    """測試布林值 False 解析"""
    with patch.dict(os.environ, {
        "ENABLE_FEEDBACK_CARDS": "False",
        "ENABLE_GENIE_FEEDBACK_API": "false",
        "VERBOSE_LOGGING": "no"
    }, clear=False):
        import importlib
        import app.core.config as config_module
        importlib.reload(config_module)

        from app.core.config import DefaultConfig

        assert DefaultConfig.ENABLE_FEEDBACK_CARDS is False
        assert DefaultConfig.ENABLE_GENIE_FEEDBACK_API is False
        # "no" 不等於 "true"，所以是 False
        assert DefaultConfig.VERBOSE_LOGGING is False


def test_config_databricks_settings():
    """測試 Databricks 配置"""
    with patch.dict(os.environ, {
        "DATABRICKS_SPACE_ID": "test-space-123",
        "DATABRICKS_HOST": "https://test.databricks.com",
        "DATABRICKS_TOKEN": "test-token-456"
    }, clear=False):
        import importlib
        import app.core.config as config_module
        importlib.reload(config_module)

        from app.core.config import DefaultConfig

        assert DefaultConfig.DATABRICKS_SPACE_ID == "test-space-123"
        assert DefaultConfig.DATABRICKS_HOST == "https://test.databricks.com"
        assert DefaultConfig.DATABRICKS_TOKEN == "test-token-456"


def test_config_sample_questions():
    """測試範例問題配置"""
    custom_questions = "Question 1;Question 2;Question 3"

    with patch.dict(os.environ, {
        "SAMPLE_QUESTIONS": custom_questions,
        "DATABRICKS_TOKEN": "dummy"  # 避免驗證錯誤
    }, clear=False):
        import importlib
        import app.core.config as config_module
        importlib.reload(config_module)

        from app.core.config import DefaultConfig

        assert DefaultConfig.SAMPLE_QUESTIONS == custom_questions


def test_config_timezone_setting():
    """測試時區配置"""
    with patch.dict(os.environ, {
        "TIMEZONE": "America/New_York",
        "DATABRICKS_TOKEN": "dummy"
    }, clear=False):
        import importlib
        import app.core.config as config_module
        importlib.reload(config_module)

        from app.core.config import DefaultConfig

        assert DefaultConfig.TIMEZONE == "America/New_York"


def test_config_admin_contact():
    """測試管理員聯絡資訊"""
    with patch.dict(os.environ, {
        "ADMIN_CONTACT_EMAIL": "support@company.com",
        "DATABRICKS_TOKEN": "dummy"
    }, clear=False):
        import importlib
        import app.core.config as config_module
        importlib.reload(config_module)

        from app.core.config import DefaultConfig

        assert DefaultConfig.ADMIN_CONTACT_EMAIL == "support@company.com"


def test_config_app_credentials():
    """測試 App 憑證配置"""
    with patch.dict(os.environ, {
        "APP_ID": "test-app-id",
        "APP_PASSWORD": "test-password",
        "APP_TENANTID": "test-tenant-id",
        "DATABRICKS_TOKEN": "dummy"
    }, clear=False):
        import importlib
        import app.core.config as config_module
        importlib.reload(config_module)

        from app.core.config import DefaultConfig

        assert DefaultConfig.APP_ID == "test-app-id"
        assert DefaultConfig.APP_PASSWORD == "test-password"
        assert DefaultConfig.APP_TENANTID == "test-tenant-id"


def test_config_log_file():
    """測試日誌檔案配置"""
    with patch.dict(os.environ, {
        "LOG_FILE": "custom_log.log",
        "DATABRICKS_TOKEN": "dummy"
    }, clear=False):
        import importlib
        import app.core.config as config_module
        importlib.reload(config_module)

        from app.core.config import DefaultConfig

        assert DefaultConfig.LOG_FILE == "custom_log.log"
