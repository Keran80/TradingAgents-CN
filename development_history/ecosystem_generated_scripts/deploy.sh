#!/bin/bash

# TradingAgents-CN 部署脚本

echo "🚀 TradingAgents-CN 部署"
echo "=========================================="

# 选择部署方式
echo "请选择部署方式:"
echo "1. Docker 部署 (推荐)"
echo "2. 直接部署"
echo "3. 开发环境部署"
echo ""
read -p "请输入选项 (1-3): " choice

case $choice in
    1)
        echo "Docker 部署..."
        cd docker
        docker-compose up -d
        echo "✅ Docker 部署完成"
        echo "访问地址：http://localhost:8501"
        ;;
    2)
        echo "直接部署..."
        pip install -e .
        echo "✅ 直接部署完成"
        ;;
    3)
        echo "开发环境部署..."
        uv venv
        source .venv/bin/activate
        uv pip install -e .
        echo "✅ 开发环境部署完成"
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
