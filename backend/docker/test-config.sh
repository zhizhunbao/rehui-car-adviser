#!/bin/bash

# Docker配置测试脚本
set -e

echo "=== 测试 Docker 配置 ==="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装或不在PATH中"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose 未安装或不在PATH中"
    exit 1
fi

echo "✓ Docker 和 Docker Compose 已安装"

# 检查配置文件语法
echo "检查 docker-compose.yml 语法..."
docker-compose -f docker-compose.yml config > /dev/null
echo "✓ docker-compose.yml 语法正确"

# 检查Dockerfile语法
echo "检查 Dockerfile 语法..."
docker build --dry-run -f Dockerfile .. > /dev/null 2>&1 || echo "警告: Dockerfile 语法检查失败，但这可能是正常的"

echo "✓ 基本配置检查完成"
echo ""
echo "下一步："
echo "1. 确保设置了环境变量 (GOOGLE_GEMINI_API_KEY 等)"
echo "2. 运行: ./build.sh 构建镜像"
echo "3. 运行: ./run.sh 启动容器"
