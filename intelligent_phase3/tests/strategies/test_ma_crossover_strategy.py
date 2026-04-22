#!/usr/bin/env python3
"""
移动平均线交叉策略测试
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.strategies.ma_crossover_strategy import MACrossoverStrategy
import pandas as pd
import numpy as np

async def test_strategy_initialization():
    """测试策略初始化"""
    print("🧪 测试策略初始化...")
    
    try:
        strategy = MACrossoverStrategy()
        
        # 测试默认初始化
        success = strategy.initialize(
            fast_period=10,
            slow_period=30,
            signal_threshold=0.02
        )
        
        assert success, "策略初始化失败"
        assert strategy.initialized, "策略未标记为已初始化"
        assert strategy.name == "移动平均线交叉策略", "策略名称不正确"
        assert strategy.version == "2.0.0", "策略版本不正确"
        
        print("  ✅ 策略初始化测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 策略初始化测试失败: {e}")
        return False

async def test_market_analysis():
    """测试市场分析"""
    print("\n🧪 测试市场分析...")
    
    try:
        strategy = MACrossoverStrategy()
        strategy.initialize(fast_period=5, slow_period=20)
        
        # 创建测试数据
        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")
        data = pd.DataFrame({
            "open": np.linspace(100, 110, 50),
            "high": np.linspace(105, 115, 50),
            "low": np.linspace(95, 105, 50),
            "close": np.linspace(100, 110, 50),
            "volume": np.random.randint(1000, 10000, 50)
        }, index=dates)
        
        # 执行市场分析
        analysis_result = await strategy.analyze_market(data)
        
        # 验证分析结果
        required_keys = [
            "current_price", "fast_ma", "slow_ma", "ma_diff_pct",
            "trend", "trend_strength", "volatility", "crossover_signals"
        ]
        
        for key in required_keys:
            assert key in analysis_result, f"缺少分析结果键: {key}"
        
        assert analysis_result["data_points"] == 50, "数据点数不正确"
        
        print(f"  ✅ 市场分析测试通过，趋势: {analysis_result['trend']}")
        return True
        
    except Exception as e:
        print(f"  ❌ 市场分析测试失败: {e}")
        return False

async def test_signal_generation():
    """测试信号生成"""
    print("\n🧪 测试信号生成...")
    
    try:
        strategy = MACrossoverStrategy()
        strategy.initialize(
            fast_period=5,
            slow_period=20,
            signal_threshold=0.01
        )
        
        # 创建测试数据 (有明显趋势的数据)
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        
        # 创建上升趋势数据
        trend_data = np.linspace(100, 120, 100)
        noise = np.random.randn(100) * 2
        close_prices = trend_data + noise
        
        data = pd.DataFrame({
            "open": close_prices - 1,
            "high": close_prices + 2,
            "low": close_prices - 2,
            "close": close_prices,
            "volume": np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        # 执行完整分析
        analysis_result = await strategy.analyze_market(data)
        signals = await strategy.generate_signals(analysis_result)
        
        # 验证信号
        if signals:
            signal = signals[0]
            required_signal_keys = [
                "timestamp", "symbol", "action", "price", 
                "quantity", "reason", "confidence", "strategy"
            ]
            
            for key in required_signal_keys:
                assert key in signal, f"缺少信号键: {key}"
            
            print(f"  ✅ 信号生成测试通过，生成 {len(signals)} 个信号")
        else:
            print("  ⚠️  未生成信号 (可能没有达到阈值)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 信号生成测试失败: {e}")
        return False

async def test_risk_calculation():
    """测试风险计算"""
    print("\n🧪 测试风险计算...")
    
    try:
        strategy = MACrossoverStrategy()
        strategy.initialize()
        
        # 创建测试信号
        test_signals = [
            {
                "action": "BUY",
                "price": 100.0,
                "quantity": 0.1,
                "confidence": 0.8
            },
            {
                "action": "SELL", 
                "price": 105.0,
                "quantity": 0.05,
                "confidence": 0.6
            }
        ]
        
        # 计算风险
        portfolio_value = 100000.0
        risk_metrics = strategy.calculate_risk(test_signals, portfolio_value)
        
        # 验证风险指标
        required_risk_keys = [
            "total_risk", "position_risk", "market_risk", "signal_quality"
        ]
        
        for key in required_risk_keys:
            assert key in risk_metrics, f"缺少风险指标键: {key}"
            assert 0 <= risk_metrics[key] <= 1, f"风险指标 {key} 超出范围: {risk_metrics[key]}"
        
        print(f"  ✅ 风险计算测试通过，总风险: {risk_metrics['total_risk']:.2%}")
        return True
        
    except Exception as e:
        print(f"  ❌ 风险计算测试失败: {e}")
        return False

async def test_performance_report():
    """测试性能报告"""
    print("\n🧪 测试性能报告...")
    
    try:
        strategy = MACrossoverStrategy()
        strategy.initialize()
        
        # 记录一些性能指标
        strategy.record_performance("test_metric_1", 0.85)
        strategy.record_performance("test_metric_2", 42.0)
        
        # 获取性能报告
        report = strategy.get_performance_report()
        
        # 验证报告
        assert report["strategy_name"] == "移动平均线交叉策略"
        assert report["strategy_version"] == "2.0.0"
        assert report["initialized"] == True
        assert "test_metric_1" in report["performance_metrics"]
        assert "test_metric_2" in report["performance_metrics"]
        assert "report_time" in report
        
        print(f"  ✅ 性能报告测试通过，指标数: {len(report['performance_metrics'])}")
        return True
        
    except Exception as e:
        print(f"  ❌ 性能报告测试失败: {e}")
        return False

async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🤖 移动平均线交叉策略测试套件")
    print("=" * 60)
    
    test_results = []
    
    # 运行测试
    test_results.append(await test_strategy_initialization())
    test_results.append(await test_market_analysis())
    test_results.append(await test_signal_generation())
    test_results.append(await test_risk_calculation())
    test_results.append(await test_performance_report())
    
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
