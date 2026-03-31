# TradingAgents-CN 仓位管理器
# Position Manager

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime


@dataclass
class PositionState:
    """持仓状态"""
    symbol: str
    quantity: int = 0                    # 持仓数量
    avg_cost: float = 0.0               # 平均成本
    current_price: float = 0.0           # 当前价格
    realized_pnl: float = 0.0            # 已实现盈亏
    unrealized_pnl: float = 0.0          # 未实现盈亏
    max_quantity: int = 10000            # 最大持仓数量
    stop_loss_price: float = 0.0        # 止损价格
    take_profit_price: float = 0.0      # 止盈价格
    entry_time: Optional[datetime] = None  # 入场时间

    @property
    def market_value(self) -> float:
        """市值"""
        return self.quantity * self.current_price

    @property
    def total_cost(self) -> float:
        """总成本"""
        return self.quantity * self.avg_cost

    @property
    def total_pnl(self) -> float:
        """总盈亏（含已实现和未实现）"""
        return self.realized_pnl + self.unrealized_pnl

    @property
    def pnl_ratio(self) -> float:
        """盈亏比例"""
        if self.total_cost == 0:
            return 0.0
        return self.total_pnl / self.total_cost


class PositionManager:
    """仓位管理器

    管理所有持仓状态、仓位限制和动态调整

    使用示例:
        pm = PositionManager(initial_cash=100000)

        # 建仓
        pm.open_position("000001.SZ", quantity=1000, price=10.0)

        # 平仓
        pm.close_position("000001.SZ", quantity=500, price=11.0)

        # 更新持仓价格
        pm.update_price("000001.SZ", 10.5)

        # 获取持仓信息
        position = pm.get_position("000001.SZ")
    """

    def __init__(
        self,
        initial_cash: float = 100000.0,
        max_total_position_ratio: float = 0.9,
        max_single_position_ratio: float = 0.2,
        max_positions: int = 10,
    ):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.max_total_position_ratio = max_total_position_ratio
        self.max_single_position_ratio = max_single_position_ratio
        self.max_positions = max_positions
        self.positions: Dict[str, PositionState] = {}
        self._trade_history: List[Dict] = []

    def get_total_assets(self) -> float:
        """总资产"""
        return self.cash + self.get_total_position_value()

    def get_total_position_value(self) -> float:
        """总持仓市值"""
        return sum(p.market_value for p in self.positions.values())

    def get_position(self, symbol: str) -> Optional[PositionState]:
        """获取持仓"""
        return self.positions.get(symbol)

    def get_all_positions(self) -> List[PositionState]:
        """获取所有持仓"""
        return list(self.positions.values())

    def get_positions_count(self) -> int:
        """持仓股票数量"""
        return len(self.positions)

    def can_open_position(
        self,
        symbol: str,
        quantity: int,
        price: float
    ) -> Tuple[bool, str]:
        """检查是否可以建仓"""
        order_value = quantity * price
        total_assets = self.get_total_assets()

        if order_value > self.cash * 1.001:
            return False, f"资金不足: 需要 {order_value:.2f}, 可用 {self.cash:.2f}"

        new_total_value = self.get_total_position_value() + order_value
        max_total = total_assets * self.max_total_position_ratio
        if new_total_value > max_total:
            return False, f"总持仓超限: {new_total_value:.2f} > {max_total:.2f}"

        if symbol in self.positions:
            current_value = self.positions[symbol].market_value
        else:
            current_value = 0
        new_single_value = current_value + order_value
        max_single = total_assets * self.max_single_position_ratio
        if new_single_value > max_single:
            return False, f"单只持仓超限: {new_single_value:.2f} > {max_single:.2f}"

        if symbol not in self.positions and self.get_positions_count() >= self.max_positions:
            return False, f"持仓数量超限: {self.get_positions_count()} >= {self.max_positions}"

        return True, "OK"

    def open_position(
        self,
        symbol: str,
        quantity: int,
        price: float,
        timestamp: datetime = None
    ) -> Tuple[bool, str]:
        """建仓"""
        if quantity <= 0 or price <= 0:
            return False, "数量或价格无效"

        can_open, reason = self.can_open_position(symbol, quantity, price)
        if not can_open:
            return False, reason

        order_value = quantity * price

        if symbol in self.positions:
            pos = self.positions[symbol]
            total_cost = pos.quantity * pos.avg_cost + order_value
            pos.quantity += quantity
            pos.avg_cost = total_cost / pos.quantity
        else:
            self.positions[symbol] = PositionState(
                symbol=symbol,
                quantity=quantity,
                avg_cost=price,
                current_price=price,
                entry_time=timestamp or datetime.now(),
            )

        self.cash -= order_value
        self._trade_history.append({
            "action": "OPEN",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "value": order_value,
            "timestamp": timestamp or datetime.now(),
        })

        return True, f"建仓成功: {symbol} {quantity}@{price}"

    def close_position(
        self,
        symbol: str,
        quantity: int,
        price: float,
        timestamp: datetime = None
    ) -> Tuple[bool, str]:
        """平仓"""
        if symbol not in self.positions:
            return False, f"无持仓: {symbol}"

        pos = self.positions[symbol]
        if quantity > pos.quantity:
            return False, f"平仓数量超限: {quantity} > {pos.quantity}"

        sell_value = quantity * price
        cost_basis = quantity * pos.avg_cost
        realized_pnl = sell_value - cost_basis

        pos.realized_pnl += realized_pnl
        pos.quantity -= quantity
        self.cash += sell_value

        self._trade_history.append({
            "action": "CLOSE",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "value": sell_value,
            "realized_pnl": realized_pnl,
            "timestamp": timestamp or datetime.now(),
        })

        if pos.quantity == 0:
            del self.positions[symbol]

        return True, f"平仓成功: {symbol} {quantity}@{price}, 盈亏 {realized_pnl:.2f}"

    def update_price(self, symbol: str, price: float):
        """更新持仓价格"""
        if symbol not in self.positions:
            return
        pos = self.positions[symbol]
        pos.current_price = price
        pos.unrealized_pnl = (price - pos.avg_cost) * pos.quantity

    def update_all_prices(self, price_map: Dict[str, float]):
        """批量更新价格"""
        for symbol, price in price_map.items():
            self.update_price(symbol, price)

    def check_stop_loss(self, symbol: str) -> Optional[float]:
        """检查止损触发"""
        pos = self.positions.get(symbol)
        if not pos or pos.stop_loss_price <= 0:
            return None
        if pos.current_price <= pos.stop_loss_price:
            return pos.stop_loss_price
        return None

    def check_take_profit(self, symbol: str) -> Optional[float]:
        """检查止盈触发"""
        pos = self.positions.get(symbol)
        if not pos or pos.take_profit_price <= 0:
            return None
        if pos.current_price >= pos.take_profit_price:
            return pos.take_profit_price
        return None

    def set_stop_loss(self, symbol: str, price: float):
        """设置止损价"""
        if symbol in self.positions:
            self.positions[symbol].stop_loss_price = price

    def set_take_profit(self, symbol: str, price: float):
        """设置止盈价"""
        if symbol in self.positions:
            self.positions[symbol].take_profit_price = price

    def get_summary(self) -> Dict:
        """获取账户摘要"""
        positions = self.get_all_positions()
        total_value = self.get_total_position_value()
        total_assets = self.get_total_assets()

        return {
            "cash": self.cash,
            "position_value": total_value,
            "total_assets": total_assets,
            "total_pnl": total_assets - self.initial_cash,
            "pnl_ratio": (total_assets - self.initial_cash) / self.initial_cash if self.initial_cash > 0 else 0,
            "position_count": len(positions),
            "positions": [
                {
                    "symbol": p.symbol,
                    "quantity": p.quantity,
                    "avg_cost": p.avg_cost,
                    "current_price": p.current_price,
                    "market_value": p.market_value,
                    "realized_pnl": p.realized_pnl,
                    "unrealized_pnl": p.unrealized_pnl,
                    "total_pnl": p.total_pnl,
                    "pnl_ratio": p.pnl_ratio,
                }
                for p in positions
            ],
        }

    def get_trade_history(self) -> List[Dict]:
        """获取交易历史"""
        return self._trade_history.copy()
