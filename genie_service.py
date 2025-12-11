"""Genie service module that encapsulates Databricks Genie interactions."""

from __future__ import annotations

import asyncio
import json
from asyncio.log import logger
from typing import Any, Dict, Optional, Tuple

import aiohttp
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import GenieAPI


class GenieService:
    """Handles all interactions with the Databricks Genie APIs."""

    def __init__(self, config: Any, workspace_client: WorkspaceClient | None = None):
        self._config = config
        self._workspace_client = workspace_client or self._create_workspace_client()
        self._genie_api = GenieAPI(self._workspace_client.api_client)

    def _create_workspace_client(self) -> WorkspaceClient:
        logger.info("正在載入 Databricks 配置...")
        logger.info("DATABRICKS_HOST: %s", self._config.DATABRICKS_HOST)
        logger.info("DATABRICKS_TOKEN 存在: %s", bool(self._config.DATABRICKS_TOKEN))
        token_length = len(self._config.DATABRICKS_TOKEN) if self._config.DATABRICKS_TOKEN else 0
        logger.info("DATABRICKS_TOKEN 長度: %s", token_length)

        if not self._config.DATABRICKS_TOKEN:
            raise ValueError("DATABRICKS_TOKEN environment variable is not set")

        try:
            client = WorkspaceClient(
                host=self._config.DATABRICKS_HOST,
                token=self._config.DATABRICKS_TOKEN,
            )
            logger.info("Databricks 客戶端初始化成功")
            return client
        except Exception as exc:
            logger.error("初始化 Databricks 客戶端失敗: %s", exc)
            raise

    async def ask(
        self,
        question: str,
        space_id: str,
        user_session: Any,
        conversation_id: Optional[str] = None,
    ) -> Tuple[str, str, str]:
        """Send a question to Genie and return the raw response payload."""

        try:
            contextual_question = f"[{user_session.email}] {question}"
            loop = asyncio.get_running_loop()

            if conversation_id is None:
                initial_message = await loop.run_in_executor(
                    None,
                    self._genie_api.start_conversation_and_wait,
                    space_id,
                    contextual_question,
                )
                conversation_id = initial_message.conversation_id
            else:
                initial_message = await loop.run_in_executor(
                    None,
                    self._genie_api.create_message_and_wait,
                    space_id,
                    conversation_id,
                    contextual_question,
                )

            query_result = None
            if initial_message.query_result is not None:
                query_result = await loop.run_in_executor(
                    None,
                    self._genie_api.get_message_attachment_query_result,
                    space_id,
                    initial_message.conversation_id,
                    initial_message.message_id,
                    initial_message.attachments[0].attachment_id,
                )

            message_content = await loop.run_in_executor(
                None,
                self._genie_api.get_message,
                space_id,
                initial_message.conversation_id,
                initial_message.message_id,
            )

            if query_result and query_result.statement_response:
                results = await loop.run_in_executor(
                    None,
                    self._workspace_client.statement_execution.get_statement,
                    query_result.statement_response.statement_id,
                )

                query_description = ""
                for attachment in message_content.attachments:
                    if attachment.query and attachment.query.description:
                        query_description = attachment.query.description
                        break

                return (
                    json.dumps(
                        {
                            "columns": results.manifest.schema.as_dict(),
                            "data": results.result.as_dict(),
                            "query_description": query_description,
                        }
                    ),
                    conversation_id,
                    initial_message.message_id,
                )

            if message_content.attachments:
                for attachment in message_content.attachments:
                    if attachment.text and attachment.text.content:
                        return (
                            json.dumps({"message": attachment.text.content}),
                            conversation_id,
                            initial_message.message_id,
                        )

            return (
                json.dumps({"message": message_content.content}),
                conversation_id,
                initial_message.message_id,
            )
        except Exception as exc:
            error_str = str(exc).lower()
            logger.error(
                "ask_genie 為使用者 %s 處理時發生錯誤: %s",
                getattr(user_session, "get_display_name", lambda: "unknown")(),
                exc,
            )

            if "ip acl" in error_str and "blocked" in error_str:
                logger.error("偵測到 IP ACL 封鎖: %s", exc)
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

        if not self._config.ENABLE_GENIE_FEEDBACK_API:
            logger.info("Genie 回饋 API 已停用，跳過 API 呼叫")
            return

        if not user_session or not getattr(user_session, "conversation_id", None):
            logger.error("找不到使用者 %s 的活動對話", getattr(user_session, "user_id", "unknown"))
            return

        genie_feedback_type = "POSITIVE" if feedback == "positive" else "NEGATIVE"
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
                "成功為對話 %s 中的訊息 %s 發送 %s 回饋",
                conversation_id,
                message_id,
                feedback_type,
            )
        except AttributeError:
            logger.warning("找不到 send_message_feedback 方法，嘗試替代方法")
            await self._send_genie_feedback_alternative(space_id, conversation_id, message_id, feedback_type)
        except Exception as exc:
            logger.error("呼叫 Genie API 進行回饋時發生錯誤: %s", exc)
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
        async with aiohttp.ClientSession() as session:
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


def process_query_results(answer_json: Dict) -> str:
    response = ""
    if "query_description" in answer_json and answer_json["query_description"]:
        response += f"## 查詢說明\n\n{answer_json['query_description']}\n\n"

    if "columns" in answer_json and "data" in answer_json:
        response += "## 查詢結果\n\n"
        columns = answer_json["columns"]
        data = answer_json["data"]
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

    return response
