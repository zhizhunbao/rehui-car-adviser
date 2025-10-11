from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CarListing(BaseModel):
    """车源信息模型"""

    id: str
    title: str
    price: str
    mileage: Optional[str] = None
    year: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    location: Optional[str] = None
    link: str
    image_url: Optional[str] = None
    platform: str = "cargurus"
    quality_score: Optional[float] = None
    price_score: Optional[float] = None
    year_score: Optional[float] = None
    mileage_score: Optional[float] = None
    overall_score: Optional[float] = None


class ParsedQuery(BaseModel):
    """解析后的查询参数"""

    make: Optional[str] = None
    model: Optional[str] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    mileage_max: Optional[int] = None
    location: Optional[str] = None
    keywords: Optional[List[str]] = None
    body_type: Optional[str] = None
    transmission: Optional[str] = None
    fuel_type: Optional[str] = None


class SearchStatus(str, Enum):
    """搜索状态枚举"""

    PENDING = "pending"  # 等待开始
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class ProgressEventType(str, Enum):
    """进度事件类型"""

    TASK_STARTED = "task_started"
    SOURCE_SEARCH_STARTED = "source_search_started"
    SOURCE_SEARCH_COMPLETED = "source_search_completed"
    SOURCE_SEARCH_FAILED = "source_search_failed"
    CARS_FOUND = "cars_found"
    CARS_SAVED = "cars_saved"
    ANALYSIS_STARTED = "analysis_started"
    RECOMMENDATION_READY = "recommendation_ready"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"


class ProgressEvent(BaseModel):
    """进度事件"""

    task_id: str
    event_type: ProgressEventType
    timestamp: datetime
    message: str
    data: Optional[Dict[str, Any]] = None
    progress_percentage: Optional[float] = None


class SearchTask(BaseModel):
    """搜索任务"""

    task_id: str
    user_id: Optional[str] = None
    parsed_query: ParsedQuery
    max_results: int = 20
    status: SearchStatus = SearchStatus.PENDING
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percentage: float = 0.0
    total_cars_found: int = 0
    total_cars_saved: int = 0
    sources_searched: List[str] = []
    sources_completed: List[str] = []
    error_message: Optional[str] = None


class SearchSource(BaseModel):
    """搜索源"""

    name: str
    display_name: str
    enabled: bool = True
    priority: int = 1  # 优先级，数字越小优先级越高


class CarRecommendation(BaseModel):
    """车源推荐"""

    car: CarListing
    score: float
    reasons: List[str]
    comparison_data: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    """搜索结果"""

    task_id: str
    total_cars_found: int
    total_cars_saved: int
    recommendations: List[CarRecommendation]
    search_summary: Dict[str, Any]
    completed_at: datetime


# API请求和响应模型
class SearchRequest(BaseModel):
    """搜索请求"""

    query: str


class SearchResponse(BaseModel):
    """搜索响应"""

    success: bool
    cars: List[CarListing]
    total_count: int
    message: str
    error: Optional[str] = None


class ConversationMessage(BaseModel):
    """对话消息"""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime


class ConversationRequest(BaseModel):
    """对话请求"""

    message: str
    session_id: Optional[str] = None
    conversation_history: Optional[List[ConversationMessage]] = None


class ConversationResponse(BaseModel):
    """对话响应"""

    success: bool
    message: str
    session_id: str
    conversation_history: List[ConversationMessage]
    should_search: Optional[bool] = False
    search_params: Optional[ParsedQuery] = None
    error: Optional[str] = None


# WebSocket 相关模型
class WebSocketMessageType(str, Enum):
    """WebSocket 消息类型"""

    # 连接管理
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"

    # 搜索相关
    SEARCH_START = "search_start"
    SEARCH_PROGRESS = "search_progress"
    SEARCH_RESULTS = "search_results"
    SEARCH_ERROR = "search_error"
    SEARCH_COMPLETE = "search_complete"

    # 对话相关
    CONVERSATION_MESSAGE = "conversation_message"
    CONVERSATION_RESPONSE = "conversation_response"

    # 任务管理
    TASK_START = "task_start"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETE = "task_complete"
    TASK_ERROR = "task_error"

    # 系统消息
    SYSTEM_NOTIFICATION = "system_notification"
    ERROR = "error"


class WebSocketMessage(BaseModel):
    """WebSocket 基础消息模型"""

    type: WebSocketMessageType
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    client_id: Optional[str] = None


class SearchProgressMessage(BaseModel):
    """搜索进度消息"""

    task_id: str
    progress_percentage: float
    current_step: str
    message: str
    total_sources: Optional[int] = None
    completed_sources: Optional[int] = None
    cars_found: Optional[int] = None


class SearchResultsMessage(BaseModel):
    """搜索结果消息"""

    task_id: str
    cars: List[Dict[str, Any]]
    total_count: int
    search_duration: float
    message: str


class TaskStatusMessage(BaseModel):
    """任务状态消息"""

    task_id: str
    status: str  # "started", "in_progress", "completed", "failed"
    progress: Optional[float] = None
    message: str
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class SystemNotificationMessage(BaseModel):
    """系统通知消息"""

    notification_type: str
    title: str
    message: str
    level: str = "info"  # "info", "warning", "error", "success"
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None


class WebSocketConnectionInfo(BaseModel):
    """WebSocket 连接信息"""

    client_id: str
    connected_at: datetime
    last_ping: Optional[datetime] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    is_active: bool = True


class WebSocketError(BaseModel):
    """WebSocket 错误消息"""

    error_code: str
    error_message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
