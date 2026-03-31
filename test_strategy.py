# -*- coding: utf-8 -*-
"""
策略库测试脚本
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.astock_utils import AStockData
from tradingagents.agents.trader.strategy import (
    MACrossoverStrategy, RSIStrategy, MACDStrategy, 
    BollingerStrategy, CombinedStrategy, create_strategy,
    analyze_stock, Signal
)
from datetime import datetime, timedelta


def test_with_real_data():
    """使用真实数据测试策略"""
    print("=" * 60)
    print("策略库测试 - 真实数据")
    print("=" * 60)
    
    # 获取平安银行日线数据
    ticker = "000001.SZ"
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=120)).strftime('%Y%m%d')
    
    print(f"\n获取 {ticker} 日线数据 ({start_date} ~ {end_date})...")
    df = AStockData.get_daily(ticker, start_date, end_date)
    
    if df.empty:
        print("获取数据失败，使用模拟数据测试")
        return test_with_mock_data()
    
    print(f"获取成功，共 {len(df)} 条数据")
    
    # 重命名列为英文（简化处理）
    rename_map = {
        '日期': 'date', '开盘': 'open', '收盘': 'close',
        '最高': 'high', '最低': 'low', '成交量': 'volume'
    }
    df = df.rename(columns=rename_map)
    
    # 测试各策略
    strategies = [
        ("MA_Crossover(5,20)", MACrossoverStrategy(5, 20)),
        ("RSI(14)", RSIStrategy()),
        ("MACD(12,26,9)", MACDStrategy()),
        ("Bollinger(20,2.0)", BollingerStrategy()),
    ]
    
    print("\n" + "-" * 60)
    print("单策略测试")
    print("-" * 60)
    
    for name, strategy in strategies:
        result = strategy.generate_signal(df)
        signal_icon = {
            Signal.BUY: "买入",
            Signal.SELL: "卖出",
            Signal.HOLD: "观望"
        }.get(result['signal'], "未知")
        
        print(f"\n【{name}】")
        print(f"  信号: {signal_icon} (置信度: {result['confidence']:.2f})")
        print(f"  原因: {result['reason']}")
    
    # 测试组合策略
    print("\n" + "-" * 60)
    print("组合策略测试")
    print("-" * 60)
    
    combined = CombinedStrategy([
        MACrossoverStrategy(5, 20),
        RSIStrategy(),
        MACDStrategy(),
    ])
    
    result = combined.generate_signal(df)
    signal_icon = {
        Signal.BUY: "买入",
        Signal.SELL: "卖出",
        Signal.HOLD: "观望"
    }.get(result['signal'], "未知")
    
    print(f"\n【组合策略】")
    print(f"  信号: {signal_icon} (置信度: {result['confidence']:.2f})")
    print(f"  原因: {result['reason']}")
    
    # 测试便捷函数
    print("\n" + "-" * 60)
    print("便捷函数测试")
    print("-" * 60)
    
    for strategy_type in ['ma_crossover', 'rsi', 'macd', 'bollinger', 'combined']:
        result = analyze_stock(df, strategy_type)
        signal_icon = {
            Signal.BUY: "买入",
            Signal.SELL: "卖出",
            Signal.HOLD: "观望"
        }.get(result['signal'], "未知")
        
        print(f"\n{strategy_type}: {signal_icon} ({result['confidence']:.2f})")
        print(f"  原因: {result['reason'][:60]}...")
    
    return True


def test_with_mock_data():
    """使用模拟数据测试策略"""
    print("\n使用模拟数据测试...")
    import pandas as pd
    import numpy as np
    
    # 生成模拟数据
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    np.random.seed(42)
    
    # 模拟上涨趋势
    base_price = 100
    prices = base_price + np.cumsum(np.random.randn(100) * 2)
    prices = np.maximum(prices, 50)  # 防止负价格
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices * 0.99,
        'close': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'volume': np.random.randint(1000000, 10000000, 100)
    })
    
    # 测试策略
    strategy = MACrossoverStrategy(5, 20)
    result = strategy.generate_signal(df)
    
    print(f"模拟数据测试结果: {result['signal'].value}")
    print(f"原因: {result['reason']}")
    
    return True


if __name__ == "__main__":
    try:
        test_with_real_data()
        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
