import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.schemas import (
    CarListing,
    SearchProgressMessage,
    SearchResultsMessage,
    SystemNotificationMessage,
    TaskStatusMessage,
    WebSocketMessage,
    WebSocketMessageType,
)
from app.utils.core.logger import logger
from app.utils.websocket.connection_manager import connection_manager


class RealtimeBroadcaster:
    """实时广播器"""

    def __init__(self):
        self.broadcast_queue = asyncio.Queue()
        self.is_running = False

    async def start(self) -> None:
        """启动广播器"""
        if not self.is_running:
            self.is_running = True
            asyncio.create_task(self._broadcast_worker())
            logger.log_result("实时广播器启动", "广播器已启动")

    async def stop(self) -> None:
        """停止广播器"""
        self.is_running = False
        logger.log_result("实时广播器停止", "广播器已停止")

    async def _broadcast_worker(self) -> None:
        """广播工作线程"""
        while self.is_running:
            try:
                # 从队列中获取消息
                message = await asyncio.wait_for(
                    self.broadcast_queue.get(), timeout=1.0
                )
                await self._process_broadcast_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.log_result("广播工作线程错误", f"错误: {str(e)}")

    async def _process_broadcast_message(
        self, message: WebSocketMessage
    ) -> None:
        """处理广播消息"""
        try:
            if message.type == WebSocketMessageType.SEARCH_PROGRESS:
                # 搜索进度广播
                task_id = message.data.get("task_id") if message.data else None
                if task_id:
                    await connection_manager.broadcast_to_task_subscribers(
                        task_id, message
                    )

            elif message.type == WebSocketMessageType.SEARCH_RESULTS:
                # 搜索结果广播
                task_id = message.data.get("task_id") if message.data else None
                if task_id:
                    await connection_manager.broadcast_to_task_subscribers(
                        task_id, message
                    )

            elif message.type == WebSocketMessageType.TASK_PROGRESS:
                # 任务进度广播
                task_id = message.data.get("task_id") if message.data else None
                if task_id:
                    await connection_manager.broadcast_to_task_subscribers(
                        task_id, message
                    )

            elif message.type == WebSocketMessageType.SYSTEM_NOTIFICATION:
                # 系统通知广播
                await connection_manager.broadcast_message(message)

            else:
                # 默认广播给所有连接
                await connection_manager.broadcast_message(message)

        except Exception as e:
            logger.log_result("处理广播消息失败", f"错误: {str(e)}")

    async def broadcast_progress_update(
        self, task_id: str, progress: float, message: str, **kwargs
    ) -> None:
        """广播进度更新"""
        try:
            progress_data = {
                "task_id": task_id,
                "progress_percentage": progress,
                "current_step": kwargs.get("current_step", ""),
                "message": message,
                "total_sources": kwargs.get("total_sources"),
                "completed_sources": kwargs.get("completed_sources"),
                "cars_found": kwargs.get("cars_found"),
            }

            progress_message = SearchProgressMessage(**progress_data)

            ws_message = WebSocketMessage(
                type=WebSocketMessageType.SEARCH_PROGRESS,
                timestamp=datetime.now(),
                data=progress_message.model_dump(),
            )

            await self.broadcast_queue.put(ws_message)

        except Exception as e:
            logger.log_result(
                "广播进度更新失败", f"任务ID: {task_id}, 错误: {str(e)}"
            )

    async def broadcast_search_results(
        self,
        task_id: str,
        results: List[CarListing],
        search_duration: float = 0.0,
        message: str = "搜索完成",
    ) -> None:
        """广播搜索结果"""
        try:
            # 转换CarListing为字典
            cars_data = []
            for car in results:
                cars_data.append(
                    car.model_dump() if hasattr(car, "model_dump") else car
                )

            results_data = {
                "task_id": task_id,
                "cars": cars_data,
                "total_count": len(results),
                "search_duration": search_duration,
                "message": message,
            }

            results_message = SearchResultsMessage(**results_data)

            ws_message = WebSocketMessage(
                type=WebSocketMessageType.SEARCH_RESULTS,
                timestamp=datetime.now(),
                data=results_message.model_dump(),
            )

            await self.broadcast_queue.put(ws_message)

        except Exception as e:
            logger.log_result(
                "广播搜索结果失败", f"任务ID: {task_id}, 错误: {str(e)}"
            )

    async def broadcast_error(
        self,
        task_id: str,
        error: str,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """广播错误消息"""
        try:
            error_data = {
                "task_id": task_id,
                "status": "failed",
                "message": error,
                "error": error,
                "result": error_details,
            }

            status_message = TaskStatusMessage(**error_data)

            ws_message = WebSocketMessage(
                type=WebSocketMessageType.TASK_ERROR,
                timestamp=datetime.now(),
                data=status_message.model_dump(),
            )

            await self.broadcast_queue.put(ws_message)

        except Exception as e:
            logger.log_result(
                "广播错误消息失败", f"任务ID: {task_id}, 错误: {str(e)}"
            )

    async def broadcast_task_start(
        self, task_id: str, message: str = "任务开始"
    ) -> None:
        """广播任务开始"""
        try:
            status_data = {
                "task_id": task_id,
                "status": "started",
                "message": message,
                "progress": 0.0,
            }

            status_message = TaskStatusMessage(**status_data)

            ws_message = WebSocketMessage(
                type=WebSocketMessageType.TASK_START,
                timestamp=datetime.now(),
                data=status_message.model_dump(),
            )

            await self.broadcast_queue.put(ws_message)

        except Exception as e:
            logger.log_result(
                "广播任务开始失败", f"任务ID: {task_id}, 错误: {str(e)}"
            )

    async def broadcast_task_complete(
        self,
        task_id: str,
        message: str = "任务完成",
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """广播任务完成"""
        try:
            status_data = {
                "task_id": task_id,
                "status": "completed",
                "message": message,
                "progress": 100.0,
                "result": result,
            }

            status_message = TaskStatusMessage(**status_data)

            ws_message = WebSocketMessage(
                type=WebSocketMessageType.TASK_COMPLETE,
                timestamp=datetime.now(),
                data=status_message.model_dump(),
            )

            await self.broadcast_queue.put(ws_message)

        except Exception as e:
            logger.log_result(
                "广播任务完成失败", f"任务ID: {task_id}, 错误: {str(e)}"
            )

    async def broadcast_system_notification(
        self,
        notification_type: str,
        title: str,
        message: str,
        level: str = "info",
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """广播系统通知"""
        try:
            notification_data = {
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "level": level,
                "timestamp": datetime.now(),
                "data": data,
            }

            notification_message = SystemNotificationMessage(
                **notification_data
            )

            ws_message = WebSocketMessage(
                type=WebSocketMessageType.SYSTEM_NOTIFICATION,
                timestamp=datetime.now(),
                data=notification_message.model_dump(),
            )

            await self.broadcast_queue.put(ws_message)

        except Exception as e:
            logger.log_result("广播系统通知失败", f"错误: {str(e)}")

    async def broadcast_conversation_message(
        self,
        session_id: str,
        message: str,
        is_user: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """广播对话消息"""
        try:
            conversation_data = {
                "session_id": session_id,
                "message": message,
                "is_user": is_user,
                "timestamp": datetime.now(),
                "metadata": metadata,
            }

            ws_message = WebSocketMessage(
                type=WebSocketMessageType.CONVERSATION_MESSAGE,
                timestamp=datetime.now(),
                data=conversation_data,
            )

            await connection_manager.broadcast_to_session_subscribers(
                session_id, ws_message
            )

        except Exception as e:
            logger.log_result(
                "广播对话消息失败", f"会话ID: {session_id}, 错误: {str(e)}"
            )

    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self.broadcast_queue.qsize()

    def get_active_connections_count(self) -> int:
        """获取活跃连接数"""
        return connection_manager.get_active_connections_count()


# 全局实时广播器实例
realtime_broadcaster = RealtimeBroadcaster()
