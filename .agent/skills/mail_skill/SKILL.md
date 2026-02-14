---
name: Mail Skill
description: 處理郵件讀取與發送
---
# Mail Skill

此 Skill 提供 Microsoft Graph API 的郵件存取功能。

Implementation: [mail_skill.py](mail_skill.py)

## Usage

```python
from .mail_skill import MailSkill

mail_skill = MailSkill(graph_service)
emails = await mail_skill.get_recent_emails(user_id="me", count=5)
```

## Methods
- `get_recent_emails`: 獲取最近郵件
- `search_emails`: 搜尋郵件
- `send_email`: 發送郵件
