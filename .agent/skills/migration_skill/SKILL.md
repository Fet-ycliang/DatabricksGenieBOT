---
name: Migration Skill
description: 協助 Bot Framework 遷移至 M365 Agent Framework
---
# Migration Skill

此 Skill 包含分析舊專案結構與產生遷移計畫的工具。

Implementation: [migration_skill.py](migration_skill.py)

## Usage

```python
from .migration_skill import MigrationSkill

migration_skill = MigrationSkill()
analysis = await migration_skill.analyze_bot_framework_project("path/to/project")
```

## Methods
- `analyze_bot_framework_project`: 分析專案結構
- `create_migration_plan`: 建立遷移計畫
- `generate_skill_template`: 產生 Skill 程式碼模板
