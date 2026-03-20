# Databricks Genie Bot 架構圖

**最後更新**：2026-02-16

## 系統架構概覽

```
┌─────────────────────────────────────────────────────────────────┐
│                        Microsoft Teams                           │
│                      (使用者介面)                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP POST /api/messages
                             │ (Bot Framework Protocol)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI 應用程式                              │
│                    (app/main.py)                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ 日誌中介軟體      │  │ 異常處理器        │                     │
│  │ RequestLogging   │  │ BotException     │                     │
│  │ Middleware       │  │ Handler          │                     │
│  │                  │  │                  │                     │
│  │ • 生成 request_id│  │ • 統一錯誤格式   │                     │
│  │ • 記錄請求/回應  │  │ • 25+ 錯誤碼     │                     │
│  │ • 性能計時       │  │ • 安全錯誤訊息   │                     │
│  └──────────────────┘  └──────────────────┘                     │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API 路由層                              │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  /api/messages    →  Bot Framework 端點                   │   │
│  │  /api/genie/*     →  Genie 測試端點                       │   │
│  │  /health          →  健康檢查                             │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Bot Framework Adapter                          │
│              (app/core/adapter.py)                               │
│                                                                   │
│  • JWT Token 驗證                                                │
│  • Activity 反序列化                                             │
│  • 回應序列化                                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MyBot (Activity Handler)                      │
│                  (bot/handlers/bot.py)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ SSO Dialog   │    │ 命令處理      │    │ Genie 查詢    │     │
│  │ (SSODialog)  │    │ (commands.py) │    │ 處理         │     │
│  │              │    │               │    │              │     │
│  │ • Teams SSO  │    │ • /setuser    │    │ • 問題解析   │     │
│  │ • Token 管理 │    │ • reset       │    │ • 結果格式化 │     │
│  │              │    │ • whoami      │    │ • 圖表生成   │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│                                                                   │
└────────────────┬──────────────────────┬──────────────────────────┘
                 │                      │
                 ▼                      ▼
    ┌────────────────────┐  ┌────────────────────┐
    │  SessionManager    │  │  GenieService      │
    │  (session_manager) │  │  (genie.py)        │
    ├────────────────────┤  ├────────────────────┤
    │                    │  │                    │
    │ • 自動清理過期    │  │ • HTTP 連接池      │
    │   sessions         │  │ • 對話管理        │
    │ • 4 小時超時      │  │ • 查詢執行        │
    │ • 統計資訊        │  │ • 結果解析        │
    │                    │  │                    │
    └────────────────────┘  └──────────┬─────────┘
                                       │
                                       │ HTTP
                                       ▼
                          ┌────────────────────────┐
                          │  Databricks Genie API  │
                          │  (genie.databricks.com)│
                          ├────────────────────────┤
                          │                        │
                          │ • 對話建立             │
                          │ • 查詢執行             │
                          │ • 結果返回             │
                          │ • 建議問題             │
                          │                        │
                          └────────────────────────┘
```

## 資料流程

### 1. 使用者發送訊息

```
Teams → POST /api/messages → Bot Framework Adapter → MyBot.on_message_activity()
```

### 2. 認證檢查與 Email 提取

```
MyBot → 檢查 user_session
   ├─ 無 session → 觸發 SSO Dialog → 取得 Token
   │                                      │
   │                                      ▼
   │                              EmailExtractor.get_email()
   │                                      │
   │                              ├─ 1. JWT Token 解碼 (< 1ms)
   │                              ├─ 2. Activity Channel Data (< 1ms)
   │                              ├─ 3. Graph API (200-500ms, 備用)
   │                              └─ 4. Placeholder (最後備案)
   │                                      │
   │                                      ▼
   │                              建立 UserSession(user_id, email, name)
   │
   └─ 有 session → 繼續處理
```

### 3. 命令處理

```
MyBot → handle_special_commands()
   ├─ /setuser → 設定使用者 email
   ├─ reset    → 清除對話
   └─ whoami   → 顯示使用者資訊
```

### 4. Genie 查詢流程

```
MyBot → GenieService.ask()
   │
   ├─ 1. 建立/取得對話 ID
   │     └─ POST /conversations (首次) 或使用現有 ID
   │
   ├─ 2. 發送查詢
   │     └─ POST /conversations/{id}/messages
   │          └─ 加入 [user@email.com] 前綴
   │
   ├─ 3. 輪詢結果
   │     └─ GET /conversations/{id}/messages/{msg_id}
   │          └─ 等待狀態 = "COMPLETED"
   │
   ├─ 4. 取得查詢結果
   │     └─ GET /conversations/{id}/messages/{msg_id}/query-result
   │
   ├─ 5. 解析回應
   │     ├─ 文字訊息 → Markdown Card
   │     ├─ 查詢結果 → 表格 + 圖表分析
   │     │    └─ ChartAnalyzer.analyze_suitability()
   │     │         ├─ 識別類別列和數值列
   │     │         └─ 決定圖表類型 (bar/pie/line)
   │     └─ 建議問題 → Action Buttons
   │
   └─ 6. 發送回應到 Teams
        └─ Adaptive Cards (表格、圖表、建議問題)
```

### 5. 圖表生成流程

```
ChartAnalyzer → 分析數據適用性
   │
   ├─ 檢查列類型（字串 vs 數值）
   ├─ 檢查數據量（>= 2 筆）
   └─ 決定圖表類型
        ├─ 時間序列 → 折線圖
        ├─ 2-8 類別 + 無負值 → 圓餅圖
        └─ 其他 → 長條圖
   │
   ▼
ChartGenerator → 生成圖片
   │
   ├─ Matplotlib/Seaborn 繪圖
   ├─ 轉換為 Base64
   └─ 嵌入 Adaptive Card
```

## 狀態管理

### Session 生命週期

```
使用者首次訊息
   │
   ▼
建立 UserSession
   │
   ├─ user_id: Teams 使用者 ID
   ├─ email: 使用者 email
   ├─ conversation_id: Genie 對話 ID
   ├─ created_at: 建立時間
   └─ last_activity: 最後活動時間
   │
   ▼
儲存到記憶體字典
   │
   ├─ BOT.user_sessions[user_id]
   └─ BOT.email_sessions[email]
   │
   ▼
SessionManager 自動清理
   │
   ├─ 每小時檢查一次
   ├─ 超過 4 小時閒置 → 刪除
   └─ 記錄清理統計
```

### 對話狀態

```
Conversation State (Bot Framework)
   │
   ├─ DialogState → SSO Dialog 狀態
   └─ (其他對話狀態)

User State (Bot Framework)
   │
   └─ (使用者偏好設定)

Memory State (自定義)
   │
   ├─ user_sessions → 對話 ID, email
   └─ email_sessions → 反向查詢
```

## 錯誤處理流程

```
異常發生
   │
   ▼
捕獲異常類型
   │
   ├─ BotException → 應用程式異常
   │    └─ 返回: { error_code, message, details, request_id }
   │
   ├─ HTTPException → FastAPI/Starlette 異常
   │    └─ 返回: { error_code: HTTP_xxx, message, request_id }
   │
   ├─ RequestValidationError → Pydantic 驗證錯誤
   │    └─ 返回: { error_code: INPUT_001, errors, request_id }
   │
   └─ Exception → 未預期的異常
        └─ 返回: { error_code: SYSTEM_001, message: "系統內部錯誤" }
             └─ (不洩漏堆疊追蹤)
```

## 日誌和追蹤

### 請求追蹤

```
HTTP 請求進入
   │
   ▼
RequestLoggingMiddleware
   │
   ├─ 生成 UUID request_id
   ├─ 加入 request.state.request_id
   │
   ▼
記錄請求開始
   │
   └─ [request_id] --> METHOD /path
   │
   ▼
處理請求
   │
   ├─ 計時開始
   ├─ 執行路由處理
   └─ 計時結束
   │
   ▼
記錄請求完成
   │
   └─ [request_id] <-- METHOD /path STATUS (duration_ms)
   │
   ▼
加入回應 header
   │
   └─ X-Request-ID: {request_id}
```

### 日誌格式

**結構化日誌**：
```json
{
  "timestamp": "2026-02-16T10:30:45.123Z",
  "level": "INFO",
  "request_id": "a1b2c3d4-...",
  "method": "POST",
  "path": "/api/messages",
  "status_code": 200,
  "duration_ms": 1234,
  "message": "請求完成"
}
```

## 安全機制

### 1. 認證保護（已廢棄 M365 端點後不適用）

```
API 請求 → auth_middleware
   │
   ├─ 檢查 Authorization header
   ├─ 驗證 JWT Token
   │    └─ Azure AD 公鑰驗證
   ├─ 檢查 audience, exp
   └─ 提取用戶資訊
        └─ { user_id, email, name, tenant_id }
```

### 2. Bot Framework 驗證

```
Teams 訊息 → Bot Framework Adapter
   │
   ├─ 驗證 JWT 簽名
   ├─ 檢查 issuer (Microsoft)
   └─ 驗證 service URL
```

### 3. 錯誤訊息安全

- ❌ 不洩漏堆疊追蹤
- ❌ 不洩漏內部路徑
- ❌ 不洩漏配置資訊
- ✅ 提供錯誤碼和使用者友善訊息
- ✅ 詳細錯誤記錄在伺服器日誌（含 request_id）

## 部署架構

```
                    ┌──────────────────┐
                    │   Azure Portal   │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌──────────────────┐  ┌──────────────┐
│ Azure Bot     │  │ Azure Web App    │  │ Azure Key    │
│ Service       │  │ (FastAPI)        │  │ Vault        │
│               │  │                  │  │              │
│ • Bot 註冊    │  │ • Python 3.11    │  │ • Databricks │
│ • Channels    │  │ • uvicorn        │  │   Token      │
│ • OAuth       │  │ • 自動擴展       │  │ • APP_ID     │
└───────────────┘  └──────────────────┘  └──────────────┘
        │                    │
        │                    │
        ▼                    ▼
┌────────────────────────────────────────┐
│         Microsoft Teams                 │
│  (Channel: MS Teams, Emulator, etc.)   │
└────────────────────────────────────────┘
```

## 相關文檔

- [專案指南 (CLAUDE.md)](../CLAUDE.md)
- [架構優化 (optimization.md)](architecture/optimization.md)
- [認證系統 (authentication.md)](authentication.md)
- [M365 移除摘要 (m365_removal_summary.md)](m365_removal_summary.md)
- [故障排除 (troubleshooting.md)](troubleshooting.md)

---

**注意**：本架構圖反映 2026-02-16 的最新狀態，包含所有架構改善和 M365 代碼移除後的結構。
