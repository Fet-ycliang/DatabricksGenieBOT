---
name: databricks-bot-test
description: |
  測試輔助工具。自動生成單元測試、整合測試、Mock 模式。
  觸發：「生成測試」「寫測試」「test coverage」「mock」「pytest」
  幫助快速建立高品質測試，確保程式碼可靠性。
---

# DatabricksGenieBOT Test Helper

快速生成測試程式碼，提供常用測試模式和 Mock 範例。

## 測試檔案結構

```
tests/
├── unit/                  # 單元測試
│   ├── test_config.py
│   ├── test_email_extractor.py
│   ├── test_user_session.py
│   └── test_*.py
├── integration/           # 整合測試
│   └── test_genie_integration.py
└── performance/          # 效能測試
    └── test_performance.py
```

---

## 1. 單元測試模板

### 基本測試結構

```python
"""
測試 [模組名稱]
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock


class TestFeatureName:
    """測試 Feature 功能"""

    def test_initialization(self):
        """測試初始化"""
        from app.module import Feature

        feature = Feature(param="value")
        assert feature.param == "value"

    def test_validation_success(self):
        """測試驗證成功案例"""
        from app.module import Feature

        result = Feature.validate("valid-input")
        assert result is True

    def test_validation_failure(self):
        """測試驗證失敗案例"""
        from app.module import Feature

        with pytest.raises(ValueError):
            Feature.validate("invalid-input")
```

### 非同步測試（使用 asyncio.run）

```python
def test_async_operation():
    """測試非同步操作"""
    from app.services.feature import FeatureService

    async def run_test():
        service = FeatureService()
        result = await service.process("data")
        return result

    # 使用 asyncio.run 執行非同步測試
    result = asyncio.run(run_test())
    assert result is not None
    assert result["status"] == "success"


def test_async_with_timeout():
    """測試非同步操作（含超時）"""
    import asyncio

    async def run_test():
        service = FeatureService()
        # 使用 asyncio.wait_for 設定超時
        result = await asyncio.wait_for(
            service.process("data"),
            timeout=5.0
        )
        return result

    result = asyncio.run(run_test())
    assert result is not None
```

---

## 2. Mock 測試模式

### Mock HTTP 請求

```python
def test_http_request_with_mock():
    """測試 HTTP 請求（使用 Mock）"""
    from app.services.feature import FeatureService
    import httpx

    with patch('app.services.feature.httpx.AsyncClient') as mock_client:
        # 設定 Mock 回應
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "success",
            "data": {"id": "123", "value": 42}
        }
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()

        # 設定 AsyncMock 客戶端
        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_instance.get.return_value = mock_response
        mock_client.return_value = mock_instance

        # 執行測試
        async def run_test():
            service = FeatureService()
            result = await service.call_api("endpoint")
            return result

        result = asyncio.run(run_test())

        # 驗證結果
        assert result["status"] == "success"
        assert result["data"]["id"] == "123"

        # 驗證 Mock 被呼叫
        mock_instance.post.assert_called_once()
```

### Mock Databricks API

```python
def test_genie_query_with_mock():
    """測試 Genie 查詢（Mock Databricks API）"""
    from app.services.genie import GenieService

    with patch('app.services.genie.httpx.AsyncClient') as mock_client:
        # Mock 建立對話
        mock_create_response = Mock()
        mock_create_response.json.return_value = {
            "conversation_id": "conv-123"
        }
        mock_create_response.status_code = 200
        mock_create_response.raise_for_status = Mock()

        # Mock 傳送訊息
        mock_message_response = Mock()
        mock_message_response.json.return_value = {
            "id": "msg-456",
            "query_result": {
                "statement_response": {
                    "result": {"data_typed_array": []}
                }
            }
        }
        mock_message_response.status_code = 200
        mock_message_response.raise_for_status = Mock()

        # 設定 Mock 客戶端
        mock_instance = AsyncMock()
        mock_instance.post.side_effect = [
            mock_create_response,
            mock_message_response
        ]
        mock_client.return_value = mock_instance

        # 執行測試
        async def run_test():
            service = GenieService()
            conv_id = await service.create_conversation()
            result = await service.send_message(conv_id, "查詢")
            return result

        result = asyncio.run(run_test())
        assert result is not None
```

### Mock Bot Framework

```python
def test_bot_handler_with_mock():
    """測試 Bot 處理器（Mock TurnContext）"""
    from bot.handlers.bot import MyBot
    from botbuilder.core import TurnContext
    from botbuilder.schema import Activity, ChannelAccount

    # 建立 Mock Activity
    activity = Activity(
        type="message",
        text="測試訊息",
        from_property=ChannelAccount(id="user-123", name="Test User"),
        channel_id="msteams"
    )

    # 建立 Mock TurnContext
    turn_context = Mock(spec=TurnContext)
    turn_context.activity = activity
    turn_context.send_activity = AsyncMock()

    # 執行測試
    async def run_test():
        bot = MyBot()
        await bot.on_message_activity(turn_context)

    asyncio.run(run_test())

    # 驗證回應被發送
    turn_context.send_activity.assert_called()
```

---

## 3. 參數化測試

```python
@pytest.mark.parametrize("input_data,expected", [
    ("valid@email.com", True),
    ("invalid-email", False),
    ("test@example.com", True),
    ("no-at-sign", False),
    ("@missing-local.com", False),
])
def test_email_validation(input_data, expected):
    """測試 Email 驗證（參數化）"""
    from app.utils.email_extractor import is_valid_email

    result = is_valid_email(input_data)
    assert result == expected


@pytest.mark.parametrize("user_id,email,should_be_valid", [
    ("user-1", "test@example.com", True),
    ("user-2", "invalid", False),
    ("user-3", None, False),
])
def test_session_creation(user_id, email, should_be_valid):
    """測試會話建立（參數化）"""
    from app.models.user_session import UserSession, is_valid_email

    if should_be_valid:
        session = UserSession(user_id, email)
        assert session.user_id == user_id
        assert session.email == email
    else:
        # 預期拋出異常或返回 False
        if email:
            assert not is_valid_email(email)
```

---

## 4. 異常測試

```python
def test_service_error_handling():
    """測試服務錯誤處理"""
    from app.services.feature import FeatureService
    from app.core.exceptions import ServiceError

    with patch('app.services.feature.httpx.AsyncClient') as mock_client:
        # Mock HTTP 錯誤
        mock_instance = AsyncMock()
        mock_instance.post.side_effect = httpx.HTTPStatusError(
            "API Error",
            request=Mock(),
            response=Mock(status_code=500, text="Internal Error")
        )
        mock_client.return_value = mock_instance

        # 測試異常處理
        with pytest.raises(ServiceError):
            async def run_test():
                service = FeatureService()
                await service.call_api("endpoint")

            asyncio.run(run_test())


def test_configuration_error():
    """測試配置錯誤"""
    from app.core.exceptions import ConfigurationError
    import os

    # 移除環境變數
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ConfigurationError):
            from app.core.config import DefaultConfig
            _ = DefaultConfig.DATABRICKS_TOKEN
```

---

## 5. 測試生成器範例

### 為 Service 生成測試

**給定程式碼**:
```python
# app/services/feature.py
class FeatureService:
    async def process_data(self, user_id: str, data: dict) -> dict:
        """處理資料"""
        result = await self._call_api(user_id, data)
        return result
```

**生成測試**:
```python
# tests/unit/test_feature_service.py
"""測試 FeatureService"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock


class TestFeatureService:
    """測試 FeatureService 類別"""

    def test_initialization(self):
        """測試服務初始化"""
        from app.services.feature import FeatureService
        service = FeatureService()
        assert service is not None

    def test_process_data_success(self):
        """測試 process_data 成功案例"""
        from app.services.feature import FeatureService

        with patch.object(
            FeatureService,
            '_call_api',
            new_callable=AsyncMock
        ) as mock_call:
            mock_call.return_value = {"status": "success"}

            async def run_test():
                service = FeatureService()
                result = await service.process_data(
                    "user-123",
                    {"key": "value"}
                )
                return result

            result = asyncio.run(run_test())
            assert result["status"] == "success"
            mock_call.assert_called_once_with("user-123", {"key": "value"})

    def test_process_data_failure(self):
        """測試 process_data 失敗案例"""
        from app.services.feature import FeatureService
        from app.core.exceptions import ServiceError

        with patch.object(
            FeatureService,
            '_call_api',
            new_callable=AsyncMock
        ) as mock_call:
            mock_call.side_effect = ServiceError("API 錯誤")

            with pytest.raises(ServiceError):
                async def run_test():
                    service = FeatureService()
                    await service.process_data("user-123", {})

                asyncio.run(run_test())
```

---

## 6. 整合測試模式

```python
"""整合測試 - Genie API"""
import pytest
import asyncio
from app.services.genie import GenieService
from app.core.config import DefaultConfig


@pytest.mark.integration
def test_genie_full_workflow():
    """測試 Genie 完整工作流程（需要真實 API）"""

    async def run_test():
        service = GenieService()

        # 1. 建立對話
        conv_id = await service.create_conversation(
            DefaultConfig.DATABRICKS_SPACE_ID
        )
        assert conv_id is not None

        # 2. 傳送查詢
        result = await service.send_message(
            DefaultConfig.DATABRICKS_SPACE_ID,
            conv_id,
            "測試查詢"
        )
        assert result is not None

        # 3. 清理
        await service.close()

    asyncio.run(run_test())


@pytest.mark.integration
@pytest.mark.skipif(
    not DefaultConfig.DATABRICKS_TOKEN,
    reason="需要 DATABRICKS_TOKEN"
)
def test_genie_with_real_api():
    """測試 Genie（跳過如果沒有 token）"""
    # 測試邏輯...
    pass
```

---

## 7. 效能測試

```python
"""效能測試"""
import pytest
import asyncio
import time


def test_cache_performance():
    """測試快取效能"""
    from app.utils.cache_utils import SimpleCache

    cache = SimpleCache(max_size=1000)

    # 測試寫入效能
    start = time.time()
    for i in range(1000):
        cache.set(f"key-{i}", f"value-{i}")
    write_time = time.time() - start

    # 測試讀取效能
    start = time.time()
    for i in range(1000):
        cache.get(f"key-{i}")
    read_time = time.time() - start

    # 驗證效能
    assert write_time < 0.1  # 寫入應該 < 100ms
    assert read_time < 0.05  # 讀取應該 < 50ms

    print(f"寫入 1000 項: {write_time*1000:.2f}ms")
    print(f"讀取 1000 項: {read_time*1000:.2f}ms")


def test_concurrent_requests():
    """測試並發請求"""
    from app.services.genie import GenieService

    async def single_request(service, query_id):
        await service.process(f"query-{query_id}")
        return query_id

    async def run_test():
        service = GenieService()

        start = time.time()
        tasks = [single_request(service, i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        assert len(results) == 10
        assert elapsed < 2.0  # 10 個請求應該 < 2 秒

        return elapsed

    elapsed = asyncio.run(run_test())
    print(f"10 個並發請求: {elapsed:.2f}s")
```

---

## 8. 測試工具函式

### Fixture 範例

```python
import pytest


@pytest.fixture
def mock_turn_context():
    """Mock TurnContext fixture"""
    from unittest.mock import Mock, AsyncMock
    from botbuilder.core import TurnContext
    from botbuilder.schema import Activity, ChannelAccount

    activity = Activity(
        type="message",
        text="測試",
        from_property=ChannelAccount(id="user-123", name="Test")
    )

    context = Mock(spec=TurnContext)
    context.activity = activity
    context.send_activity = AsyncMock()

    return context


@pytest.fixture
def mock_genie_service():
    """Mock GenieService fixture"""
    from unittest.mock import Mock, AsyncMock

    service = Mock()
    service.create_conversation = AsyncMock(return_value="conv-123")
    service.send_message = AsyncMock(return_value={"status": "success"})
    service.close = AsyncMock()

    return service


# 使用 fixture
def test_with_fixtures(mock_turn_context, mock_genie_service):
    """使用 fixtures 的測試"""
    assert mock_turn_context.activity.text == "測試"

    async def run_test():
        conv_id = await mock_genie_service.create_conversation()
        assert conv_id == "conv-123"

    asyncio.run(run_test())
```

---

## 9. 測試覆蓋率

### 執行測試並檢查覆蓋率

```bash
# 安裝 pytest-cov
pip install pytest-cov

# 執行測試並生成覆蓋率報告
pytest --cov=app --cov-report=html tests/

# 查看覆蓋率報告
# 開啟 htmlcov/index.html
```

### 覆蓋率目標

```python
# pytest.ini 或 pyproject.toml
[tool:pytest]
addopts = --cov=app --cov-report=term-missing --cov-fail-under=80
```

---

## 10. 測試執行命令

```bash
# 執行所有測試
pytest

# 執行特定檔案
pytest tests/unit/test_feature.py

# 執行特定類別
pytest tests/unit/test_feature.py::TestFeatureName

# 執行特定測試
pytest tests/unit/test_feature.py::TestFeatureName::test_method

# 只執行標記的測試
pytest -m integration    # 整合測試
pytest -m "not integration"  # 排除整合測試

# 顯示詳細輸出
pytest -v -s

# 失敗時立即停止
pytest -x

# 重新執行失敗的測試
pytest --lf
```

---

## 檢查清單

撰寫測試前檢查:

- [ ] 測試檔案命名：`test_*.py`
- [ ] 測試類別命名：`TestFeatureName`
- [ ] 測試方法命名：`test_method_name`
- [ ] 包含成功和失敗案例
- [ ] 使用 Mock 隔離外部依賴
- [ ] 非同步測試使用 `asyncio.run()`
- [ ] 參數化測試涵蓋多種情況
- [ ] 測試異常處理
- [ ] 清理資源（close clients）
- [ ] 測試覆蓋率 > 80%
