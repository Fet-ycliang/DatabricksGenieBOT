# 📋 Graph API 用戶資料卡片功能

## 概述

應用程式現在支援通過 Microsoft Graph API 顯示富互動的用戶資料卡片 (Adaptive Card)，以下列形式展示用戶信息：

- 👤 用戶名稱和頭銜
- 📧 電子郵件地址
- 🏢 部門信息
- 💼 職位
- 📍 辦公地點
- 📞 電話號碼
- 🔐 Azure AD ID

## 使用方式

### 1. 自動顯示（首次加入）

當用戶首次加入聊天時，如果滿足以下條件，系統會自動發送用戶資料卡片：

✅ 條件：
- `ENABLE_GRAPH_API_AUTO_LOGIN=True` （環境變量）
- Graph API 已正確配置
- 成功取得用戶信息

顯示順序：
1. 歡迎消息
2. **用戶資料卡片** ← 自動發送
3. 建議問題

### 2. 命令查詢

用戶可以隨時使用以下命令查看完整的用戶資料卡片：

```
/me
```

或

```
whoami
```

**觸發時的顯示順序**：
1. 文本形式的用戶信息（名稱、郵件、ID 等）
2. **Graph API 資料卡片** ← 詳細信息

## 卡片設計

### Adaptive Card 結構

```json
{
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "Container",
      "style": "emphasis",
      "items": [
        {
          "type": "ColumnSet",
          "columns": [
            {
              "text": "👤",
              "size": "Large"
            },
            {
              "text": "使用者資料",
              "weight": "Bolder",
              "color": "Accent"
            },
            {
              "text": "[用戶名稱]",
              "isSubtle": true
            }
          ]
        }
      ]
    },
    {
      "type": "FactSet",
      "facts": [
        { "name": "📧 電子郵件", "value": "..." },
        { "name": "🏢 部門", "value": "..." },
        { "name": "💼 職位", "value": "..." },
        { "name": "📍 辦公地點", "value": "..." },
        { "name": "📞 電話", "value": "..." }
      ]
    },
    {
      "type": "TextBlock",
      "text": "🔐 Azure AD ID: ...",
      "isSubtle": true,
      "size": "Small"
    }
  ]
}
```

### 視覺效果

**卡片標題區**：
- 🎨 強調風格 (emphasis)
- 👤 圖示 + "使用者資料" 標題
- 用戶顯示名稱

**信息區**：
- 📊 Fact Set 格式
- 結構化的鍵值對
- 動態字段（跳過空值）

**底部**：
- Azure AD ID 預覽（隱密格式）
- 用於識別

## 功能特點

### 🎯 智能字段顯示

卡片會自動跳過空值字段，只展示有實際內容的數據：

| 字段 | 顯示條件 | 圖示 |
|------|---------|------|
| 電子郵件 | 始終顯示 | 📧 |
| 部門 | 始終顯示 | 🏢 |
| 職位 | 非空時顯示 | 💼 |
| 辦公地點 | 非空時顯示 | 📍 |
| 電話 | 非空時顯示 | 📞 |
| Azure AD ID | 始終顯示（隱密） | 🔐 |

### 🔄 數據來源

1. **基礎信息**（來自 Teams Channel Data）
   - 用戶名稱
   - 電子郵件
   - Azure AD Object ID

2. **詳細信息**（來自 Graph API - 如果可用）
   - 職位
   - 部門
   - 辦公地點
   - 電話號碼
   - 顯示名稱
   - 其他 Azure AD 屬性

### 🛡️ 隱私與安全

- **Azure AD ID**: 只顯示前 12 個字符 + "..." （隱密格式）
- **數據快取**: 使用 HTTP 連接池優化性能
- **錯誤處理**: 如果 Graph API 失敗，應用仍正常運行

## 配置

### 環境變量

```bash
# 啟用 Graph API 自動登錄
ENABLE_GRAPH_API_AUTO_LOGIN=True

# OAuth 連線名稱（必須與 Azure Portal 中的設定一致）
OAUTH_CONNECTION_NAME=GraphConnection
```

### Azure Portal 配置

1. 進入 **Bot Channels Registration**
2. 導航到 **Settings** → **OAuth Connection Settings**
3. 添加 OAuth 連線：
   - **連線名稱**: `GraphConnection`
   - **服務提供者**: `Azure Active Directory v2`
   - **客戶端識別碼**: 您的應用 ID
   - **客戶端密碼**: 您的應用密碼
   - **租戶 ID**: 您的 Azure AD 租戶 ID

## API 調用流程

```
用戶首次加入或執行 /me 命令
    ↓
get_user_token(turn_context)
    └─ 從 Teams 獲得 OAuth token
    ↓
get_user_email_and_id(turn_context)
    └─ 基礎信息（Teams Channel Data）
    ↓
get_user_profile(token)
    └─ 詳細信息（Graph API）
    ↓
create_user_profile_card(user_info)
    └─ 生成 Adaptive Card
    ↓
發送卡片到 Teams
```

## 技術實現

### 核心函式

#### 1. `GraphService.create_user_profile_card(user_info)`

**位置**: `graph_service.py`

**功能**: 靜態方法，根據用戶信息生成 Adaptive Card

**參數**:
```python
user_info = {
    'email': str,              # 電子郵件
    'name': str,               # 顯示名稱
    'id': str,                 # Azure AD Object ID
    'phone_numbers': list,     # 電話號碼列表
    'office_location': str,    # 辦公地點
    'job_title': str,          # 職位
    'department': str          # 部門
}
```

**回傳**: Adaptive Card JSON 結構

#### 2. `handle_special_commands()` - 增強

**位置**: `command_handler.py`

**增強功能**:
- 新增 `graph_service` 參數
- `/me` 命令支持
- 自動發送用戶資料卡片

**觸發條件**:
```python
/me, whoami, /whoami, who am i, me
```

#### 3. `on_members_added_activity()` - 增強

**位置**: `app.py`

**新增功能**:
- 首次加入時自動發送用戶資料卡片
- 與歡迎消息一起發送
- 集成 Graph API 信息

## 錯誤處理

### 案例 1: Graph API 不可用

如果 Graph API 無法連接：

✅ 應用繼續正常運行  
⚠️ 只顯示基礎信息（無詳細資料）  
📝 警告日誌記錄

### 案例 2: OAuth Token 獲取失敗

✅ 應用繼續正常運行  
⚠️ 只發送文本格式的用戶信息  
❌ 不發送卡片

### 案例 3: 用戶未授權 Graph API

✅ 應用繼續正常運行  
⚠️ 顯示基礎信息和登錄提示  
🔐 可提示用戶授權

## 性能優化

### HTTP 連接池

```python
# 重用 HTTP Session
connector = aiohttp.TCPConnector(limit=50, limit_per_host=10)
timeout = aiohttp.ClientTimeout(total=30)
self._http_session = aiohttp.ClientSession(
    connector=connector,
    timeout=timeout
)
```

**優勢**:
- ⚡ 連接重用（減少 TLS 握手）
- 🔗 連接池管理（最多 50 個連接）
- ⏱️ 30 秒超時限制
- 💾 自動內存管理

### 字段數動態調整

卡片只包含有實際內容的字段，減少網絡傳輸大小。

## 命令參考

### `/me` 命令

```
使用者輸入: /me

機器人回應:
1. ✅ 文本消息（用戶基本信息）
2. 🎫 Adaptive Card（Graph API 詳細信息）
```

### `whoami` 命令

等同於 `/me`，別名支持。

### `info` 命令

會提及 `/me` 命令用於查看 Graph API 資料卡片。

## 測試

### 本地測試

在模擬器中測試 `/me` 命令：

```bash
# 1. 啟動機器人
python -m aiohttp.web -P 5168 app:init_func

# 2. 使用 Bot Framework Emulator
# 連接到: http://localhost:3978/api/messages

# 3. 發送命令
/me
```

### Teams 測試

1. 添加機器人到 Teams 頻道
2. @ 機器人並發送 `/me`
3. 驗證卡片是否正確顯示

## 故障排除

### 問題：卡片未顯示

**可能原因**:
- ❌ `ENABLE_GRAPH_API_AUTO_LOGIN=False`
- ❌ OAuth 連線未配置
- ❌ Graph API Token 獲取失敗

**解決方案**:
1. 檢查 .env 文件中的設定
2. 驗證 Azure Portal 中的 OAuth 連線
3. 查看應用日誌中的錯誤信息

### 問題：顯示 "N/A"

**原因**: Graph API 未返回該字段  
**解決方案**: 確認用戶在 Azure AD 中的資料完整

### 問題：Azure AD ID 為空

**原因**: 可能是非 Azure AD 用戶  
**解決方案**: 使用標準 Teams 身份驗證，而不是 OAuth

## 相關文件

- [graph_service.py](graph_service.py) - Graph API 服務實現
- [command_handler.py](command_handler.py) - 命令處理和卡片生成
- [app.py](app.py) - 主應用程式邏輯

## 更新歷史

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-01-05 | 1.0 | 首次實現 Graph API 用戶資料卡片功能 |

---

**功能狀態**: ✅ 已實現  
**支持平台**: Microsoft Teams (Teams Web, Teams Desktop)  
**需求**: Graph API OAuth 連線已配置
