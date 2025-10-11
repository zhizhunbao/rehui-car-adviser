import json
from datetime import datetime
from typing import Any, Dict

from fastapi import WebSocket

from app.models.schemas import (
    SearchProgressMessage,
    SearchResultsMessage,
    TaskStatusMessage,
    WebSocketError,
    WebSocketMessage,
    WebSocketMessageType,
)
from app.utils.core.logger import logger
from app.utils.websocket.connection_manager import connection_manager


class MessageHandler:
    """WebSocket 消息处理器"""

    def __init__(self):
        self.handlers = {
            WebSocketMessageType.PING: self._handle_ping,
            WebSocketMessageType.PONG: self._handle_pong,
            WebSocketMessageType.SEARCH_START: self._handle_search_start,
            WebSocketMessageType.SEARCH_PROGRESS: self._handle_search_progress,
            WebSocketMessageType.SEARCH_RESULTS: self._handle_search_results,
            WebSocketMessageType.SEARCH_ERROR: self._handle_search_error,
            WebSocketMessageType.CONVERSATION_MESSAGE: self._handle_conversation_message,
            WebSocketMessageType.TASK_START: self._handle_task_start,
            WebSocketMessageType.TASK_PROGRESS: self._handle_task_progress,
            WebSocketMessageType.TASK_COMPLETE: self._handle_task_complete,
            WebSocketMessageType.TASK_ERROR: self._handle_task_error,
        }

    async def handle_message(
        self, websocket: WebSocket, message: str, client_id: str
    ) -> None:
        """处理接收到的WebSocket消息"""
        try:
            # 解析消息
            message_data = json.loads(message)
            message_type = message_data.get("type")

            if not message_type:
                await self._send_error_message(websocket, "消息类型不能为空")
                return

            # 验证消息类型
            try:
                ws_message_type = WebSocketMessageType(message_type)
            except ValueError:
                await self._send_error_message(
                    websocket, f"无效的消息类型: {message_type}"
                )
                return

            # 调用对应的处理器
            if ws_message_type in self.handlers:
                await self.handlers[ws_message_type](
                    websocket, message_data, client_id
                )
            else:
                await self._send_error_message(
                    websocket, f"不支持的消息类型: {message_type}"
                )

        except json.JSONDecodeError:
            await self._send_error_message(websocket, "无效的JSON格式")
        except Exception as e:
            logger.log_result(
                "处理WebSocket消息失败",
                f"客户端ID: {client_id}, 错误: {str(e)}",
            )
            await self._send_error_message(
                websocket, f"处理消息时发生错误: {str(e)}"
            )

    async def _handle_ping(
        self,
        websocket: WebSocket,
        message_data: Dict[str, Any],
        client_id: str,
    ) -> None:
        """处理ping消息"""
        pong_message = WebSocketMessage(
            type=WebSocketMessageType.PONG,
            timestamp=datetime.now(),
            message="pong",
            client_id=client_id,
        )
        await websocket.send_text(pong_message.model_dump_json())

    async def _handle_pong(
        self,
        websocket: WebSocket,
        message_data: Dict[str, Any],
        client_id: str,
    ) -> None:
        """处理pong消息"""
        # 更新连接的最后ping时间
        connection_info = connection_manager.get_connection_info(client_id)
        if connection_info:
            connection_info.last_ping = datetime.now()

    async def _handle_search_start(
        self,
        websocket: WebSocket,
        message_data: Dict[str, Any],
        client_id: str,
    ) -> None:
        """处理搜索开始消息"""
        task_id = message_data.get("data", {}).get("task_id")
        if not task_id:
            await self._send_error_message(websocket, "搜索任务ID不能为空")
            return

        # 订阅任务更新
        connection_manager.subscribe_to_task(client_id, task_id)

        # 发送确认消息
        confirm_message = WebSocketMessage(
            type=WebSocketMessageType.SEARCH_START,
            timestamp=datetime.now(),
            message=f"已开始搜索任务: {task_id}",
            client_id=client_id,
            data={"task_id": task_id},
        )
        await websocket.send_text(confirm_message.model_dump_json())

    async def _handle_search_progress(
        self,
        websocket: WebSocket,
        message_data: Dict[str, Any],
        client_id: str,
    ) -> None:
        """处理搜索进度消息"""
        # 这里可以记录搜索进度或转发给其他订阅者
        logger.log_result(
            "收到搜索进度", f"客户端ID: {client_id}, 数据: {message_data}"
        )

    async def _handle_search_results(
        self,
        websocket: WebSocket,
        message_data: Dict[str, Any],
        client_id: str,
    ) -> None:
        """处理搜索结果消息"""
        # 这里可以处理搜索结果或转发给其他订阅者
        logger.log_result(
            "收到搜索结果", f"客户端ID: {client_id}, 数据: {message_data}"
        )

    async def _handle_search_error(
        self,
        websocket: WebSocket,
        message_data: Dict[str, Any],
        client_id: str,
    ) -> None:
        """处理搜索错误消息"""
        error_message = message_data.get("message", "搜索过程中发生错误")
        logger.log_result(
            "搜索错误", f"客户端ID: {client_id}, 错误: {error_message}"
        )

    async def _handle_conversation_message(
        self,
        websocket: WebSocket,
        message_data: Dict[str, Any],
        client_id: str,
    ) -> None:
        """处理对话消息"""
        session_id = message_data.get("data", {}).get("session_id")
        if session_id:
            # 订阅会话更新
            connection_manager.subscribe_to_session(client_id, session_id)

        logger.log_result(
            "收到对话消息", f"客户端ID: {client_id}, 会话ID: {session_id}"
        )

    async def _handle_task_start(
        self,
        websocket: WebSocket,
        message_data: Dict[str, Any],
        client_id: str,
    ) -> None:
        """处理任务开始消息"""
        task_id = message_data.get("data", {}).get("task_id")
        if task_id:
            connection_manager.subscribe_to_task(client_id, task_id)

        logger.log_result(
            "任务开始", f"客户端ID: {client_id}, 任务ID: {task_id}"
        )

    async def _handle_task_progress(
        self,
        websocket: WebSocket,
        message_data: Dict[str, Any],
        client_id: str,
    ) -> None:
        """处理任务进度消息"""
        logger.log_result(
            "任务进度更新", f"客户端ID: {client_id}, 数据: {message_data}"
        )

    async def _handle_task_complete(
        self,
        websocket: WebSocket,
        message_data: Dict[str, Any],
        client_id: str,
    ) -> None:
        """处理任务完成消息"""
        task_id = message_data.get("data", {}).get("task_id")
        if task_id:
            connection_manager.unsubscribe_from_task(client_id, task_id)

        logger.log_result(
            "任务完成", f"客户端ID: {client_id}, 任务ID: {task_id}"
        )

    async def _handle_task_error(
        self,
        websocket: WebSocket,
        message_data: Dict[str, Any],
        client_id: str,
    ) -> None:
        """处理任务错误消息"""
        task_id = message_data.get("data", {}).get("task_id")
        error_message = message_data.get("message", "任务执行过程中发生错误")

        if task_id:
            connection_manager.unsubscribe_from_task(client_id, task_id)

        logger.log_result(
            "任务错误",
            f"客户端ID: {client_id}, 任务ID: {task_id}, 错误: {error_message}",
        )

    async def _send_error_message(
        self, websocket: WebSocket, error_message: str
    ) -> None:
        """发送错误消息"""
        try:
            error = WebSocketError(
                error_code="MESSAGE_HANDLING_ERROR",
                error_message=error_message,
                timestamp=datetime.now(),
            )

            message = WebSocketMessage(
                type=WebSocketMessageType.ERROR,
                timestamp=datetime.now(),
                message=error_message,
                data=error.model_dump(),
            )

            await websocket.send_text(message.model_dump_json())
        except Exception as e:
            logger.log_result("发送错误消息失败", f"错误: {str(e)}")

    async def process_search_progress(
        self, task_id: str, progress_data: Dict[str, Any]
    ) -> None:
        """处理搜索进度更新"""
        progress_message = SearchProgressMessage(
            task_id=task_id,
            progress_percentage=progress_data.get("progress_percentage", 0.0),
            current_step=progress_data.get("current_step", ""),
            message=progress_data.get("message", ""),
            total_sources=progress_data.get("total_sources"),
            completed_sources=progress_data.get("completed_sources"),
            cars_found=progress_data.get("cars_found"),
        )

        ws_message = WebSocketMessage(
            type=WebSocketMessageType.SEARCH_PROGRESS,
            timestamp=datetime.now(),
            data=progress_message.model_dump(),
        )

        await connection_manager.broadcast_to_task_subscribers(
            task_id, ws_message
        )

    async def process_search_results(
        self, task_id: str, results_data: Dict[str, Any]
    ) -> None:
        """处理搜索结果"""
        results_message = SearchResultsMessage(
            task_id=task_id,
            cars=results_data.get("cars", []),
            total_count=results_data.get("total_count", 0),
            search_duration=results_data.get("search_duration", 0.0),
            message=results_data.get("message", "搜索完成"),
        )

        ws_message = WebSocketMessage(
            type=WebSocketMessageType.SEARCH_RESULTS,
            timestamp=datetime.now(),
            data=results_message.model_dump(),
        )

        await connection_manager.broadcast_to_task_subscribers(
            task_id, ws_message
        )

    async def process_task_status(
        self, task_id: str, status_data: Dict[str, Any]
    ) -> None:
        """处理任务状态更新"""
        status_message = TaskStatusMessage(
            task_id=task_id,
            status=status_data.get("status", "unknown"),
            progress=status_data.get("progress"),
            message=status_data.get("message", ""),
            error=status_data.get("error"),
            result=status_data.get("result"),
        )

        ws_message = WebSocketMessage(
            type=WebSocketMessageType.TASK_PROGRESS,
            timestamp=datetime.now(),
            data=status_message.model_dump(),
        )

        await connection_manager.broadcast_to_task_subscribers(
            task_id, ws_message
        )


# 全局消息处理器实例
message_handler = MessageHandler()
