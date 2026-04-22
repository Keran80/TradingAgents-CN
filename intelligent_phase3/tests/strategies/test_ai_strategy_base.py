#!/usr/bin/env python3
"""
AI策略基类测试
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.strategies.ai_strategy_base import AIStrategyBase, StrategyFactory
import pandas as pd
import numpy as np

class TestStrategy(AIStrategyBase):
    """测试策略"""
    
    def __init__(self):
        super().__init__(name="测试策略", version="1.0.0")
        self.default_params = {"test_param": 42}
    
    def _on_initialize(self):
        self.initialized_called = True
    
    async def analyze_market(self, data):
        return {"test_analysis": True}
    
    async def generate_signals(self, analysis_result):
        return [{"action": "TEST", "confidence": 0.8}]
    
    def calculate_risk(self, signals, portfolio_value):
        return {"total_risk": 0.1}

async def test_strategy_initialization():
    """测试策略初始化"""
    print("🧪 测试策略初始化...")
    
    try:
        strategy = TestStrategy()
        
        # 测试默认初始化
        success = strategy.initialize(test_param=42)
        
        assert success, "策略初始化失败"
        assert strategy.initialized, "策略未标记为已初始化"
        assert strategy.name == "测试策略", "策略名称不正确"
        assert strategy.version == "1.0.0", "策略版本不正确"
        assert strategy.parameters["test_param"] == 42, "策略参数不正确"
        assert hasattr(strategy, 'initialized_called'), "初始化方法未调用"
        
        print("  ✅ 策略初始化测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 策略初始化测试失败: {e}")
        return False

async def test_market_analysis():
    """测试市场分析"""
    print("\n🧪 测试市场分析...")
    
    try:
        strategy = TestStrategy()
        strategy.initialize()
        
        # 创建测试数据
        data = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [105, 106, 107],
            "low": [95, 96, 97],
            "close": [100, 101, 102],
            "volume": [1000, 1100, 1200]
        })
        
        # 执行市场分析
        analysis_result = await strategy.analyze_market(data)
        
        # 验证分析结果
        assert "test_analysis" in analysis_result, "分析结果缺少test_analysis"
        assert analysis_result["test_analysis"] == True, "分析结果不正确"
        
        print("  ✅ 市场分析测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 市场分析测试失败: {e}")
        return False

async def test_signal_generation():
    """测试信号生成"""
    print("\n🧪 测试信号生成...")
    
    try:
        strategy = TestStrategy()
        strategy.initialize()
        
        # 执行信号生成
        analysis_result = {"test_analysis": True}
        signals = await strategy.generate_signals(analysis_result)
        
        # 验证信号
        assert len(signals) == 1, "信号数量不正确"
        signal = signals[0]
        assert signal["action"] == "TEST", "信号动作不正确"
        assert signal["confidence"] == 0.8, "信号置信度不正确"
        
        print("  ✅ 信号生成测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 信号生成测试失败: {e}")
        return False

async def test_risk_calculation():
    """测试风险计算"""
    print("\n🧪 测试风险计算...")
    
    try:
        strategy = TestStrategy()
        strategy.initialize()
        
        # 测试信号
        test_signals = [{"action": "TEST", "confidence": 0.8}]
        
        # 计算风险
        portfolio_value = 100000.0
        risk_metrics = strategy.calculate_risk(test_signals, portfolio_value)
        
        # 验证风险指标
        assert "total_risk" in risk_metrics, "风险指标缺少total_risk"
        assert risk_metrics["total_risk"] == 0.1, "风险计算不正确"
        
        print("  ✅ 风险计算测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 风险计算测试失败: {e}")
        return False

async def test_strategy_factory():
    """测试策略工厂"""
    print("\n🧪 测试策略工厂...")
    
    try:
        # 注册策略
        StrategyFactory.register_strategy("test_strategy", TestStrategy)
        
        # 创建策略实例
        strategy = StrategyFactory.create_strategy("test_strategy", test_param=42)
        
        assert strategy is not None, "策略创建失败"
        assert isinstance(strategy, TestStrategy), "创建的策略类型不正确"
        
        # 列出策略
        strategies = StrategyFactory.list_strategies()
        assert "test_strategy" in strategies, "策略未在工厂中列出"
        
        print("  ✅ 策略工厂测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 策略工厂测试失败: {e}")
        return False

async def test_performance_report():
    """测试性能报告"""
    print("\n🧪 测试性能报告...")
    
    try:
        strategy = TestStrategy()
        strategy.initialize()
        
        # 记录性能指标
        strategy.record_performance("test_metric", 0.85)
        strategy.record_performance("another_metric", 42.0)
        
        # 获取性能报告
        report = strategy.get_performance_report()
        
        # 验证报告
        assert report["strategy_name"] == "测试策略"
        assert report["strategy_version"] == "1.0.0"
        assert report["initialized"] == True
        assert "test_metric" in report["performance_metrics"]
        assert "another_metric" in report["performance_metrics"]
        assert report["performance_metrics"]["test_metric"] == 0.85
        assert report["performance_metrics"]["another_metric"] == 42.0
        assert "report_time" in report
        
        print("  ✅ 性能报告测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 性能报告测试失败: {e}")
        return False

async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🤖 AI策略基类测试套件")
    print("=" * 60)
    
    test_results = []
    
    # 运行测试
    test_results.append(await test_strategy_initialization())
    test_results.append(await test_market_analysis())
    test_results.append(await test_signal_generation())
    test_results.append(await test_risk_calculation())
    test_results.append(await test_strategy_factory())
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
