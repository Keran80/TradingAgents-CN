# -*- coding: utf-8 -*-
"""
回测模块示例

演示如何使用回测引擎和绩效分析模块进行策略回测
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置输出编码为UTF-8
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from tradingagents.backtest import (
    BacktestEngine, BacktestConfig, BacktestMode,
    PerformanceAnalyzer,
    ReportGenerator, ReportConfig
)
from tradingagents.backtest.engine import moving_average_crossover_strategy


def generate_sample_data(symbol: str, start_date: str, end_date: str, initial_price: float = 10.0) -> pd.DataFrame:
    """生成模拟股票数据"""
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    dates = pd.date_range(start, end, freq='B')  # 工作日
    
    np.random.seed(42)
    
    # 生成价格序列
    returns = np.random.normal(0.0005, 0.02, len(dates))  # 日收益率
    prices = initial_price * (1 + returns).cumprod()
    
    # 生成OHLCV数据
    data = pd.DataFrame({
        'symbol': symbol,
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, len(dates))),
        'high': prices * (1 + np.random.uniform(0, 0.02, len(dates))),
        'low': prices * (1 + np.random.uniform(-0.02, 0, len(dates))),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, len(dates))
    }, index=dates)
    
    return data


def example_basic_backtest():
    """基本回测示例"""
    print("=" * 60)
    print("示例1: 基本回测")
    print("=" * 60)
    
    # 创建配置
    config = BacktestConfig(
        start_date="2024-01-01",
        end_date="2024-06-30",
        initial_cash=1000000,
        mode=BacktestMode.VECTORIZED,  # 使用向量化模式
        commission_rate=0.0003,
        slippage_rate=0.0001
    )
    
    # 创建回测引擎
    engine = BacktestEngine(config)
    
    # 加载数据
    print("\n[1] 加载数据...")
    engine.load_data("000001.SZ", generate_sample_data("000001.SZ", "2024-01-01", "2024-06-30", 10.0))
    print(f"    数据加载完成: {len(engine.data['000001.SZ'])} 条记录")
    
    # 运行回测
    print("\n[2] 运行回测...")
    result = engine.run()
    print(f"    回测完成!")
    
    # 打印结果
    print("\n[3] 回测结果:")
    print(f"    初始资金: ¥{result.initial_cash:,.2f}")
    print(f"    最终资金: ¥{result.final_cash:,.2f}")
    print(f"    总收益率: {result.total_return:.2%}")
    print(f"    年化收益率: {result.annual_return:.2%}")
    print(f"    总交易次数: {result.total_trades}")
    print(f"    胜率: {result.win_rate:.2%}")
    
    return result


def example_event_driven_backtest():
    """事件驱动回测示例"""
    print("\n" + "=" * 60)
    print("示例2: 事件驱动回测 + 均线策略")
    print("=" * 60)
    
    # 创建配置
    config = BacktestConfig(
        start_date="2024-01-01",
        end_date="2024-12-31",
        initial_cash=1000000,
        mode=BacktestMode.EVENT_DRIVEN,
        commission_rate=0.0003,
        slippage_rate=0.0001
    )
    
    # 创建回测引擎
    engine = BacktestEngine(config)
    
    # 加载数据
    print("\n[1] 加载数据...")
    data = generate_sample_data("000001.SZ", "2024-01-01", "2024-12-31", 10.0)
    engine.load_data("000001.SZ", data)
    print(f"    数据加载完成: {len(engine.data['000001.SZ'])} 条记录")
    
    # 设置策略
    print("\n[2] 设置均线交叉策略...")
    engine.set_strategy(
        lambda data, current_date, positions: moving_average_crossover_strategy(
            data, current_date, positions, short_window=5, long_window=20
        )
    )
    
    # 运行回测
    print("\n[3] 运行回测...")
    result = engine.run()
    print(f"    回测完成!")
    
    # 打印结果
    print("\n[4] 回测结果:")
    print(f"    初始资金: ¥{result.initial_cash:,.2f}")
    print(f"    最终资金: ¥{result.final_cash:,.2f}")
    print(f"    总收益率: {result.total_return:.2%}")
    print(f"    年化收益率: {result.annual_return:.2%}")
    print(f"    总交易次数: {result.total_trades}")
    
    return result


def example_performance_analysis(result):
    """绩效分析示例"""
    print("\n" + "=" * 60)
    print("示例3: 绩效分析")
    print("=" * 60)
    
    # 创建分析器
    analyzer = PerformanceAnalyzer(risk_free_rate=0.03)
    
    # 生成净值曲线（如果没有）
    if result.equity_curve is None or len(result.equity_curve) == 0:
        # 使用模拟净值
        dates = pd.date_range(result.start_date, result.end_date, freq='B')
        equity = result.initial_cash * (1 + result.total_return * np.linspace(0, 1, len(dates)))
        equity_curve = pd.DataFrame({'equity': equity}, index=dates)
    else:
        equity_curve = result.equity_curve
    
    # 完整分析
    print("\n[1] 计算绩效指标...")
    metrics = analyzer.analyze(
        equity_curve=equity_curve,
        returns=result.daily_returns,
        trades=result.trades
    )
    
    # 打印报告
    print("\n[2] 绩效摘要:")
    print(analyzer.summary_report(metrics))
    
    return metrics


def example_report_generation(result, metrics):
    """报告生成示例"""
    print("\n" + "=" * 60)
    print("示例4: 生成HTML报告")
    print("=" * 60)
    
    # 创建报告生成器
    report_config = ReportConfig(
        strategy_name="均线交叉策略",
        include_charts=True,
        include_trades=True
    )
    generator = ReportGenerator(report_config)
    
    # 生成净值曲线（如果没有）
    if result.equity_curve is None or len(result.equity_curve) == 0:
        dates = pd.date_range(result.start_date, result.end_date, freq='B')
        equity = result.initial_cash * (1 + result.total_return * np.linspace(0, 1, len(dates)))
        equity_curve = pd.DataFrame({'equity': equity}, index=dates)
    else:
        equity_curve = result.equity_curve
    
    # 生成HTML报告
    print("\n[1] 生成HTML报告...")
    html_report = generator.generate_html_report(
        metrics=metrics,
        equity_curve=equity_curve,
        trades=result.trades
    )
    
    # 保存报告
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "backtest_report.html"
    )
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_report)
    print(f"    报告已保存: {report_path}")
    
    # 生成JSON导出
    print("\n[2] 生成JSON导出...")
    json_export = generator.generate_json_export(
        metrics=metrics,
        equity_curve=equity_curve,
        trades=result.trades
    )
    json_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "backtest_report.json"
    )
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(json_export)
    print(f"    JSON已保存: {json_path}")
    
    # 生成Markdown报告
    print("\n[3] 生成Markdown报告...")
    md_report = generator.generate_markdown_report(
        metrics=metrics,
        equity_curve=equity_curve,
        trades=result.trades
    )
    md_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "backtest_report.md"
    )
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    print(f"    Markdown已保存: {md_path}")


def example_multi_symbol_backtest():
    """多股票回测示例"""
    print("\n" + "=" * 60)
    print("示例5: 多股票组合回测")
    print("=" * 60)
    
    # 创建配置
    config = BacktestConfig(
        start_date="2024-01-01",
        end_date="2024-06-30",
        initial_cash=2000000,
        mode=BacktestMode.VECTORIZED
    )
    
    engine = BacktestEngine(config)
    
    # 加载多只股票
    print("\n[1] 加载多只股票数据...")
    symbols = ["000001.SZ", "000002.SZ", "600000.SH"]
    for i, symbol in enumerate(symbols):
        data = generate_sample_data(symbol, "2024-01-01", "2024-06-30", 10.0 + i * 5)
        engine.load_data(symbol, data)
        print(f"    {symbol}: {len(data)} 条记录")
    
    # 运行回测
    print("\n[2] 运行组合回测...")
    result = engine.run()
    print(f"    回测完成!")
    
    print("\n[3] 组合回测结果:")
    print(f"    总收益率: {result.total_return:.2%}")
    print(f"    年化收益率: {result.annual_return:.2%}")
    print(f"    总交易次数: {result.total_trades}")
    
    return result


def example_comparison_backtest():
    """对比回测示例"""
    print("\n" + "=" * 60)
    print("示例6: 策略对比回测")
    print("=" * 60)
    
    # 数据
    data = generate_sample_data("000001.SZ", "2024-01-01", "2024-12-31", 10.0)
    
    # 策略1: 5/20均线
    print("\n[1] 策略1: 5/20均线交叉...")
    config1 = BacktestConfig(mode=BacktestMode.VECTORIZED)
    engine1 = BacktestEngine(config1)
    engine1.load_data("000001.SZ", data)
    result1 = engine1.run()
    print(f"    收益率: {result1.total_return:.2%}")
    
    # 策略2: 10/30均线
    print("\n[2] 策略2: 10/30均线交叉...")
    config2 = BacktestConfig(mode=BacktestMode.VECTORIZED)
    engine2 = BacktestEngine(config2)
    engine2.load_data("000001.SZ", data)
    result2 = engine2.run()
    print(f"    收益率: {result2.total_return:.2%}")
    
    # 对比结果
    print("\n[3] 对比结果:")
    print("-" * 40)
    print(f"策略          | 收益率    | 交易次数")
    print("-" * 40)
    print(f"5/20均线      | {result1.total_return:>8.2%} | {result1.total_trades:>6}")
    print(f"10/30均线     | {result2.total_return:>8.2%} | {result2.total_trades:>6}")
    print("-" * 40)


def main():
    """主函数"""
    print("\n" + "#" * 60)
    print("# TradingAgents-CN 回测模块示例")
    print("#" * 60)
    
    # 示例1: 基本回测
    result = example_basic_backtest()
    
    # 示例2: 事件驱动回测
    result2 = example_event_driven_backtest()
    
    # 示例3: 绩效分析
    metrics = example_performance_analysis(result2)
    
    # 示例4: 报告生成
    example_report_generation(result2, metrics)
    
    # 示例5: 多股票回测
    example_multi_symbol_backtest()
    
    # 示例6: 策略对比
    example_comparison_backtest()
    
    print("\n" + "#" * 60)
    print("# 所有示例执行完成!")
    print("#" * 60)


if __name__ == "__main__":
    main()
