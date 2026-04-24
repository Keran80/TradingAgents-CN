"""
策略模块

包含预置的回测策略函数。
"""

from typing import Any, Dict, List, Optional

import pandas as pd


class Signal:
    """策略信号类"""

    def __init__(self, symbol: str, action: str, quantity: Optional[int] = None):
        self.symbol = symbol
        self.action = action  # "BUY" / "SELL"
        self.quantity = quantity


def moving_average_crossover_strategy(
    data: Dict[str, pd.DataFrame],
    current_date: Any,
    positions: Dict[str, int],
    short_window: int = 5,
    long_window: int = 20
) -> List:
    """
    均线交叉策略

    Args:
        data: 股票数据字典
        current_date: 当前日期
        positions: 当前持仓
        short_window: 短期均线周期
        long_window: 长期均线周期

    Returns:
        Signal列表
    """
    signals = []

    for symbol, df in data.items():
        # 获取历史数据
        hist = df[df.index < current_date]
        if len(hist) < long_window:
            continue

        current_position = positions.get(symbol, 0)

        # 计算均线
        ma_short = hist['close'].iloc[-short_window:].mean()
        ma_long = hist['close'].iloc[-long_window:].mean()

        ma_short_prev = hist['close'].iloc[-short_window-1:-1].mean()
        ma_long_prev = hist['close'].iloc[-long_window-1:-1].mean()

        # 金叉买入
        if ma_short > ma_long and ma_short_prev <= ma_long_prev and current_position == 0:
            signals.append(Signal(symbol, "BUY"))

        # 死叉卖出
        elif ma_short < ma_long and ma_short_prev >= ma_long_prev and current_position > 0:
            signals.append(Signal(symbol, "SELL"))

    return signals
