# -*- coding: utf-8 -*-
"""
TradingAgents-CN 回测示例

演示如何在回测环境中使用 Phase 1 模块
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradingagents.execution import (
    SimulatorBroker,
    TradingEngine,
    Signal,
    SignalType,
    Account,
    Portfolio
)

# AkShare utilities are optional for examples
try:
    from tradingagents.dataflows.akshare_stock_utils import AkShareUtils as AkShareStockUtils
except ImportError:
    AkShareStockUtils = None


def generate_mock_data(symbol: str, days: int = 30, start_price: float = 12.0) -> pd.DataFrame:
    """生成模拟行情数据"""
    import numpy as np

    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    np.random.seed(42)

    prices = start_price * (1 + np.cumsum(np.random.randn(days) * 0.02))
    volumes = np.random.randint(1000000, 5000000, days)

    df = pd.DataFrame({
        'date': dates,
        'symbol': symbol,
        'open': prices * (1 + np.random.randn(days) * 0.005),
        'high': prices * (1 + np.abs(np.random.randn(days)) * 0.01),
        'low': prices * (1 - np.abs(np.random.randn(days)) * 0.01),
        'close': prices,
        'volume': volumes
    })
    return df


def simple_strategy(data: pd.DataFrame, symbol: str) -> Signal:
    """
    简单策略：MA5 上穿 MA20 买入，下穿卖出
    """
    # 简化：使用最后一天数据判断
    if len(data) < 20:
        return None

    ma5 = data['close'].rolling(5).mean().iloc[-1]
    ma20 = data['close'].rolling(20).mean().iloc[-1]
    ma5_prev = data['close'].rolling(5).mean().iloc[-2]
    ma20_prev = data['close'].rolling(20).mean().iloc[-2]

    price = data['close'].iloc[-1]

    # 金叉
    if ma5_prev <= ma20_prev and ma5 > ma20:
        return Signal(
            symbol=symbol,
            signal_type=SignalType.BUY,
            price=price,
            quantity=1000,
            confidence=0.8,
            reason=f"MA金叉: MA5={ma5:.2f} > MA20={ma20:.2f}",
            strategy_name="SimpleMAStrategy"
        )
    # 死叉
    elif ma5_prev >= ma20_prev and ma5 < ma20:
        return Signal(
            symbol=symbol,
            signal_type=SignalType.SELL,
            price=price,
            quantity=0,  # 全部卖出
            confidence=0.8,
            reason=f"MA死叉: MA5={ma5:.2f} < MA20={ma20:.2f}",
            strategy_name="SimpleMAStrategy"
        )

    return None


def run_backtest():
    """运行回测"""
    print("=" * 60)
    print("TradingAgents-CN 回测示例")
    print("=" * 60)

    # 初始化
    broker = SimulatorBroker()
    broker.connect()

    engine = TradingEngine(
        broker=broker,
        initial_capital=1000000.0,
    )

    # 模拟数据
    symbol = "000001.SZ"
    print(f"\n生成模拟数据: {symbol}")
    data = generate_mock_data(symbol, days=30, start_price=12.0)

    print("\n回测过程:")
    signals_log = []

    # 逐日回测
    for i, row in data.iterrows():
        date = row['date']
        price = row['close']

        # 更新行情
        broker.update_price(symbol, price)
        if i > 0:
            broker.set_prev_close(symbol, data.iloc[i-1]['close'])

        # 生成信号
        signal = simple_strategy(data.iloc[:i+1], symbol)

        if signal:
            print(f"\n  {date.strftime('%Y-%m-%d')} 信号: {signal.signal_type.value} {signal.symbol} @{price:.2f}")
            print(f"    原因: {signal.reason}")

            result = engine.execute_signal(signal)
            print(f"    结果: {result.message}")

            signals_log.append({
                'date': date,
                'signal': signal.signal_type.value,
                'price': price,
                'result': result.message
            })

    # 回测结果
    print("\n" + "=" * 60)
    print("回测结果汇总")
    print("=" * 60)

    status = engine.get_portfolio_status()
    print(f"\n最终账户状态:")
    print(f"  初始资金: {engine.initial_capital:,.2f}")
    print(f"  最终净值: {status['total_value']:,.2f}")
    print(f"  总收益率: {(status['total_value'] - engine.initial_capital) / engine.initial_capital * 100:.2f}%")

    account = status['account']
    print(f"\n  现金: {account['cash']:,.2f}")
    print(f"  持仓市值: {account['market_value']:,.2f}")
    print(f"  累计手续费: {account['total_commission']:,.2f}")
    print(f"  累计印花税: {account['total_stamp_tax']:,.2f}")

    print(f"\n信号统计: 共 {len(signals_log)} 个信号")

    broker.disconnect()


if __name__ == "__main__":
    run_backtest()
