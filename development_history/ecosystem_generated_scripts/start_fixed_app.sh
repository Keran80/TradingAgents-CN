#!/bin/bash
# 启动修复后的 Streamlit 应用

echo "🚀 启动 TradingAgents-CN Streamlit 应用"
echo "======================================"

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install streamlit pandas numpy plotly scikit-learn

# 启动应用
echo "启动应用..."
echo "访问地址: http://localhost:8501"
echo "按 Ctrl+C 停止应用"
echo ""
streamlit run app_buttons_tables_windows.py
