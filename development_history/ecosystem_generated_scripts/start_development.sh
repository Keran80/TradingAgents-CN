#!/bin/bash
# TradingAgents-CN 开发启动脚本

set -e

echo "🚀 启动 TradingAgents-CN 开发环境"
echo "======================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Python环境
echo -e "${YELLOW}📋 检查环境...${NC}"
python3 --version
pip3 --version

# 安装项目依赖
echo -e "${YELLOW}📦 安装依赖...${NC}"
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    echo -e "${GREEN}✅ 项目依赖安装完成${NC}"
else
    echo -e "${RED}❌ requirements.txt 不存在${NC}"
fi

# 安装测试依赖
if [ -f "requirements-test.txt" ]; then
    pip3 install -r requirements-test.txt
    echo -e "${GREEN}✅ 测试依赖安装完成${NC}"
else
    echo -e "${YELLOW}⚠️  requirements-test.txt 不存在，跳过${NC}"
fi

# 清理Python缓存
echo -e "${YELLOW}🧹 清理缓存...${NC}"
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete
echo -e "${GREEN}✅ 缓存清理完成${NC}"

# 运行语法检查
echo -e "${YELLOW}🔍 语法检查...${NC}"
ERROR_COUNT=0
for py_file in $(find . -name "*.py" -type f); do
    if python3 -m py_compile "$py_file" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $py_file"
    else
        echo -e "  ${RED}✗${NC} $py_file"
        ERROR_COUNT=$((ERROR_COUNT + 1))
    fi
done

if [ $ERROR_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ 所有Python文件语法正确${NC}"
else
    echo -e "${RED}❌ 发现 $ERROR_COUNT 个语法错误${NC}"
fi

# 运行测试
echo -e "${YELLOW}🧪 运行测试...${NC}"
if [ -f "run_tests.sh" ]; then
    chmod +x run_tests.sh
    ./run_tests.sh
else
    echo -e "${YELLOW}⚠️  run_tests.sh 不存在，运行基础测试${NC}"
    python3 -m pytest tests/ -v --tb=short 2>/dev/null || true
fi

# 显示项目状态
echo -e "${YELLOW}📊 项目状态...${NC}"
echo "项目目录: $(pwd)"
echo "Python文件: $(find . -name "*.py" -type f | wc -l) 个"
echo "测试文件: $(find tests -name "*.py" -type f 2>/dev/null | wc -l) 个"
echo "文档文件: $(find . -name "*.md" -type f | wc -l) 个"

# 显示开发提示
echo -e "${YELLOW}💡 开发提示:${NC}"
echo "1. 查看开发进度: cat DEVELOPMENT_PROGRESS.md"
echo "2. 运行测试: ./run_tests.sh 或 python3 -m pytest"
echo "3. 检查语法: find . -name \"*.py\" -exec python3 -m py_compile {} \\;"
echo "4. 查看Git状态: git status"
echo "5. 代码格式化: black . && isort ."

echo -e "${GREEN}🎉 开发环境准备就绪！${NC}"
echo "开始你的 TradingAgents-CN 开发之旅吧！"
