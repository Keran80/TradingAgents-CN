#!/usr/bin/env python3
"""
简单测试脚本 - 验证阶段1模块
"""

import asyncio
import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_basic():
    """基础测试"""
    print("🧪 测试阶段1模块基础功能...")
    
    try:
        # 测试导入
        print("1. 测试模块导入...")
        from intelligent_phase2.strategies.ml_trend_predictor import MLTrendPredictor
        from intelligent_phase2.data_sources.multi_source_adapter import MultiSourceAdapter, DataRequest, DataSourceType
        from intelligent_phase2.risk_management.advanced_risk_monitor import AdvancedRiskMonitor
        
        print("✅ 模块导入成功")
        
        # 测试创建对象
        print("\n2. 测试对象创建...")
        predictor = MLTrendPredictor(model_type="random_forest")
        print(f"✅ 创建预测器: {predictor.model_type}")
        
        monitor = AdvancedRiskMonitor()
        print(f"✅ 创建风险监控器")
        
        print("\n3. 测试数据源适配器...")
        async with MultiSourceAdapter() as adapter:
            print(f"✅ 创建数据源适配器")
            print(f"   可用数据源: {len([s for s, avail in adapter.sources_available.items() if avail])}")
        
        print("\n🎉 基础测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_quick():
    """快速功能测试"""
    print("\n🚀 快速功能测试...")
    
    try:
        import numpy as np
        import pandas as pd
        from datetime import datetime
        
        # 测试机器学习预测器
        print("1. 测试ML预测器...")
        from intelligent_phase2.strategies.ml_trend_predictor import MLTrendPredictor
        
        predictor = MLTrendPredictor(model_type="random_forest")
        
        # 创建模拟数据
        dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
        historical_data = pd.DataFrame({
            'close': np.random.randn(50).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, 50)
        }, index=dates)
        
        features = await predictor.prepare_features(historical_data)
        print(f"✅ 特征准备: {features.shape if not features.empty else '空'}")
        
        if not features.empty:
            await predictor.train(features)
            print(f"✅ 模型训练完成")
        
        # 测试风险监控器
        print("\n2. 测试风险监控器...")
        from intelligent_phase2.risk_management.advanced_risk_monitor import AdvancedRiskMonitor
        
        monitor = AdvancedRiskMonitor()
        
        portfolio_data = {
            "portfolio_id": "test_portfolio",
            "returns": np.random.randn(20).tolist(),
            "positions": [
                {"symbol": "AAPL", "weight": 0.5, "value": 50000},
                {"symbol": "GOOGL", "weight": 0.3, "value": 30000},
                {"symbol": "MSFT", "weight": 0.2, "value": 20000}
            ]
        }
        
        risk_assessment = await monitor.assess_portfolio_risk(portfolio_data)
        print(f"✅ 风险评估: {risk_assessment.overall_risk.value}")
        print(f"   指标数量: {len(risk_assessment.metrics)}")
        
        print("\n🎉 快速测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("=" * 60)
    print("TradingAgents-CN 阶段1模块验证")
    print("=" * 60)
    
    # 运行基础测试
    basic_ok = await test_basic()
    
    if basic_ok:
        # 运行快速测试
        quick_ok = await test_quick()
    else:
        quick_ok = False
    
    # 显示结果
    print("\n" + "=" * 60)
    print("测试结果:")
    print(f"基础测试: {'✅ 通过' if basic_ok else '❌ 失败'}")
    print(f"快速测试: {'✅ 通过' if quick_ok else '❌ 失败'}")
    
    if basic_ok and quick_ok:
        print("\n🎉 所有测试通过!")
        print("\n📁 生成的模块:")
        print("  • intelligent_phase2/strategies/ml_trend_predictor.py")
        print("  • intelligent_phase2/data_sources/multi_source_adapter.py")
        print("  • intelligent_phase2/risk_management/advanced_risk_monitor.py")
        print("\n🚀 阶段1开发完成!")
        return True
    else:
        print("\n⚠️  测试失败，请检查模块实现")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)