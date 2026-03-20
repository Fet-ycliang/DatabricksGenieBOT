"""Genie service module that encapsulates Databricks Genie interactions."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)
from typing import Any, Dict, Optional, Tuple, Union

import httpx
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import GenieAPI, GenieFeedbackRating

from app.core.config import DefaultConfig
from app.utils.resilience import retry_async, CircuitBreaker, CircuitBreakerError


# ── Structured Response / Request Context ──


@dataclass
class GenieResponse:
    """Genie API 的結構化回應。

    response_type 決定哪些欄位有值：
    - "data":  columns, data, query_description 有值
    - "text":  message 有值
    - "error": error 有值

    未來 LLM orchestrator 可直接消費此物件，
    不需要 json.loads() 再解析。
    """

    response_type: str  # "data" | "text" | "error"
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    # data 回應
    columns: Optional[Dict] = None
    data: Optional[Dict] = None
    query_description: str = ""
    sql_query: str = ""
    # text 回應
    message: str = ""
    # error 回應
    error: str = ""
    # 共用
    suggested_questions: list = field(default_factory=list)

    def to_json(self) -> str:
        """轉為 JSON 字串（向後相容 ask() 的回傳格式）。"""
        if self.response_type == "data":
            return json.dumps({
                "columns": self.columns,
                "data": self.data,
                "query_description": self.query_description,
                "suggested_questions": self.suggested_questions,
            })
        elif self.response_type == "text":
            payload: Dict[str, Any] = {
                "message": self.message,
                "suggested_questions": self.suggested_questions,
            }
            if self.query_description:
                payload["query_description"] = self.query_description
            return json.dumps(payload)
        else:
            return json.dumps({"error": self.error})

    def to_tuple(self) -> Tuple[str, Optional[str], Optional[str]]:
        """向後相容：轉為 (json_str, conversation_id, message_id)。"""
        return (self.to_json(), self.conversation_id, self.message_id)


@dataclass
class _RequestContext:
    """ask() 內部的請求追蹤狀態。"""

    request_id: str
    question: str
    space_id: str
    user_email: str
    conversation_id: Optional[str]
    query_start_time: float


class QueryMetrics:
    """查詢性能指標收集器"""
    def __init__(self):
        self.total_queries = 0
        self.successful_queries = 0
        self.failed_queries = 0
        self.total_duration = 0.0
        self._last_logged_total = 0
    
    def record_query(self, duration: float, success: bool = True) -> None:
        """記錄查詢指標"""
        self.total_queries += 1
        if success:
            self.successful_queries += 1
        else:
            self.failed_queries += 1
        
        self.total_duration += duration
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計資訊"""
        avg_duration = self.total_duration / self.total_queries if self.total_queries > 0 else 0
        success_rate = (self.successful_queries / self.total_queries * 100) if self.total_queries > 0 else 0
        
        return {
            'total_queries': self.total_queries,
            'successful_queries': self.successful_queries,
            'failed_queries': self.failed_queries,
            'average_duration': round(avg_duration, 2),
            'total_duration': round(self.total_duration, 2),
            'success_rate': round(success_rate, 2)
        }
    
    def log_stats(self) -> None:
        """記錄統計資訊到日誌（無新查詢時跳過）"""
        if self.total_queries == 0 or self.total_queries == self._last_logged_total:
            return
        self._last_logged_total = self.total_queries
        stats = self.get_stats()
        logger.info(
            "\n" + "="*80 + "\n"
            "📊 查詢統計摘要\n"
            "-"*80 + "\n"
            f"  總查詢數:     {stats['total_queries']:>6}\n"
            f"  成功查詢:     {stats['successful_queries']:>6}\n"
            f"  失敗查詢:     {stats['failed_queries']:>6}\n"
            f"  成功率:       {stats['success_rate']:>5.2f}%\n"
            f"  平均耗時:     {stats['average_duration']:>6.2f}s\n"
            f"  總耗時:       {stats['total_duration']:>6.2f}s\n"
            + "="*80
        )


class GenieService:
    """Handles all interactions with the Databricks Genie APIs."""

    def __init__(self, config: Any, workspace_client: WorkspaceClient | None = None):
        self._config = config
        self._workspace_client = workspace_client or self._create_workspace_client()
        self._genie_api = GenieAPI(self._workspace_client.api_client)
        self._supports_feedback_api = hasattr(self._genie_api, "send_message_feedback")
        # HTTP 連接池
        self._http_session = None
        self._http_session_lock = asyncio.Lock()
        # 性能指標收集器
        self.metrics = QueryMetrics()
        # ✅ 日誌採樣 - 每 60 秒或 1% 隨機採樣記錄一次統計
        self.last_stats_log_time = time.time()
        self.stats_log_interval = 60
        # Circuit breaker：連續 5 次失敗後熔斷 60 秒
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
            name="genie-api",
        )

    def _create_workspace_client(self) -> WorkspaceClient:
        logger.info(
            "\n" + "="*80 + "\n"
            "🔧 正在載入 Databricks 配置\n"
            "-"*80
        )
        # ✅ 隱藏敏感信息：不記錄 HOST、TOKEN 長度等
        logger.info("  認證狀態:     %s", "已配置" if self._config.DATABRICKS_TOKEN else "未配置")
        logger.info("  Workspace:    %s", "已連接" if self._config.DATABRICKS_HOST else "未配置")
        logger.info("="*80)

        if not self._config.DATABRICKS_TOKEN:
            raise ValueError("DATABRICKS_TOKEN environment variable is not set")

        try:
            client = WorkspaceClient(
                host=self._config.DATABRICKS_HOST,
                token=self._config.DATABRICKS_TOKEN,
            )
            logger.info("✅ Databricks 客戶端初始化成功")
            return client
        except Exception as exc:
            logger.error("❌ 初始化 Databricks 客戶端失敗: %s", exc)
            raise

    def should_log_stats(self) -> bool:
        """決定是否記錄統計信息（僅時間條件，每 60 秒最多一次）"""
        current_time = time.time()
        if current_time - self.last_stats_log_time >= self.stats_log_interval:
            self.last_stats_log_time = current_time
            return True
        return False

    @asynccontextmanager
    async def get_http_session(self):
        """重用 HTTP Session 減少連接開銷，配置超時防止掛起"""
        async with self._http_session_lock:
            if self._http_session is None or self._http_session.is_closed:
                timeout = httpx.Timeout(
                    timeout=30.0,
                    connect=5.0,
                    read=10.0,
                    write=10.0,
                )
                limits = httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=30,
                )
                self._http_session = httpx.AsyncClient(
                    timeout=timeout,
                    limits=limits,
                    headers={
                        "User-Agent": "DatabricksGenieBOT/1.0",
                        "Accept-Encoding": "gzip, deflate",
                    },
                )
                logger.info("✅ HTTP Client 已建立，超時配置：總 30s, 連接 5s, 讀取 10s")
        try:
            yield self._http_session
        finally:
            pass  # 重用，不關閉

    async def close(self):
        """關閉 HTTP Session（應用程式關閉時調用）"""
        try:
            if self._http_session and not self._http_session.is_closed:
                await self._http_session.aclose()
                logger.info("🔌 已關閉 HTTP Session")
        except Exception as e:
            logger.error(f"關閉 HTTP Session 時發生錯誤: {e}")
        finally:
            self._http_session = None

    def _format_json_for_logging(self, data: Any, indent: int = 2) -> str:
        """將 Python 物件格式化為漂亮的 JSON 字符串
        
        Args:
            data: 要格式化的數據
            indent: 縮進級別
        
        Returns:
            格式化的 JSON 字符串
        """
        try:
            return json.dumps(data, ensure_ascii=False, indent=indent, default=str)
        except Exception as e:
            logger.warning(f"無法序列化數據為 JSON: {e}")
            return str(data)

    def _log_api_response(self, request_id: str, response_data: Dict, total_elapsed: float) -> None:
        """打印完整格式化的 API 響應
        
        Args:
            request_id: 請求 ID
            response_data: API 響應數據
            total_elapsed: 總耗時（秒）
        """
        logger.info(
            f"\n{'='*80}\n"
            f"[{request_id}] 📤 API 響應 - 完整輸出\n"
            f"{'-'*80}\n"
            f"耗時: {total_elapsed:.2f}s\n"
            f"{'-'*80}\n"
            f"{self._format_json_for_logging(response_data)}\n"
            f"{'='*80}"
        )

    def _log_message_attachments(self, request_id: str, message: Any) -> None:
        """記錄訊息附件中的重要物件"""
        if not message.attachments:
            return
        
        logger.info(f"[{request_id}] 📎 解析訊息附件:")
        
        for idx, attachment in enumerate(message.attachments, 1):
            # 1. Query 物件
            if hasattr(attachment, 'query') and attachment.query:
                query = attachment.query
                logger.info(
                    f"[{request_id}]   [{idx}] 📊 Query 物件\n"
                    f"        Attachment ID: {attachment.attachment_id}\n"
                    f"        Statement ID:  {query.statement_id if hasattr(query, 'statement_id') else 'N/A'}\n"
                    f"        SQL:           {query.query[:100] if hasattr(query, 'query') and query.query else 'N/A'}{'...' if hasattr(query, 'query') and query.query and len(query.query) > 100 else ''}\n"
                    f"        說明:          {query.description if hasattr(query, 'description') else 'N/A'}\n"
                    f"        Row Count:     {query.query_result_metadata.row_count if hasattr(query, 'query_result_metadata') and query.query_result_metadata else 'N/A'}"
                )
            
            # 2. Suggested Questions 物件
            if hasattr(attachment, 'suggested_questions') and attachment.suggested_questions:
                questions = attachment.suggested_questions
                if hasattr(questions, 'questions') and questions.questions:
                    logger.info(
                        f"[{request_id}]   [{idx}] 💡 Suggested Questions 物件\n"
                        f"        Attachment ID: {attachment.attachment_id}\n"
                        f"        問題數量:      {len(questions.questions)}"
                    )
                    for q_idx, question in enumerate(questions.questions, 1):
                        logger.info(f"        [{q_idx}] {question}")
            
            # 3. Text 物件
            if hasattr(attachment, 'text') and attachment.text:
                text = attachment.text
                if hasattr(text, 'content') and text.content:
                    logger.info(
                        f"[{request_id}]   [{idx}] 💬 Text 物件\n"
                        f"        Attachment ID: {attachment.attachment_id}\n"
                        f"        內容:          {text.content[:100]}{'...' if len(text.content) > 100 else ''}"
                    )
        
        # 4. Query Result 物件（在訊息層級）
        if hasattr(message, 'query_result') and message.query_result:
            qr = message.query_result
            logger.info(
                f"[{request_id}]   🎯 Query Result 物件 (訊息層級)\n"
                f"        Statement ID:  {qr.statement_id if hasattr(qr, 'statement_id') else 'N/A'}\n"
                f"        Row Count:     {qr.row_count if hasattr(qr, 'row_count') else 0}"
            )

    @staticmethod
    def _extract_suggested_questions(message_content) -> list:
        """從訊息附件中提取建議問題列表"""
        if not message_content or not message_content.attachments:
            return []
        for attachment in message_content.attachments:
            if hasattr(attachment, 'suggested_questions') and attachment.suggested_questions:
                if hasattr(attachment.suggested_questions, 'questions') and attachment.suggested_questions.questions:
                    return list(attachment.suggested_questions.questions)
        return []

    # ── Public API ──

    async def ask(
        self,
        question: str,
        space_id: str,
        user_session: Any,
        conversation_id: Optional[str] = None,
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """Send a question to Genie and return the raw response payload.

        向後相容的薄包裝，內部委派給 ask_structured()。
        """
        response = await self.ask_structured(question, space_id, user_session, conversation_id)
        return response.to_tuple()

    async def ask_structured(
        self,
        question: str,
        space_id: str,
        user_session: Any,
        conversation_id: Optional[str] = None,
    ) -> GenieResponse:
        """結構化版本的 ask()，回傳 GenieResponse。

        未來 LLM orchestrator 應優先使用此方法。
        """
        ctx = _RequestContext(
            request_id=str(uuid.uuid4())[:8],
            question=question,
            space_id=space_id,
            user_email=user_session.email,
            conversation_id=conversation_id,
            query_start_time=time.time(),
        )
        self._log_request(ctx)

        try:
            # 1. 送出請求
            result = await self._send_to_genie(ctx)
            if isinstance(result, GenieResponse):
                return result  # CircuitBreakerError → 提前回傳
            initial_message, ctx.conversation_id = result

            # 2. 取得查詢結果 + 訊息內容
            query_result, message_content = await self._fetch_query_and_content(
                ctx, initial_message,
            )

            # 3. 根據回應類型建構 GenieResponse
            if query_result and query_result.statement_response:
                response = await self._build_data_response(
                    ctx, initial_message, query_result, message_content,
                )
            elif message_content.attachments:
                response = self._build_text_response(
                    ctx, initial_message, message_content,
                )
            else:
                response = self._build_default_response(
                    ctx, initial_message, message_content,
                )

            # 4. 記錄指標
            self._record_success(ctx, response)
            return response

        except Exception as exc:
            response = self._build_error_response(ctx, exc)
            self._record_failure(ctx)
            return response

    # ── Private helpers ──

    def _log_request(self, ctx: _RequestContext) -> None:
        """記錄新查詢請求。"""
        logger.info(
            f"\n{'='*80}\n"
            f"[{ctx.request_id}] 📥 新查詢請求\n"
            f"{'-'*80}\n"
            f"  使用者:       {ctx.user_email}\n"
            f"  問題:         {ctx.question[:80]}{'...' if len(ctx.question) > 80 else ''}\n"
            f"  對話 ID:      {ctx.conversation_id or '新對話'}\n"
            f"  Space ID:     {ctx.space_id}\n"
            f"{'='*80}"
        )

    async def _send_to_genie(
        self, ctx: _RequestContext,
    ) -> Union[tuple, GenieResponse]:
        """送出請求到 Genie API（含 circuit breaker + retry）。

        Returns:
            (initial_message, conversation_id) 或 GenieResponse(error)。
        """
        contextual_question = f"[{ctx.user_email}] {ctx.question}"
        loop = asyncio.get_running_loop()

        try:
            if ctx.conversation_id is None:
                logger.info(f"[{ctx.request_id}] 🆕 啟動新對話...")

                async def _start_conversation():
                    return await loop.run_in_executor(
                        None,
                        self._genie_api.start_conversation_and_wait,
                        ctx.space_id,
                        contextual_question,
                    )

                initial_message = await self._circuit_breaker.call(
                    retry_async,
                    _start_conversation,
                    max_retries=2,
                    base_delay=2.0,
                    operation_name=f"[{ctx.request_id}] start_conversation",
                )
                conversation_id = initial_message.conversation_id
                logger.info(
                    f"[{ctx.request_id}] ✅ 對話已創建\n"
                    f"  對話 ID:      {conversation_id}\n"
                    f"  訊息 ID:      {initial_message.message_id}\n"
                    f"  訊息狀態:     {initial_message.status}\n"
                    f"  附件數量:     {len(initial_message.attachments) if initial_message.attachments else 0}\n"
                    f"  查詢結果:     {'有' if initial_message.query_result else '無'}"
                )
                self._log_message_attachments(ctx.request_id, initial_message)
            else:
                logger.info(f"[{ctx.request_id}] 💬 在現有對話中發送訊息: {ctx.conversation_id}")

                async def _create_message():
                    return await loop.run_in_executor(
                        None,
                        self._genie_api.create_message_and_wait,
                        ctx.space_id,
                        ctx.conversation_id,
                        contextual_question,
                    )

                initial_message = await self._circuit_breaker.call(
                    retry_async,
                    _create_message,
                    max_retries=2,
                    base_delay=2.0,
                    operation_name=f"[{ctx.request_id}] create_message",
                )
                conversation_id = ctx.conversation_id
                logger.info(
                    f"[{ctx.request_id}] ✅ 訊息已發送\n"
                    f"  訊息 ID:      {initial_message.message_id}\n"
                    f"  訊息狀態:     {initial_message.status}\n"
                    f"  附件數量:     {len(initial_message.attachments) if initial_message.attachments else 0}\n"
                    f"  查詢結果:     {'有' if initial_message.query_result else '無'}"
                )
                self._log_message_attachments(ctx.request_id, initial_message)

            return (initial_message, conversation_id)

        except CircuitBreakerError:
            logger.error(f"[{ctx.request_id}] 🔌 Circuit breaker OPEN — Databricks API 暫時不可用")
            return GenieResponse(
                response_type="error",
                conversation_id=ctx.conversation_id,
                error=(
                    "⚠️ **服務暫時不可用**\n\n"
                    "Databricks Genie API 目前遇到問題，系統已暫時停止請求以保護服務。\n\n"
                    "請稍後再試。"
                ),
            )

    async def _fetch_query_and_content(
        self, ctx: _RequestContext, initial_message: Any,
    ) -> Tuple[Any, Any]:
        """並發取得 query_result 和 message_content。"""
        loop = asyncio.get_running_loop()
        query_result = None
        message_content = None

        if initial_message.query_result is not None:
            logger.info(
                f"[{ctx.request_id}] ⚡ 開始並發獲取查詢結果和訊息內容...\n"
                f"  Statement ID: {initial_message.query_result.statement_id if initial_message.query_result else 'N/A'}\n"
                f"  Row Count:    {initial_message.query_result.row_count if initial_message.query_result else 0}\n"
                f"  提示:         SDK 將自動輪詢直到查詢完成 (PENDING_WAREHOUSE → COMPLETED)"
            )
            fetch_start = time.time()

            query_attachment_id = None
            if initial_message.attachments:
                for attachment in initial_message.attachments:
                    if hasattr(attachment, "query") and attachment.query:
                        query_attachment_id = attachment.attachment_id
                        break

            message_content_task = loop.run_in_executor(
                None,
                self._genie_api.get_message,
                ctx.space_id,
                initial_message.conversation_id,
                initial_message.message_id,
            )

            if query_attachment_id:
                query_result_task = loop.run_in_executor(
                    None,
                    self._genie_api.get_message_attachment_query_result,
                    ctx.space_id,
                    initial_message.conversation_id,
                    initial_message.message_id,
                    query_attachment_id,
                )
                query_result, message_content = await asyncio.gather(
                    query_result_task,
                    message_content_task,
                )
            else:
                logger.warning(
                    f"[{ctx.request_id}] ⚠️ 找不到 Query 附件，跳過 query-result 取得"
                )
                message_content = await message_content_task

            fetch_elapsed = time.time() - fetch_start

            if query_result and query_result.statement_response:
                statement_state = query_result.statement_response.status.state
                row_count = (
                    query_result.statement_response.manifest.total_row_count
                    if query_result.statement_response.manifest
                    else 0
                )
                logger.info(
                    f"[{ctx.request_id}] ✅ 並發獲取完成\n"
                    f"  耗時:         {fetch_elapsed:.2f}s\n"
                    f"  最終狀態:     {statement_state}\n"
                    f"  資料筆數:     {row_count}\n"
                    f"  說明:         輪詢已完成，查詢已執行完畢"
                )
                logger.info(
                    f"[{ctx.request_id}] 🔄 輪詢後的訊息狀態: "
                    f"{message_content.status if message_content else 'N/A'}"
                )
                if message_content:
                    self._log_message_attachments(ctx.request_id, message_content)
            else:
                logger.info(
                    f"[{ctx.request_id}] ✅ 並發獲取完成\n"
                    f"  耗時:         {fetch_elapsed:.2f}s\n"
                    f"  狀態:         無 statement_response"
                )
        else:
            logger.info(f"[{ctx.request_id}] 📄 獲取訊息內容（無查詢結果）...")
            message_content = await loop.run_in_executor(
                None,
                self._genie_api.get_message,
                ctx.space_id,
                initial_message.conversation_id,
                initial_message.message_id,
            )
            logger.info(f"[{ctx.request_id}] ✅ 訊息內容已獲取")
            if message_content:
                self._log_message_attachments(ctx.request_id, message_content)

        return (query_result, message_content)

    async def _build_data_response(
        self,
        ctx: _RequestContext,
        initial_message: Any,
        query_result: Any,
        message_content: Any,
    ) -> GenieResponse:
        """解析 data 類型回應 → GenieResponse(type="data")。"""
        loop = asyncio.get_running_loop()

        logger.info(
            f"[{ctx.request_id}] 📊 處理查詢結果...\n"
            f"  API 端點:     /spaces/.../messages/.../attachments/.../query-result\n"
            f"  Statement ID: {query_result.statement_response.statement_id}"
        )
        results = await loop.run_in_executor(
            None,
            self._workspace_client.statement_execution.get_statement,
            query_result.statement_response.statement_id,
        )

        # 記錄 statement_response 詳細信息
        if results.status:
            logger.info(
                f"[{ctx.request_id}] 🎯 Statement Response 詳細信息\n"
                f"  狀態:         {results.status.state}\n"
                f"  Statement ID: {results.statement_id if hasattr(results, 'statement_id') else 'N/A'}"
            )

        # 記錄 manifest 信息
        if results.manifest:
            manifest = results.manifest
            logger.info(
                f"[{ctx.request_id}] 📋 Manifest 信息\n"
                f"  格式:         {manifest.format if hasattr(manifest, 'format') else 'N/A'}\n"
                f"  欄位數:       {manifest.schema.column_count if manifest.schema else 0}\n"
                f"  總筆數:       {manifest.total_row_count if hasattr(manifest, 'total_row_count') else 0}\n"
                f"  總位元組:     {manifest.total_byte_count if hasattr(manifest, 'total_byte_count') else 0}\n"
                f"  是否截斷:     {manifest.truncated if hasattr(manifest, 'truncated') else False}"
            )
            if manifest.schema and manifest.schema.columns:
                logger.info(f"[{ctx.request_id}] 🗂️  Schema 欄位:")
                for col in manifest.schema.columns:
                    logger.info(
                        f"        [{col.position}] {col.name} ({col.type_name})"
                    )

        # 記錄 result 數據
        if results.result:
            result_obj = results.result
            data_preview = ""
            if hasattr(result_obj, 'data_array') and result_obj.data_array:
                preview_rows = result_obj.data_array[:3]
                data_preview = "\n".join([f"        {row}" for row in preview_rows])
                if len(result_obj.data_array) > 3:
                    data_preview += f"\n        ... (還有 {len(result_obj.data_array) - 3} 筆)"
            logger.info(
                f"[{ctx.request_id}] 📦 Result 數據\n"
                f"  Chunk Index:  {result_obj.chunk_index if hasattr(result_obj, 'chunk_index') else 0}\n"
                f"  Row Offset:   {result_obj.row_offset if hasattr(result_obj, 'row_offset') else 0}\n"
                f"  Row Count:    {result_obj.row_count if hasattr(result_obj, 'row_count') else 0}\n"
                f"  數據預覽:\n{data_preview if data_preview else '        (無數據)'}"
            )

        # 提取 query 描述和 SQL
        query_description = ""
        sql_query = ""
        for attachment in message_content.attachments:
            if attachment.query:
                if attachment.query.description:
                    query_description = attachment.query.description
                if attachment.query.query:
                    sql_query = attachment.query.query
                break

        row_count = len(results.result.data_array) if results.result and results.result.data_array else 0
        col_count = results.manifest.schema.column_count if results.manifest and results.manifest.schema else 0

        logger.info(
            f"[{ctx.request_id}] 🗒️  查詢詳細信息\n"
            f"  SQL:          {sql_query[:100] if sql_query else 'N/A'}{'...' if len(sql_query) > 100 else ''}\n"
            f"  說明:         {query_description[:80] if query_description else 'N/A'}{'...' if len(query_description) > 80 else ''}"
        )

        suggested_questions = self._extract_suggested_questions(message_content)
        message_status = message_content.status if message_content else None
        logger.info(
            f"[{ctx.request_id}] 📌 訊息狀態: {message_status}, 建議問題: {len(suggested_questions)} 個"
        )

        # 防禦：as_dict() 使用 truthiness check，data_array=None/[] 時回傳空 dict
        result_dict = results.result.as_dict() if results.result else {}

        if not result_dict.get("data_array"):
            # 嘗試直接從屬性讀取（SDK as_dict 用 truthiness 過濾 None/[]）
            if results.result and getattr(results.result, 'data_array', None):
                result_dict["data_array"] = list(results.result.data_array)
                result_dict["row_count"] = len(results.result.data_array)
                logger.warning(
                    f"[{ctx.request_id}] as_dict() 遺失 data_array，已從屬性手動補回"
                )
            elif results.result and getattr(results.result, 'external_links', None):
                logger.warning(
                    f"[{ctx.request_id}] 結果使用 EXTERNAL_LINKS 模式，"
                    f"共 {len(results.result.external_links)} 個外部連結，目前不支援下載"
                )
            else:
                logger.warning(
                    f"[{ctx.request_id}] 查詢結果無資料 "
                    f"(data_array=None, external_links=None)"
                )

        total_elapsed = time.time() - ctx.query_start_time

        # 偵測「偽裝成查詢結果的文字訊息」：
        # Genie 有時會透過 SQL 回傳單欄 message、單列文字，應轉為 text 回應
        data_array = result_dict.get("data_array", [])
        if (
            col_count == 1
            and row_count == 1
            and results.manifest
            and results.manifest.schema
            and results.manifest.schema.columns
            and results.manifest.schema.columns[0].name.lower() == "message"
            and len(data_array) == 1
            and len(data_array[0]) == 1
            and data_array[0][0]
        ):
            text_message = str(data_array[0][0])
            logger.info(
                f"[{ctx.request_id}] 💬 偵測到文字訊息結果（單欄 message），轉為 text 回應\n"
                f"  總耗時:       {total_elapsed:.2f}s\n"
                f"  訊息:         {text_message[:80]}"
            )
            return GenieResponse(
                response_type="text",
                conversation_id=ctx.conversation_id,
                message_id=initial_message.message_id,
                message=text_message,
                query_description=query_description,
                suggested_questions=suggested_questions,
            )

        logger.info(
            f"[{ctx.request_id}] ✅ 查詢完成\n"
            f"  總耗時:       {total_elapsed:.2f}s\n"
            f"  資料筆數:     {row_count}\n"
            f"  欄位數:       {col_count}\n"
            f"  說明:         {query_description[:60]}{'...' if len(query_description) > 60 else ''}"
        )

        return GenieResponse(
            response_type="data",
            conversation_id=ctx.conversation_id,
            message_id=initial_message.message_id,
            columns=results.manifest.schema.as_dict(),
            data=result_dict,
            query_description=query_description,
            sql_query=sql_query,
            suggested_questions=suggested_questions,
        )

    def _build_text_response(
        self,
        ctx: _RequestContext,
        initial_message: Any,
        message_content: Any,
    ) -> GenieResponse:
        """解析 text 類型回應 → GenieResponse(type="text")。"""
        for attachment in message_content.attachments:
            if attachment.text and attachment.text.content:
                suggested_questions = self._extract_suggested_questions(message_content)

                total_elapsed = time.time() - ctx.query_start_time
                logger.info(
                    f"[{ctx.request_id}] 💬 文字回覆已完成\n"
                    f"  總耗時:       {total_elapsed:.2f}s\n"
                    f"  訊息長度:     {len(attachment.text.content)}"
                )

                return GenieResponse(
                    response_type="text",
                    conversation_id=ctx.conversation_id,
                    message_id=initial_message.message_id,
                    message=attachment.text.content,
                    suggested_questions=suggested_questions,
                )

        # 所有附件都沒有 text.content → 退回 default
        return self._build_default_response(ctx, initial_message, message_content)

    def _build_default_response(
        self,
        ctx: _RequestContext,
        initial_message: Any,
        message_content: Any,
    ) -> GenieResponse:
        """預設回應 → GenieResponse(type="text")。"""
        suggested_questions = self._extract_suggested_questions(message_content)

        total_elapsed = time.time() - ctx.query_start_time
        logger.info(
            f"[{ctx.request_id}] 📝 預設回覆已完成\n"
            f"  總耗時:       {total_elapsed:.2f}s\n"
            f"  訊息長度:     {len(message_content.content)}"
        )

        return GenieResponse(
            response_type="text",
            conversation_id=ctx.conversation_id,
            message_id=initial_message.message_id,
            message=message_content.content,
            suggested_questions=suggested_questions,
        )

    def _build_error_response(
        self, ctx: _RequestContext, exc: Exception,
    ) -> GenieResponse:
        """錯誤處理 → GenieResponse(type="error")。"""
        total_elapsed = time.time() - ctx.query_start_time
        error_str = str(exc).lower()

        logger.error(
            f"\n{'='*80}\n"
            f"[{ctx.request_id}] ❌ 查詢失敗\n"
            f"{'-'*80}\n"
            f"  使用者:       {ctx.user_email}\n"
            f"  問題:         {ctx.question[:60]}{'...' if len(ctx.question) > 60 else ''}\n"
            f"  對話 ID:      {ctx.conversation_id or '新對話'}\n"
            f"  耗時:         {total_elapsed:.2f}s\n"
            f"  錯誤類型:     {type(exc).__name__}\n"
            f"  錯誤訊息:     {str(exc)[:200]}\n"
            f"{'='*80}"
        )

        if "ip acl" in error_str and "blocked" in error_str:
            logger.error(f"[{ctx.request_id}] 🚫 偵測到 IP ACL 封鎖")
            return GenieResponse(
                response_type="error",
                conversation_id=ctx.conversation_id,
                error=(
                    "⚠️ **IP 存取被封鎖**\n\n"
                    "機器人的 IP 地址被 Databricks 帳戶 IP 存取控制清單 (ACL) 封鎖。\n\n"
                    "**需要管理員操作：**\n"
                    "請查看 TROUBLESHOOTING.md 文件，以獲取有關將機器人的 IP 地址添加到 Databricks 帳戶 IP 允許清單的說明。"
                ),
            )

        return GenieResponse(
            response_type="error",
            conversation_id=ctx.conversation_id,
            error="處理您的請求時發生錯誤。",
        )

    # ── Metrics finalization（消除 3x 重複）──

    def _record_success(self, ctx: _RequestContext, response: GenieResponse) -> None:
        """成功查詢的 metrics 記錄。"""
        elapsed = time.time() - ctx.query_start_time
        self.metrics.record_query(elapsed, success=True)
        if self.should_log_stats():
            self._log_api_response(ctx.request_id, json.loads(response.to_json()), elapsed)
            self.metrics.log_stats()

    def _record_failure(self, ctx: _RequestContext) -> None:
        """失敗查詢的 metrics 記錄。"""
        elapsed = time.time() - ctx.query_start_time
        self.metrics.record_query(elapsed, success=False)
        if self.should_log_stats():
            self.metrics.log_stats()

    async def send_feedback(self, user_session: Any, message_id: str, feedback: str) -> None:
        """Submit feedback for a specific Genie message."""
        feedback_id = str(uuid.uuid4())[:8]

        if not self._config.ENABLE_GENIE_FEEDBACK_API:
            logger.info(f"[{feedback_id}] ⚠️  Genie 回饋 API 已停用，跳過")
            return

        if not user_session or not getattr(user_session, "conversation_id", None):
            logger.error(
                f"[{feedback_id}] ❌ 找不到活動對話\n"
                f"  使用者 ID:    {getattr(user_session, 'user_id', 'unknown')}"
            )
            return

        genie_feedback_type = "POSITIVE" if feedback == "positive" else "NEGATIVE"
        logger.info(
            f"[{feedback_id}] 👍 發送回饋\n"
            f"  使用者:       {user_session.email}\n"
            f"  訊息 ID:      {message_id}\n"
            f"  回饋類型:     {genie_feedback_type}"
        )
        
        await self._send_genie_feedback(
            space_id=self._config.DATABRICKS_SPACE_ID,
            conversation_id=user_session.conversation_id,
            message_id=message_id,
            feedback_type=genie_feedback_type,
        )

    async def _send_genie_feedback(
        self,
        space_id: str,
        conversation_id: str,
        message_id: str,
        feedback_type: str,
    ) -> None:
        loop = asyncio.get_running_loop()
        try:
            if self._supports_feedback_api:
                rating = (
                    GenieFeedbackRating.POSITIVE
                    if feedback_type == "POSITIVE"
                    else GenieFeedbackRating.NEGATIVE
                )
                await loop.run_in_executor(
                    None,
                    self._genie_api.send_message_feedback,
                    space_id,
                    conversation_id,
                    message_id,
                    rating,
                )
                logger.info(
                    f"✅ 回饋已發送\n"
                    f"  對話 ID:      {conversation_id}\n"
                    f"  訊息 ID:      {message_id}\n"
                    f"  類型:         {feedback_type}"
                )
                return

            logger.info("ℹ️  Genie SDK 無 send_message_feedback，改用 HTTP API")
            await self._send_genie_feedback_alternative(space_id, conversation_id, message_id, feedback_type)
        except Exception as exc:
            logger.error(
                f"❌ 回饋發送失敗\n"
                f"  對話 ID:      {conversation_id}\n"
                f"  訊息 ID:      {message_id}\n"
                f"  錯誤:         {str(exc)[:200]}"
            )
            raise

    async def _send_genie_feedback_alternative(
        self,
        space_id: str,
        conversation_id: str,
        message_id: str,
        feedback_type: str,
    ) -> None:
        base_url = self._config.DATABRICKS_HOST.rstrip('/')
        api_endpoint = (
            f"{base_url}/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/feedback"
        )
        payload = {"rating": feedback_type}
        headers = {
            "Authorization": f"Bearer {self._config.DATABRICKS_TOKEN}",
            "Content-Type": "application/json",
        }

        logger.info("正在發送回饋到: %s", api_endpoint)
        async with self.get_http_session() as session:
            response = await session.post(api_endpoint, json=payload, headers=headers)
            response_text = response.text
            if response.status_code == 200:
                logger.info("透過 HTTP API 成功發送 %s 回饋", feedback_type)
            else:
                logger.error(
                    "透過 HTTP API 發送回饋失敗: %s - %s",
                    response.status_code,
                    response_text,
                )
                raise Exception(f"HTTP {response.status_code}: {response_text}")

    async def get_last_message_id(self, conversation_id: Optional[str]) -> Optional[str]:
        if not conversation_id:
            return None

        loop = asyncio.get_running_loop()
        messages = None
        try:
            messages = await loop.run_in_executor(
                None,
                self._genie_api.list_conversation_messages,
                self._config.DATABRICKS_SPACE_ID,
                conversation_id,
            )
        except AttributeError:
            try:
                messages = await loop.run_in_executor(
                    None,
                    self._genie_api.get_conversation_messages,
                    self._config.DATABRICKS_SPACE_ID,
                    conversation_id,
                )
            except AttributeError:
                logger.warning("找不到適合列出 Genie 對話訊息的方法")
                return None

        if not messages:
            return None

        def _sort_key(message: Any) -> Any:
            return getattr(message, 'created_at', 0)

        try:
            if hasattr(messages, 'messages') and messages.messages:
                sorted_messages = sorted(messages.messages, key=_sort_key, reverse=True)
                return sorted_messages[0].message_id if sorted_messages else None
            if hasattr(messages, '__len__') and len(messages) > 0:
                sorted_messages = sorted(messages, key=_sort_key, reverse=True)
                return sorted_messages[0].message_id if sorted_messages else None
            if hasattr(messages, '__iter__'):
                message_list = list(messages)
                sorted_messages = sorted(message_list, key=_sort_key, reverse=True)
                return sorted_messages[0].message_id if sorted_messages else None
        except Exception as exc:
            logger.warning("無法按時間戳記排序訊息: %s", exc)
            if hasattr(messages, 'messages') and messages.messages:
                return messages.messages[-1].message_id
            if hasattr(messages, '__len__') and len(messages) > 0:
                return messages[-1].message_id
            if hasattr(messages, '__iter__'):
                message_list = list(messages)
                return message_list[-1].message_id if message_list else None

        logger.warning("無法從類型為 %s 的回應中提取訊息", type(messages))
        return None
