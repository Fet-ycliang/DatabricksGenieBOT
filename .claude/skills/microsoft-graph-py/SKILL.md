---
name: microsoft-graph-py
description: Interact with Microsoft Graph API using standard HTTP patterns (aiohttp/requests). Use for fetching user profiles, photos, calendars, etc.
---

# Microsoft Graph API (Python)

Patterns for calling Microsoft Graph API using raw HTTP clients (lightweight, no SDK required).

## Base URL

`https://graph.microsoft.com/v1.0`

## 1. Fetch User Profile

Using `aiohttp` (Async):

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

## 2. Fetch User Photo (Binary)

Photos are returned as binary streams.

```python
async def get_photo(access_token: str):
    url = "https://graph.microsoft.com/v1.0/me/photo/$value"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                return await resp.read()  # Returns bytes
            return None
```

## 3. Common Endpoints

| Resource         | Method | Endpoint           | Permission           |
| ---------------- | ------ | ------------------ | -------------------- |
| **Profile**      | GET    | `/me`              | `User.Read`          |
| **Photo**        | GET    | `/me/photo/$value` | `User.Read`          |
| **Manager**      | GET    | `/me/manager`      | `User.Read`          |
| **Joined Teams** | GET    | `/me/joinedTeams`  | `Team.ReadBasic.All` |
| **Send Mail**    | POST   | `/me/sendMail`     | `Mail.Send`          |

## 4. Error Handling

Graph errors usually return a JSON body:

```json
{
  "error": {
    "code": "InvalidAuthenticationToken",
    "message": "Access token validation failure.",
    "innerError": { ... }
  }
}
```

**Best Practice**: Always check `resp.status` and parse the JSON error body for details.

## 5. Pagination

Graph uses `@odata.nextLink` for paging.

```python
async def get_all_users(access_token: str):
    users = []
    url = "https://graph.microsoft.com/v1.0/users"

    async with aiohttp.ClientSession() as session:
        while url:
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()
                users.extend(data.get('value', []))
                url = data.get('@odata.nextLink')  # Get next page URL

    return users
```
