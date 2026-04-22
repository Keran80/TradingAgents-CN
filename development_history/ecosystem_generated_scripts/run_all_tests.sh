#!/bin/bash

echo "🚀 TradingAgents-CN 完整测试套件"
echo "========================================"
echo "开始时间: $(date)"
echo ""

# 运行单元测试
echo "=== 单元测试 ==="
python3 -m pytest tests/tradingagents/ tests/events/ -v

# 运行集成测试  
echo ""
echo "=== 集成测试 ==="
python3 -m pytest tests/integration/ -v

# 运行性能测试
echo ""
echo "=== 性能测试 ==="
python3 -m pytest tests/performance/ -m performance -v

# 语法检查
echo ""
echo "=== 语法检查 ==="
errors=$(find . -name "*.py" -exec python3 -m py_compile {} \; 2>&1 | grep -c "SyntaxError")
if [ $errors -eq 0 ]; then
    echo "✅ 语法检查通过"
else
    echo "❌ 语法检查失败: $errors 个错误"
fi

echo ""
echo "========================================"
echo "完成时间: $(date)"
echo "✅ 测试执行完成"
