# Kaleido/Chrome 依賴故障排查指南

## 🔴 問題

```
Kaleido requires Google Chrome to be installed.
Either download and install Chrome yourself or run: $ plotly_get_chrome
```

## 🎯 根本原因

Plotly 的 `kaleido` 庫用於將 Plotly 圖表導出為靜態圖像 (PNG/SVG)，**需要 Chrome/Chromium 瀏覽器**。

---

## ✅ 解決方案

### 情景 1️⃣: 本地開發環境 (Windows/Mac/Linux)

#### 選項 A: 讓 Plotly 自動安裝 Chrome (推薦)

```bash
# 激活虛擬環境
source env/bin/activate  # Linux/Mac
# 或
.\env\Scripts\Activate.ps1  # Windows PowerShell

# 運行命令自動下載並安裝 Chromium
plotly_get_chrome

# 驗證安裝
python -c "import kaleido; print(kaleido.__version__)"
```

**預期輸出**:
```
0.2.1  # 或更新版本
```

#### 選項 B: 手動安裝 Google Chrome

1. **下載 Chrome**: https://www.google.com/chrome/
2. **安裝到默認位置**
3. **驗證安裝**:

```bash
# Windows
where chrome
where chromium

# Linux
which chromium-browser
which google-chrome

# Mac
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
```

#### 選項 C: 使用 Chocolatey (Windows)

```bash
choco install googlechrome
```

或 Homebrew (Mac):

```bash
brew install --cask google-chrome
```

---

### 情景 2️⃣: Azure App Service 部署

#### 方案 A: 使用啟動腳本 (推薦)

**第 1 步**: 創建 `startup.sh`

```bash
#!/bin/bash

# 1. 更新包管理器
apt-get update

# 2. 安裝 Chrome 依賴
apt-get install -y \
    chromium-browser \
    chromium \
    fonts-noto-cjk

# 3. 驗證 Chrome 安裝
which chromium-browser || which chromium || echo "Chrome installation failed"

# 4. 啟動應用
python -m aiohttp.web -H 0.0.0.0 -P 8000 app:init_func
```

**第 2 步**: 在 Azure Portal 中配置啟動命令

1. 進入 **App Service** → **Configuration**
2. 找到 **Startup Command** 欄位
3. 輸入:
```
bash /home/site/wwwroot/startup.sh
```

或設定為:
```
apt-get update && apt-get install -y chromium-browser && python -m aiohttp.web -H 0.0.0.0 -P 8000 app:init_func
```

**第 3 步**: 重啟應用

```bash
az webapp restart --resource-group <rg> --name <app-name>
```

#### 方案 B: 修改 `web.config` (Azure App Service)

如果使用 `web.config` 部署：

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <webSocket enabled="false" />
    <handlers>
      <add name="PythonHandler" path="*" verb="*" modules="httpPlatformHandler" resourceType="Unspecified" />
    </handlers>
    <httpPlatform processPath="D:\home\python\latest\python.exe" 
                  arguments="-m aiohttp.web -H 0.0.0.0 -P %HTTP_PLATFORM_PORT% app:init_func" 
                  stdoutLogEnabled="true"
                  stdoutLogFile="D:\home\LogFiles\python_service.log">
      <environmentVariables>
        <environmentVariable name="PATH" value="D:\home\site\wwwroot;D:\home\site\wwwroot\env\Scripts;%PATH%" />
      </environmentVariables>
    </httpPlatform>
  </system.webServer>
</configuration>
```

並在 **啟動命令** 中添加:
```
apt-get update && apt-get install -y chromium-browser
```

---

### 情景 3️⃣: Docker 容器部署

如果使用 Docker，在 `Dockerfile` 中添加：

```dockerfile
FROM python:3.13-slim

# ✅ 安裝 Chrome 依賴
RUN apt-get update && apt-get install -y \
    chromium-browser \
    chromium \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 依賴
COPY requirements.txt .
RUN pip install -r requirements.txt

# 複製應用
COPY . /app
WORKDIR /app

# 啟動
CMD ["python", "-m", "aiohttp.web", "-H", "0.0.0.0", "-P", "8000", "app:init_func"]
```

構建並運行：

```bash
docker build -t genie-bot .
docker run -p 8000:8000 genie-bot
```

---

## 🔄 備選方案：無需 Chrome

### 選項 1: 禁用圖表導出 (快速修復)

如果只是暫時禁用圖表功能：

**在 `config.py` 中添加**:

```python
# 是否啟用圖表生成
ENABLE_CHART_GENERATION = False  # 設為 False 禁用
```

**在 `command_handler.py` 中**:

```python
if not CONFIG.ENABLE_CHART_GENERATION:
    logger.info("圖表生成已禁用（未安裝 Chrome）")
    return  # 跳過圖表
```

### 選項 2: 使用線上服務 (Plotly Cloud)

使用 Plotly 線上 API 而不是本地導出：

```python
# 不使用 Kaleido，直接返回 Plotly JSON
# 讓用戶在 Teams 中查看交互式圖表
return plotly_json_data  # 無需 Chrome
```

但這需要重新架構圖表生成邏輯。

---

## 📋 診斷檢查清單

### 本地環境診斷

```bash
# 1. 驗證 Kaleido 安裝
python -c "import kaleido; print(f'Kaleido {kaleido.__version__}')"

# 2. 驗證 Chrome 位置
# Windows
python -c "import kaleido; print(kaleido.scope.chromium_executable)"

# Linux/Mac
which chromium-browser || which google-chrome

# 3. 測試圖表生成
python -c "
import plotly.graph_objects as go
fig = go.Figure(data=go.Bar(x=['A', 'B'], y=[1, 2]))
fig.write_image('test.png')
print('✅ 圖表生成成功')
"
```

### Azure App Service 診斷

```bash
# 查看應用日誌
az webapp log tail --resource-group <rg> --name <app-name>

# 驗證 Chrome 安裝
# (進入 Kudu 控制台或 SSH)
which chromium-browser

# 重新安裝 Chrome
apt-get update && apt-get install -y chromium-browser
```

---

## 🛠️ 快速修復步驟

### 對於 Windows/Mac/Linux 本地開發:

```bash
# 1. 激活虛擬環境
source env/bin/activate  # Linux/Mac
.\env\Scripts\Activate.ps1  # Windows

# 2. 安裝 Chrome
plotly_get_chrome

# 3. 驗證
python app.py

# 4. 測試圖表
# 在機器人中測試 chart 命令
```

### 對於 Azure 生產部署:

```bash
# 1. 進入 Azure Portal
# 2. Bot Channels Registration → Configuration
# 3. 設定啟動命令:
apt-get update && apt-get install -y chromium-browser && python -m aiohttp.web -H 0.0.0.0 -P 8000 app:init_func

# 4. 重啟應用
az webapp restart --resource-group <rg> --name <app-name>

# 5. 驗證
# 查看日誌中是否有 Chrome 安裝成功的消息
az webapp log tail --resource-group <rg> --name <app-name>
```

---

## ✅ 驗證修復

### 成功指標

機器人日誌中應該看到:

```
✅ 圖表生成成功
   類型: bar chart
   大小: 45KB
   格式: PNG
```

或

```
📊 圖表生成跳過 (Chrome 未安裝，使用表格展示)
```

### 測試命令

在 Teams/Emulator 中發送:

```
chart

# 預期結果:
# 1. 如果 Chrome 已安裝 → 顯示圖表圖片
# 2. 如果 Chrome 未安裝 → 顯示文字表格 (降級)
```

---

## 🚨 常見問題

### Q: 在 Windows 上執行 `plotly_get_chrome` 失敗

**解決方案**:
```bash
# 手動安裝
python -m pip install --upgrade kaleido
# 或
choco install googlechrome
```

### Q: Azure 部署後仍然出現 Chrome 錯誤

**解決方案**:
```bash
# 檢查日誌
az webapp log tail --resource-group <rg> --name <app-name> | grep -i chrome

# 重新安裝
# 進入 Kudu (https://<app-name>.scm.azurewebsites.net)
# 打開 Debug console → bash
apt-get update && apt-get install -y chromium-browser

# 重啟應用
az webapp restart --resource-group <rg> --name <app-name>
```

### Q: 圖表生成很慢

**原因**: Chrome 進程啟動耗時

**解決方案**:
- 在機器人啟動時預啟動 Chrome (可選優化)
- 使用異步圖表生成

```python
# 在 chart_generator.py 中
import asyncio

async def generate_chart_image_async(chart_info):
    """異步圖表生成"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, generate_chart_image, chart_info)
```

---

## 📊 Chrome 安裝狀態檢查

```python
# 新建: check_chrome.py
import subprocess
import sys

def check_chrome():
    """檢查 Chrome 是否正確安裝"""
    
    # 嘗試多個可能的位置
    chrome_paths = [
        'chromium-browser',
        'chromium',
        'google-chrome',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
    ]
    
    for path in chrome_paths:
        try:
            result = subprocess.run([path, '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Chrome 已安裝: {path}")
                print(f"   版本: {result.stdout.strip()}")
                return True
        except (FileNotFoundError, OSError):
            continue
    
    print("❌ Chrome 未找到")
    print("   請運行: plotly_get_chrome")
    return False

if __name__ == '__main__':
    if not check_chrome():
        sys.exit(1)
```

運行:
```bash
python check_chrome.py
```

---

## 🎯 最終建議

| 環境 | 推薦方案 | 備註 |
|------|--------|------|
| **本地開發** | `plotly_get_chrome` | 最簡單，自動下載 Chromium |
| **Azure App Service** | 啟動腳本安裝 chromium-browser | 完全自動化 |
| **Docker** | 在 Dockerfile 中安裝 | 容器化，可重現 |
| **測試環境** | 禁用圖表功能 | 快速驗證其他功能 |

---

## 📞 仍有問題？

如果修復後仍有問題，請檢查：

```bash
# 1. 重新安裝依賴
pip install --upgrade kaleido plotly

# 2. 清除緩存
rm -rf ~/.cache/plotly/  # Linux/Mac
rmdir %APPDATA%\plotly   # Windows

# 3. 重新安裝 Chrome
# 使用上述任何方法

# 4. 測試
python -c "
import plotly.graph_objects as go
fig = go.Figure(data=go.Bar(x=['A'], y=[1]))
fig.write_image('test.png')
"

# 5. 查看詳細錯誤
python -c "import kaleido; print(kaleido.chromium_path())"
```

---

**現在運行上述任何解決方案，應該能修復 Chrome 依賴問題！** ✅
