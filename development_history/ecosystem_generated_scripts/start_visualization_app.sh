#!/bin/bash
# TradingAgents-CN 可视化应用启动脚本

echo "🚀 启动 TradingAgents-CN 可视化平台"
echo "======================================"

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

echo "✅ Python3 版本: $(python3 --version)"

# 检查虚拟环境
if [ -d ".venv" ]; then
    echo "📦 激活虚拟环境"
    source .venv/bin/activate
else
    echo "📦 创建虚拟环境"
    python3 -m venv .venv
    source .venv/bin/activate
fi

# 安装依赖
echo "📥 安装依赖..."
pip install --upgrade pip
pip install streamlit pandas numpy plotly

# 检查依赖
echo "🔍 检查依赖..."
python3 -c "
try:
    import streamlit as st
    print('✅ Streamlit', st.__version__)
except ImportError:
    print('❌ Streamlit 安装失败')
    exit(1)

try:
    import pandas as pd
    print('✅ Pandas', pd.__version__)
except ImportError:
    print('❌ Pandas 安装失败')
    exit(1)

try:
    import plotly
    print('✅ Plotly', plotly.__version__)
except ImportError:
    print('❌ Plotly 安装失败')
    exit(1)

print('🎉 所有依赖检查通过！')
"

# 启动应用
echo "🌐 启动 Streamlit 应用..."
echo "📊 访问地址: http://localhost:8501"
echo "🔄 按 Ctrl+C 停止应用"

streamlit run app_visualization_integrated.py --server.port 8501 --server.address 0.0.0.0