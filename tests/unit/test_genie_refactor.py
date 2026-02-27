"""
測試 GenieResponse / _RequestContext dataclass 及 ask() 重構。
"""

import json
import time

import pytest

from app.services.genie import GenieResponse, _RequestContext


# ── GenieResponse ──


class TestGenieResponseToJson:
    """to_json() 應根據 response_type 產生正確的 JSON 結構。"""

    def test_data_response(self):
        r = GenieResponse(
            response_type="data",
            columns={"columns": [{"name": "id", "type_name": "INT"}]},
            data={"data_array": [["1"], ["2"]]},
            query_description="查詢說明",
            suggested_questions=["Q1", "Q2"],
        )
        parsed = json.loads(r.to_json())
        assert "columns" in parsed
        assert "data" in parsed
        assert parsed["query_description"] == "查詢說明"
        assert parsed["suggested_questions"] == ["Q1", "Q2"]
        # data 回應不應有 message 或 error
        assert "message" not in parsed
        assert "error" not in parsed

    def test_text_response(self):
        r = GenieResponse(
            response_type="text",
            message="這是文字回覆",
            suggested_questions=["Q1"],
        )
        parsed = json.loads(r.to_json())
        assert parsed["message"] == "這是文字回覆"
        assert parsed["suggested_questions"] == ["Q1"]
        assert "columns" not in parsed
        assert "error" not in parsed

    def test_error_response(self):
        r = GenieResponse(
            response_type="error",
            error="發生錯誤",
        )
        parsed = json.loads(r.to_json())
        assert parsed["error"] == "發生錯誤"
        assert "message" not in parsed
        assert "columns" not in parsed

    def test_empty_suggested_questions_default(self):
        r = GenieResponse(response_type="text", message="hi")
        parsed = json.loads(r.to_json())
        assert parsed["suggested_questions"] == []

    def test_data_response_with_sql_query(self):
        """sql_query 不會出現在 to_json() 中（它是給 LLM 用的）。"""
        r = GenieResponse(
            response_type="data",
            columns={},
            data={},
            sql_query="SELECT * FROM t",
        )
        parsed = json.loads(r.to_json())
        assert "sql_query" not in parsed


class TestGenieResponseToTuple:
    """to_tuple() 應回傳向後相容的 (json_str, conversation_id, message_id)。"""

    def test_basic_tuple(self):
        r = GenieResponse(
            response_type="text",
            conversation_id="conv-123",
            message_id="msg-456",
            message="hello",
        )
        json_str, conv_id, msg_id = r.to_tuple()
        assert conv_id == "conv-123"
        assert msg_id == "msg-456"
        assert json.loads(json_str)["message"] == "hello"

    def test_error_tuple_has_none_message_id(self):
        r = GenieResponse(
            response_type="error",
            conversation_id="conv-123",
            error="boom",
        )
        json_str, conv_id, msg_id = r.to_tuple()
        assert conv_id == "conv-123"
        assert msg_id is None
        assert "error" in json.loads(json_str)

    def test_none_ids(self):
        r = GenieResponse(response_type="error", error="fail")
        _, conv_id, msg_id = r.to_tuple()
        assert conv_id is None
        assert msg_id is None


class TestGenieResponseFields:
    """GenieResponse 的欄位可直接存取（為 LLM orchestrator 設計）。"""

    def test_data_fields_accessible(self):
        r = GenieResponse(
            response_type="data",
            columns={"col": 1},
            data={"row": 2},
            query_description="desc",
            sql_query="SELECT 1",
            suggested_questions=["Q"],
        )
        assert r.response_type == "data"
        assert r.columns == {"col": 1}
        assert r.data == {"row": 2}
        assert r.query_description == "desc"
        assert r.sql_query == "SELECT 1"
        assert r.suggested_questions == ["Q"]

    def test_text_fields_accessible(self):
        r = GenieResponse(response_type="text", message="hi")
        assert r.response_type == "text"
        assert r.message == "hi"

    def test_error_fields_accessible(self):
        r = GenieResponse(response_type="error", error="bad")
        assert r.response_type == "error"
        assert r.error == "bad"


# ── _RequestContext ──


class TestRequestContext:
    def test_fields(self):
        ctx = _RequestContext(
            request_id="abc12345",
            question="test question",
            space_id="space-1",
            user_email="user@example.com",
            conversation_id=None,
            query_start_time=time.time(),
        )
        assert ctx.request_id == "abc12345"
        assert ctx.question == "test question"
        assert ctx.space_id == "space-1"
        assert ctx.user_email == "user@example.com"
        assert ctx.conversation_id is None
        assert ctx.query_start_time > 0

    def test_conversation_id_mutable(self):
        ctx = _RequestContext(
            request_id="x",
            question="q",
            space_id="s",
            user_email="e",
            conversation_id=None,
            query_start_time=0.0,
        )
        ctx.conversation_id = "conv-new"
        assert ctx.conversation_id == "conv-new"


# ── ask() 向後相容驗證（import 層級）──


def test_ask_method_exists():
    """ask() 應仍然存在且可呼叫。"""
    from app.services.genie import GenieService
    assert hasattr(GenieService, "ask")
    assert callable(getattr(GenieService, "ask"))


def test_ask_structured_method_exists():
    """ask_structured() 應存在（新的公開 API）。"""
    from app.services.genie import GenieService
    assert hasattr(GenieService, "ask_structured")
    assert callable(getattr(GenieService, "ask_structured"))


def test_genie_response_importable():
    """GenieResponse 應可從 app.services.genie import。"""
    from app.services.genie import GenieResponse
    r = GenieResponse(response_type="text", message="test")
    assert r.to_json() == json.dumps({"message": "test", "suggested_questions": []})


# ── GenieResponse empty data 防禦 ──


class TestGenieResponseEmptyData:
    """data={} 時 to_json() 和 to_tuple() 的行為應正確。"""

    def test_empty_dict_data_produces_valid_json(self):
        """data={} 時 to_json() 仍應包含 'data' 鍵。"""
        r = GenieResponse(
            response_type="data",
            columns={"columns": [{"name": "id", "type_name": "INT"}]},
            data={},
            query_description="查詢說明",
        )
        parsed = json.loads(r.to_json())
        assert "data" in parsed
        assert parsed["data"] == {}
        assert "columns" in parsed
        assert parsed["query_description"] == "查詢說明"

    def test_none_data_produces_valid_json(self):
        """data=None 時 to_json() 應包含 'data': null。"""
        r = GenieResponse(
            response_type="data",
            columns={"columns": [{"name": "id", "type_name": "INT"}]},
            data=None,
            query_description="查詢說明",
        )
        parsed = json.loads(r.to_json())
        assert "data" in parsed
        assert parsed["data"] is None

    def test_empty_dict_data_to_tuple(self):
        """data={} 時 to_tuple() 的 JSON 結構仍正確。"""
        r = GenieResponse(
            response_type="data",
            conversation_id="conv-1",
            message_id="msg-1",
            columns={"columns": []},
            data={},
        )
        json_str, conv_id, msg_id = r.to_tuple()
        assert conv_id == "conv-1"
        assert msg_id == "msg-1"
        parsed = json.loads(json_str)
        assert parsed["data"] == {}

    def test_empty_data_array_in_data(self):
        """data_array=[] 時，data 欄位應正確序列化。"""
        r = GenieResponse(
            response_type="data",
            columns={"columns": [{"name": "x", "type_name": "INT"}]},
            data={"data_array": []},
            query_description="空結果查詢",
        )
        parsed = json.loads(r.to_json())
        assert parsed["data"]["data_array"] == []


# ── Text response with query_description ──


class TestGenieResponseTextWithQueryDescription:
    """text 回應帶 query_description 時 to_json() 應包含它。"""

    def test_text_with_query_description(self):
        r = GenieResponse(
            response_type="text",
            message="Insufficient data",
            query_description="查詢說明",
        )
        parsed = json.loads(r.to_json())
        assert parsed["message"] == "Insufficient data"
        assert parsed["query_description"] == "查詢說明"

    def test_text_without_query_description(self):
        """純文字回應不應有 query_description 鍵。"""
        r = GenieResponse(
            response_type="text",
            message="hello",
        )
        parsed = json.loads(r.to_json())
        assert "query_description" not in parsed

    def test_text_empty_query_description(self):
        """query_description 為空字串時不應出現在 JSON 中。"""
        r = GenieResponse(
            response_type="text",
            message="hello",
            query_description="",
        )
        parsed = json.loads(r.to_json())
        assert "query_description" not in parsed
