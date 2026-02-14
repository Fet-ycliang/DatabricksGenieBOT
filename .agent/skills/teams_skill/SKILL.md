---
name: Teams Skill
description: 處理 Teams 團隊與頻道操作
---
# Teams Skill

此 Skill 提供 Microsoft Teams 相關功能，如讀取頻道訊息與發送訊息。

Implementation: [teams_skill.py](teams_skill.py)

## Usage

```python
from .teams_skill import TeamsSkill

teams_skill = TeamsSkill(graph_service)
teams = await teams_skill.list_teams(user_id="me")
```

## Methods
- `list_teams`: 列出參與的團隊
- `list_channels`: 列出團隊頻道
- `get_channel_messages`: 獲取頻道訊息
- `send_message_to_channel`: 發送訊息到頻道
