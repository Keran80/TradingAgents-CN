#!/usr/bin/env python3
"""
股票数据源适配器测试
"""

import asyncio
import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from stock_data_source import StockDataSource

async def test_stock_adapter():
    """测试股票数据源适配器"""
    print("🧪 测试股票数据源适配器")
    
    # 配置
    config = {
        "api_key": "test_key",
        "cache_enabled": True,
        "timeout": 10
    }
    
    adapter = StockDataSource(config)
    
    tests_passed = 0
    total_tests = 5
    
    try:
        # 测试1: 连接
        print("1. 测试连接...")
        await adapter.connect()
        assert adapter.is_connected
        print("   ✅ 连接测试通过")
        tests_passed += 1
        
        # 测试2: 健康检查
        print("2. 测试健康检查...")
        health = await adapter.health_check()
        assert health["status"] == "healthy"
        print(f"   ✅ 健康检查通过: {health['status']}")
        tests_passed += 1
        
        # 测试3: 获取支持的股票代码
        print("3. 测试获取支持的股票代码...")
        symbols = await adapter.get_supported_symbols("a_share")
        assert len(symbols) > 0
        print(f"   ✅ 获取到 {len(symbols)} 个A股代码")
        tests_passed += 1
        
        # 测试4: 获取历史数据
        print("4. 测试获取历史数据...")
        historical = await adapter.fetch_historical_data(
            symbol="000001",
            start_date="2026-01-01",
            end_date="2026-01-05"
        )
        assert len(historical) > 0
        print(f"   ✅ 获取到 {len(historical)} 条历史数据")
        tests_passed += 1
        
        # 测试5: 获取实时数据
        print("5. 测试获取实时数据...")
        realtime = await adapter.fetch_realtime_data("000001")
        assert "price" in realtime
        print(f"   ✅ 获取实时数据: 价格={realtime['price']}")
        tests_passed += 1
        
        # 断开连接
        await adapter.disconnect()
        
        # 测试结果
        print(f"\n📊 测试结果: {tests_passed}/{total_tests} 通过")
        if tests_passed == total_tests:
            print("🎉 所有测试通过!")
            return True
        else:
            print(f"⚠️  {total_tests - tests_passed} 个测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_stock_adapter())
    sys.exit(0 if success else 1)
