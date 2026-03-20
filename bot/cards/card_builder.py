"""統一的 Adaptive Card 構建器。

提供共用的 Card 結構模板，確保所有卡片使用一致的版本、
Schema 和視覺風格。使用語義顏色以支援 Dark Mode。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from bot.cards.constants import (
    ADAPTIVE_CARD_CONTENT_TYPE,
    ADAPTIVE_CARD_SCHEMA,
    ADAPTIVE_CARD_VERSION,
)


class CardBuilder:
    """Adaptive Card 構建器，封裝常用的卡片結構模式。"""

    @staticmethod
    def create_card(
        body: List[Dict[str, Any]],
        actions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """建立基礎 Adaptive Card 結構。"""
        card: Dict[str, Any] = {
            "type": "AdaptiveCard",
            "version": ADAPTIVE_CARD_VERSION,
            "$schema": ADAPTIVE_CARD_SCHEMA,
            "body": body,
        }
        if actions:
            card["actions"] = actions
        return card

    @staticmethod
    def wrap_as_attachment(card: Dict[str, Any]) -> Dict[str, Any]:
        """將 Card 包裝為 Bot Framework Attachment 格式。"""
        return {
            "contentType": ADAPTIVE_CARD_CONTENT_TYPE,
            "content": card,
        }

    @staticmethod
    def create_header(
        icon: str,
        title: str,
        subtitle: Optional[str] = None,
        title_color: str = "Accent",
    ) -> Dict[str, Any]:
        """建立帶有圖示的標題區塊（ColumnSet 佈局）。"""
        title_items: List[Dict[str, Any]] = [
            {
                "type": "TextBlock",
                "text": title,
                "weight": "Bolder",
                "size": "Medium",
                "color": title_color,
            }
        ]
        if subtitle:
            title_items.append(
                {
                    "type": "TextBlock",
                    "text": subtitle,
                    "isSubtle": True,
                    "spacing": "None",
                    "size": "Small",
                }
            )

        return {
            "type": "Container",
            "style": "emphasis",
            "items": [
                {
                    "type": "ColumnSet",
                    "columns": [
                        {
                            "type": "Column",
                            "width": "auto",
                            "items": [
                                {"type": "TextBlock", "text": icon, "size": "Large"}
                            ],
                        },
                        {
                            "type": "Column",
                            "width": "stretch",
                            "items": title_items,
                        },
                    ],
                }
            ],
        }

    @staticmethod
    def text_block(
        text: str,
        *,
        wrap: bool = True,
        size: str = "Default",
        weight: str = "Default",
        color: str = "Default",
        is_subtle: bool = False,
        spacing: Optional[str] = None,
        horizontal_alignment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """建立文字區塊。"""
        block: Dict[str, Any] = {
            "type": "TextBlock",
            "text": text,
            "wrap": wrap,
            "size": size,
        }
        if weight != "Default":
            block["weight"] = weight
        if color != "Default":
            block["color"] = color
        if is_subtle:
            block["isSubtle"] = True
        if spacing:
            block["spacing"] = spacing
        if horizontal_alignment:
            block["horizontalAlignment"] = horizontal_alignment
        return block

    @staticmethod
    def action_submit(
        title: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """建立 Action.Submit 按鈕。"""
        return {
            "type": "Action.Submit",
            "title": title,
            "data": data,
        }

    @staticmethod
    def separator() -> Dict[str, Any]:
        """建立分隔線（使用空 Container 的 separator 屬性）。"""
        return {
            "type": "Container",
            "separator": True,
            "spacing": "Small",
            "items": [],
        }
