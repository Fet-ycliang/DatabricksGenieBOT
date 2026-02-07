# 快速安裝和故障排查指南

## 🚀 5 分鐘快速開始

### Step 1: 克隆並設置環境

```bash
# 克隆項目
git clone https://github.com/carrossoni/DatabricksGenieBOT.git
cd DatabricksGenieBOT

# 創建虛擬環境
python -m venv env

# 激活虛擬環境
# Linux/Mac:
source env/bin/activate
# Windows PowerShell:
.\env\Scripts\Activate.ps1
```

### Step 2: 安裝依賴 (使用 uv)

```bash
# 安裝 uv (如果尚未安裝)
pip install uv

# 同步依賴
uv sync
```

### Step 3: 安裝 Chrome (用於圖表)

選擇其中一個方法：

#### 方法 A: 自動安裝 (推薦)

```bash
plotly_get_chrome
```

#### 方法 B: 手動安裝

```bash
# Windows (使用 Chocolatey)
choco install googlechrome

# macOS (使用 Homebrew)
brew install --cask google-chrome

# Linux (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y chromium-browser
```

### Step 4: 配置環境變數

```bash
# 複製示例配置
cp env.example .env

# 編輯 .env 並填入:
# DATABRICKS_TOKEN=你的_token
# APP_ID=你的_app_id
# APP_PASSWORD=你的_app_password
```

### Step 5: 驗證安裝

```bash
# 運行診斷
python scripts/diagnose.py

# 應該看到全部 ✅
```

### Step 6: 啟動機器人

```bash
uv run fastapi dev app/main.py

# 預期輸出:
# INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

## 🆘 常見問題快速修復

### ❌ 錯誤: `Kaleido requires Google Chrome`

**解決方案:**

```bash
plotly_get_chrome
# 或
pip install --upgrade kaleido
# 或手動安裝 Chrome (見上面 Step 3)
```

### ❌ 錯誤: `CloudAdapter has no attribute get_user_token`

**原因:** OAuth 未配置

**解決方案:** 參考 [../troubleshooting.md](../troubleshooting.md) 中的 OAuth 章節

### ❌ 錯誤: `ModuleNotFoundError: No module named 'aiohttp'`

**解決方案:**

```bash
# 確保在虛擬環境中
source env/bin/activate  # Linux/Mac
.\env\Scripts\Activate.ps1  # Windows

# 重新安裝依賴
pip install -r requirements.txt
```

### ❌ 錯誤: `No module named 'aiohttp.web'`

**解決方案:**

```bash
pip install --upgrade aiohttp
```

### ❌ 錯誤: `DATABRICKS_TOKEN not set`

**解決方案:**

```bash
# 複製 env.example
cp env.example .env

# 編輯 .env，添加您的 token
nano .env  # 或 vi, code, notepad 等

# 設定環境變數 (如果不使用 .env)
export DATABRICKS_TOKEN=your_token  # Linux/Mac
set DATABRICKS_TOKEN=your_token     # Windows CMD
```

---

## 🔍 完整診斷

### 自動診斷所有問題

```bash
python scripts/diagnose.py

# 如果看到問題，嘗試自動修復:
python scripts/diagnose.py
# 當提示時輸入 y
```

### 手動檢查

```bash
# 檢查 Python
python --version

# 檢查虛擬環境
echo $VIRTUAL_ENV  # 應該顯示路徑

# 檢查 Chrome
chrome --version
chromium-browser --version
google-chrome --version

# 檢查包
python -c "import aiohttp; print(aiohttp.__version__)"
python -c "import kaleido; print(kaleido.__version__)"

# 測試圖表生成
python -c "
import plotly.graph_objects as go
fig = go.Figure(data=go.Bar(x=['A'], y=[1]))
fig.write_image('test.png')
print('✅ 圖表生成成功')
"
```

---

## 📋 安裝檢查清單

- [ ] Python 3.11+ 已安裝
- [ ] `uv sync` 已運行
- [ ] .env 文件已創建並配置
- [ ] 運行 `python scripts/diagnose.py` 全部通過 ✅

---

## 🚀 下一步

### 本地測試

```bash
# 啟動機器人
uv run fastapi dev app/main.py

# 測試健康檢查
curl http://localhost:8000/health
```

### 部署到 Azure

參考 [../../README.md](../../README.md) 中的 **與 MS Teams 整合** 部分

或快速命令:

```bash
az webapp up --name <app-name> --resource-group <rg> --runtime "PYTHON:3.13" --sku B1
```

---

## 📚 完整文檔

- [README.md](../../README.md) - 項目概述
- [troubleshooting.md](../troubleshooting.md) - 通用故障排查

---

## 💬 需要幫助？

1. **運行診斷**: `python scripts/diagnose.py`
2. **查看日誌**: 檢查控制台輸出或 `logs/` 目錄
3. **查閱文檔**: 見上面的文檔列表
4. **檢查 GitHub Issues**: https://github.com/carrossoni/DatabricksGenieBOT/issues

---

**祝您安裝順利！🎉**
