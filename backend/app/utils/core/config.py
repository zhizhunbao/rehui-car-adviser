import os

from dotenv import load_dotenv

from .path_util import get_env_file_path

# 加载环境变量 - 从项目根目录加载 .env 文件
env_path = get_env_file_path()
load_dotenv(dotenv_path=env_path)


class Config:
    # Supabase 配置
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD")
    SUPABASE_TOKEN = os.getenv("SUPABASE_TOKEN")
    # 数据库配置 - Supabase连接URL（可选，主要用于迁移等场景）
    DATABASE_URL = os.getenv("DATABASE_URL")  # 连接池URL
    DIRECT_URL = os.getenv("DIRECT_URL")  # 直接连接URL

    # Gemini API 配置
    GOOGLE_GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")

    # 应用配置
    APP_NAME = "Rehui Car Adviser"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # CORS 配置
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @classmethod
    def validate_config(cls):
        """验证必需的配置项"""
        required_vars = [
            "GOOGLE_GEMINI_API_KEY",
        ]

        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: "
                f"{', '.join(missing_vars)}"
            )

        return True
