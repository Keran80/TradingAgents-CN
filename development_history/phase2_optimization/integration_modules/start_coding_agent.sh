#!/bin/bash
# CODING Agent 启动脚本

set -e

echo "=========================================="
echo "   CODING Agent 启动脚本"
echo "   项目: TradingAgents-CN"
echo "   时间: $(date)"
echo "=========================================="

# 检查 Python 环境
echo -n "检查 Python 环境... "
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
echo -n "检查 Python 依赖... "
if $PYTHON_CMD -c "import aiohttp, json, logging, asyncio" &> /dev/null; then
    echo "✅ 基本依赖已安装"
else
    echo "⚠️  缺少依赖，尝试安装..."
    pip install aiohttp
fi

# 创建工作目录
echo -n "创建工作目录... "
mkdir -p /tmp/CODING_agent/{logs,projects/TradingAgents-CN/{requirements,plans,tasks,reports,backups},templates,workflows}
echo "✅ 完成"

# 检查 OpenSpace 服务
echo -n "检查 OpenSpace 服务... "
if curl -s http://127.0.0.1:7788/health > /dev/null 2>&1; then
    echo "✅ 运行中 (http://127.0.0.1:7788)"
    OPENSPACE_ONLINE=true
else
    echo "⚠️  未运行 (离线模式)"
    OPENSPACE_ONLINE=false
fi

# 检查 Vite 前端
echo -n "检查 Vite 前端... "
if curl -s http://127.0.0.1:3789 > /dev/null 2>&1; then
    echo "✅ 运行中 (http://127.0.0.1:3789)"
else
    echo "⚠️  未运行"
fi

# 设置环境变量
export CODING_AGENT_HOME="/tmp/CODING_agent"
export CODING_PROJECT="TradingAgents-CN"
export OPENSPACE_API_URL="http://127.0.0.1:7788"
export LOG_LEVEL="INFO"

echo ""
echo "环境变量:"
echo "  CODING_AGENT_HOME: $CODING_AGENT_HOME"
echo "  CODING_PROJECT: $CODING_PROJECT"
echo "  OPENSPACE_API_URL: $OPENSPACE_API_URL"
echo "  LOG_LEVEL: $LOG_LEVEL"
echo "  OPENSPACE_ONLINE: $OPENSPACE_ONLINE"

# 启动模式选择
echo ""
echo "选择启动模式:"
echo "  1) 演示模式 (运行完整演示)"
echo "  2) 交互模式 (启动后等待命令)"
echo "  3) 服务模式 (作为后台服务运行)"
echo "  4) 测试模式 (运行单元测试)"
echo ""
read -p "请输入选择 (1-4): " MODE_CHOICE

case $MODE_CHOICE in
    1)
        echo "启动演示模式..."
        $PYTHON_CMD coding_agent.py
        ;;
    2)
        echo "启动交互模式..."
        echo "可用命令:"
        echo "  create_plan    - 创建项目开发方案"
        echo "  execute_plan   - 执行方案"
        echo "  optimize_plan  - 优化方案"
        echo "  get_status     - 获取状态"
        echo "  help           - 显示帮助"
        echo ""
        $PYTHON_CMD -c "
import asyncio
from coding_agent import CODINGAgent

async def interactive_mode():
    agent = CODINGAgent('TradingAgents-CN')
    await agent.initialize()
    
    print('CODING Agent 交互模式已启动')
    print('输入命令或 help 查看帮助')
    
    while True:
        try:
            cmd = input('CODING> ').strip().lower()
            
            if cmd == 'exit' or cmd == 'quit':
                print('退出交互模式')
                break
            elif cmd == 'help':
                print('可用命令:')
                print('  create_plan    - 创建项目开发方案')
                print('  execute_plan   - 执行方案')
                print('  optimize_plan  - 优化方案')
                print('  get_status     - 获取状态')
                print('  exit/quit      - 退出')
            elif cmd == 'get_status':
                status = await agent.get_status()
                print(f'状态: {status}')
            elif cmd == 'create_plan':
                # 这里可以添加创建方案的逻辑
                print('创建方案功能待实现')
            elif cmd == '':
                continue
            else:
                print(f'未知命令: {cmd}')
                
        except KeyboardInterrupt:
            print('\n退出交互模式')
            break
        except Exception as e:
            print(f'错误: {e}')
    
    await agent.stop()

asyncio.run(interactive_mode())
"
        ;;
    3)
        echo "启动服务模式..."
        # 这里可以添加服务模式的具体实现
        echo "服务模式待实现"
        ;;
    4)
        echo "启动测试模式..."
        if [ -f "test_coding_agent.py" ]; then
            $PYTHON_CMD test_coding_agent.py
        else
            echo "❌ 测试文件不存在"
        fi
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "   CODING Agent 执行完成"
echo "   日志文件: /tmp/CODING_agent/logs/coding_agent.log"
echo "   项目目录: /tmp/CODING_agent/projects/TradingAgents-CN"
echo "=========================================="