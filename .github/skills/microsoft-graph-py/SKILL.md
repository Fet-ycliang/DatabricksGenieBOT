---
name: microsoft-graph-py
description: 使用標準 HTTP 模式 (aiohttp/requests) 與 Microsoft Graph API 互動。用於擷取使用者設定檔、照片、日曆等。
---

# Microsoft Graph API (Python)

使用原始 HTTP 用戶端 (輕量級，無需 SDK) 呼叫 Microsoft Graph API 的模式。

## Base URL

`https://graph.microsoft.com/v1.0`

## 1. 擷取使用者設定檔

使用 `aiohttp` (Async):

```python
import aiohttp

async def get_me(access_token: str):
    url = "https://graph.microsoft.com/v1.0/me"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                raise Exception(f"Graph API Error: {resp.status}")
```

## 2. 擷取使用者照片 (Binary)

照片以二進位串流形式回傳。

```python
async def get_photo(access_token: str):
    url = "https://graph.microsoft.com/v1.0/me/photo/$value"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                return await resp.read()  # 回傳 bytes
            return None
```

## 3. 常見端點

| 資源             | 方法   | 端點               | 權限                 |
| ---------------- | ------ | ------------------ | -------------------- |
| **Profile**      | GET    | `/me`              | `User.Read`          |
| **Photo**        | GET    | `/me/photo/$value` | `User.Read`          |
| **Manager**      | GET    | `/me/manager`      | `User.Read`          |
| **Joined Teams** | GET    | `/me/joinedTeams`  | `Team.ReadBasic.All` |
| **Send Mail**    | POST   | `/me/sendMail`     | `Mail.Send`          |

## 4. 錯誤處理

Graph 錯誤通常回傳 JSON body：

```json
{
  "error": {
    "code": "InvalidAuthenticationToken",
    "message": "Access token validation failure.",
    "innerError": { ... }
  }
}
```

**最佳實踐**：務必檢查 `resp.status` 並解析 JSON 錯誤 body 以取得細節。

## 5. 分頁 (Pagination)

Graph 使用 `@odata.nextLink` 進行分頁。

```python
async def get_all_users(access_token: str):
    users = []
    url = "https://graph.microsoft.com/v1.0/users"

    async with aiohttp.ClientSession() as session:
        while url:
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()
                users.extend(data.get('value', []))
                url = data.get('@odata.nextLink')  # 取得下一頁 URL

    return users
```
