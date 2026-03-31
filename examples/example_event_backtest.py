"""
事件驱动回测示例 - TradingAgents-CN
===================================

演示完整的事件驱动回测系统：
- EventEngine 事件引擎
- 策略模板
- 信号到订单的执行流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import logging
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, List

from tradingagents.event_engine import (
    EventEngine, BarEvent, SignalEvent, TradeEvent,
    SignalEventData, TradeEventData, OrderEvent, OrderEventData
)
from tradingagents.strategies.templates import (
    StrategyConfig, MomentumStrategy, MeanReversionStrategy
)
from tradingagents.execution.simulators.simulator import SimulatorBroker
from tradingagents.execution.portfolio import Portfolio
from tradingagents.execution.account import Account
from tradingagents.execution.broker import Order, OrderType, OrderSide

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    事件驱动回测引擎
    """

    def __init__(self, initial_capital: float = 1000000.0):
        # 事件引擎
        self.event_engine = EventEngine(async_mode=False)

        # 账户
        self.account = Account(
            account_id="BACKTEST",
            initial_capital=initial_capital,
            cash=initial_capital
        )
        self.portfolio = Portfolio(self.account)

        # 模拟券商
        self.broker = SimulatorBroker(
            account=self.account,
            portfolio=self.portfolio
        )

        # 策略列表
        self.strategies: List[any] = []

        # 信号处理
        self.event_engine.register(SignalEvent, self._on_signal)

        # 统计
        self.stats = {
            "total_signals": 0,
            "total_orders": 0,
            "total_trades": 0,
            "final_equity": initial_capital
        }

    def add_strategy(self, strategy):
        """添加策略"""
        self.strategies.append(strategy)
        strategy.set_engine(self.event_engine)
        strategy.on_init()
        logger.info(f"Added strategy: {strategy.name}")

    def load_data(self, data: pd.DataFrame):
        """加载数据"""
        self.data = data

    def run(self):
        """运行回测"""
        logger.info("Starting backtest...")

        symbol = self.data["symbol"].iloc[0]

        # 逐日处理
        for idx, row in self.data.iterrows():
            bar = BarEvent(
                symbol=symbol,
                interval="1d",
                open_price=row["open"],
                high_price=row["high"],
                low_price=row["low"],
                close_price=row["close"],
                volume=int(row["volume"]),
                datetime=row["date"] if "date" in row else idx
            )

            # 更新行情
            self.broker.update_price(symbol, row["close"])

            # 策略处理
            for strategy in self.strategies:
                strategy.on_bar(bar)

            # 处理事件
            self.event_engine.process()

        # 最终统计
        self.stats["final_equity"] = self.account.total_assets

        logger.info("Backtest completed")
        self._print_stats()

        return self.stats

    def _on_signal(self, event: SignalEvent):
        """处理信号事件"""
        self.stats["total_signals"] += 1
        signal = event.signal_data

        logger.debug(f"Signal: {signal.signal_type.value} {signal.symbol} "
                     f"@ {signal.price} x {signal.quantity}")

        # 检查持仓状态
        position = self.portfolio.get_position(signal.symbol)
        position = position.quantity if position else 0

        if signal.signal_type == SignalEventData.SignalType.BUY:
            if position > 0:
                logger.debug(f"Already have position, skip buy")
                return

            # 创建订单对象
            order = Order(
                symbol=signal.symbol,
                order_type=OrderType.MARKET,
                side=OrderSide.BUY,
                quantity=signal.quantity,
                price=signal.price
            )
            result = self.broker.place_order(order)

            if result.success:
                self.stats["total_orders"] += 1
                self._update_position_from_trade(signal.symbol, result.trade)

        elif signal.signal_type == SignalEventData.SignalType.SELL:
            if position <= 0:
                logger.debug(f"No position to sell")
                return

            # 卖出全部
            quantity = min(position, signal.quantity)
            order = Order(
                symbol=signal.symbol,
                order_type=OrderType.MARKET,
                side=OrderSide.SELL,
                quantity=quantity,
                price=signal.price
            )
            result = self.broker.place_order(order)

            if result.success:
                self.stats["total_orders"] += 1
                self._update_position_from_trade(signal.symbol, result.trade)

    def _update_position_from_trade(self, symbol: str, trade):
        """根据成交更新持仓"""
        if not trade:
            return

        self.stats["total_trades"] += 1

        # 更新策略状态
        for strategy in self.strategies:
            is_buy = trade.side == "BUY"
            strategy.update_position(symbol, trade.quantity, trade.price, is_buy)

    def _print_stats(self):
        """打印统计"""
        print("\n" + "=" * 50)
        print("回测统计")
        print("=" * 50)
        print(f"初始资金:      {self.account.initial_capital:,.2f}")
        print(f"最终权益:      {self.account.total_assets:,.2f}")
        print(f"总收益率:      {(self.account.total_assets / self.account.initial_capital - 1) * 100:.2f}%")
        print(f"信号数量:      {self.stats['total_signals']}")
        print(f"订单数量:      {self.stats['total_orders']}")
        print(f"成交数量:      {self.stats['total_trades']}")
        print(f"已实现盈亏:    {self.account.realized_pnl:,.2f}")
        print(f"总手续费:      {self.account.total_commission:,.2f}")


def generate_sample_data(symbol: str, days: int = 250) -> pd.DataFrame:
    """生成样本数据"""
    np.random.seed(42)
    prices = [100.0]
    for _ in range(days - 1):
        change = np.random.normal(0.001, 0.02)
        prices.append(prices[-1] * (1 + change))

    dates = pd.date_range(end=datetime.now(), periods=days, freq="D")

    data = []
    for date, close in zip(dates, prices):
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


def main():
    """主函数"""
    print("=" * 60)
    print("事件驱动回测示例 - TradingAgents-CN")
    print("=" * 60)

    # 生成数据
    symbol = "000001.SZ"
    print(f"\n生成样本数据: {symbol}")
    data = generate_sample_data(symbol, days=250)
    print(f"数据范围: {data['date'].iloc[0].date()} ~ {data['date'].iloc[-1].date()}")

    # 创建回测引擎
    engine = BacktestEngine(initial_capital=1000000.0)

    # 添加策略
    config = StrategyConfig(
        name="MA_10_30",
        symbols=[symbol],
        initial_capital=1000000.0,
        max_position_ratio=0.3
    )
    strategy = MomentumStrategy(config=config, fast_period=10, slow_period=30)
    engine.add_strategy(strategy)

    # 运行回测
    engine.load_data(data)
    stats = engine.run()

    # 策略统计
    print("\n" + "=" * 50)
    print("策略统计")
    print("=" * 50)
    strategy_stats = strategy.get_stats()
    for k, v in strategy_stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
