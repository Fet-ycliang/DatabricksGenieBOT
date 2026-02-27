"""統一的查詢結果渲染器。

將所有 UI 渲染邏輯從 bot handler 中抽取出來，
handler 只需呼叫 render_response() 即可完成所有 UI 更新。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from botbuilder.core import MessageFactory, TurnContext
from botbuilder.schema import Attachment

from app.models.user_session import UserSession
from app.utils.chart_analyzer import ChartAnalyzer
from bot.cards.chart_generator import (
    create_suggested_questions_card,
    generate_chart_image,
)
from bot.cards.constants import CHART_ICONS, EMOJI_CHART_BAR
from bot.cards.data_table_card import create_data_table_card
from bot.cards.feedback_cards import send_feedback_card

logger = logging.getLogger(__name__)


async def render_response(
    turn_context: TurnContext,
    response_data: Dict[str, Any],
    user_session: UserSession,
    enable_feedback_cards: bool,
) -> None:
    """統一渲染 Genie API 回應結果。

    根據 response_data 的內容決定渲染策略：
    - error: 顯示錯誤訊息
    - message: 顯示文字回覆 + 建議問題
    - data: 顯示表格 + 圖表 + 建議問題
    - 其他: 發送 feedback card

    Args:
        turn_context: Bot Framework TurnContext
        response_data: 解析後的 Genie API 回應 dict
        user_session: 使用者 session
        enable_feedback_cards: 是否啟用回饋卡片
    """
    try:
        if "error" in response_data:
            await turn_context.send_activity(f"Error: {response_data['error']}")
            return

        if "message" in response_data:
            await _render_text_response(turn_context, response_data)
        elif "data" in response_data:
            await _render_data_response(turn_context, response_data)
    finally:
        # 統一發送回饋卡片（不管走哪個分支）
        await send_feedback_card(turn_context, user_session, enable_feedback_cards)

        # 統一發送建議問題
        await _send_suggested_questions(turn_context, response_data)


async def _render_text_response(
    turn_context: TurnContext,
    response_data: Dict[str, Any],
) -> None:
    """渲染文字類型的回應。"""
    if response_data.get("query_description"):
        await turn_context.send_activity(
            f"{EMOJI_CHART_BAR} {response_data['query_description']}"
        )
    await turn_context.send_activity(response_data["message"])


async def _render_data_response(
    turn_context: TurnContext,
    response_data: Dict[str, Any],
) -> None:
    """渲染資料表格和圖表。"""
    # 查詢描述已包含在 data_table_card header 中，不需要額外發送

    columns = response_data.get("columns")
    data = response_data.get("data")

    # 分析圖表適用性
    if columns and data:
        chart_info = ChartAnalyzer.analyze_suitability(columns, data)
        if chart_info.get('suitable'):
            response_data['chart_info'] = chart_info
            logger.info(
                f"圖表適用: {chart_info.get('chart_type')} 圖 "
                f"(類別: {chart_info.get('category_column')}, 數值: {chart_info.get('value_column')})"
            )

    # 發送資料表格卡片（即使 data={} 也要呼叫，讓 _send_data_table 顯示「無資料」提示）
    if columns is not None:
        await _send_data_table(turn_context, columns, data or {}, response_data.get("query_description"))

    # 發送圖表
    if response_data.get("chart_info"):
        await _send_chart(turn_context, response_data["chart_info"])


async def _send_data_table(
    turn_context: TurnContext,
    columns: Any,
    data: Any,
    query_description: Optional[str] = None,
) -> None:
    """發送資料表格 Adaptive Card。"""
    try:
        data_array = data.get("data_array", []) if isinstance(data, dict) else []
        if not data_array:
            await turn_context.send_activity("查詢成功，但沒有資料返回。")
            return

        table_card = create_data_table_card(
            columns=columns,
            data=data,
            query_description=query_description,
            total_rows=len(data_array),
        )
        attachment = {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": table_card,
        }
        await turn_context.send_activity(MessageFactory.attachment(attachment))
    except Exception as table_error:
        logger.error(f"顯示資料表格時發生錯誤: {table_error}", exc_info=True)
        await turn_context.send_activity("顯示資料時發生錯誤，請稍後再試。")


async def _send_chart(
    turn_context: TurnContext,
    chart_info: Dict[str, Any],
) -> None:
    """生成並發送圖表。"""
    try:
        image_base64 = generate_chart_image(chart_info)

        chart_type = chart_info.get("chart_type", "bar")
        category_col = chart_info.get("category_column", "")
        value_col = chart_info.get("value_column", "")
        chart_icon = CHART_ICONS.get(chart_type, CHART_ICONS['bar'])

        await turn_context.send_activity(f"{chart_icon} **{category_col} vs {value_col}**")

        image_attachment = Attachment(
            name="chart.png",
            content_type="image/png",
            content_url=f"data:image/png;base64,{image_base64}",
        )
        await turn_context.send_activity(MessageFactory.attachment(image_attachment))
        logger.info("圖表已發送")
    except Exception as chart_error:
        logger.error(f"生成圖表時發生錯誤: {chart_error}", exc_info=True)


async def _send_suggested_questions(
    turn_context: TurnContext,
    response_data: Dict[str, Any],
) -> None:
    """發送建議問題卡片（若有）。"""
    suggested = response_data.get("suggested_questions")
    if not suggested:
        return

    card = create_suggested_questions_card(suggested)
    if card:
        await turn_context.send_activity(MessageFactory.attachment(card))
