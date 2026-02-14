---
name: Authentication Skill
description: 處理身份驗證、SSO 和 Token 管理
---
# Authentication Skill

此 Skill 負責處理使用者的身份驗證流程，包括 SSO、Token 獲取與刷新。

Implementation: [authentication_skill.py](authentication_skill.py)

## Usage

```python
from .authentication_skill import AuthenticationSkill

auth_skill = AuthenticationSkill()
# 檢查使用者是否已驗證
is_auth = await auth_skill.is_user_authenticated("user_id")
```

## Methods
- `get_auth_prompt`: 獲取認證提示
- `authenticate_user`: 驗證使用者並儲存 Token
- `get_user_profile`: 獲取使用者個人資料
- `refresh_token`: 刷新 Token
- `logout_user`: 登出使用者
