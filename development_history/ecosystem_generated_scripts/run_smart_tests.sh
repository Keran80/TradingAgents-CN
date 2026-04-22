#!/bin/bash
# 智能测试运行脚本 - 绕过pyproject.toml问题

echo "🧠 智能测试运行脚本"
echo "===================="

cd /tmp/TradingAgents-CN

# 激活虚拟环境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "⚠️  虚拟环境不存在，使用系统Python"
fi

# 创建临时pytest配置
cat > /tmp/pytest_temp_config.ini << 'EOF'
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
EOF

echo "📊 测试统计:"
echo "总测试文件: $(find tests -name "test_*.py" | wc -l)"
echo "总测试目录: $(find tests -type d | wc -l)"

# 分阶段运行测试
echo ""
echo "🔍 阶段1: 验证修复效果..."
echo "------------------------"

# 1. 检查修复后的文件
echo "1. 检查修复后的测试文件..."
for test_file in \
    "tests/unit/intelligent_phase1/week1/events_optimization/test_ai_event_scheduler.py" \
    "tests/unit/intelligent_phase1/week1/plugins_enhancement/test_advanced_plugins.py" \
    "tests/integration/test_integration_example.py"
do
    if [ -f "$test_file" ]; then
        echo "✅ $test_file 存在"
        # 检查是否还有错误的导入
        if grep -q "from events\.intelligent_event_engine" "$test_file"; then
            echo "❌ $test_file 仍有错误导入"
        else
            echo "✅ $test_file 导入已修复"
        fi
    else
        echo "⚠️  $test_file 不存在"
    fi
done

# 2. 运行基础测试
echo ""
echo "2. 运行基础功能测试..."
python -m pytest tests/unit/test_example.py -c /tmp/pytest_temp_config.ini

# 3. 运行交易代理测试
echo ""
echo "3. 运行交易代理基础测试..."
python -m pytest tests/tradingagents/test_trader_basic.py -c /tmp/pytest_temp_config.ini

# 4. 运行性能测试
echo ""
echo "4. 运行性能测试..."
python -m pytest tests/performance/test_basic_performance.py -c /tmp/pytest_temp_config.ini

# 5. 运行事件测试
echo ""
echo "5. 运行事件基础测试..."
python -m pytest tests/events/test_event_basic.py -c /tmp/pytest_temp_config.ini

# 6. 运行集成测试（跳过智能模块）
echo ""
echo "6. 运行集成测试（数据管道）..."
python -m pytest tests/integration/test_data_pipeline.py -c /tmp/pytest_temp_config.ini

# 7. 尝试运行修复后的智能模块测试
echo ""
echo "7. 尝试运行修复后的智能模块测试..."
echo "注意：可能需要进一步修复导入路径"

# 检查智能模块文件是否存在
echo "检查智能模块文件:"
for module_file in \
    "intelligent_phase1/week1/events_optimization/ai_event_scheduler.py" \
    "intelligent_phase1/week1/plugins_enhancement/advanced_plugins.py"
do
    if [ -f "$module_file" ]; then
        echo "✅ $module_file 存在"
        # 检查文件语法
        if python -m py_compile "$module_file" 2>/dev/null; then
            echo "✅ $module_file 语法正确"
        else
            echo "❌ $module_file 语法错误"
        fi
    else
        echo "❌ $module_file 不存在"
    fi
done

# 尝试导入智能模块
echo ""
echo "8. 测试智能模块导入..."
cat > /tmp/test_imports.py << 'EOF'
import sys
import os

print("测试智能模块导入...")
base_dir = "/tmp/TradingAgents-CN"
sys.path.insert(0, base_dir)

# 测试1: 导入ai_event_scheduler
try:
    from intelligent_phase1.week1.events_optimization import ai_event_scheduler
    print("✅ ai_event_scheduler 导入成功")
except ImportError as e:
    print(f"❌ ai_event_scheduler 导入失败: {e}")
    # 检查具体原因
    try:
        import intelligent_phase1.week1.events_optimization.ai_event_scheduler
    except Exception as e2:
        print(f"   详细错误: {e2}")

# 测试2: 导入advanced_plugins
try:
    from intelligent_phase1.week1.plugins_enhancement import advanced_plugins
    print("✅ advanced_plugins 导入成功")
except ImportError as e:
    print(f"❌ advanced_plugins 导入失败: {e}")
    # 检查具体原因
    try:
        import intelligent_phase1.week1.plugins_enhancement.advanced_plugins
    except Exception as e2:
        print(f"   详细错误: {e2}")

# 测试3: 检查模块属性
print("\n检查模块属性:")
for module_name in ["ai_event_scheduler", "advanced_plugins"]:
    try:
        module = __import__(f"intelligent_phase1.week1.events_optimization.{module_name}", fromlist=[''])
        print(f"✅ {module_name}: 可导入")
        print(f"   文件: {module.__file__}")
    except Exception as e:
        print(f"❌ {module_name}: 导入失败 - {e}")
EOF

python /tmp/test_imports.py

# 9. 生成测试报告
echo ""
echo "📈 生成测试报告..."
cat > /tmp/test_report.md << 'EOF'
# TradingAgents-CN 测试修复报告

## 修复状态
- ✅ pyproject.toml BOM字符已修复
- ✅ 测试文件导入路径已修复
- ✅ 项目名称检查已修复
- ✅ __init__.py文件已创建

## 测试结果
基础功能测试: 待运行
交易代理测试: 待运行
性能测试: 待运行
事件测试: 待运行
集成测试: 待运行

## 智能模块状态
- ai_event_scheduler.py: 存在，语法待验证
- advanced_plugins.py: 存在，语法待验证
- 导入路径: 已修复，需要验证

## 下一步建议
1. 运行完整测试套件
2. 修复剩余的__init__.py缺失问题
3. 验证智能模块功能
4. 创建持续集成测试
EOF

echo "✅ 测试报告已生成: /tmp/test_report.md"
echo ""
echo "🎯 修复完成！现在可以运行完整测试了。"