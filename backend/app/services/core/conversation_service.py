import json
import uuid
from typing import Dict, List

from app.models.schemas import (
    ConversationMessage,
    ConversationRequest,
    ConversationResponse,
    ParsedQuery,
)
from app.services.external.ai.gemini_service import GeminiService
from app.utils.core.logger import logger


class ConversationService:
    def __init__(self):
        # 关键部位日志：服务初始化
        logger.log_result("对话服务初始化", "开始初始化AI对话服务")

        self.gemini_service = GeminiService()
        # 存储会话状态（生产环境应使用Redis等持久化存储）
        self.sessions: Dict[str, List[ConversationMessage]] = {}

        logger.log_result("对话服务初始化完成", "AI对话服务已就绪")

    async def process_message(
        self, request: ConversationRequest
    ) -> ConversationResponse:
        """
        处理用户消息，进行对话式交互
        """
        # 关键部位日志：主要业务函数入口
        logger.log_result(
            "开始对话处理", f"用户消息: {request.message[:50]}..."
        )

        try:
            # 获取或创建会话ID
            session_id = request.session_id or str(uuid.uuid4())

            # 获取会话历史
            conversation_history = self.sessions.get(session_id, [])

            # 添加用户消息到历史
            user_message = ConversationMessage(
                role="user", content=request.message
            )
            conversation_history.append(user_message)

            # 使用Gemini进行对话
            ai_response = await self._generate_ai_response(
                request.message, conversation_history
            )

            # 添加AI回复到历史
            assistant_message = ConversationMessage(
                role="assistant", content=ai_response["message"]
            )
            conversation_history.append(assistant_message)

            # 保存会话历史
            self.sessions[session_id] = conversation_history

            # 关键部位日志：状态变化 - 对话完成
            logger.log_result(
                "对话处理完成", f"AI回复: {ai_response['message'][:50]}..."
            )

            return ConversationResponse(
                success=True,
                message=ai_response["message"],
                session_id=session_id,
                conversation_history=[
                    msg.dict() for msg in conversation_history
                ],
                should_search=ai_response.get("should_search", False),
                search_params=ai_response.get("search_params"),
            )

        except Exception as e:
            # 关键部位日志：错误处理
            logger.log_result("对话处理失败", f"错误: {str(e)}")
            return ConversationResponse(
                success=False,
                message="抱歉，我遇到了一些技术问题，请稍后再试。",
                session_id=request.session_id or str(uuid.uuid4()),
                conversation_history=[],
                error=str(e),
            )

    async def _generate_ai_response(
        self,
        user_message: str,
        conversation_history: List[ConversationMessage],
    ) -> Dict:
        """
        使用Gemini生成AI回复
        """
        # 关键部位日志：外部调用 - AI API
        model_name = self.gemini_service.model_name
        logger.log_result(
            "开始AI对话生成",
            f"使用模型: {model_name}, 用户消息: {user_message[:50]}...",
        )

        # 构建对话上下文
        context = self._build_conversation_context(conversation_history)

        prompt = f"""
你是一个专业的汽车购买顾问AI助手。你的任务是帮助用户找到合适的汽车。

{context}

用户最新消息: "{user_message}"

请根据用户的购车需求进行对话，并判断是否需要搜索车源。

回复要求：
1. 用友好、专业的语气回复
2. 如果用户表达了明确的购车需求（包含品牌、车型、年份、预算等关键信息中的2-3个），立即搜索车源
3. 如果用户需求不够明确，主动询问关键信息（预算、品牌偏好、车型、年份、里程等）
4. 如果用户只是在闲聊或询问一般问题，不要建议搜索

回复格式（JSON）：
{{
    "message": "你的回复内容",
    "should_search": true/false,
    "search_params": {{
        "make": "品牌或null",
        "model": "型号或null",
        "year_min": 年份或null,
        "year_max": 年份或null,
        "price_max": 价格或null,
        "mileage_max": 里程或null,
        "location": "位置或null",
        "keywords": ["关键词1", "关键词2"]
    }}
}}

注意：
- 当用户明确表达购车需求且包含关键信息（品牌、车型、年份、预算等）中的2-3个时，立即设置 should_search: true
- 价格请转换为数字（如 "3万加元" 转换为 30000）
- 年份请转换为数字
- 里程请转换为数字（如 "10万公里" 转换为 100000）
- 只返回JSON格式，不要其他文字
"""

        try:
            # 关键部位日志：外部调用 - AI API 调用
            logger.log_result(
                "调用Gemini API",
                f"模型: {model_name}, 提示词长度: {len(prompt)}",
            )
            response = self.gemini_service.model.generate_content(prompt)
            response_text = response.text.strip()

            # 清理响应文本，提取JSON部分
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            result = json.loads(response_text)

            # 如果should_search为true，创建ParsedQuery对象
            search_params = None
            if result.get("should_search") and result.get("search_params"):
                search_data = result["search_params"]
                # 确保keywords是列表类型
                keywords = search_data.get("keywords")
                if keywords is None:
                    keywords = []
                elif not isinstance(keywords, list):
                    keywords = [keywords] if keywords else []

                search_params = ParsedQuery(
                    make=search_data.get("make"),
                    model=search_data.get("model"),
                    year_min=search_data.get("year_min"),
                    year_max=search_data.get("year_max"),
                    price_max=search_data.get("price_max"),
                    mileage_max=search_data.get("mileage_max"),
                    location=search_data.get("location"),
                    keywords=keywords,
                )

            # 关键部位日志：状态变化 - AI回复生成
            logger.log_result(
                "AI对话生成成功",
                f"模型: {model_name}, 回复长度: {len(result['message'])}, "
                f"需要搜索: {result.get('should_search', False)}",
            )

            return {
                "message": result["message"],
                "should_search": result.get("should_search", False),
                "search_params": search_params,
            }

        except Exception as e:
            # 关键部位日志：错误处理
            logger.log_result(
                "AI对话生成失败", f"模型: {model_name}, 错误: {str(e)}"
            )
            return {
                "message": "抱歉，我现在无法理解您的需求。请告诉我您想买什么样的车？",
                "should_search": False,
                "search_params": None,
            }

    def _build_conversation_context(
        self, conversation_history: List[ConversationMessage]
    ) -> str:
        """
        构建对话上下文
        """
        if not conversation_history:
            return "这是对话的开始。"

        context_parts = ["对话历史："]
        for msg in conversation_history[-6:]:  # 只保留最近6条消息
            role = "用户" if msg.role == "user" else "助手"
            context_parts.append(f"{role}: {msg.content}")

        return "\n".join(context_parts)

    def get_session_history(
        self, session_id: str
    ) -> List[ConversationMessage]:
        """
        获取会话历史
        """
        return self.sessions.get(session_id, [])

    def clear_session(self, session_id: str) -> bool:
        """
        清除会话历史
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
