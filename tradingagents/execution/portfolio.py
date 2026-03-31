# -*- coding: utf-8 -*-
"""
Portfolio - 持仓管理

管理股票持仓、计算市值和盈亏
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Position:
    """
    持仓数据类

    Attributes:
        symbol: 股票代码
        quantity: 持仓数量（正数）
        avg_cost: 成本价
        today_quantity: 今日买入数量（用于判断能否卖出）
        frozen_quantity: 冻结数量（挂单中）
        last_price: 最新价
        today_buy_amount: 今日买入金额
        today_sell_amount: 今日卖出金额
    """

    symbol: str
    quantity: int = 0
    avg_cost: float = 0.0
    today_quantity: int = 0
    frozen_quantity: int = 0
    last_price: float = 0.0
    today_buy_amount: float = 0.0
    today_sell_amount: float = 0.0

    @property
    def market_value(self) -> float:
        """市值 = 持仓数量 × 最新价"""
        return self.quantity * self.last_price

    @property
    def cost(self) -> float:
        """持仓成本 = 持仓数量 × 成本价"""
        return self.quantity * self.avg_cost

    @property
    def unrealized_pnl(self) -> float:
        """浮动盈亏 = 市值 - 成本"""
        return self.market_value - self.cost

    @property
    def unrealized_pnl_pct(self) -> float:
        """浮动盈亏率（百分比）"""
        if self.cost == 0:
            return 0.0
        return (self.last_price - self.avg_cost) / self.avg_cost * 100

    @property
    def available_quantity(self) -> int:
        """可卖出数量 = 持仓数量 - 冻结数量 - 今日买入（T+1限制）"""
        yesterday_qty = self.quantity - self.today_quantity
        return max(0, yesterday_qty - self.frozen_quantity)

    @property
    def can_sell_today(self) -> bool:
        """今日是否可以卖出（科创板/创业板无T+1限制）"""
        return self.today_quantity > 0

    def update_price(self, price: float):
        """更新最新价"""
        self.last_price = price

    def add_position(self, quantity: int, price: float):
        """
        加仓

        Args:
            quantity: 买入数量
            price: 买入价格
        """
        if quantity <= 0 or price <= 0:
            return

        total_cost = self.cost + quantity * price
        self.quantity += quantity
        self.avg_cost = total_cost / self.quantity if self.quantity > 0 else 0.0
        self.today_quantity += quantity
        self.today_buy_amount += quantity * price

    def reduce_position(self, quantity: int, price: float) -> float:
        """
        减仓/平仓

        Args:
            quantity: 卖出数量
            price: 卖出价格

        Returns:
            实现盈亏
        """
        if quantity <= 0 or price <= 0:
            return 0.0

        sell_qty = min(quantity, self.quantity)
        realized_pnl = (price - self.avg_cost) * sell_qty

        self.quantity -= sell_qty
        self.today_sell_amount += sell_qty * price

        # 如果完全平仓，重置成本价
        if self.quantity == 0:
            self.avg_cost = 0.0
            self.today_quantity = 0

        return realized_pnl

    def freeze(self, quantity: int) -> bool:
        """
        冻结持仓（挂单时调用）

        Args:
            quantity: 冻结数量

        Returns:
            是否成功
        """
        if quantity <= self.available_quantity:
            self.frozen_quantity += quantity
            return True
        return False

    def unfreeze(self, quantity: int):
        """
        解冻持仓（撤单时调用）

        Args:
            quantity: 解冻数量
        """
        self.frozen_quantity = max(0, self.frozen_quantity - quantity)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "avg_cost": self.avg_cost,
            "cost": self.cost,
            "last_price": self.last_price,
            "market_value": self.market_value,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_pct": f"{self.unrealized_pnl_pct:.2f}%",
            "available_quantity": self.available_quantity,
        }


class Portfolio:
    """
    组合持仓管理

    管理多个股票的持仓，计算整体市值和盈亏
    """

    def __init__(self, account_id: str = "SIM001"):
        """
        初始化组合

        Args:
            account_id: 账户ID
        """
        self.account_id = account_id
        self.positions: Dict[str, Position] = {}
        self.last_reset_date = datetime.now().strftime("%Y-%m-%d")

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        获取持仓

        Args:
            symbol: 股票代码

        Returns:
            Position对象或None
        """
        return self.positions.get(symbol)

    def get_or_create_position(self, symbol: str) -> Position:
        """
        获取或创建持仓

        Args:
            symbol: 股票代码

        Returns:
            Position对象
        """
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        return self.positions[symbol]

    def update_position_price(self, symbol: str, price: float):
        """
        更新持仓价格

        Args:
            symbol: 股票代码
            price: 最新价
        """
        if symbol in self.positions:
            self.positions[symbol].update_price(price)

    def update_all_prices(self, prices: Dict[str, float]):
        """
        批量更新持仓价格

        Args:
            prices: {symbol: price} 字典
        """
        for symbol, price in prices.items():
            self.update_position_price(symbol, price)

    @property
    def total_market_value(self) -> float:
        """组合总市值"""
        return sum(p.market_value for p in self.positions.values())

    @property
    def total_cost(self) -> float:
        """组合总成本"""
        return sum(p.cost for p in self.positions.values())

    @property
    def total_unrealized_pnl(self) -> float:
        """组合总浮动盈亏"""
        return sum(p.unrealized_pnl for p in self.positions.values())

    @property
    def total_unrealized_pnl_pct(self) -> float:
        """组合浮动盈亏率"""
        if self.total_cost == 0:
            return 0.0
        return self.total_unrealized_pnl / self.total_cost * 100

    @property
    def position_count(self) -> int:
        """持仓数量"""
        return len([p for p in self.positions.values() if p.quantity > 0])

    def get_all_positions(self) -> List[Position]:
        """获取所有有效持仓"""
        return [p for p in self.positions.values() if p.quantity > 0]

    def get_position_ratio(self, symbol: str, total_value: float) -> float:
        """
        获取持仓占比

        Args:
            symbol: 股票代码
            total_value: 组合总价值

        Returns:
            持仓占比（百分比）
        """
        if symbol not in self.positions or total_value == 0:
            return 0.0
        return self.positions[symbol].market_value / total_value * 100

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "account_id": self.account_id,
            "position_count": self.position_count,
            "total_market_value": self.total_market_value,
            "total_cost": self.total_cost,
            "total_unrealized_pnl": self.total_unrealized_pnl,
            "positions": [p.to_dict() for p in self.get_all_positions()],
        }

    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"Portfolio({self.account_id}): "
            f"持仓数={self.position_count}, "
            f"市值={self.total_market_value:,.2f}, "
            f"盈亏={self.total_unrealized_pnl:,.2f}"
        )
