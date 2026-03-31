"""
策略回测示例 - TradingAgents-CN
===============================

演示如何使用事件驱动引擎和策略模板进行回测。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from tradingagents.event_engine import (
    EventEngine, BarEvent, SignalEvent,
    SignalEventData, TickEvent
)
from tradingagents.strategies.templates import (
    StrategyConfig, MomentumStrategy, MeanReversionStrategy
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def generate_sample_data(symbol: str, days: int = 250) -> pd.DataFrame:
    """
    生成样本数据（模拟价格走势）

    Args:
        symbol: 股票代码
        days: 数据天数

    Returns:
        DataFrame with OHLCV data
    """
    np.random.seed(42)

    # 模拟价格
    prices = [100.0]
    for _ in range(days - 1):
        change = np.random.normal(0.001, 0.02)
        prices.append(prices[-1] * (1 + change))

    dates = pd.date_range(end=datetime.now(), periods=days, freq="D")

    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # 生成OHLC
        daily_range = close * 0.02
        high = close + abs(np.random.normal(0, daily_range / 2))
        low = close - abs(np.random.normal(0, daily_range / 2))
        open_price = low + (high - low) * np.random.random()

        volume = int(1e6 + np.random.randn() * 2e5)

        data.append({
            "symbol": symbol,
            "date": date,
            "open": round(open_price, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(close, 2),
            "volume": volume
        })

    return pd.DataFrame(data)


def run_backtest(strategy_class, strategy_params: dict, data: pd.DataFrame):
    """
    运行回测

    Args:
        strategy_class: 策略类
        strategy_params: 策略参数
        data: 历史数据

    Returns:
        回测结果
    """
    # 配置
    initial_capital = 1000000.0
    commission_rate = 0.0003
    slippage = 0.001

    # 创建策略配置
    config = StrategyConfig(
        name=strategy_class.__name__,
        symbols=[data["symbol"].iloc[0]],
        initial_capital=initial_capital,
        commission_rate=commission_rate,
        slippage=slippage
    )

    # 创建策略
    strategy = strategy_class(config=config, **strategy_params)

    # 初始化策略
    strategy.on_init()

    # 状态变量
    cash = initial_capital
    position = 0
    avg_cost = 0.0
    equity_curve = []
    trades = []

    # 逐日处理
    for idx, row in data.iterrows():
        # 创建Bar事件
        bar = BarEvent(
            symbol=row["symbol"],
            interval="1d",
            open_price=row["open"],
            high_price=row["high"],
            low_price=row["low"],
            close_price=row["close"],
            volume=row["volume"],
            datetime=row["date"]
        )

        # 策略处理
        strategy.on_bar(bar)

        # 简单撮合
        state = strategy.state.get(row["symbol"])

        # 检查买入信号
        if state and position == 0:
            # 简单策略：收盘价 > 20日均线
            if len(data[data.index < idx]) >= 20:
                ma20 = data[data.index < idx]["close"].iloc[-20:].mean()
                if row["close"] > ma20:
                    price = row["close"] * (1 + slippage)
                    max_position_value = initial_capital * 0.3
                    quantity = int(max_position_value / price / 100) * 100

                    if quantity > 0:
                        cost = price * quantity
                        commission = cost * commission_rate
                        if cash >= cost + commission:
                            position = quantity
                            avg_cost = price
                            cash -= (cost + commission)
                            strategy.update_position(row["symbol"], quantity, price, True)
                            trades.append({
                                "date": row["date"],
                                "action": "BUY",
                                "price": price,
                                "quantity": quantity,
                                "pnl": 0
                            })

        # 检查卖出信号
        elif state and position > 0:
            if len(data[data.index < idx]) >= 20:
                ma20 = data[data.index < idx]["close"].iloc[-20:].mean()
                if row["close"] < ma20:
                    price = row["close"] * (1 - slippage)
                    revenue = price * position
                    commission = revenue * commission_rate
                    stamp_tax = revenue * 0.001

                    pnl = revenue - avg_cost * position - commission - stamp_tax
                    cash += (revenue - commission - stamp_tax)

                    trades.append({
                        "date": row["date"],
                        "action": "SELL",
                        "price": price,
                        "quantity": position,
                        "pnl": pnl
                    })

                    position = 0
                    avg_cost = 0.0

        # 记录权益
        equity = cash + position * row["close"]
        equity_curve.append({
            "date": row["date"],
            "equity": equity
        })

    # 最终平仓
    if position > 0:
        last_close = data["close"].iloc[-1]
        revenue = last_close * position
        commission = revenue * commission_rate
        stamp_tax = revenue * 0.001
        pnl = revenue - avg_cost * position - commission - stamp_tax
        cash += (revenue - commission - stamp_tax)

    final_equity = cash
    total_return = (final_equity - initial_capital) / initial_capital

    # 计算指标
    equity_df = pd.DataFrame(equity_curve)
    returns = equity_df["equity"].pct_change().dropna()

    sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if len(returns) > 0 and returns.std() > 0 else 0

    cummax = equity_df["equity"].cummax()
    drawdown = (cummax - equity_df["equity"]) / cummax
    max_drawdown = drawdown.max()

    sell_trades = [t for t in trades if t["action"] == "SELL"]
    win_trades = [t for t in sell_trades if t["pnl"] > 0]
    win_rate = len(win_trades) / len(sell_trades) if sell_trades else 0

    total_pnl = sum(t["pnl"] for t in trades)

    return {
        "strategy": strategy_class.__name__,
        "params": strategy_params,
        "initial_capital": initial_capital,
        "final_equity": final_equity,
        "total_return": total_return,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
        "total_trades": len(sell_trades),
        "total_pnl": total_pnl,
        "trades": trades
    }


def main():
    """主函数"""
    print("=" * 60)
    print("策略回测示例 - TradingAgents-CN")
    print("=" * 60)

    # 生成样本数据
    symbol = "000001.SZ"
    print(f"\n生成样本数据: {symbol}")
    data = generate_sample_data(symbol, days=250)
    print(f"数据范围: {data['date'].iloc[0]} ~ {data['date'].iloc[-1]}")
    print(f"数据点数: {len(data)}")
    print(f"价格范围: {data['close'].min():.2f} ~ {data['close'].max():.2f}")

    # 均线动量策略
    print("\n" + "-" * 40)
    print("测试均线动量策略 (MA 10/30)")
    result = run_backtest(
        MomentumStrategy,
        {"fast_period": 10, "slow_period": 30},
        data
    )
    print_result(result)

    # 均值回归策略
    print("\n" + "-" * 40)
    print("测试均值回归策略 (Lookback=20, Std=2.0)")
    result = run_backtest(
        MeanReversionStrategy,
        {"lookback": 20, "std_dev": 2.0},
        data
    )
    print_result(result)


def print_result(result: dict):
    """打印回测结果"""
    print(f"\n{'='*40}")
    print(f"策略: {result['strategy']}")
    print(f"参数: {result['params']}")
    print(f"{'='*40}")
    print(f"初始资金:    {result['initial_capital']:,.2f}")
    print(f"最终权益:    {result['final_equity']:,.2f}")
    print(f"总收益率:    {result['total_return']*100:.2f}%")
    print(f"夏普比率:    {result['sharpe_ratio']:.4f}")
    print(f"最大回撤:    {result['max_drawdown']*100:.2f}%")
    print(f"胜率:        {result['win_rate']*100:.2f}%")
    print(f"交易次数:    {result['total_trades']}")
    print(f"总盈亏:      {result['total_pnl']:,.2f}")

    if result["trades"]:
        print(f"\n最近5笔交易:")
        for t in result["trades"][-5:]:
            print(f"  {t['date'].strftime('%Y-%m-%d')} {t['action']:4s} "
                  f"@ {t['price']:.2f} x {t['quantity']}  PnL: {t['pnl']:,.2f}")


if __name__ == "__main__":
    main()
