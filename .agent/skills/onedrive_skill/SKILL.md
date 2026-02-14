---
name: OneDrive Skill
description: 處理雲端硬碟檔案操作
---
# OneDrive Skill

此 Skill 提供 OneDrive/SharePoint 檔案存取功能。

Implementation: [onedrive_skill.py](onedrive_skill.py)

## Usage

```python
from .onedrive_skill import OneDriveSkill

drive_skill = OneDriveSkill(graph_service)
items = await drive_skill.list_drive_items(user_id="me")
```

## Methods
- `list_drive_items`: 列出檔案與資料夾
- `search_files`: 搜尋檔案
- `create_folder`: 建立資料夾
- `get_file_metadata`: 獲取檔案資訊
