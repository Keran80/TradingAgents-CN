#!/usr/bin/env python3
"""
期货数据源适配器测试
"""

import asyncio
import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from futures_data_source import FuturesDataSource

async def test_futures_adapter():
    """测试期货数据源适配器"""
    print("🧪 测试期货数据源适配器")
    
    # 配置
    config = {
        "api_key": "test_key",
        "cache_enabled": True,
        "timeout": 10,
        "max_depth": 5
    }
    
    adapter = FuturesDataSource(config)
    
    tests_passed = 0
    total_tests = 6
    
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
        
        # 测试3: 获取支持的期货代码
        print("3. 测试获取支持的期货代码...")
        symbols = await adapter.get_supported_symbols("commodity_futures")
        assert len(symbols) > 0
        print(f"   ✅ 获取到 {len(symbols)} 个商品期货代码")
        tests_passed += 1
        
        # 测试4: 获取历史数据
        print("4. 测试获取历史数据...")
        historical = await adapter.fetch_historical_data(
            symbol="AU",
            start_date="2026-01-01",
            end_date="2026-01-05"
        )
        assert len(historical) > 0
        print(f"   ✅ 获取到 {len(historical)} 条历史数据")
        tests_passed += 1
        
        # 测试5: 获取实时数据
        print("5. 测试获取实时数据...")
        realtime = await adapter.fetch_realtime_data("AU")
        assert "price" in realtime
        print(f"   ✅ 获取实时数据: 价格={realtime['price']}")
        tests_passed += 1
        
        # 测试6: 获取市场深度
        print("6. 测试获取市场深度...")
        market_depth = await adapter.fetch_market_depth("AU", depth=3)
        assert "bids" in market_depth and "asks" in market_depth
        print(f"   ✅ 获取市场深度: 买盘{len(market_depth['bids'])}档, 卖盘{len(market_depth['asks'])}档")
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
    success = asyncio.run(test_futures_adapter())
    sys.exit(0 if success else 1)
