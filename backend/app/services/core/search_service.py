from app.models.schemas import (
    ConversationRequest,
    ConversationResponse,
    ParsedQuery,
    SearchRequest,
    SearchResponse,
)
from app.services.aggregation.multi_platform_car_aggregator import (
    MultiPlatformCarAggregator,
)
from app.services.core.conversation_service import ConversationService
from app.services.data.car_storage_service import CarStorageService
from app.services.data.database_car_recommendation_service import (
    DatabaseCarRecommendationService,
)
from app.services.external.ai.gemini_service import GeminiService
from app.services.external.crawler.cargurus_crawler_coordinator import (
    CargurusCrawlerCoordinator,
)
from app.services.external.location.ip_to_zip_service import ip_to_zip_service
from app.utils.business.profile_utils import generate_daily_profile_name

# from app.services.mcp_supabase_service import DatabaseManager  # 已移除
from app.utils.core.logger import logger


class SearchService:
    def __init__(self):
        # 关键部位日志：服务初始化
        logger.log_result("搜索服务初始化", "开始初始化AI解析、对话和爬虫服务")

        logger.log_result("初始化步骤1", "初始化GeminiService")
        self.gemini_service = GeminiService()

        logger.log_result("初始化步骤2", "初始化ConversationService")
        self.conversation_service = ConversationService()

        # 初始化多平台聚合器
        logger.log_result("初始化步骤3", "初始化MultiPlatformCarAggregator")
        self.multi_platform_aggregator = MultiPlatformCarAggregator()

        # 延迟初始化 CarGurusCrawler，因为需要动态参数
        logger.log_result("初始化步骤4", "设置延迟初始化标志")
        self._cargurus_crawler = None

        # 初始化数据库相关服务
        logger.log_result("初始化步骤5", "初始化数据库服务")

        logger.log_result("初始化步骤6", "初始化CarStorageService")
        self.car_storage_service = CarStorageService()

        logger.log_result(
            "初始化步骤7", "初始化DatabaseCarRecommendationService"
        )
        self.db_recommendation_service = DatabaseCarRecommendationService()

        logger.log_result("搜索服务初始化完成", "所有组件已就绪")

    async def _get_zip_from_ip(self, ip_address: str) -> str:
        """
        通过IP地址获取ZIP码，如果失败则返回默认值

        Args:
            ip_address: 用户IP地址

        Returns:
            ZIP码
        """
        try:
            zip_code = await ip_to_zip_service.get_zip_from_ip(ip_address)
            if zip_code:
                logger.log_result(
                    "IP转ZIP成功", f"IP {ip_address} -> ZIP {zip_code}"
                )
                return zip_code
            else:
                logger.log_result("IP转ZIP失败", "使用默认ZIP码: M5V")
                return "M5V"  # 默认多伦多ZIP码
        except Exception as e:
            logger.log_result("IP转ZIP异常", f"错误: {e}, 使用默认ZIP码: M5V")
            return "M5V"

    def _get_cargurus_crawler(
        self, make_name: str = "Toyota", zip_code: str = "M5V"
    ) -> CargurusCrawlerCoordinator:
        """
        获取或创建 CargurusCrawlerCoordinator 实例
        使用延迟初始化，避免在 SearchService 初始化时就需要所有参数
        """
        if self._cargurus_crawler is None:
            # 使用默认参数创建 CargurusCrawlerCoordinator
            # 生成带时间戳的profile名称
            profile_name = generate_daily_profile_name("search_profile")
            self._cargurus_crawler = CargurusCrawlerCoordinator(
                make_name=make_name,
                zip_code=zip_code,
                profile_name=profile_name,
            )
        return self._cargurus_crawler

    def _validate_search_parameters(self, parsed_query: ParsedQuery) -> dict:
        """
        验证搜索参数是否足够进行搜索
        """
        # 检查必要参数
        if not parsed_query.make:
            return {
                "valid": False,
                "message": "请提供汽车品牌信息，例如：'丰田凯美瑞' 或 'Honda Civic'",
            }

        if not parsed_query.model:
            return {
                "valid": False,
                "message": f"请提供具体的车型信息，例如：'{parsed_query.make}凯美瑞' 或 '{parsed_query.make}Corolla'",
            }

        # 检查是否有其他有用的过滤条件
        has_filters = any(
            [
                parsed_query.year_min,
                parsed_query.year_max,
                parsed_query.price_min,
                parsed_query.price_max,
                parsed_query.mileage_max,
            ]
        )

        if not has_filters:
            return {
                "valid": True,
                "message": "参数验证通过，但建议添加更多过滤条件以获得更精确的结果，例如年份、价格范围等",
            }

        return {"valid": True, "message": "参数验证通过"}

    async def search_cars(
        self, request: SearchRequest, user_ip: str = None
    ) -> SearchResponse:
        """
        执行车源搜索的主要服务方法
        """
        # 关键部位日志：主要业务函数入口
        logger.log_result("开始车源搜索流程", f"用户查询: {request.query}")

        try:
            # 关键部位日志：外部调用 - AI解析
            parsed_query = await self.gemini_service.parse_user_query(
                request.query
            )
            logger.log_result(
                "AI解析成功",
                f"品牌={parsed_query.make}, " f"车型={parsed_query.model}",
            )

            # 参数验证：检查是否有足够的搜索条件
            validation_result = self._validate_search_parameters(parsed_query)
            if not validation_result["valid"]:
                logger.log_result("参数验证失败", validation_result["message"])
                return SearchResponse(
                    success=False, error=validation_result["message"]
                )

            # 确定搜索位置：优先使用用户输入的位置，其次使用IP获取的ZIP码
            search_location = parsed_query.location
            if not search_location and user_ip:
                search_location = await self._get_zip_from_ip(user_ip)
                logger.log_result(
                    "使用IP获取的位置", f"ZIP码: {search_location}"
                )
            elif not search_location:
                search_location = "M5V"  # 默认多伦多
                logger.log_result("使用默认位置", f"ZIP码: {search_location}")

            # 关键部位日志：外部调用 - 爬虫搜索
            crawler = self._get_cargurus_crawler(
                make_name=parsed_query.make, zip_code=search_location
            )
            cars = await crawler.search_cars(parsed_query)
            logger.log_result("爬虫搜索完成", f"找到{len(cars)}辆车源")

            # 关键部位日志：状态变化 - 返回结果
            if cars:
                logger.log_result("搜索流程完成", f"成功返回{len(cars)}条结果")
                return SearchResponse(
                    success=True,
                    data=cars,
                    message=f"找到 {len(cars)} 辆车源",
                    total_count=len(cars),
                )
            else:
                logger.log_result("搜索流程完成", "未找到匹配的车源")
                return SearchResponse(
                    success=True,
                    data=[],
                    message="未找到匹配的车源，请尝试其他搜索条件",
                    total_count=0,
                )

        except Exception as e:
            # 关键部位日志：错误处理
            logger.log_result("搜索流程失败", f"错误: {str(e)}")
            return SearchResponse(
                success=False, error=f"搜索过程中发生错误: {str(e)}"
            )

    async def search_cars_multi_platform(
        self, request: SearchRequest, user_ip: str = None
    ) -> SearchResponse:
        """
        多平台车源搜索 - 从多个平台聚合最优车源
        """
        logger.log_result("开始多平台车源搜索", f"用户查询: {request.query}")

        try:
            # AI解析用户查询
            parsed_query = await self.gemini_service.parse_user_query(
                request.query
            )
            logger.log_result(
                "AI解析成功",
                f"品牌={parsed_query.make}, " f"车型={parsed_query.model}",
            )

            # 确定搜索位置：优先使用用户输入的位置，其次使用IP获取的ZIP码
            if not parsed_query.location and user_ip:
                parsed_query.location = await self._get_zip_from_ip(user_ip)
                logger.log_result(
                    "多平台搜索使用IP获取的位置",
                    f"ZIP码: {parsed_query.location}",
                )

            # 多平台并行搜索
            cars = await self.multi_platform_aggregator.search_cars_multi_platform(
                parsed_query, max_total_results=20
            )
            logger.log_result("多平台搜索完成", f"聚合了{len(cars)}辆最优车源")

            # 返回结果
            if cars:
                logger.log_result(
                    "多平台搜索流程完成", f"成功返回{len(cars)}条结果"
                )
                return SearchResponse(
                    success=True,
                    data=cars,
                    message=f"从多个平台找到 {len(cars)} 辆最优车源",
                    total_count=len(cars),
                )
            else:
                logger.log_result("多平台搜索流程完成", "未找到匹配的车源")
                return SearchResponse(
                    success=True,
                    data=[],
                    message="未找到匹配的车源，请尝试其他搜索条件",
                    total_count=0,
                )

        except Exception as e:
            logger.log_result("多平台搜索失败", f"多平台搜索时出错: {e}")
            return SearchResponse(
                success=False,
                data=[],
                message=f"多平台搜索失败: {str(e)}",
                total_count=0,
            )

    async def search_cars_with_database_storage(
        self, request: SearchRequest, user_ip: str = None
    ) -> SearchResponse:
        """
        带数据库存储的车源搜索 - 先爬取数据存储到数据库，再从数据库推荐
        """
        logger.log_result("开始数据库存储搜索", f"用户查询: {request.query}")

        try:
            # 1. AI解析用户查询
            parsed_query = await self.gemini_service.parse_user_query(
                request.query
            )
            logger.log_result(
                "AI解析成功",
                f"品牌={parsed_query.make}, " f"车型={parsed_query.model}",
            )

            # 确定搜索位置：优先使用用户输入的位置，其次使用IP获取的ZIP码
            if not parsed_query.location and user_ip:
                parsed_query.location = await self._get_zip_from_ip(user_ip)
                logger.log_result(
                    "数据库搜索使用IP获取的位置",
                    f"ZIP码: {parsed_query.location}",
                )

            # 2. 从数据库获取推荐车源
            recommended_cars = await self.db_recommendation_service.recommend_cars_from_database(
                parsed_query, max_results=20
            )

            if recommended_cars:
                logger.log_result(
                    "数据库推荐完成",
                    f"从数据库推荐了{len(recommended_cars)}辆车源",
                )
                return SearchResponse(
                    success=True,
                    data=recommended_cars,
                    message=f"从数据库找到 {len(recommended_cars)} 辆优质车源",
                    total_count=len(recommended_cars),
                )

            # 3. 如果数据库中没有足够车源，则爬取新数据
            logger.log_result("数据库车源不足", "开始爬取新数据")

            # 使用CarGurus爬取数据
            crawler = self._get_cargurus_crawler(
                make_name=parsed_query.make, zip_code="M5V"  # 默认多伦多
            )

            cars = await crawler.search_cars(parsed_query)
            logger.log_result("爬取完成", f"爬取了{len(cars)}辆车源")

            if cars:
                # 4. 将爬取的数据存储到数据库
                storage_stats = (
                    await self.car_storage_service.store_car_listings(
                        cars, platform="cargurus"
                    )
                )
                logger.log_result("数据存储完成", f"存储统计: {storage_stats}")

                # 5. 从数据库重新推荐
                recommended_cars = await self.db_recommendation_service.recommend_cars_from_database(
                    parsed_query, max_results=20
                )

                if recommended_cars:
                    logger.log_result(
                        "数据库推荐完成",
                        f"推荐了{len(recommended_cars)}辆车源",
                    )
                    return SearchResponse(
                        success=True,
                        data=recommended_cars,
                        message=f"找到 {len(recommended_cars)} 辆优质车源",
                        total_count=len(recommended_cars),
                    )

            # 6. 如果仍然没有结果
            logger.log_result("搜索完成", "未找到匹配的车源")
            return SearchResponse(
                success=True,
                data=[],
                message="未找到匹配的车源，请尝试其他搜索条件",
                total_count=0,
            )

        except Exception as e:
            logger.log_result("数据库存储搜索失败", f"搜索时出错: {e}")
            return SearchResponse(
                success=False,
                data=[],
                message=f"搜索失败: {str(e)}",
                total_count=0,
            )

    async def update_database_from_platforms(
        self, make_name: str = "Toyota"
    ) -> dict:
        """
        从各平台更新数据库车源数据
        """
        logger.log_result("开始更新数据库", f"更新品牌: {make_name}")

        try:
            # 使用CarGurus爬取数据
            crawler = self._get_cargurus_crawler(
                make_name=make_name, zip_code="M5V"
            )

            # 创建基础查询条件
            from app.models.schemas import ParsedQuery

            parsed_query = ParsedQuery(make=make_name)

            # 爬取车源数据
            cars = await crawler.search_cars(parsed_query)
            logger.log_result("爬取完成", f"爬取了{len(cars)}辆车源")

            if cars:
                # 存储到数据库
                storage_stats = (
                    await self.car_storage_service.store_car_listings(
                        cars, platform="cargurus"
                    )
                )
                logger.log_result("数据更新完成", f"更新统计: {storage_stats}")
                return storage_stats
            else:
                logger.log_result("数据更新完成", "没有爬取到新数据")
                return {
                    "total": 0,
                    "inserted": 0,
                    "updated": 0,
                    "skipped": 0,
                    "errors": 0,
                }

        except Exception as e:
            logger.log_result("数据库更新失败", f"更新时出错: {e}")
            return {"error": str(e)}

    async def get_database_statistics(self) -> dict:
        """
        获取数据库统计信息
        """
        try:
            stats = await self.db_recommendation_service.get_car_statistics()
            analytics = (
                await self.db_recommendation_service.get_recommendation_analytics()
            )

            return {"statistics": stats, "analytics": analytics}
        except Exception as e:
            logger.log_result("获取统计信息失败", f"错误: {e}")
            return {"error": str(e)}

    async def start_conversation(
        self, request: ConversationRequest, user_ip: str = None
    ) -> ConversationResponse:
        """
        开始对话式搜索流程
        """
        # 关键部位日志：主要业务函数入口
        logger.log_result(
            "开始对话式搜索", f"用户消息: {request.message[:50]}..."
        )

        try:
            # 使用对话服务处理消息
            conversation_response = (
                await self.conversation_service.process_message(request)
            )

            # 如果AI建议搜索车源，执行搜索
            if (
                conversation_response.should_search
                and conversation_response.search_params
            ):
                logger.log_result("AI建议搜索车源", "开始执行车源搜索")

                # 确定搜索位置：优先使用AI解析的位置，其次使用IP获取的ZIP码
                search_location = conversation_response.search_params.location
                if not search_location and user_ip:
                    search_location = await self._get_zip_from_ip(user_ip)
                    logger.log_result(
                        "对话搜索使用IP获取的位置", f"ZIP码: {search_location}"
                    )
                elif not search_location:
                    search_location = "M5V"  # 默认多伦多

                # 执行车源搜索
                crawler = self._get_cargurus_crawler(
                    make_name=conversation_response.search_params.make,
                    zip_code=search_location,
                )
                search_result = await crawler.search_cars(
                    conversation_response.search_params
                )

                # 更新对话响应，添加搜索结果
                if search_result:
                    conversation_response.message += f"\n\n我为您找到了 {len(search_result)} 辆车源，请查看搜索结果。"
                    logger.log_result(
                        "车源搜索完成", f"找到{len(search_result)}辆车源"
                    )
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
                error=str(e),
            )
