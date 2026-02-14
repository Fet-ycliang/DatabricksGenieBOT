---
name: Bot Core Skill
description: 處理基礎對話流程與歡迎訊息
---
# Bot Core Skill

此 Skill 負責 Bot 的核心互動邏輯，如成員加入事件和訊息路由。

Implementation: [bot_core_skill.py](bot_core_skill.py)

## Usage

```python
from .bot_core_skill import BotCoreSkill

bot_skill = BotCoreSkill()
response = await bot_skill.handle_message(user_id="user1", message_text="hi")
```

## Methods
- `handle_member_added`: 處理成員加入
- `handle_message`: 處理使用者訊息
- `handle_reset`: 重置對話
- `get_conversation_context`: 獲取對話上下文
