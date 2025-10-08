#!/bin/bash

# Docker运行脚本
set -e

echo "=== 运行 Rehui Car Models Collector ==="

# 检查环境变量文件
if [ ! -f "../.env" ]; then
    echo "警告: 未找到.env文件，请确保设置了必要的环境变量"
fi

# 创建必要的目录
mkdir -p ../data/cargurus
mkdir -p ../logs
mkdir -p ../chrome_profiles
mkdir -p ../tmp

# 运行容器
echo "启动容器..."
docker-compose up --build

echo "容器已停止"
