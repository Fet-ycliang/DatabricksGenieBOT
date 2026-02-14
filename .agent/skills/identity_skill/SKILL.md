---
name: Identity Skill
description: 處理使用者身分識別與 Email 輸入
---
# Identity Skill

此 Skill 負責在使用者尚未認證時，引導輸入 Email 並進行身分確認。

Implementation: [identity_skill.py](identity_skill.py)

## Usage

```python
from .identity_skill import IdentitySkill

id_skill = IdentitySkill()
if await id_skill.is_user_pending_email("user1"):
    response = await id_skill.handle_user_identification("user1", "email@example.com")
```

## Methods
- `handle_user_identification`: 處理身分識別流程
- `validate_email`: 驗證 Email 格式
- `confirm_email`: 確認使用者身分
