#!/bin/bash
# 测试框架验证脚本

echo "🧪 验证TradingAgents-CN测试框架"
echo "======================================"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}1. 检查测试目录结构...${NC}"
if [ -d "tests" ]; then
    echo -e "  ${GREEN}✅ tests目录存在${NC}"
    
    # 检查子目录
    for subdir in "unit" "integration" "performance"; do
        if [ -d "tests/$subdir" ]; then
            echo -e "    ${GREEN}✅ tests/$subdir 存在${NC}"
        else
            echo -e "    ${YELLOW}⚠️  tests/$subdir 不存在${NC}"
        fi
    done
else
    echo -e "  ${RED}❌ tests目录不存在${NC}"
fi

echo -e "\n${YELLOW}2. 检查测试配置文件...${NC}"
if [ -f "pytest.ini" ]; then
    echo -e "  ${GREEN}✅ pytest.ini存在${NC}"
    echo "  内容:"
    head -10 pytest.ini
else
    echo -e "  ${RED}❌ pytest.ini不存在${NC}"
fi

if [ -f "requirements-test.txt" ]; then
    echo -e "  ${GREEN}✅ requirements-test.txt存在${NC}"
else
    echo -e "  ${YELLOW}⚠️  requirements-test.txt不存在${NC}"
fi

echo -e "\n${YELLOW}3. 检查测试文件...${NC}"
test_files=$(find tests -name "*.py" -type f 2>/dev/null | wc -l)
echo -e "  找到 ${test_files} 个测试文件"

if [ $test_files -gt 0 ]; then
    echo -e "  ${GREEN}✅ 测试文件存在${NC}"
    echo "  测试文件列表:"
    find tests -name "*.py" -type f 2>/dev/null | head -5
    if [ $test_files -gt 5 ]; then
        echo "  ... 还有更多文件"
    fi
else
    echo -e "  ${RED}❌ 未找到测试文件${NC}"
fi

echo -e "\n${YELLOW}4. 检查智能阶段1测试...${NC}"
if [ -d "tests/unit/intelligent_phase1" ]; then
    echo -e "  ${GREEN}✅ 智能阶段1测试目录存在${NC}"
    
    phase1_tests=$(find tests/unit/intelligent_phase1 -name "*.py" -type f 2>/dev/null | wc -l)
    echo -e "  找到 ${phase1_tests} 个智能阶段1测试文件"
    
    if [ $phase1_tests -gt 0 ]; then
        echo "  文件列表:"
        find tests/unit/intelligent_phase1 -name "*.py" -type f 2>/dev/null
    fi
else
    echo -e "  ${YELLOW}⚠️  智能阶段1测试目录不存在${NC}"
fi

echo -e "\n${YELLOW}5. 检查核心文件语法...${NC}"
error_count=0
for py_file in intelligent_phase1/week1/events_optimization/ai_event_scheduler.py \
               intelligent_phase1/week1/plugins_enhancement/advanced_plugins.py \
               intelligent_phase1/week1/events_optimization/optimized_event_engine.py; do
    if [ -f "$py_file" ]; then
        if python3 -m py_compile "$py_file" 2>/dev/null; then
            echo -e "  ${GREEN}✅ $py_file 语法正确${NC}"
        else
            echo -e "  ${RED}❌ $py_file 语法错误${NC}"
            error_count=$((error_count + 1))
        fi
    else
        echo -e "  ${YELLOW}⚠️  $py_file 不存在${NC}"
    fi
done

echo -e "\n${YELLOW}6. 检查测试运行脚本...${NC}"
if [ -f "run_tests.sh" ]; then
    echo -e "  ${GREEN}✅ run_tests.sh存在${NC}"
    if [ -x "run_tests.sh" ]; then
        echo -e "    ${GREEN}✅ 可执行${NC}"
    else
        echo -e "    ${YELLOW}⚠️  不可执行，运行: chmod +x run_tests.sh${NC}"
    fi
else
    echo -e "  ${RED}❌ run_tests.sh不存在${NC}"
fi

if [ -f "start_development.sh" ]; then
    echo -e "  ${GREEN}✅ start_development.sh存在${NC}"
else
    echo -e "  ${YELLOW}⚠️  start_development.sh不存在${NC}"
fi

echo -e "\n${YELLOW}7. 总结...${NC}"
echo "测试框架状态:"
echo "  - 测试目录结构: $(if [ -d "tests" ]; then echo "✅"; else echo "❌"; fi)"
echo "  - 测试配置文件: $(if [ -f "pytest.ini" ]; then echo "✅"; else echo "❌"; fi)"
echo "  - 测试文件数量: $test_files"
echo "  - 智能阶段1测试: $phase1_tests"
echo "  - 语法错误数量: $error_count"

if [ $error_count -eq 0 ] && [ $test_files -gt 0 ]; then
    echo -e "\n${GREEN}🎉 测试框架验证通过！${NC}"
    echo "可以运行: ./run_tests.sh 或 python3 -m pytest"
    exit 0
else
    echo -e "\n${YELLOW}⚠️  测试框架需要改进${NC}"
    if [ $error_count -gt 0 ]; then
        echo "  - 修复 $error_count 个语法错误"
    fi
    if [ $test_files -eq 0 ]; then
        echo "  - 添加测试文件"
    fi
    exit 1
fi
