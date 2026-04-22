#!/bin/bash
# 运行优化的事件引擎演示

echo "🚀 开始运行优化的事件引擎演示..."
echo "时间: $(date)"
echo ""

cd "$(dirname "$0")"

# 检查Python
python3 --version

# 运行演示
echo "运行演示脚本..."
python3 -c "
import asyncio
import sys
sys.path.append('.')

async def main():
    try:
        from demo_optimized_engine import demo_optimized_engine
        await demo_optimized_engine()
    except Exception as e:
        print(f'❌ 演示运行失败: {e}')
        import traceback
        traceback.print_exc()

asyncio.run(main())
"

echo ""
echo "✅ 演示运行完成"
echo "时间: $(date)"