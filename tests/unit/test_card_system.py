"""測試 Adaptive Card 設計系統。

涵蓋 card_builder、constants、data_table_card、error_card、
feedback_cards、welcome_messages 和 chart_generator 的單元測試。
"""

from unittest.mock import AsyncMock, patch

import pytest

from bot.cards.card_builder import CardBuilder
from bot.cards.constants import (
    ADAPTIVE_CARD_CONTENT_TYPE,
    ADAPTIVE_CARD_SCHEMA,
    ADAPTIVE_CARD_VERSION,
    CHART_ICONS,
    EMOJI_BOT,
    EMOJI_ERROR,
)
from bot.cards.data_table_card import (
    create_data_table_card,
    _extract_columns,
    _extract_data_array,
    _format_cell_value,
)
from bot.cards.error_card import create_user_error_card, create_warning_card
from bot.cards.feedback_cards import (
    create_error_card,
    create_feedback_card,
    create_thank_you_card,
)


# ─── CardBuilder ────────────────────────────────────────


class TestCardBuilder:
    def test_create_card_basic(self):
        body = [{"type": "TextBlock", "text": "Hello"}]
        card = CardBuilder.create_card(body=body)

        assert card["type"] == "AdaptiveCard"
        assert card["version"] == ADAPTIVE_CARD_VERSION
        assert card["$schema"] == ADAPTIVE_CARD_SCHEMA
        assert card["body"] == body
        assert "actions" not in card

    def test_create_card_with_actions(self):
        body = [{"type": "TextBlock", "text": "Hello"}]
        actions = [{"type": "Action.Submit", "title": "Click"}]
        card = CardBuilder.create_card(body=body, actions=actions)

        assert card["actions"] == actions

    def test_wrap_as_attachment(self):
        card = CardBuilder.create_card(body=[])
        attachment = CardBuilder.wrap_as_attachment(card)

        assert attachment["contentType"] == ADAPTIVE_CARD_CONTENT_TYPE
        assert attachment["content"] is card

    def test_create_header(self):
        header = CardBuilder.create_header(
            icon=EMOJI_BOT, title="Test Title", subtitle="Sub"
        )

        assert header["type"] == "Container"
        assert header["style"] == "emphasis"
        column_set = header["items"][0]
        assert column_set["type"] == "ColumnSet"
        assert len(column_set["columns"]) == 2
        # Icon column
        assert column_set["columns"][0]["items"][0]["text"] == EMOJI_BOT
        # Title column
        title_items = column_set["columns"][1]["items"]
        assert title_items[0]["text"] == "Test Title"
        assert title_items[1]["text"] == "Sub"

    def test_create_header_no_subtitle(self):
        header = CardBuilder.create_header(icon="X", title="Title Only")
        title_items = header["items"][0]["columns"][1]["items"]
        assert len(title_items) == 1

    def test_text_block_defaults(self):
        block = CardBuilder.text_block("Hello")
        assert block["text"] == "Hello"
        assert block["wrap"] is True
        assert block["size"] == "Default"
        assert "weight" not in block
        assert "color" not in block

    def test_text_block_custom(self):
        block = CardBuilder.text_block(
            "Bold",
            weight="Bolder",
            color="Accent",
            is_subtle=True,
            spacing="Medium",
            horizontal_alignment="Center",
        )
        assert block["weight"] == "Bolder"
        assert block["color"] == "Accent"
        assert block["isSubtle"] is True
        assert block["spacing"] == "Medium"
        assert block["horizontalAlignment"] == "Center"

    def test_action_submit(self):
        action = CardBuilder.action_submit("Click", {"key": "val"})
        assert action["type"] == "Action.Submit"
        assert action["title"] == "Click"
        assert action["data"] == {"key": "val"}

    def test_separator(self):
        sep = CardBuilder.separator()
        assert sep["type"] == "Container"
        assert sep["separator"] is True


# ─── DataTableCard ──────────────────────────────────────


class TestDataTableCard:
    SAMPLE_COLUMNS = {
        "columns": [
            {"name": "Name", "type_name": "STRING"},
            {"name": "Revenue", "type_name": "DECIMAL"},
            {"name": "Count", "type_name": "INT"},
        ]
    }
    SAMPLE_DATA = {
        "data_array": [
            ["Alice", "1234.56", "100"],
            ["Bob", "789.01", "50"],
        ]
    }

    def test_create_data_table_card(self):
        card = create_data_table_card(
            columns=self.SAMPLE_COLUMNS,
            data=self.SAMPLE_DATA,
            query_description="Test query",
        )

        assert card["type"] == "AdaptiveCard"
        assert card["version"] == ADAPTIVE_CARD_VERSION
        # Should contain: header + table + footer
        assert len(card["body"]) >= 3

    def test_empty_data(self):
        card = create_data_table_card(
            columns=self.SAMPLE_COLUMNS,
            data={"data_array": []},
        )
        # Should show success but no data message
        body_texts = [
            item.get("text", "")
            for item in card["body"]
            if item.get("type") == "TextBlock"
        ]
        assert any("沒有資料" in t for t in body_texts)

    def test_empty_dict_data(self):
        """data={} 時應顯示「沒有資料」提示（UAT bug fix）。"""
        card = create_data_table_card(
            columns=self.SAMPLE_COLUMNS,
            data={},
        )
        body_texts = [
            item.get("text", "")
            for item in card["body"]
            if item.get("type") == "TextBlock"
        ]
        assert any("沒有資料" in t for t in body_texts)

    def test_extract_columns(self):
        cols = _extract_columns(self.SAMPLE_COLUMNS)
        assert len(cols) == 3
        assert cols[0]["name"] == "Name"

    def test_extract_columns_invalid(self):
        assert _extract_columns("bad") == []
        assert _extract_columns({}) == []

    def test_extract_data_array(self):
        arr = _extract_data_array(self.SAMPLE_DATA)
        assert len(arr) == 2

    def test_extract_data_array_invalid(self):
        assert _extract_data_array("bad") == []
        assert _extract_data_array({}) == []

    def test_format_cell_value(self):
        assert _format_cell_value(None, "STRING") == "\u2014"
        assert _format_cell_value("1234.56", "DECIMAL") == "1,234.56"
        assert _format_cell_value("1000", "INT") == "1,000"
        assert _format_cell_value("hello", "STRING") == "hello"
        assert _format_cell_value("bad", "INT") == "bad"


# ─── ErrorCard ──────────────────────────────────────────


class TestErrorCard:
    def test_create_user_error_card_basic(self):
        card = create_user_error_card()
        assert card["type"] == "AdaptiveCard"
        assert card["version"] == ADAPTIVE_CARD_VERSION
        assert len(card["body"]) >= 1

    def test_create_user_error_card_with_admin(self):
        card = create_user_error_card(admin_email="admin@test.com")
        body_texts = _collect_texts(card["body"])
        assert any("admin@test.com" in t for t in body_texts)

    def test_create_user_error_card_with_retry(self):
        card = create_user_error_card(show_retry=True)
        assert "actions" in card
        assert len(card["actions"]) == 1

    def test_create_user_error_card_without_retry(self):
        card = create_user_error_card(show_retry=False)
        assert "actions" not in card

    def test_create_warning_card(self):
        card = create_warning_card("Something happened")
        assert card["type"] == "AdaptiveCard"


# ─── FeedbackCards ──────────────────────────────────────


class TestFeedbackCards:
    def test_create_feedback_card(self):
        card = create_feedback_card("msg123", "user456")
        assert card["type"] == "AdaptiveCard"
        assert card["version"] == ADAPTIVE_CARD_VERSION
        assert len(card["actions"]) == 2
        # Check action data
        assert card["actions"][0]["data"]["feedback"] == "positive"
        assert card["actions"][1]["data"]["feedback"] == "negative"
        assert card["actions"][0]["data"]["messageId"] == "msg123"

    def test_create_thank_you_card(self):
        card = create_thank_you_card()
        assert card["type"] == "AdaptiveCard"
        body_texts = _collect_texts(card["body"])
        assert any("感謝" in t for t in body_texts)

    def test_create_error_card(self):
        card = create_error_card("Something went wrong")
        assert card["type"] == "AdaptiveCard"
        body_texts = _collect_texts(card["body"])
        assert any("Something went wrong" in t for t in body_texts)


# ─── QueryResultRenderer（靜默失敗修復驗證）────────────────


class TestRenderDataResponseEmptyData:
    """驗證 _render_data_response 在 data={} 時不再靜默失敗。"""

    def test_empty_data_still_calls_send_data_table(self):
        """data={} 時，_send_data_table 應仍被呼叫（顯示「無資料」提示）。"""
        import asyncio
        from bot.cards.query_result_renderer import _render_data_response

        mock_context = AsyncMock()

        response_data = {
            "query_description": "測試查詢",
            "columns": {"columns": [{"name": "id", "type_name": "INT"}]},
            "data": {},
        }

        with patch(
            "bot.cards.query_result_renderer._send_data_table",
            new_callable=AsyncMock,
        ) as mock_send:
            asyncio.run(_render_data_response(mock_context, response_data))
            mock_send.assert_called_once()

    def test_none_columns_skips_data_table(self):
        """columns=None 時，_send_data_table 不應被呼叫。"""
        import asyncio
        from bot.cards.query_result_renderer import _render_data_response

        mock_context = AsyncMock()

        response_data = {
            "query_description": "測試",
            "columns": None,
            "data": {"data_array": [["1"]]},
        }

        with patch(
            "bot.cards.query_result_renderer._send_data_table",
            new_callable=AsyncMock,
        ) as mock_send:
            asyncio.run(_render_data_response(mock_context, response_data))
            mock_send.assert_not_called()

    def test_valid_data_still_works(self):
        """正常 data 時，_send_data_table 應被正常呼叫。"""
        import asyncio
        from bot.cards.query_result_renderer import _render_data_response

        mock_context = AsyncMock()

        response_data = {
            "query_description": "測試",
            "columns": {"columns": [{"name": "id", "type_name": "INT"}]},
            "data": {"data_array": [["1"], ["2"]]},
        }

        with patch(
            "bot.cards.query_result_renderer._send_data_table",
            new_callable=AsyncMock,
        ) as mock_send:
            asyncio.run(_render_data_response(mock_context, response_data))
            mock_send.assert_called_once()


class TestRenderTextResponseWithDescription:
    """驗證 text 回應帶 query_description 時會先顯示描述。"""

    def test_text_with_query_description_sends_two_messages(self):
        """有 query_description 時應先送描述再送訊息。"""
        import asyncio
        from bot.cards.query_result_renderer import _render_text_response

        mock_context = AsyncMock()

        response_data = {
            "message": "Insufficient data, cannot determine",
            "query_description": "查詢說明",
        }
        asyncio.run(_render_text_response(mock_context, response_data))
        assert mock_context.send_activity.call_count == 2
        first_call_text = mock_context.send_activity.call_args_list[0][0][0]
        assert "查詢說明" in first_call_text
        second_call_text = mock_context.send_activity.call_args_list[1][0][0]
        assert second_call_text == "Insufficient data, cannot determine"

    def test_text_without_query_description_sends_one_message(self):
        """無 query_description 時只送訊息。"""
        import asyncio
        from bot.cards.query_result_renderer import _render_text_response

        mock_context = AsyncMock()

        response_data = {"message": "Hello"}
        asyncio.run(_render_text_response(mock_context, response_data))
        assert mock_context.send_activity.call_count == 1


# ─── Constants ──────────────────────────────────────────


class TestConstants:
    def test_version_is_1_5(self):
        assert ADAPTIVE_CARD_VERSION == "1.5"

    def test_chart_icons_complete(self):
        assert "bar" in CHART_ICONS
        assert "pie" in CHART_ICONS
        assert "line" in CHART_ICONS


# ─── Helpers ────────────────────────────────────────────


def _collect_texts(body: list) -> list[str]:
    """遞迴收集 Card body 中所有 TextBlock 的文字。"""
    texts = []
    for item in body:
        if isinstance(item, dict):
            if item.get("type") == "TextBlock":
                texts.append(item.get("text", ""))
            # 遞迴搜索 Container 等嵌套結構
            for key in ("items", "columns"):
                if key in item:
                    nested = item[key]
                    if isinstance(nested, list):
                        texts.extend(_collect_texts(nested))
            if "items" not in item and "columns" not in item:
                for val in item.values():
                    if isinstance(val, list):
                        texts.extend(_collect_texts(val))
    return texts
