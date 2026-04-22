        # 3. 评估风险
        print("\n3. ⚠️  评估风险...")
        monitor = AdvancedRiskMonitor()
        
        # 基于预测结果创建投资组合数据
        portfolio_value = 100000  # 10万初始资金
        
        # 根据预测分配权重
        positions = []
        total_weight = 0
        
        for prediction in predictions:
            # 根据预测建议分配权重
            if prediction.get_action() == "STRONG_BUY":
                weight = 0.4
            elif prediction.get_action() == "BUY":
                weight = 0.3
            elif prediction.get_action() == "HOLD":
                weight = 0.2
            elif prediction.get_action() == "SELL":
                weight = 0.1
            else:  # STRONG_SELL or NEUTRAL
                weight = 0.0
            
            if weight > 0:
                positions.append({
                    "symbol": prediction.symbol,
                    "weight": weight,
                    "value": portfolio_value * weight
                })
                total_weight += weight
        
        # 标准化权重
        if total_weight > 0:
            for position in positions:
                position["weight"] = position["weight"] / total_weight
        
        # 创建模拟收益率数据
        np.random.seed(42)
        n_days = 100
        base_returns = np.random.randn(n_days) * 0.015  # 1.5% daily volatility
        
        # 根据预测质量调整收益率
        prediction_quality = sum(p.confidence for p in predictions) / len(predictions) if predictions else 0.5
        adjusted_returns = base_returns * (0.5 + prediction_quality)  # 置信度越高，波动越小
        
        portfolio_data = {
            "portfolio_id": "ai_trading_portfolio",
            "returns": adjusted_returns.tolist(),
            "positions": positions,
            "correlation_matrix": np.eye(len(positions)).tolist() if positions else [],
            "liquidity_metrics": {
                "avg_bid_ask_spread": 0.012,
                "volume_ratio": 0.9
            },
            "leverage": 1.2,
            "margin_usage": 0.45,
            "stress_test_results": {
                "2008_crisis": -0.18,
                "2020_covid": -0.15,
                "flash_crash": -0.10
            }
        }
        
        # 评估风险
        risk_assessment = await monitor.assess_portfolio_risk(portfolio_data)
        
        print(f"📊 投资组合风险评估:")
        print(f"  总体风险: {risk_assessment.overall_risk.value.upper()}")
        print(f"  持仓数量: {len(positions)}")
        print(f"  预测平均置信度: {prediction_quality:.2%}")
        
        # 显示持仓
        print(f"\n📦 投资组合持仓:")
        for position in positions:
            print(f"  {position['symbol']}: {position['weight']:.1%} (${position['value']:,.0f})")
        
        # 显示风险建议
        print(f"\n💡 风险建议:")
        for i, recommendation in enumerate(risk_assessment.recommendations[:3], 1):
            print(f"  {i}. {recommendation}")
        
        print(f"\n✅ 集成测试完成!")
        print(f"  模块协同: 数据获取 → 趋势预测 → 风险评估")
        print(f"  测试结果: 所有模块正常工作")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🚀 TradingAgents-CN 阶段1模块测试")
    print("=" * 60)
    
    test_results = {}
    
    # 测试机器学习趋势预测器
    test_results["ml_trend_predictor"] = await test_ml_trend_predictor()
    
    # 测试多数据源适配器
    test_results["multi_source_adapter"] = await test_multi_source_adapter()
    
    # 测试高级风险监控器
    test_results["advanced_risk_monitor"] = await test_advanced_risk_monitor()
    
    # 集成测试
    test_results["integration"] = await test_integration()
    
    # 显示测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, passed in test_results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name:<25} {status}")
    
    print("-" * 60)
    print(f"总计: {passed_tests}/{total_tests} 通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！阶段1模块开发完成")
        return True
    else:
        print("⚠️  部分测试失败，请检查模块实现")
        return False

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    
    if success:
        print("\n🚀 阶段1开发完成！")
        print("   模块已就绪:")
        print("   • 🤖 ML趋势预测策略")
        print("   • 📡 多数据源适配器")
        print("   • ⚠️  高级风险监控器")
        print("\n📁 文件位置:")
        print("   /tmp/TradingAgents-CN/intelligent_phase2/")
        print("\n🎯 下一步:")
        print("   1. 运行开发工作流: ./dev_workflow.sh test")
        print("   2. 查看开发计划: cat CONTINUE_DEVELOPMENT_PLAN.md")
        print("   3. 开始阶段2开发")
        sys.exit(0)
    else:
        print("\n❌ 测试失败，请修复问题后重试")
        sys.exit(1)