#!/bin/bash

echo "📊 TradingAgents-CN 测试监控"
echo "========================================"
echo "监控时间: $(date)"
echo ""

# 测试用例数量
total_tests=$(python3 -m pytest tests/ --collect-only 2>/dev/null | grep -c "test_")
echo "总测试用例: $total_tests"

# 测试文件数量
test_files=$(find tests/ -name "test_*.py" | wc -l)
echo "测试文件: $test_files"

# 语法错误
errors=$(find . -name "*.py" -exec python3 -m py_compile {} \; 2>&1 | grep -c "SyntaxError")
echo "语法错误: $errors"

echo ""
echo "✅ 监控完成"
