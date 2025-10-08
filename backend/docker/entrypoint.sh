#!/bin/bash

# Docker容器入口脚本
set -e

echo "=== Rehui Car Models Collector Starting ==="

# 检查必需的环境变量
if [ -z "$GOOGLE_GEMINI_API_KEY" ]; then
    echo "错误: GOOGLE_GEMINI_API_KEY 环境变量未设置"
    exit 1
fi

# 创建必要的目录
mkdir -p /app/data/cargurus
mkdir -p /app/logs
mkdir -p /app/chrome_profiles
mkdir -p /app/tmp

# 设置Chrome相关环境变量
export CHROME_BIN=/usr/bin/google-chrome
export CHROME_PATH=/usr/bin/google-chrome

# 启动虚拟显示器（用于无头模式）
if [ "$DISPLAY" = ":99" ]; then
    echo "启动虚拟显示器..."
    Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
    sleep 2
fi

# 检查Chrome和ChromeDriver
echo "检查Chrome安装..."
google-chrome --version
echo "检查ChromeDriver安装..."
chromedriver --version

# 如果提供了命令行参数，则执行指定的命令
if [ $# -gt 0 ]; then
    echo "执行命令: $@"
    exec "$@"
else
    # 默认执行车型收集脚本
    echo "开始执行车型数据收集..."
    exec python scripts/collect_models.py
fi
