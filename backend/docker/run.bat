@echo off
echo === 运行 Rehui Car Models Collector ===

REM 检查环境变量文件
if not exist "..\.env" (
    echo 警告: 未找到.env文件，请确保设置了必要的环境变量
)

REM 创建必要的目录
if not exist "..\data\cargurus" mkdir "..\data\cargurus"
if not exist "..\logs" mkdir "..\logs"
if not exist "..\chrome_profiles" mkdir "..\chrome_profiles"
if not exist "..\tmp" mkdir "..\tmp"

REM 运行容器
echo 启动容器...
docker-compose up --build

echo 容器已停止
pause
