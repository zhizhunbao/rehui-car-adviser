from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

from app.models.schemas import (
    WebSocketConnectionInfo,
    WebSocketMessage,
    WebSocketMessageType,
)
from app.utils.core.logger import logger


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # 存储活跃连接: client_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # 存储连接信息: client_id -> ConnectionInfo
        self.connection_info: Dict[str, WebSocketConnectionInfo] = {}
        # 存储任务订阅: task_id -> Set[client_id]
        self.task_subscriptions: Dict[str, Set[str]] = {}
        # 存储会话订阅: session_id -> Set[client_id]
        self.session_subscriptions: Dict[str, Set[str]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        user_agent: str = None,
        ip_address: str = None,
    ) -> None:
        """建立WebSocket连接"""
        try:
            await websocket.accept()
            self.active_connections[client_id] = websocket

            # 记录连接信息
            self.connection_info[client_id] = WebSocketConnectionInfo(
                client_id=client_id,
                connected_at=datetime.now(),
                user_agent=user_agent,
                ip_address=ip_address,
                is_active=True,
            )

            # 发送连接成功消息
            await self.send_message(
                client_id,
                WebSocketMessage(
                    type=WebSocketMessageType.CONNECT,
                    timestamp=datetime.now(),
                    message="连接成功",
                    client_id=client_id,
                ),
            )

            logger.log_result(
                "WebSocket连接建立", f"客户端ID: {client_id}, IP: {ip_address}"
            )

        except Exception as e:
            logger.log_result(
                "WebSocket连接失败", f"客户端ID: {client_id}, 错误: {str(e)}"
            )
            raise

    def disconnect(self, client_id: str) -> None:
        """断开WebSocket连接"""
        try:
            # 移除活跃连接
            if client_id in self.active_connections:
                del self.active_connections[client_id]

            # 更新连接信息
            if client_id in self.connection_info:
                self.connection_info[client_id].is_active = False

            # 清理订阅
            self._cleanup_subscriptions(client_id)

            logger.log_result("WebSocket连接断开", f"客户端ID: {client_id}")

        except Exception as e:
            logger.log_result(
                "WebSocket断开失败", f"客户端ID: {client_id}, 错误: {str(e)}"
            )

    async def send_message(
        self, client_id: str, message: WebSocketMessage
    ) -> bool:
        """发送消息给指定客户端"""
        try:
            if client_id in self.active_connections:
                websocket = self.active_connections[client_id]
                await websocket.send_text(message.model_dump_json())
                return True
            return False
        except WebSocketDisconnect:
            self.disconnect(client_id)
            return False
        except Exception as e:
            logger.log_result(
                "发送WebSocket消息失败",
                f"客户端ID: {client_id}, 错误: {str(e)}",
            )
            return False

    async def broadcast_message(
        self, message: WebSocketMessage, exclude_clients: List[str] = None
    ) -> int:
        """广播消息给所有连接的客户端"""
        exclude_clients = exclude_clients or []
        sent_count = 0

        for client_id in list(self.active_connections.keys()):
            if client_id not in exclude_clients:
                if await self.send_message(client_id, message):
                    sent_count += 1

        return sent_count

    async def broadcast_to_task_subscribers(
        self, task_id: str, message: WebSocketMessage
    ) -> int:
        """广播消息给任务订阅者"""
        if task_id not in self.task_subscriptions:
            return 0

        sent_count = 0
        for client_id in list(self.task_subscriptions[task_id]):
            if await self.send_message(client_id, message):
                sent_count += 1

        return sent_count

    async def broadcast_to_session_subscribers(
        self, session_id: str, message: WebSocketMessage
    ) -> int:
        """广播消息给会话订阅者"""
        if session_id not in self.session_subscriptions:
            return 0

        sent_count = 0
        for client_id in list(self.session_subscriptions[session_id]):
            if await self.send_message(client_id, message):
                sent_count += 1

        return sent_count

    def subscribe_to_task(self, client_id: str, task_id: str) -> None:
        """订阅任务更新"""
        if task_id not in self.task_subscriptions:
            self.task_subscriptions[task_id] = set()
        self.task_subscriptions[task_id].add(client_id)

    def unsubscribe_from_task(self, client_id: str, task_id: str) -> None:
        """取消订阅任务更新"""
        if task_id in self.task_subscriptions:
            self.task_subscriptions[task_id].discard(client_id)
            if not self.task_subscriptions[task_id]:
                del self.task_subscriptions[task_id]

    def subscribe_to_session(self, client_id: str, session_id: str) -> None:
        """订阅会话更新"""
        if session_id not in self.session_subscriptions:
            self.session_subscriptions[session_id] = set()
        self.session_subscriptions[session_id].add(client_id)

    def unsubscribe_from_session(
        self, client_id: str, session_id: str
    ) -> None:
        """取消订阅会话更新"""
        if session_id in self.session_subscriptions:
            self.session_subscriptions[session_id].discard(client_id)
            if not self.session_subscriptions[session_id]:
                del self.session_subscriptions[session_id]

    def _cleanup_subscriptions(self, client_id: str) -> None:
        """清理客户端的所有订阅"""
        # 清理任务订阅
        for task_id in list(self.task_subscriptions.keys()):
            self.task_subscriptions[task_id].discard(client_id)
            if not self.task_subscriptions[task_id]:
                del self.task_subscriptions[task_id]

        # 清理会话订阅
        for session_id in list(self.session_subscriptions.keys()):
            self.session_subscriptions[session_id].discard(client_id)
            if not self.session_subscriptions[session_id]:
                del self.session_subscriptions[session_id]

    def get_active_connections_count(self) -> int:
        """获取活跃连接数"""
        return len(self.active_connections)

    def get_connection_info(
        self, client_id: str
    ) -> Optional[WebSocketConnectionInfo]:
        """获取连接信息"""
        return self.connection_info.get(client_id)

    def get_all_connections_info(self) -> List[WebSocketConnectionInfo]:
        """获取所有连接信息"""
        return list(self.connection_info.values())

    async def ping_all_connections(self) -> int:
        """向所有连接发送ping"""
        ping_message = WebSocketMessage(
            type=WebSocketMessageType.PING,
            timestamp=datetime.now(),
            message="ping",
        )

        sent_count = 0
        for client_id in list(self.active_connections.keys()):
            if await self.send_message(client_id, ping_message):
                sent_count += 1
                # 更新ping时间
                if client_id in self.connection_info:
                    self.connection_info[client_id].last_ping = datetime.now()

        return sent_count


# 全局连接管理器实例
connection_manager = ConnectionManager()
