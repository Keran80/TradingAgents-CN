#!/bin/bash
# AI策略测试脚本

echo "🤖 AI策略测试套件"
echo "===================="

cd "$(dirname "$0")/../.."

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 检查Python环境
echo -e "${BLUE}检查Python环境...${NC}"
python3 --version
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Python3未安装${NC}"
    exit 1
fi

# 添加项目路径
export PYTHONPATH="$PYTHONPATH:$(pwd)/src"

# 测试结果统计
total_tests=0
passed_tests=0
failed_tests=0

# 测试函数
run_test() {
    local test_name="$1"
    local test_file="$2"
    
    echo -e "${BLUE}测试: ${test_name}${NC}"
    
    if [ ! -f "$test_file" ]; then
        echo -e "${YELLOW}⚠️  测试文件不存在: $test_file${NC}"
        return 1
    fi
    
    # 运行测试
    python3 "$test_file"
    local result=$?
    
    if [ $result -eq 0 ]; then
        echo -e "${GREEN}✅ 测试通过: ${test_name}${NC}"
        ((passed_tests++))
        return 0
    else
        echo -e "${RED}❌ 测试失败: ${test_name}${NC}"
        ((failed_tests++))
        return 1
    fi
}

echo -e "${BLUE}开始测试AI策略...${NC}"

# 1. 测试AI策略基类
run_test "AI策略基类测试" "tests/strategies/test_ai_strategy_base.py"

# 2. 测试移动平均线交叉策略
run_test "移动平均线交叉策略测试" "tests/strategies/test_ma_crossover_strategy.py"

# 3. 测试RSI策略
run_test "RSI策略测试" "tests/strategies/test_rsi_strategy.py"

# 4. 测试布林带策略  
run_test "布林带策略测试" "tests/strategies/test_bollinger_strategy.py"

# 5. 测试MACD策略
run_test "MACD策略测试" "tests/strategies/test_macd_strategy.py"

# 统计结果
total_tests=$((passed_tests + failed_tests))

echo -e "${BLUE}\n📊 测试结果汇总${NC}"
echo -e "总测试数: ${total_tests}"
echo -e "${GREEN}通过数: ${passed_tests}${NC}"
echo -e "${RED}失败数: ${failed_tests}${NC}"

if [ $failed_tests -eq 0 ] && [ $total_tests -gt 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！${NC}"
    exit 0
elif [ $total_tests -eq 0 ]; then
    echo -e "${YELLOW}⚠️  未运行任何测试${NC}"
    exit 0
else
    echo -e "${RED}⚠️  部分测试失败${NC}"
    exit 1
fi
