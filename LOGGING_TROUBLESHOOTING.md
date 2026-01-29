# Bot Framework 日誌記錄故障排查指南

## 📋 診斷步驟

### 第 1 步：驗證環境配置

```bash
python bot_diagnostic.py
```

**應看到的輸出：**
```
╔════════════════════════════════════════════╗
║     Bot Framework 環境診斷工具             ║
╚════════════════════════════════════════════╝

[✓] Python 版本: 3.12.x
[✓] 項目根目錄: D:\azure_code\DatabricksGenieBOT
[✓] 必需的模塊已安裝
[✓] .env 文件已找到
[✓] Databricks 工作區: https://adb-xxxx.azuredatabricks.net/
```

### 第 2 步：檢查日誌配置

```bash
python -c "from setup_logging import setup_logging; setup_logging(); print('✓ 日誌初始化成功')"
```

### 第 3 步：測試日誌功能

```bash
python test_logging.py
```

**預期輸出：**
```
✓ 日誌寫入成功
✓ 日誌文件 test_logging.log 已創建
✓ 日誌級別設置正確
```

---

## 🐛 常見問題及解決方案

### 問題 1：日誌完全不輸出

#### 症狀
- 運行應用程序時沒有任何日誌消息
- 控制台為空

#### 解決方案

**步驟 A：驗證 .env 文件**
```bash
# Windows - 檢查 .env 是否存在
dir .env

# 檢查內容
type .env
```

**步驟 B：確保 DATABRICKS_HOST 已設置**
```bash
# .env 應包含
DATABRICKS_HOST=https://adb-2654999172504234.14.azuredatabricks.net
DATABRICKS_SPACE_ID=your_space_id
DATABRICKS_TOKEN=dapi_xxxxxxxxxxxxxxxx
```

**步驟 C：檢查 setup_logging 導入**
```python
# app.py 頂部應有：
from setup_logging import setup_logging

# 且在 init_func() 中調用：
setup_logging(verbose=os.getenv('VERBOSE_LOGGING', 'False').lower() == 'true')
```

### 問題 2：只有控制台輸出，沒有文件輸出

#### 症狀
- 控制台顯示日誌
- 但 bot_debug.log 文件未創建或為空

#### 解決方案

**步驟 A：檢查日誌文件路徑**
```bash
# Windows - 檢查文件是否存在
dir *.log

# 如果不存在，檢查寫入權限
icacls .
```

**步驟 B：更改日誌文件位置**

編輯 `.env`：
```bash
LOG_FILE=./logs/bot_debug.log
```

創建日誌目錄：
```bash
mkdir logs
```

**步驟 C：重新啟動應用程序**
```bash
python -m aiohttp.web -P 5168 app:init_func
```

### 問題 3：日誌包含 "KeyError: DATABRICKS_HOST"

#### 症狀
```
KeyError: 'DATABRICKS_HOST'
```

#### 解決方案

**步驟 A：驗證 .env 文件編碼**
```bash
# 確保使用 UTF-8 編碼（不是 UTF-16）
file .env

# 如果編碼錯誤，重新創建文件
del .env
# 在 VS Code 中創建新的 .env 文件，確保編碼為 UTF-8
```

**步驟 B：檢查 .env 語法**
```bash
# 確保沒有空行或特殊字符
type .env | findstr "DATABRICKS"
```

### 問題 4：日誌顯示 "Invalid access token"

#### 症狀
```
[ERROR] Invalid access token. [ReqId: xxxxxxxx]
```

#### 解決方案

**步驟 A：驗證 token 格式**
- Databricks token 必須以 `dapi_` 開頭
- 應該是 32 個字符的長隨機字符串

**步驟 B：檢查 token 有效期**
- 在 Databricks 工作區進入 Settings > Developer > Access tokens
- 檢查 token 是否已過期

**步驟 C：生成新 token**

1. 登錄 Databricks 工作區
2. 進入設置（用戶名 > Settings）
3. 左側選擇 "Developer"
4. 點擊 "Generate new token"
5. 設置過期時間（建議 90 天）
6. 複製生成的 token
7. 更新 `.env` 文件：
   ```bash
   DATABRICKS_TOKEN=dapi_your_new_token_here
   ```

**步驟 D：驗證新 token**
```bash
python verify_databricks_token.py
```

預期輸出：
```
✓ Token 驗證成功
✓ 工作區連接正常
```

### 問題 5：日誌級別不對

#### 症狀
- 設置 `VERBOSE_LOGGING=True` 但仍然只看到 INFO 日誌
- 或反之，看到太多 DEBUG 日誌

#### 解決方案

**步驟 A：確認環境變數**
```bash
# Windows - 檢查環境變數
echo %VERBOSE_LOGGING%

# 或直接檢查 .env
findstr "VERBOSE_LOGGING" .env
```

**步驟 B：重新啟動應用程序**
```bash
# 環境變數更改後必須重新啟動應用程序
# 使用 Ctrl+C 停止當前進程
# 然後重新運行：
python -m aiohttp.web -P 5168 app:init_func
```

**步驟 C：驗證級別設置**

編輯 `setup_logging.py` 並確保：
```python
if verbose:
    root_logger.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG)
else:
    root_logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
```

### 問題 6：日誌文件不斷增大

#### 症狀
- bot_debug.log 文件數 GB
- 磁盤空間不足

#### 解決方案

**步驟 A：刪除舊日誌**
```bash
# 備份重要日誌（如果需要）
copy bot_debug.log bot_debug.log.backup

# 刪除舊日誌
del bot_debug.log
```

**步驟 B：配置日誌輪轉（可選）**

編輯 `setup_logging.py` 使用 RotatingFileHandler：
```python
from logging.handlers import RotatingFileHandler

file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5           # 保留 5 個備份
)
```

---

## 📊 解釋常見日誌消息

### 正常流程
```
[INFO] [app] === 新的訊息活動開始 ===
[INFO] [app] 訊息活動文字: 查詢上個月的用量
[INFO] [genie_service] 📥 新查詢請求
[INFO] [genie_service] ⏳ 正在向 Genie API 發送查詢...
[INFO] [genie_service] ✅ 已接收查詢 ID: xxx
[INFO] [genie_service] 📊 已收到結果: ...
[INFO] [app] === 訊息活動結束 ===
```

### 警告消息（不影響功能）
```
[WARNING] [aiohttp] Connection pool is full (size=30, total=30)
```
→ 正常警告，應用程序會自動重試

### 錯誤消息（需要採取行動）
```
[ERROR] Invalid access token
```
→ 需要更新 Databricks token（見問題 4）

```
[ERROR] Connection refused
```
→ 檢查 Databricks 工作區 URL 和網絡連接

---

## 🔍 調試技巧

### 技巧 1：搜索特定日誌

**Windows PowerShell：**
```powershell
# 搜索所有錯誤
Select-String "ERROR|WARN" bot_debug.log

# 搜索特定活動
Select-String "訊息活動" bot_debug.log

# 顯示最後 50 行
Get-Content bot_debug.log -Tail 50
```

### 技巧 2：實時監視日誌

**Windows PowerShell：**
```powershell
# 實時顯示日誌（類似 tail -f）
Get-Content bot_debug.log -Wait
```

### 技巧 3：分析日誌時序

```bash
# 查找查詢開始和結束時間
findstr "新的訊息活動開始\|訊息活動結束" bot_debug.log
```

→ 可以計算處理時間

### 技巧 4：導出統計信息

```powershell
# 計算錯誤數
@(Select-String "ERROR" bot_debug.log).Count

# 顯示唯一的錯誤信息
Select-String "ERROR" bot_debug.log | ForEach-Object { $_.Line.Split(']')[2] } | Sort | Get-Unique
```

---

## 🚀 完整診斷流程

如果日誌問題持續，請按順序執行：

```bash
# 1. 診斷環境
python bot_diagnostic.py

# 2. 測試日誌系統
python test_logging.py

# 3. 驗證 Databricks token
python verify_databricks_token.py

# 4. 啟動應用程序（調試模式）
set VERBOSE_LOGGING=True
python -m aiohttp.web -P 5168 app:init_func

# 5. 檢查日誌輸出
# 在 VS Code 中打開 bot_debug.log
# 或使用：
type bot_debug.log
```

將輸出結果複製到此文件中，請求協助。

---

## 📞 需要幫助？

如果以上步驟都不能解決問題，請提供：

1. **bot_diagnostic.py 的完整輸出**
2. **bot_debug.log 的最後 200 行**
3. **您正在執行的確切命令**
4. **Windows 版本和 Python 版本**

---

**最後更新**: 2026-01-29  
**相關文件**: setup_logging.py, bot_diagnostic.py, test_logging.py
