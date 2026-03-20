# Azure 託管方案全面比較：Web App vs Container Apps

**專案**：Databricks Genie Bot
**更新日期**：2026-02-16
**當前部署**：Azure Web App

---

## 📋 目錄

1. [快速建議](#快速建議)
2. [資源需求分析](#資源需求分析)
3. [Web App 規格建議](#web-app-規格建議)
4. [全面比較表](#全面比較表)
5. [詳細分析](#詳細分析)
6. [成本比較](#成本比較)
7. [遷移指南](#遷移指南)
8. [最終建議](#最終建議)

---

## 🎯 快速建議

### 當前最佳選擇：**Azure App Service (Web App) - B2 方案**

**理由**：
- ✅ **最適合此專案**：中小型 Bot 應用
- ✅ **成本效益高**：$73 USD/月
- ✅ **零學習曲線**：您已經在使用
- ✅ **維護簡單**：托管服務，Azure 管理基礎設施
- ✅ **功能完整**：內建 CI/CD、SSL、日誌、Application Insights

### 何時考慮 Container Apps？

⏸️ **需要更高級功能時**：
- 需要 Kubernetes 級別的控制
- 需要微服務架構（多個容器）
- 需要 Dapr、KEDA 等高級功能
- 團隊有 Docker/Kubernetes 經驗

---

## 📊 資源需求分析

### 當前專案特性

**應用類型**：
- Microsoft Teams Bot（事件驅動）
- FastAPI Web 服務
- Python 3.11

**主要依賴**（影響資源需求）：

| 依賴 | 記憶體影響 | CPU 影響 |
|------|-----------|---------|
| Bot Framework SDK | 中 (~50MB) | 低 |
| FastAPI + Uvicorn | 低 (~30MB) | 低 |
| Databricks SDK | 低 (~40MB) | 低 |
| matplotlib + seaborn | **高 (~150MB)** | 中 |
| numpy | 中 (~80MB) | 中 |
| **基礎 Python 環境** | 中 (~100MB) | - |
| **合計（啟動）** | **~450-500MB** | - |

**工作負載特性**：

| 特性 | 值 | 說明 |
|------|-----|------|
| **請求類型** | 低頻、長時間 | 使用者發訊息時觸發 |
| **平均回應時間** | 1-3 秒 | Databricks API 調用 |
| **併發請求** | 低 (1-10) | Teams 使用者數量決定 |
| **記憶體增長** | 線性 | Session + Cache |
| **CPU 密集** | 中等 | 圖表生成時較高 |

**預估負載**（生產環境）：

| 使用者數 | 每日查詢 | 併發請求 | 記憶體需求 | CPU 需求 |
|---------|---------|---------|-----------|---------|
| 1-10 人 | < 50 | 1-2 | 512MB | 0.5 vCPU |
| 10-50 人 | 50-250 | 2-5 | 1GB | 1 vCPU |
| 50-100 人 | 250-500 | 5-10 | 1.75GB | 1 vCPU |
| 100-200 人 | 500-1000 | 10-20 | 3.5GB | 2 vCPU |

---

## 💻 Web App 規格建議

### 推薦規格階梯

#### 方案 1：開發/測試環境 ✅

**App Service Plan**: **B1 (Basic)**

| 規格 | 值 |
|------|-----|
| vCPU | 1 核心 |
| 記憶體 | 1.75 GB |
| 儲存空間 | 10 GB |
| 每月成本 | **~$13 USD** |

**適用場景**：
- ✅ 開發和測試環境
- ✅ < 10 個使用者
- ✅ 低頻使用（每日 < 50 次查詢）
- ⚠️ 不含自動擴展
- ⚠️ 無部署槽位

**優點**：
- 價格最便宜
- 功能完整（SSL、自訂網域、Application Insights）

**缺點**：
- 無法自動擴展
- 單一實例（無高可用性）

---

#### 方案 2：小型生產環境（推薦）⭐

**App Service Plan**: **B2 (Basic)**

| 規格 | 值 |
|------|-----|
| vCPU | 2 核心 |
| 記憶體 | 3.5 GB |
| 儲存空間 | 10 GB |
| 每月成本 | **~$73 USD** |

**適用場景**：
- ✅ **小型生產環境（推薦）**
- ✅ 10-100 個使用者
- ✅ 中等頻率使用（每日 50-500 次查詢）
- ✅ 足夠的記憶體支援 matplotlib 圖表生成
- ⚠️ 無自動擴展

**優點**：
- 記憶體充足（3.5GB）
- 雙核心處理併發請求
- 價格合理
- 支援所有 Basic 功能

**缺點**：
- 無自動擴展
- 無部署槽位

**為什麼選 B2？**
- matplotlib/seaborn 圖表生成需要較多記憶體
- 雙核心可以更好處理併發查詢
- 3.5GB 記憶體足夠支援 50-100 併發 session

---

#### 方案 3：中型生產環境

**App Service Plan**: **S1 (Standard)**

| 規格 | 值 |
|------|-----|
| vCPU | 1 核心 |
| 記憶體 | 1.75 GB |
| 儲存空間 | 50 GB |
| 每月成本 | **~$70 USD** |
| **自動擴展** | ✅ 最多 10 個實例 |
| **部署槽位** | ✅ 5 個 |

**適用場景**：
- ✅ 需要自動擴展
- ✅ 需要 Staging 環境（部署槽位）
- ✅ 50-200 個使用者
- ⚠️ 記憶體較少（1.75GB）

**優點**：
- 自動擴展（根據 CPU/記憶體自動增加實例）
- 部署槽位（藍綠部署）
- 與 B2 價格相近

**缺點**：
- 單一實例記憶體較少
- 需要配置自動擴展規則

---

#### 方案 4：大型生產環境

**App Service Plan**: **S2 (Standard)**

| 規格 | 值 |
|------|-----|
| vCPU | 2 核心 |
| 記憶體 | 3.5 GB |
| 儲存空間 | 50 GB |
| 每月成本 | **~$140 USD** |
| **自動擴展** | ✅ 最多 10 個實例 |
| **部署槽位** | ✅ 5 個 |

**適用場景**：
- ✅ 100-500 個使用者
- ✅ 高頻使用（每日 > 500 次查詢）
- ✅ 需要高可用性
- ✅ 需要 Staging 環境

**優點**：
- 記憶體充足 + 自動擴展
- 高可用性
- 完整的企業級功能

**缺點**：
- 價格較高

---

#### 方案 5：Premium（不推薦）

**App Service Plan**: **P1V3 (Premium V3)**

| 規格 | 值 |
|------|-----|
| vCPU | 2 核心 |
| 記憶體 | 8 GB |
| 儲存空間 | 250 GB |
| 每月成本 | **~$241 USD** |

**評估**：
- ❌ **過度配置**：此 Bot 不需要 8GB 記憶體
- ❌ **成本過高**：性價比不佳
- ⚠️ 僅在極高負載（> 500 使用者）時考慮

---

### 📊 規格選擇決策樹

```
開始
│
├─ 是否為生產環境？
│  │
│  ├─ 否 → B1 ($13/月) ✅
│  │
│  └─ 是 → 使用者數量？
│     │
│     ├─ < 100 人 → B2 ($73/月) ⭐ 推薦
│     │
│     ├─ 100-200 人 + 需要自動擴展？
│     │  │
│     │  ├─ 是 → S2 ($140/月)
│     │  └─ 否 → B2 ($73/月) ⭐
│     │
│     └─ > 200 人 → S2 ($140/月) + 自動擴展
```

---

## 📊 全面比較表

### Azure App Service (Web App) vs Azure Container Apps

| 比較項目 | Azure App Service (Web App) | Azure Container Apps |
|---------|---------------------------|---------------------|
| **🎯 定位** | PaaS Web 應用託管 | Serverless 容器平台 |
| **👥 目標用戶** | Web 開發者 | DevOps、微服務架構師 |
| **📦 部署方式** | Code 或 Docker | Docker 容器（必須） |
| **🔧 複雜度** | **低** ⭐ | 中-高 |
| **⚡ 啟動速度** | 中（1-2 分鐘） | 快（< 30 秒）|
| **💰 最低成本** | $13/月 (B1) | $0（空閒時） + 用量計費 |
| **💰 典型成本** | **$73/月 (B2)** ⭐ | $30-100/月（視用量） |
| **🔄 自動擴展** | S1+ 支援 | ✅ 內建（零到多實例） |
| **📊 擴展模式** | 垂直 + 水平 | 水平（0-300 實例）|
| **🌐 負載平衡** | 內建 | 內建（更強大）|
| **🔐 HTTPS/SSL** | 自動（免費） | 自動（免費） |
| **📝 自訂網域** | ✅ 簡單 | ✅ 簡單 |
| **🚀 CI/CD** | ✅ GitHub、Azure DevOps | ✅ GitHub Actions、Azure DevOps |
| **📊 監控** | Application Insights | Application Insights + Log Analytics |
| **🔍 日誌** | Log Stream、Kudu | Log Analytics |
| **🛠️ 部署槽位** | ✅ (Standard+) | ❌ 需手動管理 |
| **🎛️ 環境變數** | ✅ Portal 設定 | ✅ Secrets + Env Vars |
| **💾 持久化儲存** | ✅ 檔案系統 | ⚠️ 需 Azure Files 掛載 |
| **🔌 VNet 整合** | ✅ (Standard+) | ✅ 內建 |
| **🐳 Docker 支援** | ✅ 可選 | ✅ 必須 |
| **☸️ Kubernetes** | ❌ | ✅ 基於 Kubernetes |
| **🔧 Dapr 支援** | ❌ | ✅ 內建 |
| **📈 KEDA 支援** | ❌ | ✅ 內建 |
| **🎯 微服務** | ⚠️ 單體應用 | ✅ 原生支援 |
| **⚙️ 維護工作** | **最少** ⭐ | 中等（Docker 管理）|
| **📚 學習曲線** | **平緩** ⭐ | 陡峭（需 Docker/K8s 知識）|
| **🔄 現有狀態** | ✅ 已部署 | ⚠️ 需遷移 |

### 評分總覽（1-5 星）

| 評分項目 | Azure App Service | Azure Container Apps |
|---------|------------------|---------------------|
| **易用性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **成本效益（小型）** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **成本效益（大型）** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **擴展性** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **功能豐富度** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **維護成本** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **適合此專案** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 🔍 詳細分析

### Azure App Service (Web App) 深入分析

#### ✅ 優點

1. **極低學習曲線**
   - 直接部署 Python 代碼
   - 無需 Docker 知識
   - 熟悉的 Web 開發模式

2. **內建功能完整**
   - SSL/HTTPS 自動配置
   - 自訂網域簡單設定
   - Application Insights 一鍵啟用
   - 部署槽位（Staging/Production）

3. **維護簡單**
   - Azure 管理基礎設施
   - 自動 OS 更新和安全性修補
   - 無需管理容器或編排器

4. **成本可預測**
   - 固定月費（$13-$140/月）
   - 無隱藏成本
   - 易於預算規劃

5. **完美適合單體應用**
   - 此 Bot 是單一服務
   - 無需微服務架構
   - 簡單部署和管理

#### ❌ 缺點

1. **擴展限制**
   - 垂直擴展有上限（P3V3: 8 核心）
   - 水平擴展最多 30 個實例（Premium）
   - 無法縮放到零（最少 1 個實例）

2. **無 Kubernetes 功能**
   - 不支援 Dapr、KEDA
   - 無容器編排
   - 無微服務原生支援

3. **較少彈性**
   - 綁定 Windows 或 Linux
   - Runtime 版本受 Azure 限制
   - 部署方式較固定

#### 🎯 最適合場景

- ✅ 單體 Web 應用或 API
- ✅ 中小型 Bot 應用（如此專案）
- ✅ 團隊沒有 Docker/K8s 經驗
- ✅ 需要快速上線
- ✅ 預算有限

---

### Azure Container Apps 深入分析

#### ✅ 優點

1. **真正的 Serverless**
   - 可以縮放到零（空閒時 $0）
   - 按實際使用計費
   - 毫秒級擴展

2. **強大的擴展能力**
   - 0-300 個副本
   - 基於多種指標擴展（CPU、記憶體、HTTP 請求、自訂指標）
   - KEDA 支援（事件驅動擴展）

3. **微服務原生**
   - 多個容器應用
   - Dapr 整合（服務調用、狀態管理）
   - 服務發現

4. **完整的容器支援**
   - 任何 Docker 映像
   - 多容器應用
   - Init 容器

5. **成本優化**
   - 低流量時幾乎免費
   - 按秒計費
   - 無最低承諾

#### ❌ 缺點

1. **學習曲線陡峭**
   - 需要 Docker 知識
   - 需要編寫 Dockerfile
   - 需要理解容器概念

2. **維護成本高**
   - 需要管理 Docker 映像
   - 需要管理容器註冊表
   - 需要更新映像和重新部署

3. **功能缺失**
   - 無內建部署槽位
   - 持久化儲存需額外配置
   - 日誌查看較複雜

4. **成本不可預測**
   - 用量計費可能波動
   - 需要監控和優化
   - 可能超出預算

5. **過度工程化（對此專案）**
   - 單一 Bot 不需要微服務
   - 無需 Dapr/KEDA
   - 增加不必要的複雜度

#### 🎯 最適合場景

- ✅ 微服務架構
- ✅ 需要縮放到零（節省成本）
- ✅ 事件驅動應用
- ✅ 需要 Kubernetes 功能但不想管理 AKS
- ✅ 團隊有 Docker/K8s 經驗
- ❌ 單體應用（過度設計）

---

## 💰 成本比較（詳細）

### 場景 1：小型團隊（10-50 人）

**假設**：
- 每日查詢：100 次
- 平均回應時間：2 秒
- 工作時間：8 小時/天
- 每月工作日：22 天

#### Azure App Service (B2)

| 項目 | 成本 |
|------|------|
| B2 方案 | $73.00 |
| Application Insights | $0（< 5GB） |
| **總計** | **$73/月** |

**優點**：
- 固定成本
- 可預測
- 包含所有功能

#### Azure Container Apps

| 項目 | 計算 | 成本 |
|------|------|------|
| vCPU 使用 | 1 vCPU × 8 小時 × 22 天 = 176 小時 | $28.16 |
| 記憶體使用 | 2GB × 176 小時 | $14.08 |
| 請求數 | 100 × 22 = 2,200 次 | $0.22 |
| 免費額度 | -前 180,000 vCPU-秒 | -$8.00 |
| **總計** | | **$34.46/月** |

**注意**：
- ⚠️ 未包含容器註冊表成本（~$5/月）
- ⚠️ 未包含額外維護時間
- ⚠️ 實際成本可能因流量波動而變化

**結論**：Container Apps 便宜約 **50%**，但需要額外的維護工作。

---

### 場景 2：中型團隊（50-100 人）

**假設**：
- 每日查詢：400 次
- 平均回應時間：2 秒
- 工作時間：10 小時/天
- 每月工作日：22 天

#### Azure App Service (B2)

| 項目 | 成本 |
|------|------|
| B2 方案 | $73.00 |
| Application Insights | $0（< 5GB） |
| **總計** | **$73/月** |

**評估**：B2 足夠應付此負載

#### Azure Container Apps

| 項目 | 計算 | 成本 |
|------|------|------|
| vCPU 使用 | 1 vCPU × 10 小時 × 22 天 = 220 小時 | $35.20 |
| 記憶體使用 | 2GB × 220 小時 | $17.60 |
| 請求數 | 400 × 22 = 8,800 次 | $0.88 |
| 免費額度 | -前 180,000 vCPU-秒 | -$8.00 |
| **總計** | | **$45.68/月** |

**結論**：Container Apps 仍便宜約 **37%**

---

### 場景 3：大型團隊（100-200 人）

**假設**：
- 每日查詢：800 次
- 需要自動擴展
- 平均 2 個實例運行

#### Azure App Service (S2 + 自動擴展)

| 項目 | 成本 |
|------|------|
| S2 方案（基礎） | $140.00 |
| 額外實例（平均 1 個） | $140.00 |
| Application Insights | $5.00 |
| **總計** | **$285/月** |

#### Azure Container Apps

| 項目 | 計算 | 成本 |
|------|------|------|
| vCPU 使用（2 副本） | 2 vCPU × 10 小時 × 22 天 = 440 小時 | $70.40 |
| 記憶體使用 | 4GB × 220 小時 | $35.20 |
| 請求數 | 800 × 22 = 17,600 次 | $1.76 |
| 免費額度 | | -$8.00 |
| **總計** | | **$99.36/月** |

**結論**：Container Apps 便宜約 **65%**（大規模時優勢明顯）

---

### 成本總結

| 規模 | Web App 成本 | Container Apps 成本 | 差異 |
|------|-------------|-------------------|------|
| 小型（< 50 人） | $73 | $35-45 | -40% |
| 中型（50-100 人） | $73 | $45-60 | -30% |
| 大型（100-200 人） | $285 | $100-150 | -65% |

**但是...**

| 隱藏成本 | Web App | Container Apps |
|---------|---------|----------------|
| 維護時間/月 | 1 小時 | 5-10 小時 |
| 學習成本 | 低 | 高 |
| 除錯複雜度 | 低 | 中-高 |
| 部署複雜度 | 低 | 中 |

**結論**：
- 💰 Container Apps **直接成本較低**
- ⚙️ 但**總成本（TCO）**需考慮維護時間
- 🎯 對小型團隊，Web App 的**簡單性**價值更高

---

## 🔄 遷移指南（Web App → Container Apps）

如果未來決定遷移，以下是步驟：

### 步驟 1：創建 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴（matplotlib 需要）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴檔案
COPY pyproject.toml ./
COPY uv.lock ./

# 安裝 uv 和依賴
RUN pip install uv
RUN uv sync --frozen

# 複製應用程式代碼
COPY app ./app
COPY bot ./bot

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 步驟 2：建立 Container Registry

```bash
# 創建 Azure Container Registry
az acr create \
  --resource-group your-rg \
  --name databricksgeniebot \
  --sku Basic

# 登入
az acr login --name databricksgeniebot
```

### 步驟 3：建構並推送映像

```bash
# 建構映像
docker build -t databricks-genie-bot:latest .

# 標記映像
docker tag databricks-genie-bot:latest \
  databricksgeniebot.azurecr.io/databricks-genie-bot:latest

# 推送映像
docker push databricksgeniebot.azurecr.io/databricks-genie-bot:latest
```

### 步驟 4：創建 Container Apps 環境

```bash
# 創建環境
az containerapp env create \
  --name genie-bot-env \
  --resource-group your-rg \
  --location eastasia

# 創建應用
az containerapp create \
  --name genie-bot \
  --resource-group your-rg \
  --environment genie-bot-env \
  --image databricksgeniebot.azurecr.io/databricks-genie-bot:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 10 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --env-vars \
    DATABRICKS_TOKEN=secretref:databricks-token \
    APP_ID=your-app-id
```

### 步驟 5：配置環境變數和 Secrets

```bash
# 設定 Secret
az containerapp secret set \
  --name genie-bot \
  --resource-group your-rg \
  --secrets databricks-token="your-token-here"

# 更新環境變數
az containerapp update \
  --name genie-bot \
  --resource-group your-rg \
  --set-env-vars \
    DATABRICKS_HOST=https://your-workspace.databricks.com \
    DATABRICKS_SPACE_ID=your-space-id
```

### 步驟 6：更新 Bot Service 端點

```bash
# 取得 Container App URL
az containerapp show \
  --name genie-bot \
  --resource-group your-rg \
  --query properties.configuration.ingress.fqdn

# 更新 Bot Service Messaging Endpoint
# Azure Portal → Bot Service → Configuration → Messaging endpoint
# https://genie-bot.xxx.azurecontainerapps.io/api/messages
```

### 預估遷移時間

| 步驟 | 時間 |
|------|------|
| 創建 Dockerfile | 30 分鐘 |
| 測試本地 Docker | 30 分鐘 |
| 設定 ACR 和推送 | 30 分鐘 |
| 創建 Container App | 30 分鐘 |
| 配置環境變數 | 30 分鐘 |
| 測試和除錯 | 2-4 小時 |
| **總計** | **5-7 小時** |

---

## 🎯 最終建議

### 當前階段：繼續使用 Azure App Service ⭐

**建議規格**：**B2 (Basic) - $73/月**

#### 理由：

1. **✅ 已經部署且運作正常**
   - 無需遷移成本
   - 團隊已熟悉

2. **✅ 完美適合此專案規模**
   - 單體 Bot 應用
   - 10-100 個使用者
   - 中低頻使用

3. **✅ 成本效益佳**
   - $73/月 固定成本
   - 包含所有必要功能
   - 無隱藏成本

4. **✅ 維護簡單**
   - 零學習曲線
   - 無需 Docker 管理
   - Azure 管理基礎設施

5. **✅ 功能完整**
   - Application Insights
   - 自訂網域和 SSL
   - 日誌串流
   - 部署槽位（如升級到 S1）

### 何時考慮遷移到 Container Apps？

考慮遷移的時機：

#### ✅ 需要微服務架構
```
當前: 單一 Bot 服務
未來: Bot + 獨立的分析服務 + 獨立的排程服務
```

#### ✅ 使用者大幅增長
```
當前: 10-100 人
未來: > 200 人，需要頻繁擴展
```

#### ✅ 需要縮放到零
```
場景: 只在工作時間使用（9AM-6PM）
節省: 50% 成本（晚上和週末縮放到零）
```

#### ✅ 團隊技能提升
```
當前: Web 開發團隊
未來: 有 DevOps 工程師，熟悉 Docker/K8s
```

### 升級路徑

```
階段 1（當前）: Web App B2
  ↓ 使用者增長到 50-100 人

階段 2: Web App B2（繼續）或 S1（需要自動擴展）
  ↓ 使用者增長到 100-200 人

階段 3: Web App S2 + 自動擴展
  ↓ 需要微服務或更高擴展性

階段 4: 考慮遷移到 Container Apps
```

---

## 📋 決策檢查清單

### 選擇 Web App 如果...

- ✅ 團隊不熟悉 Docker/Kubernetes
- ✅ 單體應用架構
- ✅ 使用者 < 200 人
- ✅ 需要快速部署和維護
- ✅ 預算有限（< $150/月）
- ✅ 需要部署槽位和簡單 CI/CD
- ✅ **大多數情況下的最佳選擇** ⭐

### 選擇 Container Apps 如果...

- ✅ 團隊熟悉 Docker/Kubernetes
- ✅ 需要微服務架構
- ✅ 需要縮放到零（節省成本）
- ✅ 需要 Dapr/KEDA 等高級功能
- ✅ 使用者 > 200 人且流量波動大
- ✅ 已有 CI/CD 流程和 Docker Registry
- ⚠️ 願意投入維護時間

---

## 📚 參考資源

- [Azure App Service 定價](https://azure.microsoft.com/pricing/details/app-service/windows/)
- [Azure Container Apps 定價](https://azure.microsoft.com/pricing/details/container-apps/)
- [Azure App Service 文檔](https://learn.microsoft.com/azure/app-service/)
- [Azure Container Apps 文檔](https://learn.microsoft.com/azure/container-apps/)
- [比較 Azure 運算服務](https://learn.microsoft.com/azure/architecture/guide/technology-choices/compute-decision-tree)

---

## 🎯 快速結論

| 問題 | 答案 |
|------|------|
| **當前最佳方案？** | **Azure App Service B2** ($73/月) ⭐ |
| **是否應該遷移到 Container Apps？** | **否**，目前不需要 |
| **何時重新評估？** | 使用者 > 100 人或需要微服務時 |
| **推薦行動？** | 繼續使用 Web App，監控效能和成本 |

**最重要的是**：選擇最簡單且滿足需求的方案，而不是最先進的技術。對於 Databricks Genie Bot，**Azure App Service B2** 是當前的最佳選擇。✨
