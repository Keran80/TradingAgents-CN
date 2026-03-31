# -*- coding: utf-8 -*-
"""
策略构建器示例
================

展示如何使用可视化策略构建器创建和运行策略
"""

from tradingagents.strategies.builder import (
    VisualStrategyBuilder,
    ComponentRegistry,
    StrategyDSL,
    get_template,
    list_templates
)
from tradingagents.strategies.builder.dsl import StrategyBlueprint, IndicatorDefinition, ConditionDefinition, SignalDefinition


def example_load_template():
    """示例：加载预定义模板"""
    print("=" * 50)
    print("示例 1: 加载预定义模板")
    print("=" * 50)

    # 列出所有模板
    templates = list_templates()
    print(f"\n可用模板: {templates}\n")

    # 加载均线交叉模板
    builder = VisualStrategyBuilder()
    builder.load_template("ma_crossover")

    # 查看策略摘要
    summary = builder.get_strategy_summary()
    print("策略摘要:")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # 编译策略
    strategy = builder.compile()
    print(f"\n编译成功: {strategy.name}")

    # 生成代码
    code = builder.generate_code()
    print("\n生成的代码预览:")
    print(code[:500] + "...")


def example_custom_strategy():
    """示例：创建自定义策略"""
    print("\n" + "=" * 50)
    print("示例 2: 创建自定义策略")
    print("=" * 50)

    builder = VisualStrategyBuilder()

    # 创建新策略
    builder.new_strategy(
        name="自定义 MACD + RSI 策略",
        symbols=["000001.SZ", "600519.SH"]
    )

    # 添加指标
    builder.add_indicator("MACD", "MACD", {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9
    })
    builder.add_indicator("RSI", "RSI", {
        "period": 14
    })
    builder.add_indicator("MA20", "MA", {
        "period": 20
    })

    # 添加条件
    builder.add_condition(
        "MACD金叉",
        "MACDCross",
        {"cross_type": "cross_up"}
    )
    builder.add_condition(
        "RSI超卖",
        "IndicatorCondition",
        {
            "indicator_name": "RSI",
            "operator": "lt",
            "compare_type": "value",
            "compare_value": 30
        }
    )

    # 设置买卖信号
    builder.set_buy_signal(
        conditions=["MACD金叉", "RSI超卖"],
        logic="AND"
    )
    builder.set_sell_signal(
        conditions=["RSI超买"],
        logic="OR"
    )

    # 配置参数
    builder.configure(
        initial_capital=2000000,
        commission_rate=0.0003,
        position_size=0.2,
        stop_loss=0.05,
        take_profit=0.15
    )

    # 查看摘要
    summary = builder.get_strategy_summary()
    print("\n自定义策略摘要:")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # 编译并生成代码
    strategy = builder.compile()
    print("\n编译成功!")

    # 保存策略
    filepath = builder.save()
    print(f"策略已保存到: {filepath}")

    return builder


def example_backtest():
    """示例：回测策略"""
    print("\n" + "=" * 50)
    print("示例 3: 回测自定义策略")
    print("=" * 50)

    # 使用刚创建的策略
    builder = example_custom_strategy()

    # 编译策略
    strategy = builder.compile()

    # 获取策略类
    StrategyClass = strategy.to_template_class()

    print(f"\n策略类: {StrategyClass.__name__}")

    # 这里可以继续进行回测
    # from tradingagents.backtest import BacktestEngine
    # engine = BacktestEngine()
    # result = engine.run(StrategyClass, symbols=["000001.SZ"])

    print("\n提示: 使用 BacktestEngine 进行实际回测")
    print("示例: engine.run(StrategyClass, start_date='2024-01-01', end_date='2024-12-31')")


def example_component_registry():
    """示例：组件注册表"""
    print("\n" + "=" * 50)
    print("示例 4: 组件注册表")
    print("=" * 50)

    registry = ComponentRegistry()

    # 列出所有组件
    components = registry.list_components()
    print("\n可用组件:")
    for category, items in components.items():
        print(f"\n  {category}:")
        for item in items:
            print(f"    - {item}")

    # 创建组件
    ma = registry.create_component("indicator", "MA", {"period": 10})
    print(f"\n创建的组件: {ma.name}, 类型: {ma.component_type.value}")


def example_export_code():
    """示例：导出策略代码"""
    print("\n" + "=" * 50)
    print("示例 5: 导出策略代码")
    print("=" * 50)

    builder = VisualStrategyBuilder()
    builder.load_template("macd_crossover")

    # 导出代码
    filepath = builder.export_code()
    print(f"\n策略代码已导出到: {filepath}")

    # 读取导出的代码
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    print(f"\n代码长度: {len(code)} 字符")
    print("\n代码预览 (前1000字符):")
    print(code[:1000])


def run_all_examples():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("TradingAgents-CN 可视化策略构建器示例")
    print("=" * 60)

    example_load_template()
    example_custom_strategy()
    example_component_registry()
    example_export_code()

    print("\n" + "=" * 60)
    print("所有示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_examples()
