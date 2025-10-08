#!/bin/bash

# Docker构建脚本
set -e

echo "=== 构建 Rehui Car Models Collector Docker 镜像 ==="

# 检查是否在正确的目录
if [ ! -f "../requirements.txt" ]; then
    echo "错误: 请在backend/docker目录下运行此脚本"
    exit 1
fi

# 构建镜像
echo "开始构建Docker镜像..."
docker build -f Dockerfile -t rehui-car-models-collector:latest ..

echo "构建完成！"
echo ""
echo "使用方法："
echo "1. 运行容器: docker run --rm -it rehui-car-models-collector"
echo "2. 使用docker-compose: docker-compose up"
echo "3. 查看帮助: docker run --rm rehui-car-models-collector --help"
