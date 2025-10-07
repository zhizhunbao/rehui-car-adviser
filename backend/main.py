import os
import sys
import warnings
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.utils.config import Config

# 设置环境变量来抑制 Google 库的警告
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_TRACE"] = ""
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["PYTHONWARNINGS"] = "ignore"

# 抑制所有警告
warnings.filterwarnings("ignore")

# 重定向 stderr 来抑制 Google 库的初始化警告
class SuppressStderr:
    def __init__(self):
        self.stderr = sys.stderr
    
    def write(self, message):
        # 只过滤掉 Google 相关的警告
        if any(keyword in message for keyword in [
            "WARNING: All log messages before absl::InitializeLog()",
            "ALTS creds ignored",
            "absl::InitializeLog"
        ]):
            return
        self.stderr.write(message)
    
    def flush(self):
        self.stderr.flush()

# 临时重定向 stderr
sys.stderr = SuppressStderr()

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
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=is_development,
        log_level="warning"
    )