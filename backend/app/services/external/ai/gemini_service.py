import json
import warnings

# 导入 Google AI 库
import google.generativeai as genai

from app.models.schemas import ParsedQuery
from app.utils.core.config import Config
from app.utils.core.logger import logger

# 抑制 Python warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)


class GeminiService:
    def __init__(self):
        # 关键部位日志：服务初始化
        api_key = Config.GOOGLE_GEMINI_API_KEY
        if not api_key:
            logger.log_result("Gemini服务初始化失败", "API密钥未设置")
            raise ValueError(
                "GOOGLE_GEMINI_API_KEY environment variable is required"
            )

        genai.configure(api_key=api_key)
        # 使用 Gemini 2.5 Flash 模型（2025年最新，免费，更快）
        self.model_name = "gemini-2.5-flash"
        self.model = genai.GenerativeModel(self.model_name)
        logger.log_result(
            "Gemini服务初始化完成",
            f"AI模型已就绪 - 使用模型: {self.model_name}",
        )

    async def parse_user_query(self, query: str) -> ParsedQuery:
        """
        使用 Gemini API 解析用户查询，提取购车需求
        """
        # 关键部位日志：外部调用 - AI API
        logger.log_result(
            "开始AI解析", f"使用模型: {self.model_name}, 原始查询: {query}"
        )

        prompt = f"""
        请解析以下用户的购车需求，提取关键信息并返回JSON格式。

        用户查询: "{query}"

        请从查询中提取以下信息：
        - make: 汽车品牌（如 Toyota, Honda, BMW 等）
        - model: 汽车型号（如 Camry, Accord, X3 等）
        - year_min: 最小年份
        - year_max: 最大年份
        - price_max: 最大价格（以数字形式，单位加元）
        - mileage_max: 最大里程（以数字形式，单位公里）
        - location: 位置/城市
        - keywords: 其他关键词列表

        注意：
        1. 如果用户没有明确指定某个字段，请设为 null
        2. 价格请转换为数字（如 "3万加元" 转换为 30000）
        3. 年份请转换为数字
        4. 里程请转换为数字（如 "10万公里" 转换为 100000）
        5. 只返回JSON格式，不要其他文字

        返回格式：
        {{
            "make": "品牌或null",
            "model": "型号或null", 
            "year_min": 年份或null,
            "year_max": 年份或null,
            "price_max": 价格或null,
            "mileage_max": 里程或null,
            "location": "位置或null",
            "keywords": ["关键词1", "关键词2"]
        }}
        """

        try:
            # 关键部位日志：外部调用 - AI API 调用
            logger.log_result(
                "调用Gemini API",
                f"模型: {self.model_name}, 提示词长度: {len(prompt)}",
            )
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # 清理响应文本，提取JSON部分
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            parsed_data = json.loads(response_text)

            result = ParsedQuery(
                make=parsed_data.get("make"),
                model=parsed_data.get("model"),
                year_min=parsed_data.get("year_min"),
                year_max=parsed_data.get("year_max"),
                price_max=parsed_data.get("price_max"),
                mileage_max=parsed_data.get("mileage_max"),
                location=parsed_data.get("location"),
                keywords=parsed_data.get("keywords", []),
            )

            # 关键部位日志：状态变化 - 解析结果
            logger.log_result(
                "AI解析成功",
                f"模型: {self.model_name}, 品牌={result.make}, 车型={result.model}, "
                f"年份={result.year_min}-{result.year_max}",
            )
            return result

        except Exception as e:
            # 关键部位日志：错误处理
            logger.log_result(
                "AI解析失败", f"模型: {self.model_name}, 错误: {str(e)}"
            )
            # 返回默认解析结果
            fallback_result = ParsedQuery(keywords=[query])
            return fallback_result

    async def generate_search_keywords(self, parsed_query: ParsedQuery) -> str:
        """
        根据解析的查询生成搜索关键词
        """
        keywords = []

        if parsed_query.make:
            keywords.append(parsed_query.make)
        if parsed_query.model:
            keywords.append(parsed_query.model)

        keywords.extend(parsed_query.keywords)

        return " ".join(keywords)
