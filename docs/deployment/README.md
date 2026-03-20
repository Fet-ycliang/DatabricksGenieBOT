# 部署文件清單和說明

本目錄包含所有部署到 Azure Web App 和 Teams 所需的文件和指南。

## 📄 文件結構

```
docs/deployment/
├── QUICK_START.md                    ⭐ 5分鐘快速版本 (從這裡開始!)
├── DEPLOYMENT_GUIDE.md               📖 詳細部署指南
├── DEPLOYMENT_CHECKLIST.md           ✅ 完整檢查清單
├── AZURE_AD_SETUP.md                 🔐 OAuth 配置指南
├── teams_deployment.md               🎨 Teams 應用整合
└── README.md                         📋 此文件
```

## 📋 推薦閱讀順序

### 🚀 第一次部署？
1. **[QUICK_START.md](./QUICK_START.md)** ⭐ (5 分鐘)
   - 快速概述 5 步部署流程
   - 適合有 Azure 經驗的開發人員

2. **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)** ✅ (逐項完成)
   - 詳細的檢查清單格式
   - 每個步驟都有複選框
   - 包含所有細節配置

### 📖 需要詳細說明？
3. **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** (深入學習)
   - 步驟解釋和原因
   - 三種部署方式比較
   - 生產環境最佳實踐

4. **[AZURE_AD_SETUP.md](./AZURE_AD_SETUP.md)** (OAuth 配置)
   - OAuth 和 Microsoft Graph 設定
   - 權限配置詳解
   - 常見問題解答

### 🎨 Teams 整合？
5. **[teams_deployment.md](./teams_deployment.md)** (Teams 特定)
   - Teams 應用程式套件準備
   - Manifest 文件說明
   - Teams 頻道整合

---

## 🎯 快速導航

### 我想要...

**快速上線** → 閱讀 [QUICK_START.md](./QUICK_START.md)
- 5 分鐘快速指南
- 關鍵步驟和代碼片段
- 立即開始部署

**一步步完成** → 使用 [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)
- 詳細的逐步指南
- 複選框追蹤進度
- 確保沒有遺漏任何步驟

**理解整個過程** → 閱讀 [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- 為什麼要做這個步驟
- 替代方案說明
- 生產環境考慮

**配置 OAuth 登入** → 參考 [AZURE_AD_SETUP.md](./AZURE_AD_SETUP.md)
- App Registration 詳細設定
- 權限配置說明
- 故障排查

**在 Teams 中測試** → 查看 [teams_deployment.md](./teams_deployment.md)
- Manifest 檔案說明
- 應用程式套件準備
- 上傳和發佈步驟

---

## 🔑 關鍵資源位置

### 在代碼倉庫中
```
DatabricksGenieBOT/
├── manifest.json                     ← Teams 應用程式定義 (編輯此檔)
├── .env                              ← 本地環境變數
├── .env.example                      ← 環境變數範本
├── web.config                        ← IIS 配置
├── Dockerfile                        ← Docker 部署配置
└── pyproject.toml                    ← Python 依賴
```

### 在 Azure 中
```
Azure Portal
├── Bot Channels Registration         ← 建立此資源
│   └── Configuration                 ← 設定訊息端點和 OAuth
├── App Service                       ← 部署代碼
│   └── Configuration                 ← 設定環境變數
└── Azure Active Directory
    └── App registrations             ← OAuth 應用程式
```

---

## 📊 檢查清單摘要

部署包含以下主要階段：

### ✅ 準備階段 (30 分鐘)
- [ ] 取得 Databricks 認證
- [ ] 建立 Azure 帳戶和訂閱
- [ ] 準備本地環境

### ✅ Azure 設定階段 (30 分鐘)
- [ ] 建立 Bot Service
- [ ] 建立 App Service
- [ ] 配置 OAuth / Azure AD

### ✅ 代碼部署階段 (10 分鐘)
- [ ] 部署代碼到 App Service
- [ ] 配置環境變數
- [ ] 驗證健康檢查

### ✅ Teams 整合階段 (15 分鐘)
- [ ] 準備 manifest.json
- [ ] 準備圖標
- [ ] 上傳到 Teams

### ✅ 測試驗證階段 (10 分鐘)
- [ ] 測試基本功能
- [ ] 測試 OAuth 登入
- [ ] 測試 Genie 查詢

**總計**：約 90 分鐘 (1.5 小時)

---

## 🚨 常見問題

### 1️⃣ 我應該從哪個文件開始？
→ 如果你熟悉 Azure，從 [QUICK_START.md](./QUICK_START.md) 開始  
→ 如果你是新手，從 [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) 開始

### 2️⃣ OAuth 是必須的嗎？
→ 建議配置，用於存取使用者資訊  
→ 若不需要，可以跳過 [AZURE_AD_SETUP.md](./AZURE_AD_SETUP.md)

### 3️⃣ 我可以在免費層運行嗎？
→ Bot Service 可以用免費層 (F0)  
→ App Service 建議 B1 基本層或以上 ($10-20/月)

### 4️⃣ Teams 應用程式必須發佈到應用商店嗎？
→ 不需要，可以先上傳為自訂應用程式進行測試  
→ 組織內部使用也可以跳過應用商店審核

### 5️⃣ 我已經部署了，出現問題怎麼辦？
→ 查看 [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) 中的故障排查部分  
→ 或查看 [troubleshooting.md](../troubleshooting.md) 瞭解更多常見問題

---

## 💾 環境變數參考

所有需要的環境變數一覽：

```
# Bot Framework (必須)
APP_ID=<Bot App ID>
APP_PASSWORD=<Bot App Password>
APP_TYPE=SingleTenant
APP_TENANTID=bb5ad653-221f-4b94-9c26-f815e04eef40

# Databricks (必須)
DATABRICKS_SPACE_ID=<Your Space ID>
DATABRICKS_HOST=<Your Databricks URL>
DATABRICKS_TOKEN=<Your PAT Token>

# OAuth (推薦)
OAUTH_CONNECTION_NAME=GraphConnection
ENABLE_GRAPH_API_AUTO_LOGIN=True

# 應用程式
PORT=8000
ADMIN_CONTACT_EMAIL=support@company.com
TIMEZONE=Asia/Taipei
SAMPLE_QUESTIONS=question1;question2;question3

# 功能開關
ENABLE_FEEDBACK_CARDS=True
ENABLE_GENIE_FEEDBACK_API=True

# 日誌 (生產環境用 False)
VERBOSE_LOGGING=False
LOG_FILE=bot_debug.log
```

詳細說明見 [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md#-第-3-階段環境變數設定)

---

## 📞 需要幫助？

- 📖 閱讀相關文檔
- 🔍 查看 [troubleshooting.md](../troubleshooting.md)
- 💬 聯絡 `ADMIN_CONTACT_EMAIL`
- 🐛 檢查 `bot_debug.log` (VERBOSE_LOGGING=True 時)

---

## 📝 版本信息

| 文件 | 版本 | 更新日期 | 狀態 |
|------|------|--------|------|
| QUICK_START.md | 1.0 | 2026-02-09 | ✅ 完成 |
| DEPLOYMENT_GUIDE.md | 1.0 | 2026-02-09 | ✅ 完成 |
| DEPLOYMENT_CHECKLIST.md | 1.0 | 2026-02-09 | ✅ 完成 |
| AZURE_AD_SETUP.md | 1.0 | 2026-02-09 | ✅ 完成 |
| teams_deployment.md | 1.0 | 2025-12-xx | ✅ 已有 |

---

## 🎯 下一步

選擇你的起點：

- **🚀 [快速開始 - 5 分鐘版本](./QUICK_START.md)**
- **✅ [詳細檢查清單 - 逐項完成](./DEPLOYMENT_CHECKLIST.md)**
- **📖 [完整指南 - 深入學習](./DEPLOYMENT_GUIDE.md)**

祝部署順利！ 🎉
