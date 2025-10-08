@echo off
echo === 构建 Rehui Car Models Collector Docker 镜像 ===

REM 检查是否在正确的目录
if not exist "..\requirements.txt" (
    echo 错误: 请在backend\docker目录下运行此脚本
    pause
    exit /b 1
)

REM 构建镜像
echo 开始构建Docker镜像...
docker build -f Dockerfile -t rehui-car-models-collector:latest ..

if %errorlevel% equ 0 (
    echo 构建完成！
    echo.
    echo 使用方法：
    echo 1. 运行容器: docker run --rm -it rehui-car-models-collector
    echo 2. 使用docker-compose: docker-compose up
    echo 3. 查看帮助: docker run --rm rehui-car-models-collector --help
) else (
    echo 构建失败！
)

pause
