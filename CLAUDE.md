# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案概要

這是一個 Microsoft Teams Bot，整合 Databricks Genie API 提供對話式資料查詢功能。機器人使用 FastAPI 作為 Web 框架，Bot Framework SDK 處理 Teams 訊息，並透過 Databricks SDK 與 Genie API 互動。

**⚠️ 重要架構決策：Bot Framework SDK 遷移狀態**

- **當前狀態**: 使用 Bot Framework SDK（已於 2026年1月5日被 Microsoft 封存 EOL）
- **未來方向**: 計畫遷移到 Microsoft 365 Agents SDK
- **🔴 重要更新 (2026-02-16)**: POC 評估發現 Python SDK 尚未準備好
  - SDK 版本 0.7.0 僅包含 Activity Protocol 類型定義
  - 缺少核心 Agent Framework (AgentApplication, Storage, Adapters)
  - **建議延後遷移至 2026 Q4 或 2027 Q1**
- **✅ M365 代碼已移除 (2026-02-16)**: 基於 POC 評估結果
  - 移除了實驗性的 M365 Agent Framework 代碼
  - 原因：SDK 不成熟 + 0% 整合度（僵屍代碼）
  - 歷史文檔保留在 `migration_archive/` 和 `docs/` 目錄
  - 將在 SDK 成熟後重新評估遷移
- **新時間表**: 等待 Python SDK 達到 1.0+ 版本並具備完整功能
- **參考**: 詳見 `poc/POC_STATUS.md`, `poc/FINDINGS_SUMMARY.md` 和 `docs/m365_agents_sdk_evaluation_report.md`

## 常用開發命令

### 安裝和設定
```bash
# 安裝依賴（使用 uv，推薦）
uv sync

# 或使用 pip
pip install -e .
```

### 執行應用程式
```bash
# 啟動 Bot 伺服器（預設 port 8000）
uv run uvicorn app.main:app --port 8000

# 使用重新載入模式（開發用）
uv run uvicorn app.main:app --port 8000 --reload
```

### 測試
```bash
# 執行所有測試
pytest

# 執行特定測試檔案
pytest tests/unit/test_health_check.py

# 執行效能測試
pytest tests/performance/

# 環境診斷
python scripts/diagnose.py
```

## 核心架構

### 應用程式進入點
- **app/main.py**: FastAPI 應用程式主進入點，定義 API 路由和中介軟體
- **app/bot_instance.py**: Bot 實例初始化
- **app/core/adapter.py**: Bot Framework Adapter 配置

### API 路由層 (app/api/)
- **bot.py**: 處理 Bot Framework 的 `/api/messages` 端點
- **genie.py**: Genie 查詢的直接 API 端點（測試用）
- **health.py**: 健康檢查端點

### 服務層 (app/services/)
- **genie.py**:
  - 封裝所有與 Databricks Genie API 的互動
  - 包含 `GenieService` 類別，處理對話建立、訊息傳送、查詢結果解析
  - 包含 `QueryMetrics` 類別用於效能指標收集
  - 使用 HTTP 連接池最佳化效能
- **graph.py**: Microsoft Graph API 整合（使用者認證和個人資料）
- **health_check.py**: 系統健康檢查邏輯

### 資料模型 (app/models/)
- **user_session.py**: 使用者會話管理，追蹤對話狀態和歷史

### 核心元件 (app/core/)
- **config.py**: 環境變數和配置管理（DefaultConfig 類別）
- **adapter.py**: Bot Framework Adapter 配置
- **auth_middleware.py**: 統一認證中介軟體（Azure AD Token 驗證）
- **exceptions.py**: 統一異常處理系統（錯誤碼和異常類別）
- **logging_middleware.py**: 請求日誌和追蹤中介軟體（request_id 生成）

### Bot Cards (bot/cards/)
- Adaptive Cards 生成邏輯
- 圖表生成器（使用 matplotlib/seaborn）

## 當前架構：Bot Framework SDK

### 訊息處理流程

```
Teams 訊息
    ↓
Bot Framework Adapter (app/api/bot.py)
    ↓
MyBot (ActivityHandler) (bot/handlers/bot.py)
    ↓
├─ SSO 認證 (bot/dialogs/sso_dialog.py) - Bot Framework Dialog
├─ 命令處理 (bot/handlers/commands.py)
└─ Genie 查詢 (app/services/genie.py)
       ↓
    Databricks Genie API
```

### 核心改善（2026-02-16）

**已實作的架構改善**：
1. ✅ **認證保護** (`app/core/auth_middleware.py`)
   - Azure AD Token 驗證
   - 統一認證依賴注入

2. ✅ **Session 管理** (`app/utils/session_manager.py`)
   - 自動清理過期 sessions（防止記憶體洩漏）
   - 4 小時閒置超時

3. ✅ **統一錯誤處理** (`app/core/exceptions.py`)
   - 25+ 錯誤碼和專用異常類別
   - 結構化錯誤回應

4. ✅ **請求追蹤** (`app/core/logging_middleware.py`)
   - 每個請求唯一 request_id
   - 結構化日誌輸出
   - 自動性能計時

5. ✅ **代碼去重** (`app/utils/chart_analyzer.py`)
   - 消除 250+ 行重複代碼
   - 統一圖表分析邏輯

### Bot Framework SDK 的 EOL 狀態

- **封存日期**: 2026年1月5日
- **支援結束**: 2025年12月31日
- **影響**: 不會收到安全更新或功能更新
- **風險等級**: 中等（短期內仍可運作）
- **遷移計畫**: 等待 M365 Agents SDK Python 版本成熟（目標：2026 Q4 或 2027 Q1）

**M365 代碼狀態**：
- ❌ 實驗性 M365 Agent Framework 代碼已移除（2026-02-16）
- 原因：Python SDK 0.7.0 不成熟，缺少核心功能
- 歷史文檔保留在 `migration_archive/` 和 `docs/m365_agents_sdk_evaluation_report.md`

## 關鍵設計決策

### 1. 單一權杖多用戶架構
- 使用單一 `DATABRICKS_TOKEN` 為所有使用者提供服務
- 每個使用者透過 `UserSession` 維護獨立的對話上下文
- 使用者電子郵件附加到查詢前面以便在 Databricks 中追蹤：`[user@company.com] query`
- **安全考量**: 權杖應存放在 Azure Key Vault 等安全儲存中

### 2. 會話管理和記憶體考量
- 會話儲存在記憶體中（未持久化）
- 預設閒置 4 小時後自動清除會話
- **已知限制**: 長時間執行可能導致記憶體累積，建議實施自動清理機制（參見 docs/architecture/optimization.md）

### 3. 非同步 HTTP 處理
- 使用 `httpx.AsyncClient` 進行非同步 HTTP 請求
- 實施連接池重用以減少連接開銷
- 配置超時設定防止無限等待（connect: 5s, read: 10s, write: 10s, total: 30s）

### 4. 圖表視覺化
- 使用 Matplotlib 和 Seaborn 生成圖表圖片
- 自動判斷資料類型並選擇適合的圖表類型（長條圖、圓餅圖、折線圖）
- 透過 Adaptive Cards 在 Teams 中顯示圖表

### 5. 回饋系統
- 整合讚/倒讚回饋機制
- 回饋直接發送到 Databricks Genie API 的 `send_message_feedback` 端點
- 可透過環境變數 `ENABLE_FEEDBACK_CARDS` 和 `ENABLE_GENIE_FEEDBACK_API` 控制

## 環境變數設定

關鍵環境變數（詳見 `.env.example`）：
- **DATABRICKS_TOKEN** (必要): Databricks 個人存取權杖
- **DATABRICKS_HOST**: Databricks 工作區 URL
- **DATABRICKS_SPACE_ID**: Genie Space ID
- **APP_ID**, **APP_PASSWORD**, **APP_TENANTID**: Azure Bot Service 憑證
- **PORT**: 應用程式連接埠（預設 3978）
- **ENABLE_GRAPH_API_AUTO_LOGIN**: 啟用 MS Graph API 自動登入
- **OAUTH_CONNECTION_NAME**: Azure OAuth Connection 名稱

## 效能優化建議

專案已識別並部分實施的優化（詳見 docs/architecture/optimization.md）：

1. **日誌採樣**: 減少 99% 日誌 I/O（每 60 秒或 1% 採樣記錄統計）
2. **連接超時配置**: 防止無限等待，加速失敗檢測
3. **HTTP 連接池**: 重用連接減少開銷
4. **會話清理機制**: 需實施自動清理避免 OOM

## 測試架構

- **tests/unit/**: 單元測試（健康檢查、圖表生成、認證技能等）
- **tests/performance/**: 效能測試和基準測試
- **tests/test_*.py**: 整合測試（Bot 核心、技能整合、完整流程）

## 部署相關

- **Azure Web App**: 支援透過 Azure CLI 部署（`az webapp up`）
- **Dockerfile**: 容器化部署支援
- **web.config**: IIS 部署配置（若使用 Windows Server）
- **GitHub Actions**: CI/CD 工作流程（.github/workflows/）

部署前檢查清單請參考：docs/deployment/DEPLOYMENT_CHECKLIST.md

## 已知問題和限制

1. **記憶體管理**: 會話無自動清理機制，長時間執行可能導致 OOM
2. **監控缺失**: 缺少應用程式級別的監控和可觀測性
3. **API 容錯**: 缺少 retry 機制和 circuit breaker
4. **測試覆蓋率**: 部分整合測試可能需要 mock 外部服務

詳細故障排除請參考：docs/troubleshooting.md

## 重要文件

- **README.md**: 專案總覽和快速開始指南
- **docs/architecture/optimization.md**: 完整效能優化分析和實施指南
- **docs/troubleshooting.md**: 故障排除和常見問題解決方案
- **docs/deployment/**: Azure 和 Teams 部署完整指南
- **ENV_CONFIGURATION.md**: 環境變數詳細說明

## 開發注意事項

- Python 版本需求: 3.11+
- 本地開發需要配置 `.env` 檔案（複製 `.env.example`）
- 使用 `uv` 包管理器以獲得更快的依賴解析
- Bot Framework Emulator 可用於本地測試（APP_ID 和 APP_PASSWORD 留空）
- 敏感資訊（權杖、密碼）不應寫入日誌或提交到版本控制
