#!/usr/bin/env python3
"""
智能回测引擎测试
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine.intelligent_backtest_engine import (
    IntelligentBacktestEngine,
    BacktestConfig,
    BacktestStatus
)

async def test_engine_initialization():
    """测试引擎初始化"""
    print("🧪 测试引擎初始化...")
    
    try:
        # 创建配置
        config = BacktestConfig(
            initial_capital=100000,
            commission_rate=0.0003,
            enable_cache=True
        )
        
        # 创建引擎
        engine = IntelligentBacktestEngine(config)
        
        # 初始化
        await engine.initialize()
        
        # 检查状态
        assert engine.status == BacktestStatus.PENDING
        print("  ✅ 引擎初始化成功")
        
        # 检查配置
        assert engine.config.initial_capital == 100000
        assert engine.config.commission_rate == 0.0003
        print("  ✅ 配置正确")
        
        # 检查AI策略
        assert len(engine.ai_strategies) > 0
        print(f"  ✅ 已注册 {len(engine.ai_strategies)} 个AI策略")
        
        # 关闭引擎
        await engine.shutdown()
        print("  ✅ 引擎关闭成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

async def test_performance_monitoring():
    """测试性能监控"""
    print("\n🧪 测试性能监控...")
    
    try:
        engine = IntelligentBacktestEngine()
        await engine.initialize()
        
        # 获取性能统计
        stats = engine.get_performance_stats()
        
        # 检查必要的统计字段
        required_fields = [
            "current_status",
            "running_time",
            "cache_size",
            "registered_strategies"
        ]
        
        for field in required_fields:
            assert field in stats, f"缺少字段: {field}"
        
        print(f"  ✅ 性能监控正常，统计: {stats}")
        
        await engine.shutdown()
        return True
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def test_config_dataclass():
    """测试配置数据类"""
    print("\n🧪 测试配置数据类...")
    
    try:
        # 测试默认配置
        config1 = BacktestConfig()
        assert config1.initial_capital == 100000.0
        assert config1.commission_rate == 0.0003
        assert config1.enable_cache == True
        
        # 测试自定义配置
        config2 = BacktestConfig(
            initial_capital=50000,
            commission_rate=0.0005,
            enable_cache=False,
            max_concurrent_tasks=20
        )
        assert config2.initial_capital == 50000
        assert config2.commission_rate == 0.0005
        assert config2.enable_cache == False
        assert config2.max_concurrent_tasks == 20
        
        print("  ✅ 配置数据类测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

async def test_ai_strategy_registration():
    """测试AI策略注册"""
    print("\n🧪 测试AI策略注册...")
    
    try:
        engine = IntelligentBacktestEngine()
        await engine.initialize()
        
        # 检查内置策略
        expected_strategies = [
            "moving_average_crossover",
            "rsi_strategy",
            "bollinger_bands"
        ]
        
        for strategy in expected_strategies:
            assert strategy in engine.ai_strategies, f"缺少策略: {strategy}"
        
        print(f"  ✅ 内置AI策略注册正确: {list(engine.ai_strategies.keys())}")
        
        # 测试自定义策略注册
        async def custom_strategy(data, **params):
            return []
        
        engine.register_ai_strategy("custom_strategy", custom_strategy)
        assert "custom_strategy" in engine.ai_strategies
        print("  ✅ 自定义策略注册成功")
        
        await engine.shutdown()
        return True
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🤖 智能阶段3 - 回测引擎测试套件")
    print("=" * 60)
    
    test_results = []
    
    # 运行测试
    test_results.append(await test_engine_initialization())
    test_results.append(await test_performance_monitoring())
    test_results.append(test_config_dataclass())
    test_results.append(await test_ai_strategy_registration())
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    print(f"总测试数: {total}")
    print(f"通过数: {passed}")
    print(f"失败数: {total - passed}")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return True
    else:
        print("\n⚠️  部分测试失败")
        return False

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(run_all_tests())
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
