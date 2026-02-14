---
name: Command Skill
description: 處理特殊指令 (help, info, etc.)
---
# Command Skill

此 Skill 負責解析與執行使用者輸入的特殊指令。

Implementation: [command_skill.py](command_skill.py)

## Usage

```python
from .command_skill import CommandSkill

cmd_skill = CommandSkill()
if await cmd_skill.is_command("/help"):
    response = await cmd_skill.handle_command("/help", user_id="user1")
```

## Methods
- `is_command`: 檢查是否為指令
- `handle_command`: 執行指令
- `get_available_commands`: 獲取可用指令列表
