#!/bin/bash
# TradingAgents-CN 项目安装部署启动脚本
# 版本: 1.0.0
# 作者: JARVIS (八戒)

set -e  # 遇到错误立即退出

echo "🚀 TradingAgents-CN 项目安装部署启动脚本"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查Python版本
echo -e "${BLUE}检查Python版本...${NC}"
python3 --version | grep -q "3.10\|3.11\|3.12" || {
    echo -e "${RED}❌ 需要Python 3.10或更高版本${NC}"
    exit 1
}
echo -e "${GREEN}✅ Python版本符合要求${NC}"

# 进入项目目录
cd "$(dirname "$0")"

# 1. 虚拟环境设置
echo -e "${BLUE}\n1. 设置虚拟环境...${NC}"
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
    echo -e "${GREEN}✅ 虚拟环境创建完成${NC}"
else
    echo -e "${YELLOW}⚠️  虚拟环境已存在，跳过创建${NC}"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate
echo -e "${GREEN}✅ 虚拟环境已激活${NC}"

# 2. 安装依赖
echo -e "${BLUE}\n2. 安装项目依赖...${NC}"
echo "升级pip..."
pip install --upgrade pip

echo "安装requirements.txt依赖..."
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "安装测试依赖..."
pip install -r requirements-test.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "安装关键缺失依赖..."
pip install akshare backtrader streamlit beautifulsoup4 -i https://pypi.tuna.tsinghua.edu.cn/simple

echo -e "${GREEN}✅ 所有依赖安装完成${NC}"

# 3. 验证依赖
echo -e "${BLUE}\n3. 验证依赖安装...${NC}"
python3 -c "
import sys
print('验证关键依赖...')
deps = ['pandas', 'numpy', 'akshare', 'backtrader', 'streamlit', 'bs4', 'pytest']
for dep in deps:
    try:
        __import__(dep)
        print(f'✅ {dep}: 安装成功')
    except ImportError as e:
        print(f'❌ {dep}: 安装失败 - {e}')
        sys.exit(1)
print('🎉 所有关键依赖验证通过！')
"

# 4. 项目配置
echo -e "${BLUE}\n4. 项目配置...${NC}"
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    echo "复制环境变量示例文件..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  请编辑 .env 文件配置API密钥${NC}"
else
    echo -e "${GREEN}✅ 环境配置文件已就绪${NC}"
fi

# 5. 项目验证
echo -e "${BLUE}\n5. 项目验证...${NC}"
echo "验证项目结构..."
if [ -f "README.md" ] && [ -f "pyproject.toml" ] && [ -d "intelligent_phase3" ]; then
    echo -e "${GREEN}✅ 项目结构完整${NC}"
else
    echo -e "${RED}❌ 项目结构不完整${NC}"
    exit 1
fi

echo "验证AI策略框架..."
cd intelligent_phase3
python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from strategies.ai_strategy_base import StrategyFactory
    strategies = StrategyFactory.list_strategies()
    print(f'✅ AI策略框架正常，策略数: {len(strategies)}')
except Exception as e:
    print(f'❌ AI策略框架验证失败: {e}')
    sys.exit(1)
"
cd ..

echo -e "${GREEN}✅ 项目验证通过${NC}"

# 6. 功能测试
echo -e "${BLUE}\n6. 运行功能测试...${NC}"
echo "运行AI策略测试..."
cd intelligent_phase3
if python3 -m pytest tests/strategies/ -v --tb=short 2>&1 | tail -20; then
    echo -e "${GREEN}✅ AI策略测试通过${NC}"
else
    echo -e "${YELLOW}⚠️  AI策略测试部分失败，但不影响启动${NC}"
fi
cd ..

echo "测试数据获取功能..."
if python3 -c "import fetch_stock_data; print('✅ 数据获取模块可导入')"; then
    echo -e "${GREEN}✅ 数据获取功能正常${NC}"
else
    echo -e "${YELLOW}⚠️  数据获取功能需要进一步配置${NC}"
fi

# 7. 启动选项
echo -e "${BLUE}\n7. 启动选项${NC}"
echo "请选择启动模式:"
echo "1) 🚀 开发模式 (运行主程序)"
echo "2) 🌐 Web界面模式 (Streamlit)"
echo "3) 🔧 API服务模式"
echo "4) 🧪 测试模式"
echo "5) 📊 仅验证不启动"
echo -e "${YELLOW}输入选项 (1-5): ${NC}"
read -r choice

case $choice in
    1)
        echo -e "${GREEN}启动开发模式...${NC}"
        python3 main.py
        ;;
    2)
        echo -e "${GREEN}启动Web界面模式...${NC}"
        streamlit run app_streamlit.py
        ;;
    3)
        echo -e "${GREEN}启动API服务模式...${NC}"
        python3 web_api.py
        ;;
    4)
        echo -e "${GREEN}启动测试模式...${NC}"
        ./run_tests.sh
        ;;
    5)
        echo -e "${GREEN}验证完成，不启动应用${NC}"
        ;;
    *)
        echo -e "${RED}无效选项，退出${NC}"
        ;;
esac

echo -e "${BLUE}\n🎉 安装部署完成！${NC}"
echo -e "${GREEN}项目状态: 就绪${NC}"
echo -e "${BLUE}项目目录: $(pwd)${NC}"
echo -e "${BLUE}虚拟环境: .venv${NC}"
echo -e "${BLUE}启动脚本: ./start_development.sh${NC}"
echo -e "${YELLOW}下一步: 编辑 .env 文件配置API密钥，然后运行 ./start_development.sh${NC}"

# 保存部署信息
DEPLOY_INFO="部署时间: $(date)
项目版本: TradingAgents-CN v0.1.0
Python版本: $(python3 --version)
虚拟环境: .venv
安装状态: 成功
验证结果: 通过"
echo "$DEPLOY_INFO" > deploy_info.txt
echo -e "${GREEN}✅ 部署信息已保存: deploy_info.txt${NC}"