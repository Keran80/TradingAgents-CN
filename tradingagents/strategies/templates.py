"""
策略模板库 - TradingAgents-CN
=============================

提供常用交易策略模板：
- StrategyTemplate: 策略基类
- MomentumStrategy: 均线动量策略
- MeanReversionStrategy: 均值回归策略
- BreakoutStrategy: 突破策略
- GridStrategy: 网格交易策略
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ..event_engine import EventEngine, BarEvent, TickEvent, TradeEvent

logger = logging.getLogger(__name__)


class StrategyState:
    """策略状态"""

    def __init__(self):
        self.position: int = 0  # 当前持仓
        self.avg_cost: float = 0.0  # 平均成本
        self.total_pnl: float = 0.0  # 累计盈亏
        self.trade_count: int = 0  # 交易次数
        self.win_count: int = 0  # 盈利次数
        self.loss_count: int = 0  # 亏损次数
        self.last_entry_price: float = 0.0  # 上次入场价格
        self.last_entry_time: Optional[datetime] = None  # 上次入场时间


@dataclass
class StrategyConfig:
    """策略配置"""
    name: str = "Strategy"
    symbols: List[str] = field(default_factory=lambda: ["000001.SZ"])
    initial_capital: float = 1000000.0
    commission_rate: float = 0.0003  # 佣金万三
    slippage: float = 0.001  # 滑点 0.1%
    max_position_ratio: float = 0.3  # 单股最大仓位 30%


class StrategyTemplate(ABC):
    """
    策略基类
    """

    def __init__(self, config: Optional[StrategyConfig] = None):
        self.config = config or StrategyConfig()
        self.name = self.config.name
        self.symbols = self.config.symbols
        self.state: Dict[str, StrategyState] = {}
        self.engine: Optional["EventEngine"] = None

        for symbol in self.symbols:
            self.state[symbol] = StrategyState()

        self._initialized = False
        self._bars: Dict[str, List[float]] = {s: [] for s in self.symbols}

        logger.info(f"Strategy {self.name} initialized with symbols: {self.symbols}")

    def set_engine(self, engine: "EventEngine") -> None:
        """设置事件引擎"""
        self.engine = engine

    def on_init(self) -> None:
        """策略初始化回调"""
        self._initialized = True
        logger.info(f"Strategy {self.name} initialized")

    @abstractmethod
    def on_bar(self, bar: "BarEvent") -> None:
        """K线数据处理 - 子类必须实现"""
        pass

    def on_tick(self, tick: "TickEvent") -> None:
        """Tick数据处理"""
        pass

    def on_trade(self, trade: "TradeEvent") -> None:
        """成交回报处理"""
        pass

    def buy(self, symbol: str, price: float, quantity: int, order_type: str = "LIMIT") -> None:
        """买入"""
        if self.engine:
            from ..event_engine import SignalEvent, SignalEventData
            signal_data = SignalEventData(
                symbol=symbol,
                signal_type=SignalEventData.SignalType.BUY,
                price=price,
                quantity=quantity,
                confidence=1.0,
                reason=f"{self.name} BUY signal"
            )
            self.engine.put(SignalEvent(signal_data=signal_data))

    def sell(self, symbol: str, price: float, quantity: int, order_type: str = "LIMIT") -> None:
        """卖出"""
        if self.engine:
            from ..event_engine import SignalEvent, SignalEventData
            signal_data = SignalEventData(
                symbol=symbol,
                signal_type=SignalEventData.SignalType.SELL,
                price=price,
                quantity=quantity,
                confidence=1.0,
                reason=f"{self.name} SELL signal"
            )
            self.engine.put(SignalEvent(signal_data=signal_data))

    def close(self, symbol: str, price: float) -> None:
        """平仓"""
        state = self.state.get(symbol)
        if state and state.position > 0:
            self.sell(symbol, price, state.position)

    def get_position(self, symbol: str) -> int:
        """获取持仓"""
        return self.state.get(symbol, StrategyState()).position

    def update_position(self, symbol: str, quantity: int, price: float, is_buy: bool) -> None:
        """更新持仓状态"""
        state = self.state[symbol]

        if is_buy:
            old_value = state.position * state.avg_cost
            new_value = quantity * price
            total_quantity = state.position + quantity

            if total_quantity > 0:
                state.avg_cost = (old_value + new_value) / total_quantity

            state.position = total_quantity
            state.last_entry_price = price
            state.last_entry_time = datetime.now()
        else:
            state.position -= quantity
            pnl = (price - state.avg_cost) * quantity
            state.total_pnl += pnl
            state.trade_count += 1

            if pnl > 0:
                state.win_count += 1
            elif pnl < 0:
                state.loss_count += 1

            if state.position == 0:
                state.avg_cost = 0.0

    def get_stats(self) -> Dict[str, Any]:
        """获取策略统计"""
        total_trades = sum(s.trade_count for s in self.state.values())
        total_wins = sum(s.win_count for s in self.state.values())
        total_pnl = sum(s.total_pnl for s in self.state.values())

        return {
            "name": self.name,
            "total_trades": total_trades,
            "win_count": total_wins,
            "loss_count": total_trades - total_wins,
            "win_rate": total_wins / total_trades if total_trades > 0 else 0,
            "total_pnl": total_pnl,
        }


class MomentumStrategy(StrategyTemplate):
    """
    均线动量策略
    金叉买入，死叉卖出
    """

    def __init__(
        self,
        config: Optional[StrategyConfig] = None,
        fast_period: int = 10,
        slow_period: int = 30
    ):
        super().__init__(config)
        self.name = f"Momentum_{fast_period}_{slow_period}"
        self.fast_period = fast_period
        self.slow_period = slow_period
        # 使用 deque 替代 list，避免 pop(0) 的 O(n) 操作
        self.prices: Dict[str, deque] = {
            s: deque(maxlen=slow_period + 2) for s in self.symbols
        }

    def on_bar(self, bar: "BarEvent") -> None:
        symbol = bar.symbol
        if symbol not in self.prices:
            return

        self.prices[symbol].append(bar.close)

        if len(self.prices[symbol]) < self.slow_period:
            return

        prices = list(self.prices[symbol])
        fast_ma = np.mean(prices[-self.fast_period:])
        slow_ma = np.mean(prices[-self.slow_period:])
        prev_fast_ma = np.mean(prices[-self.fast_period-1:-1])
        prev_slow_ma = np.mean(prices[-self.slow_period-1:-1])

        state = self.state[symbol]

        # 金叉买入
        if prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma and state.position == 0:
            quantity = self._calculate_quantity(bar.close)
            if quantity > 0:
                self.buy(symbol, bar.close, quantity)
                logger.info(f"[{symbol}] GOLDEN CROSS: Buy {quantity} @ {bar.close}")

        # 死叉卖出
        elif prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma and state.position > 0:
            self.sell(symbol, bar.close, state.position)
            logger.info(f"[{symbol}] DEATH CROSS: Sell {state.position} @ {bar.close}")

    def _calculate_quantity(self, price: float) -> int:
        if price <= 0:
            return 0
        max_value = self.config.initial_capital * self.config.max_position_ratio
        return max(0, int(max_value / price / 100) * 100)


class MeanReversionStrategy(StrategyTemplate):
    """
    均值回归策略
    价格偏离均值超过阈值时买入/卖出
    """

    def __init__(
        self,
        config: Optional[StrategyConfig] = None,
        lookback: int = 20,
        std_dev: float = 2.0
    ):
        super().__init__(config)
        self.name = f"MeanReversion_{lookback}_{std_dev}"
        self.lookback = lookback
        self.std_dev = std_dev
        # 使用 deque 替代 list，避免 pop(0) 的 O(n) 操作
        self.prices: Dict[str, deque] = {
            s: deque(maxlen=lookback + 2) for s in self.symbols
        }

    def on_bar(self, bar: "BarEvent") -> None:
        symbol = bar.symbol
        if symbol not in self.prices:
            return

        self.prices[symbol].append(bar.close)

        if len(self.prices[symbol]) < self.lookback:
            return

        prices = list(self.prices[symbol])
        mean = np.mean(prices[-self.lookback:])
        std = np.std(prices[-self.lookback:])
        current_price = bar.close

        state = self.state[symbol]

        # 买入：价格低于下轨
        if current_price < mean - self.std_dev * std and state.position == 0:
            quantity = self._calculate_quantity(current_price)
            if quantity > 0:
                self.buy(symbol, current_price, quantity)
                logger.info(f"[{symbol}] MEAN REVERT BUY @ {current_price}")

        # 卖出：价格高于上轨
        elif current_price > mean + self.std_dev * std and state.position > 0:
            self.sell(symbol, current_price, state.position)
            logger.info(f"[{symbol}] MEAN REVERT SELL @ {current_price}")

    def _calculate_quantity(self, price: float) -> int:
        if price <= 0:
            return 0
        max_value = self.config.initial_capital * self.config.max_position_ratio
        return max(0, int(max_value / price / 100) * 100)


class BreakoutStrategy(StrategyTemplate):
    """
    突破策略
    价格突破N日高点买入，跌破N日低点卖出
    """

    def __init__(
        self,
        config: Optional[StrategyConfig] = None,
        lookback: int = 20
    ):
        super().__init__(config)
        self.name = f"Breakout_{lookback}"
        self.lookback = lookback
        self.prices: Dict[str, Dict[str, List[float]]] = {}

        for symbol in self.symbols:
            self.prices[symbol] = {"high": [], "low": [], "close": []}

    def on_bar(self, bar: "BarEvent") -> None:
        symbol = bar.symbol
        if symbol not in self.prices:
            return

        prices = self.prices[symbol]
        prices["high"].append(bar.high)
        prices["low"].append(bar.low)
        prices["close"].append(bar.close)

        max_len = self.lookback + 1
        for key in prices:
            if len(prices[key]) > max_len:
                prices[key].pop(0)

        if len(prices["close"]) < self.lookback:
            return

        highest_high = max(prices["high"][-self.lookback:])
        lowest_low = min(prices["low"][-self.lookback:])
        current_price = bar.close
        state = self.state[symbol]

        # 突破买入
        if current_price > highest_high and state.position == 0:
            quantity = self._calculate_quantity(current_price)
            if quantity > 0:
                self.buy(symbol, current_price, quantity)
                logger.info(f"[{symbol}] BREAKOUT BUY @ {current_price}")

        # 跌破止损
        elif current_price < lowest_low and state.position > 0:
            self.sell(symbol, current_price, state.position)
            logger.info(f"[{symbol}] BREAKOUT SELL @ {current_price}")

    def _calculate_quantity(self, price: float) -> int:
        if price <= 0:
            return 0
        max_value = self.config.initial_capital * self.config.max_position_ratio
        return max(0, int(max_value / price / 100) * 100)


class GridStrategy(StrategyTemplate):
    """
    网格交易策略
    在价格区间内设置网格，跌买涨卖
    """

    def __init__(
        self,
        config: Optional[StrategyConfig] = None,
        grid_num: int = 10,
        grid_ratio: float = 0.02,
        base_quantity: int = 100
    ):
        super().__init__(config)
        self.name = f"Grid_{grid_num}_{grid_ratio}"
        self.grid_num = grid_num
        self.grid_ratio = grid_ratio
        self.base_quantity = base_quantity
        self.grid_prices: Dict[str, List[float]] = {}
        self.grid_levels: Dict[str, int] = {s: 0 for s in self.symbols}
        self.base_price: Dict[str, float] = {}

    def set_base_price(self, symbol: str, price: float) -> None:
        """设置基准价格并初始化网格"""
        self.base_price[symbol] = price
        grid_prices = []

        for i in range(self.grid_num + 1):
            level = i - self.grid_num // 2
            grid_price = price * (1 + level * self.grid_ratio)
            grid_prices.append(grid_price)

        self.grid_prices[symbol] = sorted(grid_prices)
        self.grid_levels[symbol] = self.grid_num // 2

    def on_bar(self, bar: "BarEvent") -> None:
        symbol = bar.symbol
        if symbol not in self.base_price:
            self.set_base_price(symbol, bar.close)
            return

        current_price = bar.close
        state = self.state[symbol]
        grid_prices = self.grid_prices[symbol]

        # 找到当前层
        current_level = 0
        for i, gp in enumerate(grid_prices):
            if current_price <= gp:
                current_level = i
                break
        else:
            current_level = len(grid_prices) - 1

        position_level = self.grid_levels[symbol]

        # 下跌买入
        while current_level < position_level and state.position < self.grid_num:
            self.buy(symbol, current_price, self.base_quantity)
            self.grid_levels[symbol] -= 1
            position_level = self.grid_levels[symbol]

        # 上涨卖出
        while current_level > position_level and state.position > 0:
            self.sell(symbol, current_price, min(self.base_quantity, state.position))
            self.grid_levels[symbol] += 1
            position_level = self.grid_levels[symbol]
