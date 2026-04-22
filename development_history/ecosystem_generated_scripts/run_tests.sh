#!/bin/bash
# TradingAgents-CN 测试运行脚本

set -e

echo "🚀 开始运行 TradingAgents-CN 测试套件"
echo "======================================"

# 检查Python环境
echo "📋 检查Python环境..."
python3 --version
pip3 --version

# 安装测试依赖
echo "📦 安装测试依赖..."
pip3 install -r requirements-test.txt

# 运行单元测试
echo "🧪 运行单元测试..."
python3 -m pytest tests/unit/ -v --cov=. --cov-report=term-missing

# 运行集成测试
echo "🔗 运行集成测试..."
python3 -m pytest tests/integration/ -v -m integration

# 运行功能测试
echo "⚙️ 运行功能测试..."
python3 -m pytest tests/integration/ -v -m functional

# 生成测试报告
echo "📊 生成测试报告..."
python3 -m pytest tests/ -v --html=test_report.html --self-contained-html

echo "✅ 测试完成！"
echo "📄 测试报告: test_report.html"
