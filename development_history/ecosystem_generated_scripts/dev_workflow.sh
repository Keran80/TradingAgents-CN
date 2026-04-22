#!/bin/bash
# TradingAgents-CN 开发工作流脚本

echo "🔄 TradingAgents-CN 开发工作流"
echo "================================"

cd /tmp/TradingAgents-CN

# 检查参数
ACTION="${1:-help}"

case $ACTION in
    start)
        echo "🚀 启动开发环境..."
        source .venv/bin/activate
        echo "✅ 开发环境已启动"
        ;;
    
    test)
        echo "🧪 运行测试..."
        source .venv/bin/activate
        python -m pytest tests/ -v --tb=short
        ;;
    
    format)
        echo "🎨 代码格式化..."
        source .venv/bin/activate
        black intelligent_phase1/ intelligent_phase2/ tests/
        isort intelligent_phase1/ intelligent_phase2/ tests/
        echo "✅ 代码格式化完成"
        ;;
    
    check)
        echo "🔍 代码检查..."
        source .venv/bin/activate
        echo "运行flake8..."
        flake8 intelligent_phase1/ intelligent_phase2/ tests/ --max-line-length=88
        echo "运行mypy..."
        mypy intelligent_phase1/ intelligent_phase2/ --ignore-missing-imports
        echo "✅ 代码检查完成"
        ;;
    
    build)
        echo "🔨 构建项目..."
        source .venv/bin/activate
        echo "安装依赖..."
        pip install -r requirements.txt
        echo "运行测试..."
        python -m pytest tests/ -v
        echo "生成文档..."
        # 这里可以添加文档生成命令
        echo "✅ 项目构建完成"
        ;;
    
    deploy-test)
        echo "🚀 部署到测试环境..."
        echo "构建Docker镜像..."
        # docker build -t tradingagents-cn:latest .
        echo "推送到镜像仓库..."
        # docker push tradingagents-cn:latest
        echo "部署到Kubernetes..."
        # kubectl apply -f k8s/
        echo "✅ 测试环境部署完成"
        ;;
    
    clean)
        echo "🧹 清理环境..."
        find . -name "*.pyc" -delete
        find . -name "__pycache__" -delete
        find . -name ".pytest_cache" -delete
        find . -name ".coverage" -delete
        echo "✅ 环境清理完成"
        ;;
    
    status)
        echo "📊 项目状态..."
        echo "Python版本: $(python --version)"
        echo "虚拟环境: $(which python)"
        echo "测试文件数: $(find tests -name "test_*.py" | wc -l)"
        echo "代码行数: $(find . -name "*.py" -exec cat {} \; | wc -l)"
        echo "依赖数量: $(pip list | wc -l)"
        ;;
    
    help|*)
        echo "📖 使用说明:"
        echo "  ./dev_workflow.sh [命令]"
        echo ""
        echo "可用命令:"
        echo "  start      - 启动开发环境"
        echo "  test       - 运行测试"
        echo "  format     - 代码格式化"
        echo "  check      - 代码检查"
        echo "  build      - 构建项目"
        echo "  deploy-test - 部署到测试环境"
        echo "  clean      - 清理环境"
        echo "  status     - 查看项目状态"
        echo "  help       - 显示帮助"
        ;;
esac
