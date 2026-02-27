"""查詢結果表格 Adaptive Card。

使用 Adaptive Card v1.5 的 Table 元素呈現查詢結果，
取代原本的 Markdown code block，提供更好的可讀性。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from bot.cards.card_builder import CardBuilder
from bot.cards.constants import EMOJI_CHART_BAR, EMOJI_SUCCESS


# 表格顯示限制
MAX_DISPLAY_COLUMNS = 8
MAX_DISPLAY_ROWS = 10

# 數值類型（靠右對齊）
_NUMERIC_TYPES = frozenset({"DECIMAL", "DOUBLE", "FLOAT", "INT", "BIGINT", "LONG"})


def create_data_table_card(
    columns: Dict[str, Any],
    data: Dict[str, Any],
    query_description: Optional[str] = None,
    total_rows: Optional[int] = None,
) -> Dict:
    """建立查詢結果的表格 Adaptive Card。

    Args:
        columns: Genie API 回傳的 columns schema dict
        data: Genie API 回傳的 data dict（含 data_array）
        query_description: 查詢的自然語言描述
        total_rows: 總資料筆數（用於顯示截斷提示）
    """
    body: List[Dict[str, Any]] = []

    # 標題區塊
    subtitle = query_description or "以下是您的查詢結果"
    body.append(
        CardBuilder.create_header(
            icon=EMOJI_CHART_BAR,
            title="查詢結果",
            subtitle=subtitle,
        )
    )

    # 解析欄位名稱和類型
    col_list = _extract_columns(columns)
    data_array = _extract_data_array(data)

    if not col_list or not data_array:
        body.append(
            CardBuilder.text_block(
                f"{EMOJI_SUCCESS} 查詢成功，但沒有資料返回。",
                is_subtle=True,
                spacing="Medium",
            )
        )
        return CardBuilder.create_card(body=body)

    # 截斷欄位（超過上限時）
    display_cols = col_list[:MAX_DISPLAY_COLUMNS]
    truncated_cols = len(col_list) > MAX_DISPLAY_COLUMNS

    # 建構 Table 元素（Adaptive Card v1.5）
    table_columns = [
        {
            "width": 1,
        }
        for _ in display_cols
    ]

    # Header row
    header_cells = []
    for col in display_cols:
        is_numeric = col.get("type_name", "STRING") in _NUMERIC_TYPES
        header_cells.append({
            "type": "TableCell",
            "items": [
                CardBuilder.text_block(
                    col["name"],
                    weight="Bolder",
                    size="Small",
                    horizontal_alignment="Right" if is_numeric else None,
                )
            ],
        })
    header_row = {
        "type": "TableRow",
        "style": "accent",
        "cells": header_cells,
    }

    # Data rows（限制顯示筆數）
    display_rows = data_array[:MAX_DISPLAY_ROWS]
    data_rows = []
    for row in display_rows:
        cells = []
        for i, col in enumerate(display_cols):
            value = row[i] if i < len(row) else ""
            type_name = col.get("type_name", "STRING")
            formatted = _format_cell_value(value, type_name)
            is_numeric = type_name in _NUMERIC_TYPES
            cells.append(
                {
                    "type": "TableCell",
                    "items": [
                        CardBuilder.text_block(
                            formatted,
                            size="Small",
                            horizontal_alignment="Right" if is_numeric else None,
                        )
                    ],
                }
            )
        data_rows.append({"type": "TableRow", "cells": cells})

    table = {
        "type": "Table",
        "columns": table_columns,
        "rows": [header_row] + data_rows,
        "gridStyle": "accent",
        "firstRowAsHeader": True,
        "showGridLines": True,
        "spacing": "Medium",
    }
    body.append(table)

    # 統計/截斷提示
    actual_total = total_rows or len(data_array)
    footer_parts = [f"共 {actual_total} 筆資料"]
    if actual_total > MAX_DISPLAY_ROWS:
        footer_parts.append(f"顯示前 {MAX_DISPLAY_ROWS} 筆")
    if truncated_cols:
        footer_parts.append(f"顯示前 {MAX_DISPLAY_COLUMNS}/{len(col_list)} 欄")

    body.append(
        CardBuilder.text_block(
            f"{EMOJI_SUCCESS} {' | '.join(footer_parts)}",
            size="Small",
            is_subtle=True,
            spacing="Small",
            horizontal_alignment="Center",
        )
    )

    return CardBuilder.create_card(body=body)


def _extract_columns(columns: Any) -> List[Dict[str, str]]:
    """從 Genie API 的 columns schema 中提取欄位資訊。"""
    if isinstance(columns, dict) and "columns" in columns:
        return [
            {"name": col.get("name", "Col"), "type_name": col.get("type_name", "STRING")}
            for col in columns["columns"]
        ]
    return []


def _extract_data_array(data: Any) -> List[List[Any]]:
    """從 Genie API 的 data 回應中提取資料陣列。"""
    if isinstance(data, dict) and "data_array" in data:
        return data["data_array"] or []
    return []


def _format_cell_value(value: Any, type_name: str) -> str:
    """格式化儲存格值。"""
    if value is None:
        return "—"
    if type_name in ("DECIMAL", "DOUBLE", "FLOAT"):
        try:
            return f"{float(value):,.2f}"
        except (ValueError, TypeError):
            return str(value)
    if type_name in ("INT", "BIGINT", "LONG"):
        try:
            return f"{int(value):,}"
        except (ValueError, TypeError):
            return str(value)
    return str(value)
