#!/usr/bin/env python3
"""
Phase 1 智能增强演示脚本
展示四个核心组件的功能
"""

import asyncio
import sys
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append('./src')

async def demo_intelligent_plugin_system():
    """演示智能插件系统"""
    print("=" * 50)
    print("🧩 演示智能插件系统")
    print("=" * 50)
    
    from plugins.intelligent_plugin_system import IntelligentPluginSystem, DataSourcePlugin, StrategyPlugin
    
    # 创建插件系统
    plugin_system = IntelligentPluginSystem()
    
    # 注册插件
    data_source = DataSourcePlugin()
    strategy = StrategyPlugin()
    
    plugin_system.register_plugin("data_source", data_source)
    plugin_system.register_plugin("strategy", strategy)
    
    # 列出插件
    print("📋 已注册插件:")
    for plugin_name in plugin_system.list_plugins():
        print(f"  • {plugin_name}")
    
    # 使用插件
    data_plugin = plugin_system.get_plugin("data_source")
    if data_plugin:
        data = await data_plugin.fetch_data("AAPL")
        print(f"📊 获取数据: {data}")
    
    strategy_plugin = plugin_system.get_plugin("strategy")
    if strategy_plugin:
        result = await strategy_plugin.execute_strategy(data)
        print(f"🎯 策略执行结果: {result}")
    
    print("✅ 智能插件系统演示完成\n")

async def demo_intelligent_event_engine():
    """演示智能事件引擎"""
    print("=" * 50)
    print("⚡ 演示智能事件引擎")
    print("=" * 50)
    
    from events.intelligent_event_engine import IntelligentEventEngine, Event, market_data_handler, trade_signal_handler
    
    # 创建事件引擎
    event_engine = IntelligentEventEngine()
    
    # 注册事件处理器
    event_engine.register_handler("market_data", market_data_handler)
    event_engine.register_handler("trade_signal", trade_signal_handler)
    
    # 启动事件引擎
    await event_engine.start()
    print("✅ 事件引擎已启动")
    
    # 发送事件
    market_event = Event(type="market_data", data={"symbol": "AAPL", "price": 150.25})
    trade_event = Event(type="trade_signal", data={"action": "BUY", "price": 150.00})
    
    await event_engine.put_event(market_event)
    await event_engine.put_event(trade_event)
    
    # 等待事件处理
    await asyncio.sleep(0.5)
    
    # 停止事件引擎
    await event_engine.stop()
    print("✅ 事件引擎已停止\n")

async def demo_intelligent_data_adapter():
    """演示智能数据适配器"""
    print("=" * 50)
    print("📊 演示智能数据适配器")
    print("=" * 50)
    
    from data.intelligent_data_adapter import IntelligentDataAdapter, MockDataAdapter
    from datetime import datetime, timedelta
    
    # 创建数据适配器
    data_adapter = IntelligentDataAdapter()
    
    # 注册模拟数据适配器
    mock_adapter = MockDataAdapter()
    data_adapter.register_adapter("mock", mock_adapter)
    
    # 设置时间范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # 获取数据
    try:
        data = await data_adapter.fetch_intelligent_data("AAPL", start_date, end_date)
        print(f"✅ 获取数据成功，数据形状: {data.shape}")
        print(f"   列名: {list(data.columns)}")
        print(f"   数据预览:")
        print(data.head())
        
        # 检查缓存
        cache_info = data_adapter.get_cache_info()
        print(f"📦 缓存信息: {cache_info}")
        
    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
    
    print("✅ 智能数据适配器演示完成\n")

async def demo_ai_integration_framework():
    """演示 AI 集成框架"""
    print("=" * 50)
    print("🤖 演示 AI 集成框架")
    print("=" * 50)
    
    from ai.integration_framework import AIIntegrationFramework
    
    # 创建 AI 集成框架（使用模拟模式）
    ai_framework = AIIntegrationFramework()
    
    # 连接 AI 服务
    await ai_framework.connect()
    
    # 市场分析
    market_data = {
        "symbol": "AAPL",
        "price": 150.25,
        "volume": 1000000,
        "trend": "up"
    }
    
    analysis = await ai_framework.analyze_market(market_data)
    print("📈 市场分析结果:")
    print(f"   分析: {analysis.get('analysis')}")
    print(f"   置信度: {analysis.get('confidence')}")
    print(f"   建议: {analysis.get('recommendation')}")
    print(f"   风险等级: {analysis.get('risk_level')}")
    
    # 策略生成
    requirements = {
        "risk_tolerance": "medium",
        "investment_horizon": "short_term",
        "capital": 100000
    }
    
    strategy = await ai_framework.generate_strategy(requirements)
    print("\n🎯 策略生成结果:")
    print(f"   策略名称: {strategy.get('strategy_name')}")
    print(f"   参数: {strategy.get('parameters')}")
    print(f"   预期收益: {strategy.get('expected_return')}")
    print(f"   最大回撤: {strategy.get('max_drawdown')}")
    
    # 风险评估
    portfolio = {
        "holdings": {"AAPL": 0.4, "GOOGL": 0.3, "MSFT": 0.3},
        "total_value": 150000,
        "leverage": 1.0
    }
    
    risk = await ai_framework.risk_assessment(portfolio)
    print("\n🛡️ 风险评估结果:")
    print(f"   总体风险: {risk.get('overall_risk')}")
    print(f"   市场风险: {risk.get('market_risk')}")
    print(f"   流动性风险: {risk.get('liquidity_risk')}")
    print(f"   建议: {risk.get('recommendations')}")
    
    print("✅ AI 集成框架演示完成\n")

async def demo_integrated_system():
    """演示集成系统"""
    print("=" * 50)
    print("🚀 演示集成系统")
    print("=" * 50)
    
    print("🎯 演示 Phase 1 四个核心组件的集成工作流程:")
    print("")
    print("1. 📊 数据获取 → 2. 🤖 AI 分析 → 3. 🎯 策略生成 → 4. ⚡ 事件执行")
    print("")
    
    # 导入所有组件
    from plugins.intelligent_plugin_system import IntelligentPluginSystem, DataSourcePlugin, StrategyPlugin
    from events.intelligent_event_engine import IntelligentEventEngine, Event
    from data.intelligent_data_adapter import IntelligentDataAdapter, MockDataAdapter
    from ai.integration_framework import AIIntegrationFramework
    from datetime import datetime, timedelta
    
    # 1. 初始化所有组件
    print("🔧 初始化所有组件...")
    
    plugin_system = IntelligentPluginSystem()
    event_engine = IntelligentEventEngine()
    data_adapter = IntelligentDataAdapter()
    ai_framework = AIIntegrationFramework()
    
    # 注册组件
    data_adapter.register_adapter("mock", MockDataAdapter())
    plugin_system.register_plugin("data_source", DataSourcePlugin())
    plugin_system.register_plugin("strategy", StrategyPlugin())
    
    # 连接 AI
    await ai_framework.connect()
    
    print("✅ 所有组件初始化完成")
    print("")
    
    # 2. 完整工作流程演示
    print("🔄 开始完整工作流程演示:")
    print("")
    
    # 步骤 1: 获取数据
    print("步骤 1: 📊 获取数据")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    try:
        data = await data_adapter.fetch_intelligent_data("AAPL", start_date, end_date)
        print(f"   ✅ 获取 {len(data)} 条数据")
    except Exception as e:
        print(f"   ❌ 获取数据失败: {e}")
        return
    
    # 步骤 2: AI 分析
    print("步骤 2: 🤖 AI 分析")
    market_data = {
        "symbol": "AAPL",
        "current_price": data['close'].iloc[-1] if len(data) > 0 else 150.0,
        "trend": "up" if len(data) > 1 and data['close'].iloc[-1] > data['close'].iloc[-2] else "down"
    }
    
    analysis = await ai_framework.analyze_market(market_data)
    print(f"   ✅ 分析完成: {analysis.get('analysis')}")
    
    # 步骤 3: 生成策略
    print("步骤 3: 🎯 生成策略")
    requirements = {
        "market_analysis": analysis,
        "risk_tolerance": "medium"
    }
    
    strategy = await ai_framework.generate_strategy(requirements)
    print(f"   ✅ 策略生成: {strategy.get('strategy_name')}")
    
    # 步骤 4: 执行策略
    print("步骤 4: ⚡ 执行策略")
    
    # 启动事件引擎
    await event_engine.start()
    
    # 创建交易事件
    trade_event = Event(
        type="trade_execution",
        data={
            "strategy": strategy.get('strategy_name'),
            "action": "BUY",
            "symbol": "AAPL",
            "price": market_data['current_price'],
            "confidence": analysis.get('confidence', 0.5)
        },
        priority=1
    )
    
    # 发送事件
    await event_engine.put_event(trade_event)
    print(f"   ✅ 交易事件已发送")
    
    # 等待事件处理
    await asyncio.sleep(0.5)
    
    # 停止事件引擎
    await event_engine.stop()
    
    print("")
    print("🎉 完整工作流程演示完成！")
    print("=" * 50)

async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("   🚀 Phase 1 智能增强系统演示")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 演示各个组件
        await demo_intelligent_plugin_system()
        await demo_intelligent_event_engine()
        await demo_intelligent_data_adapter()
        await demo_ai_integration_framework()
        
        # 演示集成系统
        await demo_integrated_system()
        
        print("🎊 所有演示完成！")
        print()
        print("📁 项目目录: /tmp/TradingAgents-CN/intelligent_phase1/")
        print("📄 核心文件:")
        print("   • src/plugins/intelligent_plugin_system.py")
        print("   • src/events/intelligent_event_engine.py")
        print("   • src/data/intelligent_data_adapter.py")
        print("   • src/ai/integration_framework.py")
        print()
        print("🚀 下一步:")
        print("   1. 运行测试: python3 -m pytest tests/")
        print("   2. 扩展功能: 添加更多插件和适配器")
        print("   3. 集成 Qwen API: 配置实际的 API key")
        print("   4. 性能优化: 优化事件引擎和数据缓存")
        print()
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())