---
name: azure-identity-py
description: |
  Azure Identity SDK for Python 身份驗證。用於 DefaultAzureCredential、受控識別 (managed identity)、服務主體 (service principals) 和權杖快取。
  Triggers: "azure-identity", "DefaultAzureCredential", "authentication", "managed identity", "service principal", "credential".
package: azure-identity
---

# Azure Identity SDK for Python

使用 Microsoft Entra ID (前身為 Azure AD) 進行 Azure SDK 用戶端身份驗證的函式庫。

## 安裝

```bash
pip install azure-identity
```

## 環境變數

```bash
# Service Principal (用於生產環境/CI)
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-client-id>
AZURE_CLIENT_SECRET=<your-client-secret>

# User-assigned Managed Identity (選填)
AZURE_CLIENT_ID=<managed-identity-client-id>
```

## DefaultAzureCredential

適用於大多數場景的推薦憑證。依序嘗試多種身份驗證方法：

```python
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

# 在本地開發和生產環境中皆可運作，無需修改程式碼
credential = DefaultAzureCredential()

client = BlobServiceClient(
    account_url="https://<account>.blob.core.windows.net",
    credential=credential
)
```

### 憑證鏈順序 (Credential Chain Order)

| 順序 | 憑證 (Credential)           | 環境                              |
| ---- | --------------------------- | --------------------------------- |
| 1    | EnvironmentCredential       | CI/CD, containers                 |
| 2    | WorkloadIdentityCredential  | Kubernetes                        |
| 3    | ManagedIdentityCredential   | Azure VMs, App Service, Functions |
| 4    | SharedTokenCacheCredential  | Windows only                      |
| 5    | VisualStudioCodeCredential  | VS Code with Azure extension      |
| 6    | AzureCliCredential          | `az login`                        |
| 7    | AzurePowerShellCredential   | `Connect-AzAccount`               |
| 8    | AzureDeveloperCliCredential | `azd auth login`                  |

### 自訂 DefaultAzureCredential

```python
# 排除你不需要的憑證
credential = DefaultAzureCredential(
    exclude_environment_credential=True,
    exclude_shared_token_cache_credential=True,
    managed_identity_client_id="<user-assigned-mi-client-id>"  # For user-assigned MI
)

# 啟用互動式瀏覽器 (預設為停用)
credential = DefaultAzureCredential(
    exclude_interactive_browser_credential=False
)
```

## 特定憑證類型

### ManagedIdentityCredential

用於 Azure 託管資源 (VMs, App Service, Functions, AKS)：

```python
from azure.identity import ManagedIdentityCredential

# System-assigned managed identity
credential = ManagedIdentityCredential()

# User-assigned managed identity
credential = ManagedIdentityCredential(
    client_id="<user-assigned-mi-client-id>"
)
```

### ClientSecretCredential

用於帶有秘密 (secret) 的服務主體：

```python
from azure.identity import ClientSecretCredential

credential = ClientSecretCredential(
    tenant_id=os.environ["AZURE_TENANT_ID"],
    client_id=os.environ["AZURE_CLIENT_ID"],
    client_secret=os.environ["AZURE_CLIENT_SECRET"]
)
```

### AzureCliCredential

使用來自 `az login` 的帳戶：

```python
from azure.identity import AzureCliCredential

credential = AzureCliCredential()
```

### ChainedTokenCredential

自訂憑證鏈：

```python
from azure.identity import (
    ChainedTokenCredential,
    ManagedIdentityCredential,
    AzureCliCredential
)

# 先嘗試受控識別，失敗則退回使用 CLI
credential = ChainedTokenCredential(
    ManagedIdentityCredential(client_id="<user-assigned-mi-client-id>"),
    AzureCliCredential()
)
```

## 憑證類型表

| 憑證                           | 使用案例          | 身份驗證方法        |
| ------------------------------ | ----------------- | ------------------- |
| `DefaultAzureCredential`       | 大多數場景        | 自動偵測            |
| `ManagedIdentityCredential`    | Azure 託管應用程式 | 受控識別            |
| `ClientSecretCredential`       | 服務主體          | 用戶端秘密          |
| `ClientCertificateCredential`  | 服務主體          | 憑證                |
| `AzureCliCredential`           | 本地開發          | Azure CLI           |
| `AzureDeveloperCliCredential`  | 本地開發          | Azure Developer CLI |
| `InteractiveBrowserCredential` | 使用者登入        | 瀏覽器 OAuth        |
| `DeviceCodeCredential`         | 無頭裝置/SSH      | 裝置代碼流程        |

## 直接取得 Token

```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()

# 取得特定範圍 (scope) 的 token
token = credential.get_token("https://management.azure.com/.default")
print(f"Token expires: {token.expires_on}")

# For Azure Database for PostgreSQL
token = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
```

## 非同步用戶端 (Async Client)

```python
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient

async def main():
    credential = DefaultAzureCredential()

    async with BlobServiceClient(
        account_url="https://<account>.blob.core.windows.net",
        credential=credential
    ) as client:
        # ... async operations
        pass

    await credential.close()
```

## 最佳實踐

1. **使用 DefaultAzureCredential** 於本地和 Azure 中執行的程式碼
2. **絕不硬編碼憑證** — 使用環境變數或受控識別
3. **優先使用受控識別** 於生產環境 Azure 部署
4. **使用 ChainedTokenCredential** 當你需要自訂憑證順序時
5. **明確關閉非同步憑證** 或使用 context managers
6. **設定 AZURE_CLIENT_ID** 用於使用者指派的受控識別
7. **排除未使用的憑證** 以加速身份驗證
