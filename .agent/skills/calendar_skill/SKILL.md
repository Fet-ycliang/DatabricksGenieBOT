---
name: Calendar Skill
description: 處理日曆與活動
---
# Calendar Skill

此 Skill 提供行事曆管理與活動查詢功能。

Implementation: [calendar_skill.py](calendar_skill.py)

## Usage

```python
from .calendar_skill import CalendarSkill

cal_skill = CalendarSkill(graph_service)
events = await cal_skill.get_upcoming_events(user_id="me")
```

## Methods
- `get_upcoming_events`: 獲取即將到來的活動
- `create_event`: 建立新活動
- `find_free_time`: 尋找共同空閒時間
