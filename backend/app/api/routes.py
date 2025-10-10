from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.models.schemas import (
    ConversationRequest,
    ConversationResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.core.search_service import SearchService
from app.services.data.car_data_service import car_data_service
from app.utils.core.logger import logger

router = APIRouter()
search_service = None


def get_search_service():
    """懒加载搜索服务，避免reload时重复初始化"""
    global search_service
    if search_service is None:
        search_service = SearchService()
    return search_service


def get_client_ip(request: Request) -> str:
    """
    获取客户端真实IP地址
    处理代理、负载均衡器等场景
    """
    # 优先检查 X-Forwarded-For 头部（代理服务器设置）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For 可能包含多个IP，取第一个
        client_ip = forwarded_for.split(",")[0].strip()
        if client_ip and client_ip != "unknown":
            return client_ip

    # 检查 X-Real-IP 头部（Nginx等设置）
    real_ip = request.headers.get("X-Real-IP")
    if real_ip and real_ip != "unknown":
        return real_ip

    # 检查 X-Forwarded 头部
    forwarded = request.headers.get("X-Forwarded")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # 最后使用直接连接IP
    if request.client and request.client.host:
        return request.client.host

    return "unknown"


class FrontendLogRequest(BaseModel):
    message: str
    sequence: str
    callStack: str
    timestamp: str


class CarDataResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


@router.post("/search", response_model=SearchResponse)
async def search_cars(request: SearchRequest, http_request: Request):
    """
    搜索车源接口

    - **query**: 用户的自然语言查询，支持中英文
    - 返回匹配的车源列表
    """
    # 获取客户端IP地址
    client_ip = get_client_ip(http_request)

    # 关键部位日志：API入口点
    logger.log_result(
        "开始搜索请求", f"用户输入: {request.query}, IP: {client_ip}"
    )

    try:
        # 输入验证
        if not request.query.strip():
            logger.log_result("查询失败", "查询内容为空")
            raise HTTPException(status_code=400, detail="查询内容不能为空")

        # 检查是否为有效购车查询
        query_lower = request.query.lower().strip()
        invalid_patterns = [
            "你妈",
            "傻逼",
            "垃圾",
            "滚",
            "操",
            "fuck",
            "shit",
            "测试",
            "test",
            "123",
            "abc",
            "hello",
            "hi",
        ]

        if any(pattern in query_lower for pattern in invalid_patterns):
            logger.log_result("查询失败", f"无效查询内容: {request.query}")
            raise HTTPException(
                status_code=400,
                detail="请输入有效的购车需求，如：'我想买一辆20万左右的SUV'",
            )

        # 检查查询长度
        if len(request.query.strip()) < 3:
            logger.log_result("查询失败", "查询内容过短")
            raise HTTPException(
                status_code=400, detail="查询内容过短，请提供更详细的购车需求"
            )

        # 关键部位日志：外部调用
        result = await get_search_service().search_cars(request, client_ip)

        if result.success:
            logger.log_result("搜索成功", f"返回{result.total_count}条结果")
        else:
            logger.log_result("搜索失败", f"错误: {result.error}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.log_result("搜索失败", f"未预期错误: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"服务器内部错误: {str(e)}"
        )


@router.post("/conversation", response_model=ConversationResponse)
async def start_conversation(
    request: ConversationRequest, http_request: Request
):
    """
    对话式搜索接口

    - **message**: 用户消息
    - **session_id**: 会话ID（可选）
    - **conversation_history**: 对话历史（可选）
    - 返回AI回复和搜索结果
    """
    # 获取客户端IP地址
    client_ip = get_client_ip(http_request)

    # 关键部位日志：API入口点
    logger.log_result(
        "开始对话请求", f"用户消息: {request.message[:50]}..., IP: {client_ip}"
    )

    try:
        # 输入验证
        if not request.message.strip():
            logger.log_result("对话失败", "消息内容为空")
            raise HTTPException(status_code=400, detail="消息内容不能为空")

        # 检查消息长度
        if len(request.message.strip()) < 1:
            logger.log_result("对话失败", "消息内容过短")
            raise HTTPException(
                status_code=400, detail="消息内容过短，请输入有效的消息"
            )

        # 关键部位日志：外部调用
        result = await get_search_service().start_conversation(
            request, client_ip
        )

        if result.success:
            logger.log_result("对话成功", f"AI回复长度: {len(result.message)}")
        else:
            logger.log_result("对话失败", f"错误: {result.error}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        error_traceback = traceback.format_exc()
        logger.log_result(
            "对话失败", f"未预期错误: {str(e)}\n堆栈追踪:\n{error_traceback}"
        )
        raise HTTPException(
            status_code=500, detail=f"服务器内部错误: {str(e)}"
        )


@router.post("/logs/frontend")
async def receive_frontend_log(
    log_request: FrontendLogRequest, http_request: Request
):
    """
    接收前端日志
    遵循设计文档规范：时间戳 | 执行序号 | 包名.方法名:行号 | 结论 - 原因
    """
    # 获取客户端IP地址
    client_ip = get_client_ip(http_request)

    # 将前端日志写入文件
    from app.utils.core.path_util import get_frontend_log_path

    frontend_log_path = get_frontend_log_path()
    with open(frontend_log_path, "a", encoding="utf-8") as f:
        # 遵循设计文档格式：时间戳 | 执行序号 | 包名.方法名:行号 | 结论 - 原因 | IP地址
        f.write(
            f"{log_request.timestamp} | {log_request.sequence} | "
            f"{log_request.callStack} | {log_request.message} | IP: {client_ip}\n"
        )

    return {"status": "success"}


@router.post("/search/database", response_model=SearchResponse)
async def search_cars_with_database(
    request: SearchRequest, http_request: Request
):
    """
    带数据库存储的车源搜索接口
    """
    # 获取客户端IP地址
    client_ip = get_client_ip(http_request)

    try:
        logger.log_result(
            "开始数据库搜索请求", f"用户输入: {request.query}, IP: {client_ip}"
        )
        service = get_search_service()
        result = await service.search_cars_with_database_storage(
            request, client_ip
        )
        return result
    except Exception as e:
        logger.log_result(
            "数据库搜索接口错误", f"错误: {str(e)}, IP: {client_ip}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/database/update")
async def update_database_from_platforms(
    make_name: str = "Toyota", http_request: Request = None
):
    """
    从平台更新数据库车源数据
    """
    # 获取客户端IP地址
    client_ip = get_client_ip(http_request) if http_request else "unknown"

    try:
        logger.log_result(
            "开始数据库更新请求", f"品牌: {make_name}, IP: {client_ip}"
        )
        service = get_search_service()
        result = await service.update_database_from_platforms(make_name)
        return result
    except Exception as e:
        logger.log_result(
            "数据库更新接口错误", f"错误: {str(e)}, IP: {client_ip}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/statistics")
async def get_database_statistics():
    """
    获取数据库统计信息
    """
    try:
        service = get_search_service()
        result = await service.get_database_statistics()
        return result
    except Exception as e:
        logger.log_result("获取统计信息接口错误", f"错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 汽车数据查询API ==========


@router.get("/car-data/makes", response_model=CarDataResponse)
async def get_all_makes():
    """
    获取所有汽车品牌列表
    """
    try:
        logger.log_result("获取汽车品牌列表", "API请求")
        makes = await car_data_service.get_all_makes()
        return CarDataResponse(success=True, data=makes)
    except Exception as e:
        logger.log_result("获取汽车品牌列表失败", str(e))
        return CarDataResponse(success=False, error=str(e))


@router.get("/car-data/makes/{make}/models", response_model=CarDataResponse)
async def get_models_by_make(make: str):
    """
    根据品牌获取型号列表
    """
    try:
        logger.log_result(f"获取{make}品牌型号列表", "API请求")
        models = await car_data_service.get_models_by_make(make)
        return CarDataResponse(success=True, data=models)
    except Exception as e:
        logger.log_result(f"获取{make}品牌型号列表失败", str(e))
        return CarDataResponse(success=False, error=str(e))


@router.get("/car-data/search/makes", response_model=CarDataResponse)
async def search_makes(keyword: str):
    """
    搜索汽车品牌
    """
    try:
        logger.log_result(f"搜索汽车品牌: {keyword}", "API请求")
        makes = await car_data_service.search_makes(keyword)
        return CarDataResponse(success=True, data=makes)
    except Exception as e:
        logger.log_result(f"搜索汽车品牌失败: {keyword}", str(e))
        return CarDataResponse(success=False, error=str(e))


@router.get("/car-data/search/models", response_model=CarDataResponse)
async def search_models(make: str, keyword: str):
    """
    搜索汽车型号
    """
    try:
        logger.log_result(f"搜索{make}品牌型号: {keyword}", "API请求")
        models = await car_data_service.search_models(make, keyword)
        return CarDataResponse(success=True, data=models)
    except Exception as e:
        logger.log_result(f"搜索汽车型号失败: {make} {keyword}", str(e))
        return CarDataResponse(success=False, error=str(e))


@router.get("/car-data/validate", response_model=CarDataResponse)
async def validate_make_model(make: str, model: str):
    """
    验证品牌和型号是否存在
    """
    try:
        logger.log_result(f"验证品牌型号: {make} {model}", "API请求")
        result = await car_data_service.validate_make_model(make, model)
        return CarDataResponse(success=True, data=result)
    except Exception as e:
        logger.log_result(f"验证品牌型号失败: {make} {model}", str(e))
        return CarDataResponse(success=False, error=str(e))


@router.get("/car-data/statistics", response_model=CarDataResponse)
async def get_car_data_statistics():
    """
    获取汽车数据统计信息
    """
    try:
        logger.log_result("获取汽车数据统计", "API请求")
        stats = await car_data_service.get_statistics()
        return CarDataResponse(success=True, data=stats)
    except Exception as e:
        logger.log_result("获取汽车数据统计失败", str(e))
        return CarDataResponse(success=False, error=str(e))
