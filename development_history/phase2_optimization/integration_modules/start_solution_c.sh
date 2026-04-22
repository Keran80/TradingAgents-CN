#!/bin/bash
# 方案 C 启动脚本 - 专门针对 TradingAgents-CN 的扩展，复用 OpenSpace 核心能力

set -e

echo "=========================================="
echo "   方案 C 启动脚本"
echo "   TradingAgents-CN 专门扩展 + OpenSpace 核心复用"
echo "   时间: $(date)"
echo "=========================================="

# 检查环境
echo -n "检查环境... "
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ 未找到 Python"
    exit 1
fi
echo "✅ 使用: $($PYTHON_CMD --version 2>&1 | head -1)"

# 检查依赖
echo -n "检查依赖... "
REQUIRED_PACKAGES="aiohttp"
if $PYTHON_CMD -c "import aiohttp, json, logging, asyncio" &> /dev/null; then
    echo "✅ 依赖已安装"
else
    echo "⚠️  安装依赖..."
    pip install $REQUIRED_PACKAGES
fi

# 检查目录结构
echo -n "检查目录结构... "
DIRS=(
    "/tmp/CODING_agent"
    "/tmp/CODING_agent/skills"
    "/tmp/CODING_agent/integration"
    "/tmp/CODING_agent/projects/TradingAgents-CN"
    "/tmp/CODING_agent/logs"
)

for dir in "${DIRS[@]}"; do
    mkdir -p "$dir"
done
echo "✅ 完成"

# 检查服务状态
echo -n "检查 OpenSpace 服务... "
if curl -s http://127.0.0.1:7788/health > /dev/null 2>&1; then
    echo "✅ 运行中"
    OPENSPACE_ONLINE=true
else
    echo "⚠️  未运行（将使用模拟模式）"
    OPENSPACE_ONLINE=false
fi

echo -n "检查 Vite 前端... "
if curl -s http://127.0.0.1:3789 > /dev/null 2>&1; then
    echo "✅ 运行中"
else
    echo "⚠️  未运行"
fi

echo ""
echo "环境状态:"
echo "  Python: $($PYTHON_CMD --version 2>&1 | head -1)"
echo "  OpenSpace: $(if $OPENSPACE_ONLINE; then echo '✅ 在线'; else echo '⚠️ 离线'; fi)"
echo "  工作目录: /tmp/CODING_agent"
echo "  项目: TradingAgents-CN"

# 选择启动组件
echo ""
echo "选择启动组件:"
echo "  1) TradingAgents-CN 专门技能"
echo "  2) OpenSpace 深度集成"
echo "  3) 完整方案 C 演示"
echo "  4) 仅 CODING Agent"
echo ""
read -p "请输入选择 (1-4): " COMPONENT_CHOICE

case $COMPONENT_CHOICE in
    1)
        echo "启动 TradingAgents-CN 专门技能..."
        cd /tmp/CODING_agent
        $PYTHON_CMD skills/tradingagents_cn_skill.py
        ;;
    2)
        echo "启动 OpenSpace 深度集成..."
        cd /tmp/CODING_agent
        $PYTHON_CMD integration/openspace_deep_integration.py
        ;;
    3)
        echo "启动完整方案 C 演示..."
        echo ""
        echo "阶段 1: 分析 TradingAgents-CN 项目"
        echo "----------------------------------------"
        cd /tmp/CODING_agent
        $PYTHON_CMD -c "
from skills.tradingagents_cn_skill import demonstrate_tradingagents_skill
skill, analysis, optimization_plan, integration_plan = demonstrate_tradingagents_skill()
print('✅ 阶段1完成: 项目分析和优化计划创建')
print(f'   优化计划ID: {optimization_plan[\"plan_id\"]}')
print(f'   集成方案ID: {integration_plan[\"integration_id\"]}')
        "
        
        echo ""
        echo "阶段 2: 初始化深度集成"
        echo "----------------------------------------"
        $PYTHON_CMD -c "
import asyncio
from integration.openspace_deep_integration import demonstrate_deep_integration
integration, workflow_result = asyncio.run(demonstrate_deep_integration())
print('✅ 阶段2完成: OpenSpace 深度集成初始化')
print(f'   集成状态: {workflow_result[\"status\"]}')
print(f'   工作流ID: {workflow_result.get(\"execution_id\", \"N/A\")}')
        "
        
        echo ""
        echo "阶段 3: 整合演示"
        echo "----------------------------------------"
        $PYTHON_CMD -c "
print('方案 C 整合演示')
print('=' * 50)
print('核心特性:')
print('1. 🎯 专门针对 TradingAgents-CN 优化')
print('2. 🔄 深度复用 OpenSpace 核心能力')
print('3. 🤖 3个专门 Agent 协同工作')
print('4. 📊 完整工作流支持')
print('5. 🔧 反馈优化闭环')
print('')
print('技术架构:')
print('  CODING Agent (项目管理层)')
print('       ↓')
print('  OpenSpace Deep Integration (集成层)')
print('       ↓')
print('  ┌─────────────────┬─────────────────┬─────────────────┐')
print('  │ Financial Code  │ Quantitative    │ Project Manager │')
print('  │    Reviewer     │ Test Generator  │                 │')
print('  └─────────────────┴─────────────────┴─────────────────┘')
print('')
print('工作流程:')
print('  分析 → 规划 → 执行 → 反馈 → 优化 → 重新执行')
print('')
print('✅ 方案 C 演示完成！')
        "
        ;;
    4)
        echo "启动仅 CODING Agent..."
        cd /tmp/CODING_agent
        ./start_coding_agent.sh
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "   方案 C 执行完成"
echo "=========================================="
echo ""
echo "📁 生成的文件:"
echo "  /tmp/CODING_agent/skills/ - TradingAgents-CN 专门技能"
echo "  /tmp/CODING_agent/integration/ - 深度集成配置"
echo "  /tmp/CODING_agent/projects/TradingAgents-CN/ - 项目文件"
echo "  /tmp/CODING_agent/logs/ - 运行日志"
echo ""
echo "🚀 下一步建议:"
echo "  1. 配置 OpenSpace API 连接"
echo "  2. 运行完整工作流测试"
echo "  3. 优化专门技能配置"
echo "  4. 监控集成性能"
echo ""
echo "💡 提示: 方案 C 专门针对 TradingAgents-CN 优化，"
echo "       深度复用 OpenSpace 核心能力，"
echo "       实现高效的项目开发管理！"