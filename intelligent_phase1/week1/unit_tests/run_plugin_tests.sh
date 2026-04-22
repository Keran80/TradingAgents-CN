#!/bin/bash
# 运行插件系统单元测试

echo "🧪 开始运行插件系统单元测试..."
echo "时间: $(date)"
echo ""

cd "$(dirname "$0")/plugins"

# 运行测试
python3 test_plugin_system.py

echo ""
echo "✅ 插件系统单元测试运行完成"
echo "时间: $(date)"