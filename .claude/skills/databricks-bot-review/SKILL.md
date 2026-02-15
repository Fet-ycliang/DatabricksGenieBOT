---
name: databricks-bot-review
description: |
  Code Review 助手。檢查程式碼品質、安全性、效能、可讀性。
  觸發：「review」「code review」「檢查程式碼」「審查」
  提供全面的程式碼審查檢查清單和最佳實踐建議。
---

# DatabricksGenieBOT Code Review Helper

提供系統化的程式碼審查指南，涵蓋安全性、效能、可讀性等方面。

## Code Review 檢查清單

### 🔒 1. 安全性 (Security)

#### 敏感資訊洩漏
```python
# ❌ 不好：硬編碼敏感資訊
API_KEY = "dapi1234567890abcdef"
PASSWORD = "my_password_123"

# ✅ 好：使用環境變數
from app.core.config import DefaultConfig
API_KEY = DefaultConfig.DATABRICKS_TOKEN
```

**檢查項目**：
- [ ] 沒有硬編碼的 API keys、tokens、passwords
- [ ] 沒有洩漏使用者個資（email、phone）
- [ ] 敏感資訊不寫入日誌
- [ ] `.env` 檔案在 `.gitignore` 中

---

#### SQL 注入防護
```python
# ❌ 不好：字串拼接（SQL 注入風險）
query = f"SELECT * FROM users WHERE name = '{user_input}'"

# ✅ 好：使用參數化查詢
query = "SELECT * FROM users WHERE name = ?"
params = [user_input]
```

**檢查項目**：
- [ ] 使用參數化查詢
- [ ] 驗證使用者輸入
- [ ] 限制查詢結果數量（LIMIT）

---

#### XSS 防護（Adaptive Cards）
```python
# ❌ 不好：直接嵌入使用者輸入
{
    "type": "TextBlock",
    "text": user_input  # 可能包含惡意 script
}

# ✅ 好：轉義 HTML 特殊字元
import html
{
    "type": "TextBlock",
    "text": html.escape(user_input)
}
```

---

### ⚡ 2. 效能 (Performance)

#### HTTP 連接池
```python
# ❌ 不好：每次建立新連接
async def call_api():
    async with httpx.AsyncClient() as client:
        return await client.get(url)

# ✅ 好：重用連接池
class Service:
    def __init__(self):
        self._client = httpx.AsyncClient(
            limits=httpx.Limits(max_keepalive_connections=5)
        )

    async def call_api(self):
        return await self._client.get(url)

    async def close(self):
        await self._client.aclose()
```

**檢查項目**：
- [ ] 使用連接池重用 HTTP 連接
- [ ] 設定合理的 timeout
- [ ] 關閉客戶端資源（close）

---

#### 快取使用
```python
# ❌ 不好：重複計算
async def expensive_query(query):
    return await genie_service.query(query)  # 每次都查詢

# ✅ 好：使用快取
from app.utils.cache_utils import cached_query

@cached_query(cache=query_cache)
async def expensive_query(query):
    return await genie_service.query(query)
```

**檢查項目**：
- [ ] 昂貴操作使用快取
- [ ] 快取有 TTL（過期時間）
- [ ] 快取有大小限制（LRU）

---

#### 非同步處理
```python
# ❌ 不好：序列處理
for item in items:
    result = await process(item)

# ✅ 好：並發處理
results = await asyncio.gather(*[process(item) for item in items])
```

**檢查項目**：
- [ ] 獨立操作使用並發處理
- [ ] 正確使用 async/await
- [ ] 沒有阻塞操作在 async 函式中

---

### 🐛 3. 錯誤處理 (Error Handling)

#### 統一異常處理
```python
# ❌ 不好：捕獲通用異常
try:
    result = await service.process()
except Exception:
    pass  # 靜默處理

# ✅ 好：具體異常處理
from app.core.exceptions import ServiceError, AuthenticationError

try:
    result = await service.process()
except AuthenticationError as e:
    logger.error(f"認證失敗: {e}", exc_info=True)
    raise
except ServiceError as e:
    logger.error(f"服務錯誤: {e}", exc_info=True)
    # 處理或重新拋出
    raise
except Exception as e:
    logger.error(f"未預期錯誤: {e}", exc_info=True)
    raise
```

**檢查項目**：
- [ ] 使用專案定義的自訂異常
- [ ] 不捕獲過於廣泛的異常
- [ ] 錯誤訊息有意義
- [ ] 記錄錯誤日誌（包含 stack trace）

---

#### 資源清理
```python
# ❌ 不好：沒有清理資源
async def process():
    client = httpx.AsyncClient()
    result = await client.get(url)
    return result  # client 沒有關閉

# ✅ 好：確保資源清理
async def process():
    client = httpx.AsyncClient()
    try:
        result = await client.get(url)
        return result
    finally:
        await client.aclose()  # 總是關閉

# 或使用 context manager
async def process():
    async with httpx.AsyncClient() as client:
        result = await client.get(url)
        return result
```

**檢查項目**：
- [ ] HTTP 客戶端有關閉
- [ ] 檔案有關閉
- [ ] 使用 try/finally 或 context manager

---

### 📝 4. 程式碼品質 (Code Quality)

#### 類型提示
```python
# ❌ 不好：沒有類型提示
async def process_data(user_id, data, timeout=None):
    pass

# ✅ 好：完整類型提示
from typing import Optional, Dict, Any

async def process_data(
    user_id: str,
    data: Dict[str, Any],
    timeout: Optional[float] = None
) -> Dict[str, Any]:
    pass
```

**檢查項目**：
- [ ] 函式參數有類型提示
- [ ] 函式返回值有類型提示
- [ ] 使用正確的 typing 模組類型

---

#### 函式長度和複雜度
```python
# ❌ 不好：函式過長（> 50 行）
def process_everything(data):
    # 100+ 行程式碼...
    pass

# ✅ 好：拆分為小函式
def process_everything(data):
    validated_data = validate_data(data)
    processed_data = transform_data(validated_data)
    result = save_data(processed_data)
    return result

def validate_data(data): ...
def transform_data(data): ...
def save_data(data): ...
```

**檢查項目**：
- [ ] 單一函式 < 50 行
- [ ] 單一職責原則
- [ ] 函式名稱清楚描述功能
- [ ] 避免深層嵌套（< 3 層）

---

#### 命名規範
```python
# ❌ 不好：不清楚的命名
def f(x, y):
    return x + y

# ✅ 好：有意義的命名
def calculate_total_price(
    base_price: float,
    tax_rate: float
) -> float:
    return base_price * (1 + tax_rate)
```

**檢查項目**：
- [ ] 變數名稱有意義
- [ ] 函式名稱使用動詞
- [ ] 類別名稱使用名詞
- [ ] 常數使用大寫（CONSTANT_NAME）
- [ ] 私有方法使用單底線前綴（_private_method）

---

### 📚 5. 文檔 (Documentation)

#### Docstring
```python
# ❌ 不好：沒有 docstring
async def process_data(user_id, data):
    result = await service.call(user_id, data)
    return result

# ✅ 好：完整 docstring
async def process_data(
    user_id: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    處理使用者資料

    Args:
        user_id: 使用者 ID
        data: 要處理的資料

    Returns:
        Dict: 處理結果，包含 status 和 data

    Raises:
        ServiceError: 當 API 呼叫失敗時
        ValidationError: 當資料驗證失敗時

    Example:
        >>> result = await process_data("user-123", {"key": "value"})
        >>> print(result["status"])
        "success"
    """
    result = await service.call(user_id, data)
    return result
```

**檢查項目**：
- [ ] 公開函式有 docstring
- [ ] 說明參數和返回值
- [ ] 說明可能的異常
- [ ] 提供使用範例（如適用）

---

### 🧪 6. 測試 (Testing)

#### 測試覆蓋率
```python
# ✅ 為關鍵功能寫測試
def test_email_validation():
    """測試 Email 驗證"""
    assert is_valid_email("test@example.com") is True
    assert is_valid_email("invalid") is False

def test_service_error_handling():
    """測試錯誤處理"""
    with pytest.raises(ServiceError):
        async def run():
            await service.call_invalid_api()
        asyncio.run(run())
```

**檢查項目**：
- [ ] 關鍵功能有單元測試
- [ ] 測試成功和失敗案例
- [ ] 測試邊界條件
- [ ] 使用 Mock 隔離外部依賴
- [ ] 測試覆蓋率 > 80%

---

### 🎯 7. 專案特定檢查

#### Bot Framework 程式碼
```python
# ✅ 正確的 Activity Handler
async def on_message_activity(self, turn_context: TurnContext):
    """處理訊息（注意 async/await）"""
    user_message = turn_context.activity.text

    try:
        response = await self.process_message(user_message)
        await turn_context.send_activity(response)  # ← 必須 await
    except Exception as e:
        logger.error(f"處理失敗: {e}", exc_info=True)
        await turn_context.send_activity("發生錯誤，請稍後再試")
```

**檢查項目**：
- [ ] ActivityHandler 方法是 async
- [ ] send_activity 有 await
- [ ] 錯誤處理適當
- [ ] 使用者看得懂的錯誤訊息

---

#### Adaptive Cards
```python
# ✅ 遵循 Adaptive Card 最佳實踐
def create_card(title: str, data: dict) -> Attachment:
    """建立卡片"""
    adaptive_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",  # ← 使用支援的版本
        "body": [
            {
                "type": "TextBlock",
                "text": title,
                "size": "Large",
                "weight": "Bolder",
                "wrap": True  # ← 自動換行
            }
        ]
    }
    # 檢查大小 < 28 KB
    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=adaptive_card
    )
```

**檢查項目**：
- [ ] Card JSON < 28 KB
- [ ] 使用支援的版本（1.4）
- [ ] TextBlock 使用 wrap=True
- [ ] 圖片使用 URL 而非 base64（如可能）

---

## Code Review 流程

### 1. 檢查 Commit
```bash
# 查看變更
git diff main...feature-branch

# 查看提交歷史
git log --oneline main..feature-branch
```

### 2. 執行測試
```bash
# 執行所有測試
pytest

# 檢查覆蓋率
pytest --cov=app --cov-report=html
```

### 3. 靜態分析（可選）
```bash
# 安裝工具
pip install pylint black mypy

# 程式碼格式檢查
black --check app/

# 類型檢查
mypy app/

# Lint 檢查
pylint app/
```

### 4. Review 檢查清單

使用本 skill 的檢查清單：
- [ ] 🔒 安全性檢查
- [ ] ⚡ 效能檢查
- [ ] 🐛 錯誤處理檢查
- [ ] 📝 程式碼品質檢查
- [ ] 📚 文檔檢查
- [ ] 🧪 測試檢查
- [ ] 🎯 專案特定檢查

---

## Review 評論範本

### 建議改進
```markdown
**建議**: 使用連接池重用 HTTP 連接

在 `app/services/feature.py:45` 中，每次 API 呼叫都建立新連接：
\`\`\`python
async with httpx.AsyncClient() as client:
    result = await client.get(url)
\`\`\`

建議改為重用連接池以提升效能：
\`\`\`python
class Service:
    def __init__(self):
        self._client = httpx.AsyncClient()

    async def call_api(self):
        return await self._client.get(url)
\`\`\`

參考: `app/services/genie.py` 的實作
```

### 指出問題
```markdown
**問題**: 潛在的記憶體洩漏

在 `app/utils/session.py:78` 中，會話物件沒有自動清理機制：
\`\`\`python
sessions[user_id] = new_session  # 永不刪除
\`\`\`

這會導致長時間執行的應用程式記憶體持續增長。

建議: 實作自動清理機制，參考 `app/utils/session_manager.py`
```

### 讚賞好的程式碼
```markdown
**👍 讚**: 良好的錯誤處理

`app/services/feature.py:120-135` 的錯誤處理很完善：
- 使用專案自訂異常
- 記錄詳細日誌
- 提供有意義的錯誤訊息

這是很好的實踐！
```

---

## 常見問題 (Anti-patterns)

### 1. 過度巢狀
```python
# ❌ 不好：深層嵌套
if condition1:
    if condition2:
        if condition3:
            if condition4:
                # 核心邏輯
                pass

# ✅ 好：提早返回
if not condition1:
    return
if not condition2:
    return
if not condition3:
    return
if not condition4:
    return
# 核心邏輯
```

### 2. 魔術數字
```python
# ❌ 不好：魔術數字
if user_age > 18:
    pass

# ✅ 好：命名常數
LEGAL_AGE = 18
if user_age > LEGAL_AGE:
    pass
```

### 3. 重複程式碼
```python
# ❌ 不好：重複邏輯
result1 = await http.post(url1, data=data1)
if result1.status_code != 200:
    raise ServiceError(f"API 錯誤: {result1.text}")

result2 = await http.post(url2, data=data2)
if result2.status_code != 200:
    raise ServiceError(f"API 錯誤: {result2.text}")

# ✅ 好：提取共用函式
async def call_api(url, data):
    result = await http.post(url, data=data)
    if result.status_code != 200:
        raise ServiceError(f"API 錯誤: {result.text}")
    return result

result1 = await call_api(url1, data1)
result2 = await call_api(url2, data2)
```

---

## Quick Reference

### 優先級

| 優先級 | 檢查項目 |
|-------|---------|
| 🔴 Critical | 安全性問題、記憶體洩漏 |
| 🟡 High | 效能問題、錯誤處理 |
| 🟢 Medium | 程式碼品質、測試覆蓋率 |
| ⚪ Low | 命名規範、註解 |

### 快速檢查命令

```bash
# 檢查測試
pytest

# 檢查覆蓋率
pytest --cov=app

# 格式檢查
black --check app/

# 類型檢查
mypy app/
```

---

## 參考資源

- [Python Best Practices](https://docs.python-guide.org/)
- [專案 Code Style](../../../CLAUDE.md)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
