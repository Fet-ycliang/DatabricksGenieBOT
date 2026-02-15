# Microsoft 365 Agents SDK 完整評估報告

**評估日期**: 2026年2月16日
**評估者**: Claude Code
**專案**: Databricks Genie Bot
**目的**: 評估從 Bot Framework SDK 遷移到 M365 Agents SDK 的可行性

---

## 執行摘要

### 關鍵發現

✅ **Microsoft 365 Agents SDK 對 Python 的支援比預期更成熟**

根據官方文件和最新資訊：
- Python 是 M365 生態系統的「**first-class citizen**」（一等公民）
- 有完整的 Python Quickstart 指南
- PyPI 套件可用且活躍維護
- 支援所有核心功能：TurnContext、Activity Protocol、Adaptive Cards、State Management

### 建議行動

**修正建議：從「保守等待」改為「積極評估 + 分階段遷移」**

原因：
1. Python 支援比預期成熟得多
2. 官方文件完整
3. Bot Framework 已 EOL
4. TeamsFx SDK 也將在 2026年9月停止支援

---

## 詳細評估

### 1. SDK 成熟度分析

#### Python 支援狀態

| 項目 | 狀態 | 證據 |
|------|------|------|
| 官方支援 | ✅ 確認 | Microsoft Learn 官方文件 |
| PyPI 套件 | ✅ 可用 | `microsoft-agents-activity` 等套件 |
| Quickstart 指南 | ✅ 存在 | [官方 Python Quickstart](https://learn.microsoft.com/en-us/microsoft-365/agents-sdk/quickstart) |
| 程式碼範例 | ✅ 完整 | GitHub Agents-for-python |
| API 文件 | ✅ 完整 | Python API 參考可用 |
| 類型安全 | ✅ 支援 | 使用 Pydantic 進行自動驗證 |

#### 核心功能支援

| 功能 | Bot Framework | M365 Agents SDK | 遷移難度 |
|------|---------------|-----------------|----------|
| Activity Handler | ✅ | ✅ | 低 |
| TurnContext | ✅ | ✅ | 低 |
| Adaptive Cards | ✅ | ✅ | 低 |
| State Management | ✅ | ✅ | 中 |
| SSO/OAuth | ✅ | ✅ | 中 |
| Teams 整合 | ✅ | ✅ | 低 |
| Conversation Flow | ✅ | ✅ | 中 |
| Storage | MemoryStorage | MemoryStorage | 低 |

### 2. 架構對比

#### Bot Framework SDK 架構

```python
# Bot Framework (舊架構)
from botbuilder.core import ActivityHandler, TurnContext, ConversationState
from botbuilder.schema import Activity

class MyBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        await turn_context.send_activity("Hello")
```

#### M365 Agents SDK 架構

```python
# M365 Agents SDK (新架構)
from microsoft_agents import AgentApplication, TurnContext, Activity
from microsoft_agents.hosting.aiohttp import AgentHostingAdapter
from microsoft_agents.storage import MemoryStorage

app = AgentApplication(
    storage=MemoryStorage(),
    adapter=CloudAdapter()
)

@app.activity("message")
async def on_message(context: TurnContext):
    await context.send_activity("Hello")
```

**相似度**: 約 70-80%
**遷移難度**: 中等
**預期工作量**: 3-5 週

### 3. 遷移路徑分析

#### 階段 1: POC 驗證（1-2 週）

**目標**: 驗證核心功能可行性

**測試項目**:
```
✓ 安裝 SDK 套件
✓ 建立基本 Agent
✓ 處理訊息
✓ 發送 Adaptive Cards
✓ 狀態管理
✓ Teams 整合測試
✓ Databricks API 整合
```

**成功標準**:
- 所有核心功能運作正常
- 效能符合要求
- 無重大阻礙問題

#### 階段 2: 並行架構（2-3 週）

**目標**: 在不影響現有服務的情況下建立新架構

**實施方式**:
```
/api/messages (Bot Framework) ─┐
                               ├─ 藍綠部署
/api/agents (M365 SDK)     ────┘
```

**測試計畫**:
- 使用測試使用者驗證新架構
- 逐步增加流量到新端點
- 保持舊端點作為備用

#### 階段 3: 完整遷移（2-3 週）

**目標**: 完全切換到 M365 Agents SDK

**步驟**:
1. 遷移所有使用者到新端點
2. 監控錯誤和效能
3. 移除 Bot Framework 依賴
4. 更新文件

#### 階段 4: 優化與穩定（1-2 週）

**目標**: 優化新架構效能和穩定性

**優化項目**:
- 效能調校
- 錯誤處理增強
- 監控和日誌
- 文件更新

### 4. 風險評估（更新）

| 風險 | 原評估 | 新評估 | 變更原因 |
|------|--------|--------|----------|
| Python SDK 不穩定 | 🔴 高 | 🟡 中低 | 官方支援較預期完整 |
| 功能缺失 | 🟠 中 | 🟢 低 | 所有核心功能已支援 |
| 文件不完整 | 🟠 中 | 🟢 低 | 官方文件完整 |
| 遷移成本 | 🟡 中 | 🟡 中 | 約 6-10 週工作量 |
| Bot Framework EOL | 🟡 低 | 🟠 中 | 已 EOL，應盡快遷移 |

### 5. 技術實施細節

#### 5.1 核心元件對應

| Bot Framework | M365 Agents SDK | 註釋 |
|---------------|-----------------|------|
| `BotFrameworkAdapter` | `CloudAdapter` | 配置方式略有不同 |
| `ActivityHandler` | `AgentApplication` + decorators | 使用 decorator 模式 |
| `ConversationState` | 內建 state management | 更簡潔 |
| `UserState` | 內建 state management | 更簡潔 |
| `MemoryStorage` | `MemoryStorage` | 相同 API |
| `TurnContext` | `TurnContext` | 幾乎相同 |
| `Activity` | `Activity` | Activity Protocol 標準 |

#### 5.2 程式碼遷移示例

##### 訊息處理

**Before (Bot Framework)**:
```python
class MyBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        text = turn_context.activity.text
        await turn_context.send_activity(f"You said: {text}")
```

**After (M365 Agents SDK)**:
```python
@app.activity("message")
async def on_message(context: TurnContext):
    text = context.activity.text
    await context.send_activity(f"You said: {text}")
```

##### 狀態管理

**Before (Bot Framework)**:
```python
conversation_state = ConversationState(MemoryStorage())
user_state = UserState(MemoryStorage())

class MyBot(ActivityHandler):
    def __init__(self, conversation_state, user_state):
        self.conversation_state = conversation_state
        self.user_state = user_state
```

**After (M365 Agents SDK)**:
```python
app = AgentApplication(
    storage=MemoryStorage(),
    # State management 內建支援
)

@app.activity("message")
async def on_message(context: TurnContext):
    # 直接使用 context 存取 state
    state = await context.get_state()
```

##### Adaptive Cards

**Before (Bot Framework)**:
```python
card = {
    "type": "AdaptiveCard",
    "body": [{"type": "TextBlock", "text": "Hello"}]
}
activity = Activity(
    type=ActivityTypes.message,
    attachments=[CardFactory.adaptive_card(card)]
)
await turn_context.send_activity(activity)
```

**After (M365 Agents SDK)**:
```python
# 相同的 Adaptive Card JSON 格式
card = {
    "type": "AdaptiveCard",
    "body": [{"type": "TextBlock", "text": "Hello"}]
}
await context.send_activity(
    Activity(
        type="message",
        attachments=[{"contentType": "application/vnd.microsoft.card.adaptive", "content": card}]
    )
)
```

### 6. 成本效益分析

#### 投資成本

| 項目 | 估計時間 | 人力成本 |
|------|----------|----------|
| POC 開發 | 1-2 週 | 1 人週 |
| 架構遷移 | 2-3 週 | 2 人週 |
| 測試驗證 | 2-3 週 | 2 人週 |
| 優化穩定 | 1-2 週 | 1 人週 |
| 文件更新 | 1 週 | 0.5 人週 |
| **總計** | **7-11 週** | **6.5-8.5 人週** |

#### 預期收益

**短期收益** (3-6 個月):
- ✅ 移除 EOL 技術債務
- ✅ 符合 Microsoft 官方建議
- ✅ 獲得持續的安全更新

**中期收益** (6-12 個月):
- ✅ 更好的 Microsoft 365 整合
- ✅ 新功能和 API 存取
- ✅ 改善的開發體驗

**長期收益** (1-2 年):
- ✅ Copilot 整合能力
- ✅ 多通道支援（Web, Mobile, etc.）
- ✅ 未來技術棧的基礎

#### ROI 分析

```
投資: 6.5-8.5 人週
風險降低: 移除 EOL 技術（價值：高）
未來能力: Copilot 整合（價值：高）

結論: 正向 ROI，建議執行
```

### 7. 時間表建議（修訂）

#### 選項 A: 積極遷移（推薦）⭐⭐⭐

```
Week 1-2 (2月下旬)
├─ POC 開發和驗證
└─ 決策：Go/No-Go

Week 3-5 (3月)
├─ 架構遷移
├─ 核心功能實作
└─ 初步測試

Week 6-8 (3-4月)
├─ 完整測試
├─ 並行運行
└─ 逐步切換

Week 9-11 (4月)
├─ 完全切換
├─ 優化調整
└─ 移除舊代碼

目標完成: 2026年4月底
```

**優點**:
- ✅ 快速移除技術債務
- ✅ 早期獲得新功能
- ✅ 符合 Microsoft 建議

**風險**:
- ⚠️ 需要專注投入時間
- ⚠️ 可能遇到邊緣案例問題

#### 選項 B: 穩健遷移

```
Q2 2026 (4-6月)
├─ POC 驗證
├─ 詳細規劃
└─ 開始實作

Q3 2026 (7-9月)
├─ 完整遷移
└─ 測試驗證

Q4 2026 (10-12月)
└─ 穩定優化

目標完成: 2026年9月
```

**優點**:
- ✅ 更充裕的時間
- ✅ 更低的風險
- ✅ 可以等待更多社群反饋

**缺點**:
- ⚠️ 更長時間依賴 EOL 技術
- ⚠️ 延後獲得新功能

### 8. 關鍵發現和建議

#### 重要發現

1. **Python 支援超出預期**
   - 官方文件完整
   - PyPI 套件可用
   - 類型安全（Pydantic）
   - 被視為「first-class citizen」

2. **遷移難度適中**
   - 架構相似度 70-80%
   - 大部分概念相同
   - 預估 6-10 週可完成

3. **風險可控**
   - 可以並行運行兩個系統
   - 完整的文件支援
   - 活躍的社群

#### 最終建議

**建議採用「選項 A：積極遷移」**

**理由**:
1. Bot Framework 已 EOL（2026年1月封存）
2. Python SDK 比預期成熟
3. 遷移成本可控（6-10 週）
4. 早期獲得新功能和支援
5. 符合 Microsoft 官方建議

**下一步行動**:
1. **立即**: 開始 POC 開發（Week 1-2）
2. **3週內**: 做出 Go/No-Go 決策
3. **4-11週**: 執行完整遷移
4. **4月底**: 完成遷移並穩定

---

## 附錄

### A. 參考資源

**官方文件**:
- [Microsoft 365 Agents SDK 文件](https://learn.microsoft.com/en-us/microsoft-365/agents-sdk/)
- [Python Quickstart](https://learn.microsoft.com/en-us/microsoft-365/agents-sdk/quickstart)
- [Activity Protocol](https://learn.microsoft.com/en-us/microsoft-365/agents-sdk/activity-protocol)
- [遷移指南](https://learn.microsoft.com/en-us/microsoft-365/agents-sdk/bf-migration-guidance)

**GitHub 資源**:
- [Agents-for-python](https://github.com/microsoft/Agents-for-python)
- [Microsoft Agents SDK](https://github.com/microsoft/Agents)

**PyPI 套件**:
- [microsoft-agents-activity](https://pypi.org/project/microsoft-agents-activity/)

**社群資源**:
- [Getting Started with M365 Agents SDK](https://spknowledge.com/2026/01/07/getting-started-with-m365-agents-sdk/)
- [Microsoft Teams SDK Evolution 2025](https://www.voitanos.io/blog/microsoft-teams-sdk-evolution-2025/)

### B. POC 測試檢查清單

詳見：`docs/m365_agents_sdk_poc_plan.md`

### C. 風險管理計畫

#### 高風險項目

1. **SSO 認證遷移**
   - 緩解：提前測試 OAuth 流程
   - 備案：保留 Bot Framework 認證作為備用

2. **狀態管理遷移**
   - 緩解：實施資料遷移腳本
   - 備案：使用相容的儲存格式

3. **Adaptive Cards 相容性**
   - 緩解：完整測試所有卡片類型
   - 備案：保留卡片生成邏輯

#### 回退計畫

```
阻礙狀況                    回退動作
├─ POC 失敗             → 延後遷移，繼續使用 Bot Framework
├─ 遷移中遇到重大問題   → 回退到舊系統
└─ 效能不達標           → 優化或回退
```

---

---

## ⚠️ 重要更新：POC 實作發現 (2026-02-16)

### 關鍵發現

在實際建立 POC 的過程中，我們發現**Microsoft 365 Agents SDK Python 版本遠不如文件描述的成熟**：

**實際可用的套件**：
- ✅ `microsoft-agents-activity` (v0.7.0) - 僅 Activity Protocol 類型
- ✅ `microsoft-agents-hosting-core` (v0.6.1) - 基礎類型
- ✅ `microsoft-agents-authentication-msal` (v0.7.0) - 認證
- ❌ `AgentApplication` - **不存在**
- ❌ `MemoryStorage` - **不存在**
- ❌ Agent Framework 高階 API - **不存在**

### 修正後的建議

**原建議**: 執行積極遷移（選項 A）
**新建議**: **延後遷移，等待 SDK 成熟**

**理由**：
1. Python SDK 0.7.0 僅包含類型定義，缺少核心框架
2. 無法使用官方文件中的 API (AgentApplication, Decorators, etc.)
3. 需要自行實作完整的 Agent 框架（風險高、成本高）
4. Bot Framework 短期內仍可運作（已 EOL 但功能完整）

### 新時間表

```
2026 Q2-Q3: 保持 Bot Framework，監控 Python SDK 進展
2026 Q4: 重新評估 SDK（目標版本 1.0+）
2027 Q1: 執行遷移（如果 SDK 準備好）
```

詳細發現請參閱：`poc/POC_STATUS.md` 和 `poc/FINDINGS_SUMMARY.md`

---

**報告版本**: 1.1
**最後更新**: 2026-02-16
**狀態**: ⚠️ 已更新 - 建議變更
**新建議**: 延後遷移至 Q4 2026 或 Q1 2027
