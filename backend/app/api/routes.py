from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.schemas import SearchRequest, SearchResponse
from app.services.search_service import SearchService
from app.utils.logger import logger

router = APIRouter()
search_service = SearchService()


class FrontendLogRequest(BaseModel):
    message: str
    sequence: str
    callStack: str
    timestamp: str


@router.post("/search", response_model=SearchResponse)
async def search_cars(request: SearchRequest):
    """
    搜索车源接口
    
    - **query**: 用户的自然语言查询，支持中英文
    - 返回匹配的车源列表
    """
    # 关键部位日志：API入口点
    logger.log_result("开始搜索请求", f"用户输入: {request.query}")
    
    try:
        # 输入验证
        if not request.query.strip():
            logger.log_result("查询失败", "查询内容为空")
            raise HTTPException(status_code=400, detail="查询内容不能为空")
        
        # 检查是否为有效购车查询
        query_lower = request.query.lower().strip()
        invalid_patterns = [
            "你妈", "傻逼", "垃圾", "滚", "操", "fuck", "shit",
            "测试", "test", "123", "abc", "hello", "hi"
        ]
        
        if any(pattern in query_lower for pattern in invalid_patterns):
            logger.log_result("查询失败", f"无效查询内容: {request.query}")
            raise HTTPException(
                status_code=400,
                detail="请输入有效的购车需求，如：'我想买一辆20万左右的SUV'"
            )
        
        # 检查查询长度
        if len(request.query.strip()) < 3:
            logger.log_result("查询失败", "查询内容过短")
            raise HTTPException(
                status_code=400,
                detail="查询内容过短，请提供更详细的购车需求"
            )
        
        # 关键部位日志：外部调用
        result = await search_service.search_cars(request)
        
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


@router.post("/logs/frontend")
async def receive_frontend_log(log_request: FrontendLogRequest):
    """
    接收前端日志
    遵循设计文档规范：时间戳 | 执行序号 | 包名.方法名:行号 | 结论 - 原因
    """
    # 将前端日志写入文件
    import os
    # 获取backend目录下的logs文件夹
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    logs_dir = os.path.join(backend_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    frontend_log_path = os.path.join(logs_dir, 'frontend.log')
    with open(frontend_log_path, 'a', encoding='utf-8') as f:
        # 遵循设计文档格式：时间戳 | 执行序号 | 包名.方法名:行号 | 结论 - 原因
        f.write(
            f"{log_request.timestamp} | {log_request.sequence} | "
            f"{log_request.callStack} | {log_request.message}\n"
        )
    
    return {"status": "success"}
