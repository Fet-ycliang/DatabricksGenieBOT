---
name: databricks-bot-card
description: |
  Teams Adaptive Card 設計器。提供常用卡片模板（歡迎、結果、圖表、錯誤、回饋）。
  觸發：「建立卡片」「Adaptive Card」「Teams card」「顯示結果」「互動按鈕」
  快速生成美觀的 Teams 訊息卡片。
---

# DatabricksGenieBOT Card Designer

快速建立 Teams Adaptive Cards，提供常用模板和設計模式。

## Adaptive Card 基礎

```python
from botbuilder.schema import Attachment

def create_basic_card(title: str, text: str) -> Attachment:
    """基本卡片"""
    adaptive_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": title,
                "size": "Large",
                "weight": "Bolder"
            },
            {
                "type": "TextBlock",
                "text": text,
                "wrap": True
            }
        ]
    }

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=adaptive_card
    )
```

---

## 1. 歡迎卡片

```python
def create_welcome_card(user_name: str) -> Attachment:
    """歡迎卡片（帶範例問題）"""

    sample_questions = [
        "📊 本月業績前 10 名客戶",
        "📈 過去 7 天的銷售趨勢",
        "🎯 本季度目標達成率"
    ]

    adaptive_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": f"👋 歡迎，{user_name}！",
                "size": "Large",
                "weight": "Bolder"
            },
            {
                "type": "TextBlock",
                "text": "我是 Databricks Genie Bot，可以幫您查詢資料。",
                "wrap": True,
                "spacing": "Medium"
            },
            {
                "type": "TextBlock",
                "text": "💡 範例問題：",
                "weight": "Bolder",
                "spacing": "Medium"
            },
            {
                "type": "TextBlock",
                "text": "\n".join(sample_questions),
                "wrap": True
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "🚀 開始查詢",
                "data": {"action": "start"}
            }
        ]
    }

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=adaptive_card
    )
```

---

## 2. 查詢結果卡片（表格）

```python
def create_result_table_card(
    title: str,
    columns: list[str],
    rows: list[list],
    total_rows: int = None
) -> Attachment:
    """查詢結果表格卡片"""

    # 建立表格行
    table_rows = []
    for row in rows[:10]:  # 最多顯示 10 行
        row_text = " | ".join([str(cell) for cell in row])
        table_rows.append({
            "type": "TextBlock",
            "text": row_text,
            "wrap": True
        })

    # 建立卡片
    card_body = [
        {
            "type": "TextBlock",
            "text": title,
            "size": "Large",
            "weight": "Bolder"
        },
        {
            "type": "TextBlock",
            "text": f"📋 欄位：{' | '.join(columns)}",
            "weight": "Bolder",
            "spacing": "Medium"
        },
        {
            "type": "Container",
            "items": table_rows,
            "spacing": "Small"
        }
    ]

    # 顯示總筆數
    if total_rows and total_rows > len(rows):
        card_body.append({
            "type": "TextBlock",
            "text": f"顯示 {len(rows)} / {total_rows} 筆資料",
            "size": "Small",
            "isSubtle": True,
            "spacing": "Medium"
        })

    adaptive_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": card_body,
        "actions": [
            {
                "type": "Action.Submit",
                "title": "👍 有幫助",
                "data": {"feedback": "positive"}
            },
            {
                "type": "Action.Submit",
                "title": "👎 沒幫助",
                "data": {"feedback": "negative"}
            }
        ]
    }

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=adaptive_card
    )
```

---

## 3. 圖表卡片

```python
def create_chart_card(
    title: str,
    chart_base64: str,
    description: str = None
) -> Attachment:
    """圖表卡片（顯示 base64 圖片）"""

    card_body = [
        {
            "type": "TextBlock",
            "text": title,
            "size": "Large",
            "weight": "Bolder"
        }
    ]

    if description:
        card_body.append({
            "type": "TextBlock",
            "text": description,
            "wrap": True,
            "spacing": "Small"
        })

    card_body.append({
        "type": "Image",
        "url": chart_base64,  # data:image/png;base64,xxx
        "size": "Large",
        "spacing": "Medium"
    })

    adaptive_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": card_body,
        "actions": [
            {
                "type": "Action.Submit",
                "title": "👍 有幫助",
                "data": {"feedback": "positive", "type": "chart"}
            },
            {
                "type": "Action.Submit",
                "title": "👎 沒幫助",
                "data": {"feedback": "negative", "type": "chart"}
            }
        ]
    }

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=adaptive_card
    )
```

---

## 4. 錯誤卡片

```python
def create_error_card(
    error_message: str,
    error_code: str = None,
    suggestions: list[str] = None
) -> Attachment:
    """錯誤訊息卡片"""

    card_body = [
        {
            "type": "TextBlock",
            "text": "⚠️ 發生錯誤",
            "size": "Large",
            "weight": "Bolder",
            "color": "Warning"
        },
        {
            "type": "TextBlock",
            "text": error_message,
            "wrap": True,
            "spacing": "Medium"
        }
    ]

    if error_code:
        card_body.append({
            "type": "TextBlock",
            "text": f"錯誤代碼: {error_code}",
            "size": "Small",
            "isSubtle": True,
            "spacing": "Small"
        })

    if suggestions:
        card_body.append({
            "type": "TextBlock",
            "text": "💡 建議：",
            "weight": "Bolder",
            "spacing": "Medium"
        })
        for suggestion in suggestions:
            card_body.append({
                "type": "TextBlock",
                "text": f"• {suggestion}",
                "wrap": True,
                "spacing": "Small"
            })

    adaptive_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": card_body,
        "actions": [
            {
                "type": "Action.Submit",
                "title": "🔄 重試",
                "data": {"action": "retry"}
            },
            {
                "type": "Action.Submit",
                "title": "❓ 尋求協助",
                "data": {"action": "help"}
            }
        ]
    }

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=adaptive_card
    )
```

---

## 5. 回饋卡片

```python
def create_feedback_card(
    query: str,
    result_id: str
) -> Attachment:
    """回饋收集卡片"""

    adaptive_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "📝 這個回答有幫助嗎？",
                "size": "Medium",
                "weight": "Bolder"
            },
            {
                "type": "TextBlock",
                "text": f"查詢: {query}",
                "wrap": True,
                "isSubtle": True,
                "spacing": "Small"
            },
            {
                "type": "Input.ChoiceSet",
                "id": "rating",
                "choices": [
                    {"title": "⭐⭐⭐⭐⭐ 非常有幫助", "value": "5"},
                    {"title": "⭐⭐⭐⭐ 有幫助", "value": "4"},
                    {"title": "⭐⭐⭐ 普通", "value": "3"},
                    {"title": "⭐⭐ 不太有幫助", "value": "2"},
                    {"title": "⭐ 完全沒幫助", "value": "1"}
                ],
                "style": "compact",
                "spacing": "Medium"
            },
            {
                "type": "Input.Text",
                "id": "comment",
                "placeholder": "額外意見（選填）",
                "isMultiline": True,
                "spacing": "Small"
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "提交回饋",
                "data": {
                    "action": "submit_feedback",
                    "result_id": result_id
                }
            }
        ]
    }

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=adaptive_card
    )
```

---

## 6. 進度卡片

```python
def create_progress_card(
    title: str,
    progress: int,  # 0-100
    status_text: str
) -> Attachment:
    """進度顯示卡片"""

    adaptive_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": title,
                "size": "Medium",
                "weight": "Bolder"
            },
            {
                "type": "TextBlock",
                "text": status_text,
                "wrap": True,
                "spacing": "Small"
            },
            {
                "type": "ProgressBar",
                "title": f"{progress}%",
                "value": progress / 100.0,
                "spacing": "Medium"
            }
        ]
    }

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=adaptive_card
    )
```

---

## 7. 選擇卡片

```python
def create_choice_card(
    question: str,
    choices: list[dict]  # [{"title": "選項1", "value": "val1"}, ...]
) -> Attachment:
    """選擇卡片（單選或多選）"""

    adaptive_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": question,
                "size": "Medium",
                "weight": "Bolder",
                "wrap": True
            },
            {
                "type": "Input.ChoiceSet",
                "id": "selected_choice",
                "choices": choices,
                "style": "expanded",
                "spacing": "Medium"
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "確認",
                "data": {"action": "choice_confirmed"}
            }
        ]
    }

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=adaptive_card
    )
```

---

## 8. FactSet 卡片（鍵值對）

```python
def create_fact_set_card(
    title: str,
    facts: dict,  # {"欄位1": "值1", "欄位2": "值2"}
    actions: list[dict] = None
) -> Attachment:
    """FactSet 卡片（顯示鍵值對資料）"""

    fact_list = [
        {"title": key, "value": str(value)}
        for key, value in facts.items()
    ]

    card_body = [
        {
            "type": "TextBlock",
            "text": title,
            "size": "Large",
            "weight": "Bolder"
        },
        {
            "type": "FactSet",
            "facts": fact_list,
            "spacing": "Medium"
        }
    ]

    card_actions = []
    if actions:
        for action in actions:
            card_actions.append({
                "type": "Action.Submit",
                "title": action.get("title", "Action"),
                "data": action.get("data", {})
            })

    adaptive_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": card_body,
        "actions": card_actions
    }

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=adaptive_card
    )
```

---

## 9. 複合卡片（多容器）

```python
def create_complex_card(
    title: str,
    sections: list[dict]  # [{"title": "...", "content": "..."}, ...]
) -> Attachment:
    """複合卡片（多個區塊）"""

    card_body = [
        {
            "type": "TextBlock",
            "text": title,
            "size": "Large",
            "weight": "Bolder"
        }
    ]

    for section in sections:
        container = {
            "type": "Container",
            "spacing": "Medium",
            "separator": True,
            "items": [
                {
                    "type": "TextBlock",
                    "text": section["title"],
                    "weight": "Bolder"
                },
                {
                    "type": "TextBlock",
                    "text": section["content"],
                    "wrap": True,
                    "spacing": "Small"
                }
            ]
        }
        card_body.append(container)

    adaptive_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": card_body
    }

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=adaptive_card
    )
```

---

## 10. Hero Card（簡化版）

```python
from botbuilder.schema import HeroCard, CardAction, CardImage

def create_hero_card(
    title: str,
    subtitle: str = None,
    text: str = None,
    images: list[str] = None,
    buttons: list[dict] = None
) -> Attachment:
    """Hero Card（較簡單的卡片格式）"""

    card_images = []
    if images:
        card_images = [CardImage(url=img) for img in images]

    card_buttons = []
    if buttons:
        for btn in buttons:
            card_buttons.append(
                CardAction(
                    type="imBack",
                    title=btn["title"],
                    value=btn["value"]
                )
            )

    hero_card = HeroCard(
        title=title,
        subtitle=subtitle,
        text=text,
        images=card_images,
        buttons=card_buttons
    )

    return Attachment(
        content_type="application/vnd.microsoft.card.hero",
        content=hero_card
    )
```

---

## 設計最佳實踐

### 1. 卡片大小限制
- 卡片 JSON 大小上限：**28 KB**
- 建議保持在 20 KB 以下
- 圖片使用 base64 會增加大小（建議使用 URL）

### 2. 視覺層次
```python
# 好的層次結構
{
    "type": "TextBlock",
    "text": "主標題",
    "size": "Large",      # 使用不同大小
    "weight": "Bolder"    # 使用不同粗細
}
{
    "type": "TextBlock",
    "text": "次標題",
    "size": "Medium",
    "weight": "Bolder",
    "spacing": "Medium"   # 使用間距
}
{
    "type": "TextBlock",
    "text": "內容文字",
    "wrap": True          # 自動換行
}
```

### 3. 顏色使用
```python
# Adaptive Card 支援的顏色
"color": "Default"    # 預設
"color": "Dark"       # 深色
"color": "Light"      # 淺色
"color": "Accent"     # 強調色
"color": "Good"       # 成功（綠色）
"color": "Warning"    # 警告（黃色）
"color": "Attention"  # 注意（紅色）
```

### 4. 響應式設計
```python
# 使用 wrap 確保文字不會超出螢幕
{
    "type": "TextBlock",
    "text": "長文字內容...",
    "wrap": True,
    "maxLines": 3  # 限制最大行數
}
```

---

## 測試卡片

### 使用 Adaptive Card Designer
1. 訪問: https://adaptivecards.io/designer/
2. 貼上 JSON
3. 預覽效果
4. 調整樣式

### 在 Teams 測試
```python
async def send_test_card(turn_context: TurnContext):
    """發送測試卡片"""
    card = create_welcome_card("Test User")
    await turn_context.send_activity(
        Activity(
            type="message",
            attachments=[card]
        )
    )
```

---

## 常見卡片模板速查

| 卡片類型 | 函式名稱 | 使用時機 |
|---------|---------|---------|
| 歡迎卡片 | `create_welcome_card()` | 用戶首次使用 |
| 結果表格 | `create_result_table_card()` | 顯示查詢結果 |
| 圖表卡片 | `create_chart_card()` | 顯示視覺化圖表 |
| 錯誤卡片 | `create_error_card()` | 錯誤訊息 |
| 回饋卡片 | `create_feedback_card()` | 收集用戶回饋 |
| 進度卡片 | `create_progress_card()` | 長時間操作 |
| 選擇卡片 | `create_choice_card()` | 用戶選擇選項 |
| FactSet | `create_fact_set_card()` | 鍵值對資料 |

---

## 參考資源

- [Adaptive Cards 官方文檔](https://adaptivecards.io/)
- [Adaptive Card Designer](https://adaptivecards.io/designer/)
- [Teams Card 範例](https://learn.microsoft.com/en-us/microsoftteams/platform/task-modules-and-cards/cards/cards-reference)
