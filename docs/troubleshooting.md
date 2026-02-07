# 疑難排解指南

## 常見問題與解決方案

### 1. 找不到 Databricks 權杖錯誤

**錯誤訊息：**

```text
ValueError: default auth: cannot configure default credentials, please check https://docs.databricks.com/en/dev-tools/auth.html#databricks-client-unified-authentication to configure credentials for your preferred authentication method.
```

**原因：** `DATABRICKS_TOKEN` 環境變數未在 Azure 中正確載入。

**解決方案：**

#### 選項 A：Azure App Service 設定

1. 前往 Azure 入口網站 → 您的 App Service
2. 導航至 **設定 (Configuration)** → **應用程式設定 (Application settings)**
3. 新增以下環境變數：
   - `DATABRICKS_TOKEN`：您的 Databricks 個人存取權杖
   - `DATABRICKS_HOST`：您的 Databricks 工作區 URL
   - `DATABRICKS_SPACE_ID`：您的 Databricks 空間 ID

#### 選項 B：檢查環境變數名稱

確保環境變數名稱完全相符（區分大小寫）：

- `DATABRICKS_TOKEN`（不是 `databricks_token` 或 `Databricks_Token`）
- `DATABRICKS_HOST`（不是 `databricks_host`）

#### 選項 C：驗證權杖格式

權杖應以 `dapi` 開頭，並且是完整的個人存取權杖：

```bash
DATABRICKS_TOKEN=dapi1234567890abcdef1234567890ab
```

注意：在環境變數中不要在權杖值周圍加上引號。

#### 選項 D：先在本地測試

1. 建立一個 `.env` 檔案，包含您的變數：

   ```bash
   DATABRICKS_TOKEN=your-token-here
   DATABRICKS_HOST=https://your-workspace.cloud.databricks.com/
   DATABRICKS_SPACE_ID=your-space-id
   ```

2. 在本地測試以確保其運作正常
3. 使用相同的值部署到 Azure

### 2. Bot Framework 驗證問題

**錯誤訊息：**

```text
BotFrameworkAdapter: Authentication failed
```

**解決方案：**

1. 驗證 `APP_ID` 和 `APP_PASSWORD` 已在 Azure App Service 中設定
2. 檢查訊息端點是否正確
3. 確保機器人已在 Azure Bot Service 中註冊

### 3. Teams 整合問題

**錯誤訊息：**

```text
Bot not responding in Teams
```

**解決方案：**

1. 驗證 Teams 頻道已在 Azure Bot Service 中啟用
2. 檢查機器人是否已安裝在 Teams 中
3. 審查 Teams 應用程式資訊清單設定

### 4. 使用者電子郵件識別問題

**問題：** 即使提供電子郵件後，機器人仍不斷詢問電子郵件

**解決方案：**

1. 驗證電子郵件格式是否有效（例如 `user@company.com`）
2. 檢查您是否不小心輸入了 `cancel`
3. 如果使用 Bot Emulator，請使用 `/setuser email@company.com Your Name` 指令
4. 使用 `logout` 清除您的工作階段並重試

**問題：** 機器人無法識別我的電子郵件

**解決方案：**

1. 確保電子郵件遵循標準格式：`name@domain.com`
2. 檢查電子郵件前後是否有額外的空格
3. 嘗試 `whoami` 指令來驗證您的工作階段
4. 如果在 Teams 中，請檢查您的 Teams 設定檔是否已設定電子郵件

### 5. Genie 空間設定問題

**錯誤訊息：**

```text
Invalid Space ID or access denied
```

**解決方案：**

1. 驗證 `DATABRICKS_SPACE_ID` 是否正確
2. 確保您的 Databricks 權杖有權存取指定的 Genie 空間
3. 檢查 Genie 空間是否存在且處於活動狀態
4. 驗證空間 ID 格式（應為長英數字串）

**錯誤訊息：**

```text
Genie API returned no results
```

**解決方案：**

1. 空間可能為空或沒有資料
2. 驗證空間已在 Databricks 中正確設定
3. 先在 Databricks UI 中直接測試空間
4. 檢查您的查詢是否與空間中的資料相容

**錯誤訊息（使用者看到）：**

```text
No data available.
```

**錯誤訊息（在記錄檔中）：**

```text
403 Forbidden
Source IP address: X.X.X.X is blocked by Databricks IP ACL for workspace
```

**原因：** 您的 Azure App Service 的輸出 IP 位址被 Databricks 帳戶 IP 存取清單 (ACLs) 封鎖

**解決方案：**

1. **尋找您的 Azure App Service 輸出 IP：**
   - 前往 Azure 入口網站 → 您的 App Service
   - 導航至 **網路 (Networking)**（在左側邊欄）
   - 尋找 **輸出 IP 位址 (Outbound IP addresses)** 區段
   - 複製列出的所有 IP 位址（可能有多個）
   - 範例：`198.51.100.10, 198.51.100.20, 198.51.100.30`

2. **將 IP 新增至 Databricks 帳戶允許清單（Web UI 方法）：**
   - 登入您的 **Databricks 帳戶主控台**（不是工作區）
   - 在側邊欄中，點擊 **設定 (Settings)**
   - 導航至 **安全性與合規性 (Security and Compliance)** 標籤
   - 點擊 **IP 存取清單 (IP Access List)**
   - 點擊 **新增規則 (Add rule)**
   - 新增每個 Azure App Service 輸出 IP 位址
   - 清楚標記（例如 "teams-genie-bot"）
   - 選擇 **ALLOW** 作為清單類型
   - 點擊 **新增規則 (Add rule)** 儲存

   **詳細說明**，請參閱：[設定帳戶主控台的 IP 存取清單](https://docs.databricks.com/aws/en/security/network/front-end/ip-access-list-account)

3. **將 IP 新增至 Databricks 帳戶允許清單（CLI 方法）：**

   如果您偏好使用 Databricks CLI，您可以透過程式設計方式將 IP 新增至您的帳戶：

   ```bash
   databricks ip-access-lists create --json '{
     "label": "teams-genie-bot",
     "list_type": "ALLOW",
     "ip_addresses": [
       "198.51.100.10/32",
       "198.51.100.20/32",
       "198.51.100.30/32"
     ]
   }'
   ```

   將 IP 位址替換為您實際的 Azure App Service 輸出 IP。`/32` 後綴表示單一 IP 位址。

   **注意**：確保您的 CLI 已設定為使用帳戶層級驗證。

   **CLI 文件**，請參閱：[Databricks CLI IP 存取清單指令](https://docs.databricks.com/aws/en/dev-tools/cli/reference/ip-access-lists-commands)

4. **替代方案：使用 Azure VNet 整合**（進階）：
   - 設定 Azure App Service VNet 整合
   - 設定到 Databricks 的私人端點
   - 這提供更安全、穩定的 IP 位址

5. **測試連線：**
   - 將 IP 新增至帳戶允許清單後，等待幾分鐘讓變更生效
   - 再次嘗試查詢機器人
   - 檢查 Azure App Service 記錄檔以確認 403 錯誤已消失
   - 如果仍然被封鎖，驗證錯誤記錄中的 IP 是否與您新增的 IP 相符

**重要注意事項：**

- **帳戶與工作區**：此錯誤發生在 **帳戶層級**，而非工作區層級。請確保您是在帳戶主控台新增 IP，而非工作區設定。
- **IP 變更**：Azure App Service 的輸出 IP 可能會在擴展或更新期間變更。
- **生產環境建議**：考慮在生產環境部署中使用 Azure NAT Gateway 的靜態輸出 IP。
- **文件記錄**：記錄所有新增至 Databricks 帳戶 ACL 的 IP 以供日後參考。
- **IP 上限**：Databricks 支援所有允許和封鎖清單中最多 1000 個 IP/CIDR 值。
- **驗證**：務必驗證錯誤記錄中的 IP 是否與您新增至允許清單的 IP 相符。

### 6. 回饋系統問題

**問題：** 回饋按鈕 (👍/👎) 未顯示

**解決方案：**

1. 檢查環境變數中的 `ENABLE_FEEDBACK_CARDS=True`
2. 驗證您使用的用戶端是否支援 Adaptive Cards（Teams 支援）
3. 檢查 Azure App Service 記錄檔是否有卡片呈現錯誤

**問題：** 回饋提交失敗

**解決方案：**

1. 驗證環境變數中的 `ENABLE_GENIE_FEEDBACK_API=True`
2. 檢查您的 Databricks 權杖是否有權限發送回饋
3. 審查記錄檔以取得特定的 API 錯誤訊息
4. 確保 Genie 訊息 ID 有效

### 7. 對話與工作階段問題

**問題：** 對話意外重設

**原因：** 對話會在閒置 4 小時後自動重設

**解決方案：**

1. 這是預期行為 - 只需開始新的問題
2. 使用 `reset` or `new chat` 指令手動重新開始
3. 如果需要，可以在程式碼中設定 4 小時的逾時時間

**問題：** 機器人不記得之前的對話

**解決方案：**

1. 檢查是否已超過 4 小時（自動逾時）
2. 驗證您使用的是相同的使用者帳戶
3. 嘗試 `whoami` 檢查您的工作階段狀態
4. 如果需要，使用 `reset` 開始新的對話

### 8. 範例問題未顯示

**問題：** 範例問題未顯示或顯示通用問題

**解決方案：**

1. 使用自訂問題設定 `SAMPLE_QUESTIONS` 環境變數
2. 格式：`問題 1;問題 2;問題 3`（以分號分隔）
3. 更改設定後重新啟動 App Service
4. 檢查問題清單是否有語法錯誤（沒有多餘的分號）

**範例設定：**

```bash
SAMPLE_QUESTIONS=我最暢銷的產品是什麼？;顯示銷售趨勢;誰是我最好的客戶？
```

### 9. 偵錯步驟

#### 檢查記錄檔

1. 前往 Azure 入口網站 → 您的 App Service
2. 導航至 **監控 (Monitoring)** → **記錄串流 (Log stream)**
3. 尋找我們新增的偵錯訊息：

   ```text
   Loading Databricks configuration...
   DATABRICKS_HOST: https://your-workspace.cloud.databricks.com/
   DATABRICKS_TOKEN present: True
   DATABRICKS_TOKEN length: 40
   ```

#### 測試環境變數

暫時將此新增至您的 `app.py` 進行偵錯：

```python
import os
print("All environment variables:")
for key, value in os.environ.items():
    if 'DATABRICKS' in key or 'APP_' in key:
        print(f"{key}: {value[:10]}..." if len(value) > 10 else f"{key}: {value}")
```

### 10. 管理員聯絡電子郵件未顯示

**問題：** Info 指令未顯示管理員聯絡電子郵件或顯示預設值

**解決方案：**

1. 在環境變數中設定 `ADMIN_CONTACT_EMAIL`
2. 格式：`ADMIN_CONTACT_EMAIL=support@yourcompany.com`
3. 設定後重新啟動 App Service
4. 使用 `info` 指令進行測試

### 11. 效能與逾時問題

**問題：** 機器人回應非常慢

**解決方案：**

1. 檢查 Databricks API 效能和配額限制
2. 驗證 Azure 和 Databricks 之間的網路連線
3. 審查 Azure App Service 方案（考慮升級以獲得更好的效能）
4. 檢查 Genie 空間是否有大型資料集導致查詢緩慢

**問題：** 機器人逾時未回應

**解決方案：**

1. 增加 Azure App Service 逾時設定
2. 最佳化 Genie 空間查詢以獲得更好的效能
3. 檢查 Azure App Service 記錄檔是否有逾時錯誤
4. 驗證 Databricks 工作區是否有回應

### 12. 機器人指令無法運作

**問題：** `help`、`info`、`whoami` 等指令沒有回應

**解決方案：**

1. 指令不區分大小寫，但請檢查是否有錯字
2. 確保您已登入（如果需要，請先提供電子郵件）
3. 嘗試使用 `/` 前綴：`/help`、`/info`、`/whoami`
4. 檢查機器人是否有回應（嘗試簡單的訊息）

**可用指令：**

- `help` 或 `/help` - 顯示所有指令
- `info` 或 `/info` - 顯示機器人資訊
- `whoami` 或 `/whoami` - 顯示使用者資訊
- `reset` 或 `new chat` - 開始新的對話
- `logout` - 清除工作階段
- `email` - 提供電子郵件地址（當提示時）

### 13. 常見設定錯誤

1. **缺少環境變數**：確保所有必要的變數都已設定
2. **變數名稱錯誤**：檢查變數名稱是否有錯字（區分大小寫）
3. **權杖格式**：確保權杖完整且有效（以 `dapi` 開頭）
4. **Azure 設定**：驗證 App Service 設定已儲存
5. **需要重新啟動**：更改設定後務必重新啟動 App Service
6. **環境變數中的引號**：不要在 Azure App Service 設定中的值周圍使用引號
7. **分號分隔符**：對於 `SAMPLE_QUESTIONS`，使用分號 `;` 而不是逗號或其他分隔符

### 14. 取得協助

如果您仍然遇到問題：

1. **先檢查記錄檔**：Azure App Service → 監控 → 記錄串流
2. **本地測試**：在部署之前使用 Bot Framework Emulator 進行測試
3. **驗證設定**：再次檢查所有環境變數
4. **聯絡管理員**：使用 `info` 指令取得管理員聯絡電子郵件
5. **查閱文件**：
   - [Databricks Genie API 文件](https://docs.databricks.com/)
   - [Bot Framework 文件](https://docs.microsoft.com/en-us/azure/bot-service/)
   - [Teams 機器人開發](https://docs.microsoft.com/en-us/microsoftteams/platform/bots/what-are-bots)

### 15. 環境變數快速參考

**必要：**

- `DATABRICKS_TOKEN` - 您的 Databricks 個人存取權杖
- `APP_ID` - Azure Bot Service 應用程式 ID（生產環境）
- `APP_PASSWORD` - Azure Bot Service 應用程式密碼（生產環境）

**建議：**

- `DATABRICKS_SPACE_ID` - 您的 Genie 空間 ID
- `DATABRICKS_HOST` - 您的 Databricks 工作區 URL
- `SAMPLE_QUESTIONS` - 自訂範例問題（以分號分隔）
- `ADMIN_CONTACT_EMAIL` - 支援聯絡電子郵件

**選用：**

- `PORT` - 應用程式連接埠（預設：3978）
- `APP_TYPE` - SingleTenant 或 MultiTenant（預設：SingleTenant）
- `APP_TENANTID` - Azure 租戶 ID
- `ENABLE_FEEDBACK_CARDS` - 啟用回饋 UI（預設：True）
- `ENABLE_GENIE_FEEDBACK_API` - 發送回饋給 Genie（預設：True）

### 16. 快速修復檢查清單

**環境設定：**

- [ ] `DATABRICKS_TOKEN` 已在 Azure App Service 中設定
- [ ] `DATABRICKS_HOST` 已正確設定（包含 https://）
- [ ] `DATABRICKS_SPACE_ID` 已設定
- [ ] 權杖有權存取指定的 Genie 空間

**機器人設定：**

- [ ] `APP_ID` 已設定（用於生產環境）
- [ ] `APP_PASSWORD` 已設定（用於生產環境）
- [ ] Bot Framework 憑證已在 Azure Bot Service 中設定
- [ ] 訊息端點正確：`https://your-app.azurewebsites.net/api/messages`

**選用功能：**

- [ ] `SAMPLE_QUESTIONS` 已針對您的使用案例進行自訂
- [ ] `ADMIN_CONTACT_EMAIL` 已設定為您的支援電子郵件
- [ ] 回饋設定已按需設定

**部署：**

- [ ] App Service 在設定變更後已重新啟動
- [ ] 記錄檔顯示 Databricks 用戶端初始化成功
- [ ] Teams 頻道已在 Azure Bot Service 中啟用
- [ ] 機器人已安裝並可在 Teams 中存取

**測試：**

- [ ] 測試 `help` 指令是否運作
- [ ] 測試 `info` 指令是否顯示正確資訊
- [ ] 測試資料查詢是否傳回結果
- [ ] 測試回饋按鈕是否出現（如果已啟用）
- [ ] 測試 `whoami` 是否顯示正確的使用者資訊

### 基本步驟

0. Python 版本 3.11+
1. 使用 `uv sync` 安裝所需相依性
2. 設定必要的環境變數（請參閱下面的環境變數部分）
3. 執行 `uv run fastapi dev app/main.py` 以啟動機器人
4. 透過 Azure Bot Framework 呼叫機器人端點，或將其部署在 Web 應用程式上以處理呼叫。

### 🔍 環境診斷

```bash
# 自動檢查和修復常見問題
python scripts/diagnose.py
```
