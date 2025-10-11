import uuid
from typing import Optional

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)

from app.models.schemas import (
    SearchRequest,
    WebSocketMessage,
    WebSocketMessageType,
)
from app.services.core.realtime_service import realtime_service
from app.utils.core.logger import logger
from app.utils.websocket import (
    connection_manager,
    message_handler,
    realtime_broadcaster,
)

router = APIRouter()


def get_client_ip(request: Request) -> str:
    """获取客户端真实IP地址"""
    # 优先检查 X-Forwarded-For 头部
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
        if client_ip and client_ip != "unknown":
            return client_ip

    # 检查 X-Real-IP 头部
    real_ip = request.headers.get("X-Real-IP")
    if real_ip and real_ip != "unknown":
        return real_ip

    # 最后使用直接连接IP
    if request.client and request.client.host:
        return request.client.host

    return "unknown"


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, client_id: Optional[str] = None
):
    """WebSocket连接端点"""
    # 生成客户端ID
    if not client_id:
        client_id = str(uuid.uuid4())

    # 获取客户端IP
    client_ip = get_client_ip(websocket)
    user_agent = websocket.headers.get("user-agent", "unknown")

    try:
        # 建立连接
        await connection_manager.connect(
            websocket, client_id, user_agent, client_ip
        )

        # 启动实时广播器（如果尚未启动）
        if not realtime_broadcaster.is_running:
            await realtime_broadcaster.start()

        logger.log_result(
            "WebSocket连接建立", f"客户端ID: {client_id}, IP: {client_ip}"
        )

        # 消息处理循环
        while True:
            try:
                # 接收消息
                message = await websocket.receive_text()

                # 处理消息
                await message_handler.handle_message(
                    websocket, message, client_id
                )

            except WebSocketDisconnect:
                logger.log_result(
                    "WebSocket连接断开", f"客户端ID: {client_id}"
                )
                break
            except Exception as e:
                logger.log_result(
                    "WebSocket消息处理错误",
                    f"客户端ID: {client_id}, 错误: {str(e)}",
                )

                # 发送错误消息
                error_message = WebSocketMessage(
                    type=WebSocketMessageType.ERROR,
                    message=f"消息处理错误: {str(e)}",
                    client_id=client_id,
                )
                await websocket.send_text(error_message.model_dump_json())

    except Exception as e:
        logger.log_result(
            "WebSocket连接错误", f"客户端ID: {client_id}, 错误: {str(e)}"
        )
    finally:
        # 断开连接
        connection_manager.disconnect(client_id)


@router.websocket("/ws/{client_id}")
async def websocket_endpoint_with_id(websocket: WebSocket, client_id: str):
    """带客户端ID的WebSocket连接端点"""
    await websocket_endpoint(websocket, client_id)


@router.post("/ws/search")
async def start_realtime_search(request: SearchRequest, http_request: Request):
    """启动实时搜索任务"""
    try:
        # 获取客户端IP
        client_ip = get_client_ip(http_request)

        # 启动实时搜索
        task_id = await realtime_service.start_realtime_search(
            request, client_ip
        )

        logger.log_result(
            "实时搜索任务启动", f"任务ID: {task_id}, 查询: {request.query}"
        )

        return {
            "success": True,
            "task_id": task_id,
            "message": "实时搜索任务已启动",
        }

    except Exception as e:
        logger.log_result("启动实时搜索失败", f"错误: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"启动实时搜索失败: {str(e)}"
        )


@router.get("/ws/task/{task_id}/status")
async def get_task_status(task_id: str):
    """获取任务状态"""
    try:
        task_status = await realtime_service.get_task_status(task_id)

        if not task_status:
            raise HTTPException(status_code=404, detail="任务不存在")

        return {"success": True, "task_status": task_status}

    except HTTPException:
        raise
    except Exception as e:
        logger.log_result(
            "获取任务状态失败", f"任务ID: {task_id}, 错误: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"获取任务状态失败: {str(e)}"
        )


@router.post("/ws/task/{task_id}/cancel")
async def cancel_task(task_id: str):
    """取消任务"""
    try:
        success = await realtime_service.cancel_task(task_id)

        if not success:
            raise HTTPException(status_code=404, detail="任务不存在")

        return {"success": True, "message": "任务已取消"}

    except HTTPException:
        raise
    except Exception as e:
        logger.log_result("取消任务失败", f"任务ID: {task_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


@router.get("/ws/tasks")
async def get_active_tasks():
    """获取所有活跃任务"""
    try:
        tasks = await realtime_service.get_active_tasks()

        return {"success": True, "tasks": tasks, "total_count": len(tasks)}

    except Exception as e:
        logger.log_result("获取活跃任务失败", f"错误: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"获取活跃任务失败: {str(e)}"
        )


@router.get("/ws/connections")
async def get_connections_info():
    """获取连接信息"""
    try:
        connections = connection_manager.get_all_connections_info()
        active_count = connection_manager.get_active_connections_count()

        return {
            "success": True,
            "active_connections": active_count,
            "connections": connections,
        }

    except Exception as e:
        logger.log_result("获取连接信息失败", f"错误: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"获取连接信息失败: {str(e)}"
        )


@router.post("/ws/system/status")
async def broadcast_system_status():
    """广播系统状态"""
    try:
        await realtime_service.broadcast_system_status()

        return {"success": True, "message": "系统状态已广播"}

    except Exception as e:
        logger.log_result("广播系统状态失败", f"错误: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"广播系统状态失败: {str(e)}"
        )


@router.post("/ws/cleanup")
async def cleanup_completed_tasks(max_age_hours: int = 24):
    """清理已完成的任务"""
    try:
        cleaned_count = await realtime_service.cleanup_completed_tasks(
            max_age_hours
        )

        return {
            "success": True,
            "cleaned_count": cleaned_count,
            "message": f"已清理 {cleaned_count} 个已完成的任务",
        }

    except Exception as e:
        logger.log_result("清理任务失败", f"错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清理任务失败: {str(e)}")


@router.post("/ws/ping")
async def ping_all_connections():
    """向所有连接发送ping"""
    try:
        sent_count = await connection_manager.ping_all_connections()

        return {
            "success": True,
            "sent_count": sent_count,
            "message": f"已向 {sent_count} 个连接发送ping",
        }

    except Exception as e:
        logger.log_result("发送ping失败", f"错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"发送ping失败: {str(e)}")
