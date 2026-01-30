"""Genie service module that encapsulates Databricks Genie interactions."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
import io
import base64
from asyncio.log import logger
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional, Tuple

import aiohttp
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import GenieAPI

from config import DefaultConfig
from chart_generator import create_chart_card_with_image


class QueryMetrics:
    """查詢性能指標收集器"""
    def __init__(self):
        self.total_queries = 0
        self.successful_queries = 0
        self.failed_queries = 0
        self.total_duration = 0.0
    
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
        """記錄統計資訊到日誌"""
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
        # HTTP 連接池
        self._http_session = None
        # 性能指標收集器
        self.metrics = QueryMetrics()

    def _create_workspace_client(self) -> WorkspaceClient:
        logger.info(
            "\n" + "="*80 + "\n"
            "🔧 正在載入 Databricks 配置\n"
            "-"*80
        )
        logger.info("  HOST:         %s", self._config.DATABRICKS_HOST)
        logger.info("  TOKEN 存在:   %s", bool(self._config.DATABRICKS_TOKEN))
        token_length = len(self._config.DATABRICKS_TOKEN) if self._config.DATABRICKS_TOKEN else 0
        logger.info("  TOKEN 長度:   %s", token_length)
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

    @asynccontextmanager
    async def get_http_session(self):
        """重用 HTTP Session 減少連接開銷"""
        if self._http_session is None or self._http_session.closed:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            timeout = aiohttp.ClientTimeout(total=60)
            self._http_session = aiohttp.ClientSession(
                connector=connector, timeout=timeout
            )
        try:
            yield self._http_session
        finally:
            pass  # 重用，不關閉

    async def close(self):
        """關閉 HTTP Session（應用程式關閉時調用）"""
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()
            logger.info("🔌 已關閉 HTTP Session")

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

    async def ask(
        self,
        question: str,
        space_id: str,
        user_session: Any,
        conversation_id: Optional[str] = None,
    ) -> Tuple[str, str, str]:
        """Send a question to Genie and return the raw response payload."""

        # 生成請求追蹤 ID
        request_id = str(uuid.uuid4())[:8]
        query_start_time = time.time()
        success = False
        
        logger.info(
            f"\n{'='*80}\n"
            f"[{request_id}] 📥 新查詢請求\n"
            f"{'-'*80}\n"
            f"  使用者:       {user_session.email}\n"
            f"  問題:         {question[:80]}{'...' if len(question) > 80 else ''}\n"
            f"  對話 ID:      {conversation_id or '新對話'}\n"
            f"  Space ID:     {space_id}\n"
            f"{'='*80}"
        )
        
        try:
            contextual_question = f"[{user_session.email}] {question}"
            loop = asyncio.get_running_loop()

            if conversation_id is None:
                logger.info(f"[{request_id}] 🆕 啟動新對話...")
                initial_message = await loop.run_in_executor(
                    None,
                    self._genie_api.start_conversation_and_wait,
                    space_id,
                    contextual_question,
                )
                conversation_id = initial_message.conversation_id
                logger.info(
                    f"[{request_id}] ✅ 對話已創建\n"
                    f"  對話 ID:      {conversation_id}\n"
                    f"  訊息 ID:      {initial_message.message_id}\n"
                    f"  訊息狀態:     {initial_message.status}\n"
                    f"  附件數量:     {len(initial_message.attachments) if initial_message.attachments else 0}\n"
                    f"  查詢結果:     {'有' if initial_message.query_result else '無'}"
                )
                
                # 解析並記錄 attachments 中的重要物件
                self._log_message_attachments(request_id, initial_message)
            else:
                logger.info(f"[{request_id}] 💬 在現有對話中發送訊息: {conversation_id}")
                initial_message = await loop.run_in_executor(
                    None,
                    self._genie_api.create_message_and_wait,
                    space_id,
                    conversation_id,
                    contextual_question,
                )
                logger.info(
                    f"[{request_id}] ✅ 訊息已發送\n"
                    f"  訊息 ID:      {initial_message.message_id}\n"
                    f"  訊息狀態:     {initial_message.status}\n"
                    f"  附件數量:     {len(initial_message.attachments) if initial_message.attachments else 0}\n"
                    f"  查詢結果:     {'有' if initial_message.query_result else '無'}"
                )
                
                # 解析並記錄 attachments 中的重要物件
                self._log_message_attachments(request_id, initial_message)

            # 並發執行：同時獲取查詢結果和訊息內容
            query_result = None
            message_content = None
            
            if initial_message.query_result is not None:
                logger.info(
                    f"[{request_id}] ⚡ 開始並發獲取查詢結果和訊息內容...\n"
                    f"  Statement ID: {initial_message.query_result.statement_id if initial_message.query_result else 'N/A'}\n"
                    f"  Row Count:    {initial_message.query_result.row_count if initial_message.query_result else 0}\n"
                    f"  提示:         SDK 將自動輪詢直到查詢完成 (PENDING_WAREHOUSE → COMPLETED)"
                )
                fetch_start = time.time()
                
                query_result_task = loop.run_in_executor(
                    None,
                    self._genie_api.get_message_attachment_query_result,
                    space_id,
                    initial_message.conversation_id,
                    initial_message.message_id,
                    initial_message.attachments[0].attachment_id,
                )
                message_content_task = loop.run_in_executor(
                    None,
                    self._genie_api.get_message,
                    space_id,
                    initial_message.conversation_id,
                    initial_message.message_id,
                )
                
                query_result, message_content = await asyncio.gather(
                    query_result_task,
                    message_content_task
                )
                
                fetch_elapsed = time.time() - fetch_start
                
                # 記錄查詢結果的詳細狀態
                if query_result and query_result.statement_response:
                    statement_state = query_result.statement_response.status.state
                    row_count = query_result.statement_response.manifest.total_row_count if query_result.statement_response.manifest else 0
                    
                    logger.info(
                        f"[{request_id}] ✅ 並發獲取完成\n"
                        f"  耗時:         {fetch_elapsed:.2f}s\n"
                        f"  最終狀態:     {statement_state}\n"
                        f"  資料筆數:     {row_count}\n"
                        f"  說明:         輪詢已完成，查詢已執行完畢"
                    )
                    
                    # 記錄 COMPLETED 狀態下的附件物件（此時 row_count 已更新）
                    logger.info(f"[{request_id}] 🔄 輪詢後的訊息狀態: {message_content.status if message_content else 'N/A'}")
                    if message_content:
                        self._log_message_attachments(request_id, message_content)
                else:
                    logger.info(
                        f"[{request_id}] ✅ 並發獲取完成\n"
                        f"  耗時:         {fetch_elapsed:.2f}s\n"
                        f"  狀態:         無 statement_response"
                    )
            else:
                logger.info(f"[{request_id}] 📄 獲取訊息內容（無查詢結果）...")
                message_content = await loop.run_in_executor(
                    None,
                    self._genie_api.get_message,
                    space_id,
                    initial_message.conversation_id,
                    initial_message.message_id,
                )
                logger.info(f"[{request_id}] ✅ 訊息內容已獲取")
                
                # 記錄無查詢結果時的附件物件
                if message_content:
                    self._log_message_attachments(request_id, message_content)

            if query_result and query_result.statement_response:
                logger.info(
                    f"[{request_id}] 📊 處理查詢結果...\n"
                    f"  API 端點:     /spaces/.../messages/.../attachments/.../query-result\n"
                    f"  Statement ID: {query_result.statement_response.statement_id}"
                )
                results = await loop.run_in_executor(
                    None,
                    self._workspace_client.statement_execution.get_statement,
                    query_result.statement_response.statement_id,
                )

                # 記錄 statement_response 的詳細信息
                if results.status:
                    logger.info(
                        f"[{request_id}] 🎯 Statement Response 詳細信息\n"
                        f"  狀態:         {results.status.state}\n"
                        f"  Statement ID: {results.statement_id if hasattr(results, 'statement_id') else 'N/A'}"
                    )
                
                # 記錄 manifest 信息
                if results.manifest:
                    manifest = results.manifest
                    logger.info(
                        f"[{request_id}] 📋 Manifest 信息\n"
                        f"  格式:         {manifest.format if hasattr(manifest, 'format') else 'N/A'}\n"
                        f"  欄位數:       {manifest.schema.column_count if manifest.schema else 0}\n"
                        f"  總筆數:       {manifest.total_row_count if hasattr(manifest, 'total_row_count') else 0}\n"
                        f"  總位元組:     {manifest.total_byte_count if hasattr(manifest, 'total_byte_count') else 0}\n"
                        f"  是否截斷:     {manifest.truncated if hasattr(manifest, 'truncated') else False}"
                    )
                    
                    # 記錄 schema 信息
                    if manifest.schema and manifest.schema.columns:
                        logger.info(f"[{request_id}] 🗂️  Schema 欄位:")
                        for col in manifest.schema.columns:
                            logger.info(
                                f"        [{col.position}] {col.name} ({col.type_name})"
                            )
                
                # 記錄 result 數據
                if results.result:
                    result_obj = results.result
                    data_preview = ""
                    if hasattr(result_obj, 'data_array') and result_obj.data_array:
                        # 只顯示前3筆數據作為預覽
                        preview_rows = result_obj.data_array[:3]
                        data_preview = "\n".join([f"        {row}" for row in preview_rows])
                        if len(result_obj.data_array) > 3:
                            data_preview += f"\n        ... (還有 {len(result_obj.data_array) - 3} 筆)"
                    
                    logger.info(
                        f"[{request_id}] 📦 Result 數據\n"
                        f"  Chunk Index:  {result_obj.chunk_index if hasattr(result_obj, 'chunk_index') else 0}\n"
                        f"  Row Offset:   {result_obj.row_offset if hasattr(result_obj, 'row_offset') else 0}\n"
                        f"  Row Count:    {result_obj.row_count if hasattr(result_obj, 'row_count') else 0}\n"
                        f"  數據預覽:\n{data_preview if data_preview else '        (無數據)'}"
                    )

                query_description = ""
                sql_query = ""
                for attachment in message_content.attachments:
                    if attachment.query:
                        if attachment.query.description:
                            query_description = attachment.query.description
                        if attachment.query.query:
                            sql_query = attachment.query.query
                        break

                # 構建結果
                row_count = len(results.result.data_array) if results.result and results.result.data_array else 0
                col_count = results.manifest.schema.column_count if results.manifest and results.manifest.schema else 0
                
                logger.info(
                    f"[{request_id}] 🗒️  查詢詳細信息\n"
                    f"  SQL:          {sql_query[:100] if sql_query else 'N/A'}{'...' if len(sql_query) > 100 else ''}\n"
                    f"  說明:         {query_description[:80] if query_description else 'N/A'}{'...' if len(query_description) > 80 else ''}"
                )
                
                # 提取 suggested_questions（只有當 status 為 COMPLETED 時）
                suggested_questions = []
                message_status = message_content.status if message_content else None
                logger.info(f"[{request_id}] 📌 訊息狀態: {message_status}")
                
                if message_status == "COMPLETED" and message_content and message_content.attachments:
                    logger.info(f"[{request_id}] 🔍 開始提取 suggested_questions...")
                    for attachment in message_content.attachments:
                        if hasattr(attachment, 'suggested_questions') and attachment.suggested_questions:
                            if hasattr(attachment.suggested_questions, 'questions') and attachment.suggested_questions.questions:
                                suggested_questions = list(attachment.suggested_questions.questions)
                                logger.info(f"[{request_id}] ✅ 成功提取 {len(suggested_questions)} 個建議問題")
                                break
                    if not suggested_questions:
                        logger.info(f"[{request_id}] ℹ️ 訊息已完成但未找到建議問題")
                else:
                    logger.info(f"[{request_id}] ⏭️ 跳過提取 suggested_questions (狀態: {message_status}，不是 COMPLETED)")
                
                result = (
                    json.dumps(
                        {
                            "columns": results.manifest.schema.as_dict(),
                            "data": results.result.as_dict(),
                            "query_description": query_description,
                            "suggested_questions": suggested_questions,
                        }
                    ),
                    conversation_id,
                    initial_message.message_id,
                )
                
                total_elapsed = time.time() - query_start_time
                logger.info(
                    f"[{request_id}] ✅ 查詢完成\n"
                    f"  總耗時:       {total_elapsed:.2f}s\n"
                    f"  資料筆數:     {row_count}\n"
                    f"  欄位數:       {col_count}\n"
                    f"  說明:         {query_description[:60]}{'...' if len(query_description) > 60 else ''}"
                )
                
                success = True
                self.metrics.record_query(total_elapsed, success=True)
                
                if self.metrics.total_queries % 100 == 0:
                    self.metrics.log_stats()
                
                return result

            if message_content.attachments:
                for attachment in message_content.attachments:
                    if attachment.text and attachment.text.content:
                        # 提取 suggested_questions
                        suggested_questions = []
                        for att in message_content.attachments:
                            if hasattr(att, 'suggested_questions') and att.suggested_questions:
                                if hasattr(att.suggested_questions, 'questions') and att.suggested_questions.questions:
                                    suggested_questions = list(att.suggested_questions.questions)
                                    break
                        
                        result = (
                            json.dumps({
                                "message": attachment.text.content,
                                "suggested_questions": suggested_questions,
                            }),
                            conversation_id,
                            initial_message.message_id,
                        )
                        
                        total_elapsed = time.time() - query_start_time
                        logger.info(
                            f"[{request_id}] 💬 文字回覆已完成\n"
                            f"  總耗時:       {total_elapsed:.2f}s\n"
                            f"  訊息長度:     {len(attachment.text.content)}"
                        )
                        
                        success = True
                        self.metrics.record_query(total_elapsed, success=True)
                        
                        if self.metrics.total_queries % 100 == 0:
                            self.metrics.log_stats()
                        
                        return result

            # 預設回覆
            # 提取 suggested_questions
            suggested_questions = []
            if message_content and message_content.attachments:
                for att in message_content.attachments:
                    if hasattr(att, 'suggested_questions') and att.suggested_questions:
                        if hasattr(att.suggested_questions, 'questions') and att.suggested_questions.questions:
                            suggested_questions = list(att.suggested_questions.questions)
                            break
            
            result = (
                json.dumps({
                    "message": message_content.content,
                    "suggested_questions": suggested_questions,
                }),
                conversation_id,
                initial_message.message_id,
            )
            
            total_elapsed = time.time() - query_start_time
            logger.info(
                f"[{request_id}] 📝 預設回覆已完成\n"
                f"  總耗時:       {total_elapsed:.2f}s\n"
                f"  訊息長度:     {len(message_content.content)}"
            )
            
            success = True
            self.metrics.record_query(total_elapsed, success=True)
            
            if self.metrics.total_queries % 100 == 0:
                self.metrics.log_stats()
            
            return result
        except Exception as exc:
            total_elapsed = time.time() - query_start_time
            
            if not success:
                self.metrics.record_query(total_elapsed, success=False)
            
            if self.metrics.total_queries % 100 == 0:
                self.metrics.log_stats()
            
            error_str = str(exc).lower()
            logger.error(
                f"\n{'='*80}\n"
                f"[{request_id}] ❌ 查詢失敗\n"
                f"{'-'*80}\n"
                f"  使用者:       {user_session.email}\n"
                f"  問題:         {question[:60]}{'...' if len(question) > 60 else ''}\n"
                f"  對話 ID:      {conversation_id or '新對話'}\n"
                f"  耗時:         {total_elapsed:.2f}s\n"
                f"  錯誤類型:     {type(exc).__name__}\n"
                f"  錯誤訊息:     {str(exc)[:200]}\n"
                f"{'='*80}"
            )

            if "ip acl" in error_str and "blocked" in error_str:
                logger.error(f"[{request_id}] 🚫 偵測到 IP ACL 封鎖")
                return (
                    json.dumps(
                        {
                            "error": "⚠️ **IP 存取被封鎖**\n\n"
                            "機器人的 IP 地址被 Databricks 帳戶 IP 存取控制清單 (ACL) 封鎖。\n\n"
                            "**需要管理員操作：**\n"
                            "請查看 TROUBLESHOOTING.md 文件，以獲取有關將機器人的 IP 地址添加到 Databricks 帳戶 IP 允許清單的說明。",
                        }
                    ),
                    conversation_id,
                    None,
                )

            return (
                json.dumps({"error": "處理您的請求時發生錯誤。"}),
                conversation_id,
                None,
            )

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
            await loop.run_in_executor(
                None,
                self._genie_api.send_message_feedback,
                space_id,
                conversation_id,
                message_id,
                feedback_type,
            )
            logger.info(
                f"✅ 回饋已發送\n"
                f"  對話 ID:      {conversation_id}\n"
                f"  訊息 ID:      {message_id}\n"
                f"  類型:         {feedback_type}"
            )
        except AttributeError:
            logger.warning("⚠️  找不到 send_message_feedback 方法，嘗試替代方法")
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
            async with session.post(api_endpoint, json=payload, headers=headers) as response:
                response_text = await response.text()
                if response.status == 200:
                    logger.info("透過 HTTP API 成功發送 %s 回饋", feedback_type)
                else:
                    logger.error(
                        "透過 HTTP API 發送回饋失敗: %s - %s",
                        response.status,
                        response_text,
                    )
                    raise Exception(f"HTTP {response.status}: {response_text}")

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

def _analyze_chart_suitability(columns: dict, data: dict) -> dict:
    """分析數據是否適合繪製圖表並返回建議的圖表類型
    
    Returns:
        dict: {
            'suitable': bool,
            'chart_type': str,  # 'bar', 'pie', 'line'
            'category_column': str,
            'value_column': str,
            'data_for_chart': list
        }
    """
    try:
        if not columns or not data:
            return {'suitable': False}
        
        # 獲取列信息
        col_list = columns.get('columns', [])
        if len(col_list) < 2:
            return {'suitable': False}
        
        # 獲取數據行
        data_array = data.get('data_array', [])
        if not data_array or len(data_array) < 2 or len(data_array) > 20:
            # 太少或太多數據都不適合圖表
            return {'suitable': False}
        
        # 分析列類型
        category_col = None
        value_col = None
        category_idx = None
        value_idx = None
        
        for idx, col in enumerate(col_list):
            col_name = col.get('name', '')
            col_type = col.get('type_text', '').lower()
            
            # 尋找類別列（字串類型）
            if not category_col and ('string' in col_type or 'varchar' in col_type):
                category_col = col_name
                category_idx = idx
            
            # 尋找數值列
            if not value_col and any(t in col_type for t in ['int', 'long', 'double', 'float', 'decimal', 'bigint']):
                value_col = col_name
                value_idx = idx
        
        if not category_col or not value_col:
            return {'suitable': False}
        
        # 準備圖表數據
        chart_data = []
        has_negative = False
        total_value = 0
        
        for row in data_array:
            if len(row) > max(category_idx, value_idx):
                category = str(row[category_idx]) if row[category_idx] is not None else 'N/A'
                value = row[value_idx]
                
                # 跳過 None 值
                if value is None:
                    continue
                
                try:
                    value = float(value)
                    if value < 0:
                        has_negative = True
                    total_value += abs(value)
                    chart_data.append({'category': category, 'value': value})
                except (ValueError, TypeError):
                    continue
        
        if len(chart_data) < 2:
            return {'suitable': False}
        
        # 決定圖表類型
        chart_type = 'bar'  # 默認使用長條圖
        
        # 如果沒有負值且類別數量適中（2-8個），可以用圓餅圖
        if not has_negative and 2 <= len(chart_data) <= 8:
            chart_type = 'pie'
        
        # 如果類別看起來像時間序列（包含日期、月份等關鍵字），用折線圖
        if any(keyword in category_col.lower() for keyword in ['date', 'time', 'month', 'year', 'day', '日期', '時間', '月份', '年']):
            chart_type = 'line'
        
        return {
            'suitable': True,
            'chart_type': chart_type,
            'category_column': category_col,
            'value_column': value_col,
            'data_for_chart': chart_data
        }
        
    except Exception as e:
        logger.error(f"分析圖表適用性時發生錯誤: {e}")
        return {'suitable': False}


def process_query_results(answer_json: Dict) -> str:
    response = ""
    if "query_description" in answer_json and answer_json["query_description"]:
        response += f"## 查詢說明\n\n{answer_json['query_description']}\n\n"

    if "columns" in answer_json and "data" in answer_json:
        columns = answer_json["columns"]
        data = answer_json["data"]
        
        # 分析數據是否適合繪製圖表
        chart_info = _analyze_chart_suitability(columns, data)
        if chart_info.get('suitable'):
            answer_json['chart_info'] = chart_info
        
        response += "## 查詢結果\n\n"
        if isinstance(columns, dict) and "columns" in columns:
            header = "| " + " | ".join(col["name"] for col in columns["columns"]) + " |"
            separator = "|" + "|".join(["---" for _ in columns["columns"]]) + "|"
            response += header + "\n" + separator + "\n"
            for row in data["data_array"]:
                formatted_row = []
                for value, col in zip(row, columns["columns"]):
                    if value is None:
                        formatted_value = "NULL"
                    elif col["type_name"] in ["DECIMAL", "DOUBLE", "FLOAT"]:
                        formatted_value = f"{float(value):,.2f}"
                    elif col["type_name"] in ["INT", "BIGINT", "LONG"]:
                        formatted_value = f"{int(value):,}"
                    else:
                        formatted_value = str(value)
                    formatted_row.append(formatted_value)
                response += "| " + " | ".join(formatted_row) + " |\n"
        else:
            response += f"非預期的欄位格式: {columns}\n\n"
    elif "error" in answer_json:
        response += f"{answer_json['error']}\n\n"
    elif "message" in answer_json:
        response += f"{answer_json['message']}\n\n"
    else:
        response += "無可用資料。\n\n"
    
    # 添加建議問題
    if "suggested_questions" in answer_json and answer_json["suggested_questions"]:
        response += "\n---\n\n## 💡 建議問題\n\n"
        response += "您可以繼續詢問以下問題：\n\n"
        for idx, question in enumerate(answer_json["suggested_questions"], 1):
            response += f"{idx}. {question}\n"
        response += "\n*直接輸入問題編號或完整問題即可查詢*\n"

    return response
