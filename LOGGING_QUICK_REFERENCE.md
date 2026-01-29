# 快速參考：Bot Framework 日誌記錄

## 🎯 問題已解決

✅ 本地日誌現在可以正常輸出  
✅ 錯誤信息包含完整的堆疊跟蹤  
✅ 日誌同時寫入控制台和文件  

---

## 📋 核心文件

| 文件 | 用途 |
|------|------|
| **setup_logging.py** | 日誌配置模組 |
| **app.py** | Bot 主應用程序（已更新） |
| **genie_service.py** | Genie API 服務（已更新） |
| **.env** | 環境配置（已更新） |

---

## 🚀 快速開始

### 1. 標準運行
```bash
python -m aiohttp.web -P 5168 app:init_func
```

**看到的輸出：**
```
[2026-01-28 17:08:56] INFO     [app] === 新的訊息活動開始 ===
[2026-01-28 17:08:56] INFO     [app] 訊息活動文字: 查詢上個月的用量
[2026-01-28 17:08:56] INFO     [genie_service] 📥 新查詢請求
```

### 2. 詳細調試模式
```bash
# 編輯 .env
VERBOSE_LOGGING=True

# 運行
python -m aiohttp.web -P 5168 app:init_func
```

**會看到額外的調試信息**

### 3. 測試日誌
```bash
python test_logging.py
```

### 4. 診斷環境
```bash
python bot_diagnostic.py
```

---

## 📁 日誌文件位置

```
D:\azure_code\DatabricksGenieBOT\
├── bot_debug.log          # 主應用程序日誌
├── bot_diagnostic.log     # 診斷工具日誌
└── test_logging.log       # 測試日誌
```

---

## 🔍 查看日誌

### Windows 命令行
```bash
# 查看實時日誌
type bot_debug.log

# 查看最後 100 行
powershell -Command "Get-Content bot_debug.log -Tail 100"

# 搜索錯誤
findstr "ERROR\|WARN" bot_debug.log
```

### 在 VS Code 中
1. 打開 `bot_debug.log` 文件
2. 使用 Ctrl+F 搜索 "ERROR" 或 "WARN"

---

## ⚙️ 環境變數配置

### .env 文件（本地配置，不提交到 git）

詳見 `.env.example` 文件以了解所有可用配置選項。

### 必需的配置
- DATABRICKS_HOST - 您的 Databricks 工作區 URL
- DATABRICKS_TOKEN - 您的 Databricks API token（從 Settings > Developer > Access tokens 生成）
- DATABRICKS_SPACE_ID - 您的 Databricks Genie Space ID

### 可選的配置
```bash
# 日誌配置
VERBOSE_LOGGING=False       # True = DEBUG 級別，False = INFO 級別
LOG_FILE=bot_debug.log      # 日誌檔案路徑

# Bot Framework
APP_ID=                     # 為空表示使用模擬器模式
APP_PASSWORD=               # 為空表示使用模擬器模式
APP_TYPE=SingleTenant
APP_TENANTID=your_tenant_id

# 時區
TIMEZONE=Asia/Taipei
```

---

## 📊 日誌級別

| 級別 | 前綴 | 何時出現 |
|------|------|---------|
| **DEBUG** | [DEBUG] | `VERBOSE_LOGGING=True` 時 |
| **INFO** | [INFO] | 默認，信息流 |
| **WARNING** | [WARN] | 警告信息 |
| **ERROR** | [ERR] | 錯誤 |

---

## 🔧 常見問題

### Q: 日誌不出現
**A:** 
1. 檢查 APP_ID 是否設置（如果為空，應使用模擬器）
2. 確保 Databricks token 有效
3. 運行 `python bot_diagnostic.py` 檢查配置

### Q: 如何禁用某個模塊的日誌
**A:** 編輯 `setup_logging.py` 中的日誌級別：
```python
logging.getLogger("aiohttp").setLevel(logging.WARNING)
```

### Q: 日誌文件太大
**A:** 刪除舊日誌文件或修改 `.env` 中的 `LOG_FILE` 路徑

---

## 🔐 安全提醒

⚠️ **重要**：
- `.env` 文件已在 `.gitignore` 中，不要提交敏感信息到 git
- 定期更換 Databricks token（建議每 90 天）
- 如果 token 泄露，立即在 Databricks 中撤銷它
- 使用 `.env.example` 作為模板配置

---

**修復完成**: 2026-01-29  
**下一步**: 啟動應用程序並檢查日誌輸出！
