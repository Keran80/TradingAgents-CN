#!/bin/bash

# TradingAgents-CN 快速启动脚本
echo "🚀 TradingAgents-CN 快速启动"
echo "========================================"
echo ""

# 检查安装
echo "🔍 检查安装状态..."
if uv run python -c "import tradingagents" 2>/dev/null; then
    echo "✅ TradingAgents 已安装"
else
    echo "⚠️  未安装，正在安装..."
    uv pip install -e . -q
    if [ $? -eq 0 ]; then
        echo "✅ 安装完成"
    else
        echo "❌ 安装失败"
        exit 1
    fi
fi

# 选择启动方式
echo ""
echo "请选择启动方式:"
echo "1. Streamlit 仪表板 (推荐)"
echo "2. Web API"
echo "3. CLI 命令行"
echo "4. Python 脚本测试"
echo "5. 运行测试套件"
echo ""
read -p "请输入选项 (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🌐 启动 Streamlit 仪表板..."
        echo "访问地址：http://localhost:8501"
        streamlit run app_streamlit.py
        ;;
    2)
        echo ""
        echo "🌐 启动 Web API..."
        echo "访问地址：http://localhost:8000"
        echo "API 文档：http://localhost:8000/docs"
        uv run python web_api.py
        ;;
    3)
        echo ""
        echo "💻 启动 CLI 命令行..."
        uv run python cli/main.py
        ;;
    4)
        echo ""
        echo "🧪 运行 Python 脚本测试..."
        uv run python simple_test.py
        ;;
    5)
        echo ""
        echo "🧪 运行测试套件..."
        bash run_quick_tests.sh
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
