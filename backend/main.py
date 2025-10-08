import os
import sys
import warnings
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.utils.config import Config

# 设置环境变量来抑制第三方库的警告和日志
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_TRACE"] = ""
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # 改为3，完全抑制
os.environ["GLOG_minloglevel"] = "3"      # Google Logging
os.environ["ABSL_LOG_LEVEL"] = "ERROR"    # Abseil
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["GOOGLE_CLOUD_PROJECT"] = ""
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ""

# 抑制所有警告
warnings.filterwarnings("ignore")

# 立即导入 stderr 抑制器来抑制 Google AI 库的输出


app = FastAPI(
    title="Rehui Car Adviser API",
    description="智能搜车顾问后端API",
    version="1.0.0"
)

# 验证配置
if __name__ == "__main__":
    try:
        Config.validate_config()
    except ValueError as e:
        print(f"配置验证失败: {e}")
        print("请检查 .env 文件中的环境变量配置")
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
    return {"message": "Rehui Car Adviser API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    # 检查是否在开发环境
    is_development = os.getenv("ENVIRONMENT", "development") == "development"
    
    # 导入我们的日志器来初始化全局日志控制
    from app.utils.logger import logger  # noqa: F401

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=is_development,
        log_level="warning",
        access_log=False  # 禁用访问日志
    )
