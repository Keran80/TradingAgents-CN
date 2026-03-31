# -*- coding: utf-8 -*-
"""
Account - 账户资金管理

管理账户资金、冻结资金、盈亏计算等
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class Account:
    """
    账户资金管理类

    Attributes:
        account_id: 账户ID
        initial_capital: 初始资金
        cash: 可用资金
        frozen_cash: 冻结资金（挂单占用）
        total_commission: 累计手续费
        total_stamp_tax: 累计印花税
        realized_pnl: 已实现盈亏
        unrealized_pnl: 浮动盈亏（需传入行情计算）
        today_pnl: 今日盈亏
        today_trades: 今日交易次数
        created_time: 创建时间
    """

    account_id: str = "SIM001"
    initial_capital: float = 1000000.0  # 默认100万
    cash: float = 1000000.0
    frozen_cash: float = 0.0
    total_commission: float = 0.0
    total_stamp_tax: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    _market_value: float = 0.0  # 内部存储持仓市值
    today_pnl: float = 0.0
    today_trades: int = 0
    today_buy_amount: float = 0.0
    today_sell_amount: float = 0.0
    created_time: datetime = field(default_factory=datetime.now)
    last_reset_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

    def __post_init__(self):
        """初始化后检查"""
        if self.cash < 0:
            raise ValueError(f"cash cannot be negative: {self.cash}")
        if self.frozen_cash < 0:
            raise ValueError(f"frozen_cash cannot be negative: {self.frozen_cash}")

    @property
    def available_cash(self) -> float:
        """可用资金 = 现金 - 冻结资金"""
        return self.cash - self.frozen_cash

    @property
    def market_value(self) -> float:
        """持仓市值"""
        return self._market_value

    @market_value.setter
    def market_value(self, value: float):
        """设置持仓市值"""
        self._market_value = value

    @property
    def total_assets(self) -> float:
        """总资产 = 现金 + 持仓市值"""
        return self.cash + self._market_value

    @property
    def equity(self) -> float:
        """账户净值 = 总资产 - 冻结资金"""
        return self.total_assets - self.frozen_cash

    @property
    def total_pnl(self) -> float:
        """总盈亏 = 已实现 + 浮动盈亏 - 手续费 - 印花税"""
        return self.realized_pnl + self.unrealized_pnl - self.total_commission - self.total_stamp_tax

    @property
    def total_return(self) -> float:
        """总收益率"""
        if self.initial_capital == 0:
            return 0.0
        return (self.total_assets - self.initial_capital) / self.initial_capital * 100

    @property
    def frozen_ratio(self) -> float:
        """冻结比例"""
        if self.cash == 0:
            return 0.0
        return self.frozen_cash / self.cash * 100

    def freeze_cash(self, amount: float) -> bool:
        """
        冻结资金

        Args:
            amount: 冻结金额

        Returns:
            是否成功
        """
        if amount <= 0:
            return False
        if amount > self.available_cash:
            return False
        self.frozen_cash += amount
        return True

    def unfreeze_cash(self, amount: float) -> bool:
        """
        解冻资金

        Args:
            amount: 解冻金额

        Returns:
            是否成功
        """
        if amount <= 0:
            return False
        if amount > self.frozen_cash:
            amount = self.frozen_cash
        self.frozen_cash -= amount
        return True

    def deduct_cash(self, amount: float) -> bool:
        """
        扣减现金（成交后调用）

        Args:
            amount: 扣减金额

        Returns:
            是否成功
        """
        if amount <= 0:
            return False
        if amount > self.available_cash:
            return False
        self.cash -= amount
        self.frozen_cash -= min(amount, self.frozen_cash)
        return True

    def add_cash(self, amount: float) -> bool:
        """
        增加现金（卖出成交后调用）

        Args:
            amount: 增加金额

        Returns:
            是否成功
        """
        if amount <= 0:
            return False
        self.cash += amount
        return True

    def add_commission(self, amount: float):
        """增加手续费"""
        if amount > 0:
            self.total_commission += amount

    def add_stamp_tax(self, amount: float):
        """增加印花税"""
        if amount > 0:
            self.total_stamp_tax += amount

    def add_realized_pnl(self, pnl: float):
        """增加已实现盈亏"""
        self.realized_pnl += pnl
        self.today_pnl += pnl

    def update_unrealized_pnl(self, pnl: float):
        """更新浮动盈亏"""
        self.unrealized_pnl = pnl

    def reset_daily(self):
        """重置每日计数"""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.last_reset_date != today:
            self.today_pnl = 0.0
            self.today_trades = 0
            self.today_buy_amount = 0.0
            self.today_sell_amount = 0.0
            self.last_reset_date = today

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "account_id": self.account_id,
            "initial_capital": self.initial_capital,
            "cash": self.cash,
            "frozen_cash": self.frozen_cash,
            "available_cash": self.available_cash,
            "market_value": self.market_value,
            "total_assets": self.total_assets,
            "equity": self.equity,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "total_pnl": self.total_pnl,
            "total_return": f"{self.total_return:.2f}%",
            "total_commission": self.total_commission,
            "total_stamp_tax": self.total_stamp_tax,
            "today_pnl": self.today_pnl,
            "today_trades": self.today_trades,
        }

    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"Account({self.account_id}): "
            f"现金={self.cash:,.2f}, "
            f"冻结={self.frozen_cash:,.2f}, "
            f"市值={self.market_value:,.2f}, "
            f"净值={self.equity:,.2f}, "
            f"盈亏={self.total_pnl:,.2f}({self.total_return:.2f}%)"
        )
