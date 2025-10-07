from app.models.schemas import (
    SearchRequest, SearchResponse, ConversationRequest, ConversationResponse
)
from app.services.gemini_service import GeminiService
from app.services.cargurus_scraper import CarGurusScraper
from app.services.conversation_service import ConversationService
from app.utils.logger import logger


class SearchService:
    def __init__(self):
        # 关键部位日志：服务初始化
        logger.log_result("搜索服务初始化", "开始初始化AI解析、对话和爬虫服务")

        self.gemini_service = GeminiService()
        self.conversation_service = ConversationService()
        self.cargurus_scraper = CarGurusScraper()

        logger.log_result("搜索服务初始化完成", "所有组件已就绪")

    async def search_cars(self, request: SearchRequest) -> SearchResponse:
        """
        执行车源搜索的主要服务方法
        """
        # 关键部位日志：主要业务函数入口
        logger.log_result("开始车源搜索流程", f"用户查询: {request.query}")

        try:
            # 关键部位日志：外部调用 - AI解析
            parsed_query = await self.gemini_service.parse_user_query(
                request.query)
            logger.log_result("AI解析成功",
                              f"品牌={parsed_query.make}, "
                              f"车型={parsed_query.model}")

            # 关键部位日志：外部调用 - 爬虫搜索
            cars = await self.cargurus_scraper.search_cars(
                parsed_query, max_results=20)
            logger.log_result("爬虫搜索完成", f"找到{len(cars)}辆车源")

            # 关键部位日志：状态变化 - 返回结果
            if cars:
                logger.log_result("搜索流程完成", f"成功返回{len(cars)}条结果")
                return SearchResponse(
                    success=True,
                    data=cars,
                    message=f"找到 {len(cars)} 辆车源",
                    total_count=len(cars)
                )
            else:
                logger.log_result("搜索流程完成", "未找到匹配的车源")
                return SearchResponse(
                    success=True,
                    data=[],
                    message="未找到匹配的车源，请尝试其他搜索条件",
                    total_count=0
                )

        except Exception as e:
            # 关键部位日志：错误处理
            logger.log_result("搜索流程失败", f"错误: {str(e)}")
            return SearchResponse(
                success=False,
                error=f"搜索过程中发生错误: {str(e)}"
            )
    
    async def start_conversation(self, request: ConversationRequest) -> ConversationResponse:
        """
        开始对话式搜索流程
        """
        # 关键部位日志：主要业务函数入口
        logger.log_result("开始对话式搜索", f"用户消息: {request.message[:50]}...")

        try:
            # 使用对话服务处理消息
            conversation_response = await self.conversation_service.process_message(request)

            # 如果AI建议搜索车源，执行搜索
            if conversation_response.should_search and conversation_response.search_params:
                logger.log_result("AI建议搜索车源", "开始执行车源搜索")

                # 执行车源搜索
                search_result = await self.cargurus_scraper.search_cars(
                    conversation_response.search_params,
                    max_results=20
                )

                # 更新对话响应，添加搜索结果
                if search_result:
                    conversation_response.message += f"\n\n我为您找到了 {len(search_result)} 辆车源，请查看搜索结果。"
                    logger.log_result("车源搜索完成", f"找到{len(search_result)}辆车源")
                else:
                    conversation_response.message += "\n\n很抱歉，没有找到符合您条件的车源，请尝试调整搜索条件。"
                    logger.log_result("车源搜索完成", "未找到匹配的车源")

            return conversation_response

        except Exception as e:
            # 关键部位日志：错误处理
            logger.log_result("对话式搜索失败", f"错误: {str(e)}")
            return ConversationResponse(
                success=False,
                message="抱歉，我遇到了一些技术问题，请稍后再试。",
                session_id=request.session_id or "error",
                conversation_history=[],
                error=str(e)
            )
