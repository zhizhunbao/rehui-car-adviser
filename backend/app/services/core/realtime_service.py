import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.schemas import CarListing, ParsedQuery, SearchRequest
from app.services.core.search_service import SearchService
from app.utils.core.logger import logger
from app.utils.websocket import connection_manager, realtime_broadcaster


class RealtimeService:
    """实时数据推送服务"""

    def __init__(self):
        self.search_service = SearchService()
        self.active_tasks: Dict[str, Dict[str, Any]] = {}

    async def start_realtime_search(
        self, request: SearchRequest, client_ip: str, task_id: str = None
    ) -> str:
        """启动实时搜索任务"""
        if not task_id:
            task_id = str(uuid.uuid4())

        # 记录任务信息
        self.active_tasks[task_id] = {
            "request": request,
            "client_ip": client_ip,
            "started_at": datetime.now(),
            "status": "started",
            "progress": 0.0,
        }

        # 广播任务开始
        await realtime_broadcaster.broadcast_task_start(
            task_id, f"开始搜索: {request.query}"
        )

        # 启动搜索任务
        asyncio.create_task(self._execute_realtime_search(task_id))

        logger.log_result(
            "实时搜索任务启动", f"任务ID: {task_id}, 查询: {request.query}"
        )
        return task_id

    async def _execute_realtime_search(self, task_id: str) -> None:
        """执行实时搜索任务"""
        try:
            task_info = self.active_tasks.get(task_id)
            if not task_info:
                await realtime_broadcaster.broadcast_error(
                    task_id, "任务信息不存在"
                )
                return

            request = task_info["request"]
            client_ip = task_info["client_ip"]

            # 更新任务状态
            self.active_tasks[task_id]["status"] = "in_progress"

            # 广播进度更新 - 开始解析查询
            await realtime_broadcaster.broadcast_progress_update(
                task_id,
                10.0,
                "正在解析用户查询...",
                current_step="parsing_query",
            )

            # 解析用户查询
            parsed_query = await self._parse_query_with_progress(
                request.query, task_id
            )

            # 广播进度更新 - 开始搜索
            await realtime_broadcaster.broadcast_progress_update(
                task_id, 30.0, "开始搜索车源...", current_step="searching_cars"
            )

            # 执行搜索
            search_results = await self._search_cars_with_progress(
                parsed_query, task_id
            )

            # 广播进度更新 - 分析结果
            await realtime_broadcaster.broadcast_progress_update(
                task_id,
                80.0,
                "正在分析搜索结果...",
                current_step="analyzing_results",
            )

            # 分析结果
            analyzed_results = await self._analyze_results_with_progress(
                search_results, request.query, task_id
            )

            # 广播进度更新 - 完成
            await realtime_broadcaster.broadcast_progress_update(
                task_id, 100.0, "搜索完成", current_step="completed"
            )

            # 广播搜索结果
            await realtime_broadcaster.broadcast_search_results(
                task_id,
                analyzed_results,
                search_duration=0.0,
                message="搜索完成",
            )

            # 广播任务完成
            await realtime_broadcaster.broadcast_task_complete(
                task_id, "搜索任务完成", {"total_cars": len(analyzed_results)}
            )

            # 更新任务状态
            self.active_tasks[task_id]["status"] = "completed"
            self.active_tasks[task_id]["progress"] = 100.0
            self.active_tasks[task_id]["completed_at"] = datetime.now()

            logger.log_result(
                "实时搜索任务完成",
                f"任务ID: {task_id}, 结果数量: {len(analyzed_results)}",
            )

        except Exception as e:
            # 广播错误
            await realtime_broadcaster.broadcast_error(
                task_id, f"搜索过程中发生错误: {str(e)}"
            )

            # 更新任务状态
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "failed"
                self.active_tasks[task_id]["error"] = str(e)
                self.active_tasks[task_id]["failed_at"] = datetime.now()

            logger.log_result(
                "实时搜索任务失败", f"任务ID: {task_id}, 错误: {str(e)}"
            )

    async def _parse_query_with_progress(
        self, query: str, task_id: str
    ) -> ParsedQuery:
        """解析查询并更新进度"""
        try:
            # 模拟解析过程
            await asyncio.sleep(0.5)  # 模拟处理时间

            # 广播进度更新
            await realtime_broadcaster.broadcast_progress_update(
                task_id, 20.0, "查询解析完成", current_step="parsing_completed"
            )

            # 调用实际的解析服务
            parsed_query = await self.search_service.parse_user_query(query)
            return parsed_query

        except Exception as e:
            await realtime_broadcaster.broadcast_progress_update(
                task_id,
                20.0,
                f"查询解析失败: {str(e)}",
                current_step="parsing_failed",
            )
            raise

    async def _search_cars_with_progress(
        self, parsed_query: ParsedQuery, task_id: str
    ) -> List[CarListing]:
        """搜索车源并更新进度"""
        try:
            # 模拟搜索过程
            await asyncio.sleep(1.0)  # 模拟处理时间

            # 广播进度更新
            await realtime_broadcaster.broadcast_progress_update(
                task_id,
                50.0,
                "正在搜索CarGurus...",
                current_step="searching_cargurus",
            )

            await asyncio.sleep(0.5)

            await realtime_broadcaster.broadcast_progress_update(
                task_id,
                60.0,
                "正在搜索Kijiji...",
                current_step="searching_kijiji",
            )

            await asyncio.sleep(0.5)

            await realtime_broadcaster.broadcast_progress_update(
                task_id,
                70.0,
                "正在搜索AutoTrader...",
                current_step="searching_autotrader",
            )

            # 调用实际的搜索服务
            search_results = (
                await self.search_service.search_cars_from_sources(
                    parsed_query
                )
            )

            # 广播进度更新
            await realtime_broadcaster.broadcast_progress_update(
                task_id,
                75.0,
                f"找到 {len(search_results)} 辆车源",
                current_step="search_completed",
                cars_found=len(search_results),
            )

            return search_results

        except Exception as e:
            await realtime_broadcaster.broadcast_progress_update(
                task_id,
                70.0,
                f"搜索失败: {str(e)}",
                current_step="search_failed",
            )
            raise

    async def _analyze_results_with_progress(
        self, results: List[CarListing], query: str, task_id: str
    ) -> List[CarListing]:
        """分析结果并更新进度"""
        try:
            # 模拟分析过程
            await asyncio.sleep(0.5)  # 模拟处理时间

            # 广播进度更新
            await realtime_broadcaster.broadcast_progress_update(
                task_id,
                85.0,
                "正在计算推荐分数...",
                current_step="calculating_scores",
            )

            await asyncio.sleep(0.3)

            await realtime_broadcaster.broadcast_progress_update(
                task_id,
                90.0,
                "正在排序结果...",
                current_step="sorting_results",
            )

            # 调用实际的分析服务
            analyzed_results = await self.search_service.analyze_car_listings(
                results, query
            )

            # 广播进度更新
            await realtime_broadcaster.broadcast_progress_update(
                task_id, 95.0, "分析完成", current_step="analysis_completed"
            )

            return analyzed_results

        except Exception as e:
            await realtime_broadcaster.broadcast_progress_update(
                task_id,
                90.0,
                f"分析失败: {str(e)}",
                current_step="analysis_failed",
            )
            raise

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        return self.active_tasks.get(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["status"] = "cancelled"
            self.active_tasks[task_id]["cancelled_at"] = datetime.now()

            # 广播任务取消
            await realtime_broadcaster.broadcast_error(task_id, "任务已取消")

            logger.log_result("任务已取消", f"任务ID: {task_id}")
            return True
        return False

    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """获取所有活跃任务"""
        return list(self.active_tasks.values())

    async def cleanup_completed_tasks(self, max_age_hours: int = 24) -> int:
        """清理已完成的任务"""
        current_time = datetime.now()
        cleaned_count = 0

        tasks_to_remove = []
        for task_id, task_info in self.active_tasks.items():
            if task_info["status"] in ["completed", "failed", "cancelled"]:
                completed_at = (
                    task_info.get("completed_at")
                    or task_info.get("failed_at")
                    or task_info.get("cancelled_at")
                )
                if (
                    completed_at
                    and (current_time - completed_at).total_seconds()
                    > max_age_hours * 3600
                ):
                    tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self.active_tasks[task_id]
            cleaned_count += 1

        if cleaned_count > 0:
            logger.log_result(
                "清理已完成任务", f"清理了 {cleaned_count} 个任务"
            )

        return cleaned_count

    async def broadcast_system_status(self) -> None:
        """广播系统状态"""
        try:
            active_connections = (
                connection_manager.get_active_connections_count()
            )
            active_tasks = len(
                [
                    t
                    for t in self.active_tasks.values()
                    if t["status"] == "in_progress"
                ]
            )
            queue_size = realtime_broadcaster.get_queue_size()

            status_data = {
                "active_connections": active_connections,
                "active_tasks": active_tasks,
                "queue_size": queue_size,
                "timestamp": datetime.now().isoformat(),
            }

            await realtime_broadcaster.broadcast_system_notification(
                "system_status",
                "系统状态更新",
                f"活跃连接: {active_connections}, 活跃任务: {active_tasks}, 队列大小: {queue_size}",
                "info",
                status_data,
            )

        except Exception as e:
            logger.log_result("广播系统状态失败", f"错误: {str(e)}")


# 全局实时服务实例
realtime_service = RealtimeService()
