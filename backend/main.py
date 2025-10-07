import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.utils.config import Config
from app.utils.logger import logger

app = FastAPI(
    title="Rehui Car Adviser API",
    description="智能搜车顾问后端API",
    version="1.0.0"
)

# 验证配置（只在主进程中执行，避免reload时的重复日志）
if __name__ == "__main__":
    try:
        Config.validate_config()
        logger.log_result("配置验证成功", "所有环境变量配置正确")
    except ValueError as e:
        logger.log_result("配置验证失败", f"错误: {e}")
        logger.log_result("配置验证失败", "请检查 .env 文件中的环境变量配置")
        exit(1)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    logger.log_result("根路径访问", "API服务正常运行")
    return {"message": "Rehui Car Adviser API is running"}


@app.get("/health")
async def health_check():
    logger.log_result("健康检查请求", "服务状态正常")
    return {"status": "healthy"}


if __name__ == "__main__":
    # 检查是否在开发环境
    is_development = os.getenv("ENVIRONMENT", "development") == "development"
    
    logger.log_result("启动API服务器", "Rehui Car Adviser API服务启动")
    logger.log_result("服务地址配置", "http://0.0.0.0:8000")
    logger.log_result("运行模式", f"{'开发模式' if is_development else '生产模式'}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=is_development
    )
