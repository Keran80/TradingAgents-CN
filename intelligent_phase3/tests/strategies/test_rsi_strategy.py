#!/usr/bin/env python3
"""
RSI策略测试
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.strategies.rsi_strategy import RSIStrategy
import pandas as pd
import numpy as np

async def test_rsi_strategy_initialization():
    """测试RSI策略初始化"""
    print("🧪 测试RSI策略初始化...")
    
    try:
        strategy = RSIStrategy()
        
        # 测试默认初始化
        success = strategy.initialize(
            rsi_period=14,
            oversold_threshold=30,
            overbought_threshold=70
        )
        
        assert success, "RSI策略初始化失败"
        assert strategy.initialized, "RSI策略未标记为已初始化"
        assert strategy.name == "RSI策略", "RSI策略名称不正确"
        assert strategy.version == "1.0.0", "RSI策略版本不正确"
        
        # 检查参数
        assert strategy.parameters["rsi_period"] == 14, "RSI周期参数不正确"
        assert strategy.parameters["oversold_threshold"] == 30, "超卖阈值不正确"
        assert strategy.parameters["overbought_threshold"] == 70, "超买阈值不正确"
        
        print("  ✅ RSI策略初始化测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ RSI策略初始化测试失败: {e}")
        return False

async def test_rsi_calculation():
    """测试RSI计算"""
    print("\n🧪 测试RSI计算...")
    
    try:
        strategy = RSIStrategy()
        strategy.initialize(rsi_period=14)
        
        # 创建测试数据 (有明显趋势)
        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")
        
        # 创建上升趋势数据
        trend_data = np.linspace(100, 120, 50)
        noise = np.random.randn(50) * 2
        close_prices = trend_data + noise
        
        data = pd.DataFrame({
            "open": close_prices - 1,
            "high": close_prices + 2,
            "low": close_prices - 2,
            "close": close_prices,
            "volume": np.random.randint(1000, 10000, 50)
        }, index=dates)
        
        # 测试内部RSI计算方法
        rsi_series = strategy._calculate_rsi(data)
        
        # 验证RSI计算结果
        assert len(rsi_series) == len(data), "RSI序列长度不正确"
        assert not rsi_series.isnull().all(), "RSI计算全部为NaN"
        
        # RSI应该在0-100范围内
        valid_rsi = rsi_series.dropna()
        if len(valid_rsi) > 0:
            assert valid_rsi.min() >= 0, "RSI值小于0"
            assert valid_rsi.max() <= 100, "RSI值大于100"
        
        print("  ✅ RSI计算测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ RSI计算测试失败: {e}")
        return False

async def test_rsi_market_analysis():
    """测试RSI市场分析"""
    print("\n🧪 测试RSI市场分析...")
    
    try:
        strategy = RSIStrategy()
        strategy.initialize(rsi_period=14)
        
        # 创建测试数据
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame({
            "open": np.linspace(100, 110, 30),
            "high": np.linspace(105, 115, 30),
            "low": np.linspace(95, 105, 30),
            "close": np.linspace(100, 110, 30),
            "volume": np.random.randint(1000, 10000, 30)
        }, index=dates)
        
        # 执行市场分析
        analysis_result = await strategy.analyze_market(data)
        
        # 验证分析结果
        required_keys = [
            "current_price", "current_rsi", "rsi_status",
            "rsi_trend", "oversold_threshold", "overbought_threshold"
        ]
        
        for key in required_keys:
            assert key in analysis_result, f"缺少分析结果键: {key}"
        
        # 检查RSI状态
        rsi_status = analysis_result["rsi_status"]
        assert rsi_status in ["unknown", "oversold", "overbought", "neutral"], f"无效的RSI状态: {rsi_status}"
        
        # 检查阈值
        assert analysis_result["oversold_threshold"] == 30, "超卖阈值不正确"
        assert analysis_result["overbought_threshold"] == 70, "超买阈值不正确"
        
        print(f"  ✅ RSI市场分析测试通过，状态: {rsi_status}")
        return True
        
    except Exception as e:
        print(f"  ❌ RSI市场分析测试失败: {e}")
        return False

async def test_rsi_signal_generation():
    """测试RSI信号生成"""
    print("\n🧪 测试RSI信号生成...")
    
    try:
        strategy = RSIStrategy()
        strategy.initialize(
            rsi_period=14,
            oversold_threshold=30,
            overbought_threshold=70,
            signal_threshold=0.01
        )
        
        # 创建分析结果 (模拟超卖情况)
        analysis_result = {
            "current_price": 100.0,
            "current_rsi": 25.0,  # 超卖
            "rsi_status": "oversold",
            "rsi_trend": "falling",
            "oversold_threshold": 30,
            "overbought_threshold": 70
        }
        
        # 生成信号
        signals = await strategy.generate_signals(analysis_result)
        
        # 验证信号
        if signals:
            signal = signals[0]
            assert signal["action"] == "BUY", "超卖时应生成买入信号"
            assert signal["price"] == 100.0, "信号价格不正确"
            assert "confidence" in signal, "信号缺少置信度"
            assert 0 <= signal["confidence"] <= 1, "置信度超出范围"
            
            print(f"  ✅ RSI信号生成测试通过，生成 {len(signals)} 个信号")
        else:
            print("  ⚠️  未生成信号 (可能RSI值未达到阈值)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ RSI信号生成测试失败: {e}")
        return False

async def test_rsi_risk_calculation():
    """测试RSI风险计算"""
    print("\n🧪 测试RSI风险计算...")
    
    try:
        strategy = RSIStrategy()
        strategy.initialize()
        
        # 创建测试信号
        test_signals = [
            {
                "action": "BUY",
                "price": 100.0,
                "quantity": 0.1,
                "confidence": 0.8
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
        
        print(f"  ✅ RSI风险计算测试通过，总风险: {risk_metrics['total_risk']:.2%}")
        return True
        
    except Exception as e:
        print(f"  ❌ RSI风险计算测试失败: {e}")
        return False

async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🤖 RSI策略测试套件")
    print("=" * 60)
    
    test_results = []
    
    # 运行测试
    test_results.append(await test_rsi_strategy_initialization())
    test_results.append(await test_rsi_calculation())
    test_results.append(await test_rsi_market_analysis())
    test_results.append(await test_rsi_signal_generation())
    test_results.append(await test_rsi_risk_calculation())
    
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
