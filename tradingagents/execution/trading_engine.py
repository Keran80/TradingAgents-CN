# -*- coding: utf-8 -*-
"""
TradingEngine - 交易引擎

整合信号生成与订单执行的核心引擎
支持风控前置检查、信号转订单、持仓同步等功能
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Callable, Any

from .broker import (
    BrokerInterface, Order, OrderType, OrderSide,
    OrderStatus, PositionEffect, OrderResult, Quote
)
from .account import Account
from .portfolio import Portfolio
from .order_manager import OrderManager


class SignalType(Enum):
    """信号类型"""
    BUY = "BUY"           # 买入
    SELL = "SELL"         # 卖出
    BUY_COVER = "BUY_COVER"  # 买入平仓（做空）
    SELL_SHORT = "SELL_SHORT"  # 卖出做空


@dataclass
class Signal:
    """
    交易信号

    Attributes:
        symbol: 股票代码
        signal_type: 信号类型
        price: 目标价格
        quantity: 数量（0表示自动计算）
        confidence: 置信度 0-1
        reason: 信号原因
        strategy_name: 策略名称
        timestamp: 时间戳
    """
    symbol: str
    signal_type: SignalType
    price: float
    quantity: int = 0
    confidence: float = 1.0
    reason: str = ""
    strategy_name: str = ""
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ExecutionResult:
    """
    执行结果

    Attributes:
        success: 是否成功
        order_id: 订单ID
        status: 状态描述
        message: 消息
        filled_quantity: 成交数量
        filled_price: 成交价格
    """
    success: bool
    order_id: str = ""
    status: str = ""
    message: str = ""
    filled_quantity: int = 0
    filled_price: float = 0.0


class TradingEngine:
    """
    交易引擎

    核心功能：
    - 信号转订单
    - 风控前置检查
    - 持仓同步
    - 交易日志
    """

    def __init__(
        self,
        broker: BrokerInterface,
        initial_capital: float = 1000000.0,
        max_position_ratio: float = 0.3,     # 单股最大仓位 30%
        max_total_position: float = 0.8,       # 总仓位上限 80%
        daily_loss_limit: float = 0.05,       # 日亏损限制 5%
        max_orders_per_day: int = 100,        # 日交易次数上限
    ):
        """
        初始化交易引擎

        Args:
            broker: 券商适配器
            initial_capital: 初始资金
            max_position_ratio: 单股最大仓位比例
            max_total_position: 总仓位上限
            daily_loss_limit: 日亏损限制
            max_orders_per_day: 日交易次数上限
        """
        self.broker = broker
        self.initial_capital = initial_capital

        # 风控参数
        self.max_position_ratio = max_position_ratio
        self.max_total_position = max_total_position
        self.daily_loss_limit = daily_loss_limit
        self.max_orders_per_day = max_orders_per_day

        # 初始化账户和持仓
        self.account = Account(initial_capital=initial_capital)
        self.portfolio = Portfolio()

        # 如果broker已初始化，同步状态
        if isinstance(broker, type) is False and hasattr(broker, 'account'):
            self.account = broker.account
            self.portfolio = broker.portfolio

        # 回调函数
        self._execution_callbacks: List[Callable] = []

    def connect(self) -> bool:
        """连接券商"""
        return self.broker.connect()

    def disconnect(self) -> bool:
        """断开连接"""
        return self.broker.disconnect()

    def register_execution_callback(self, callback: Callable[[ExecutionResult], None]):
        """
        注册执行回调

        Args:
            callback: 回调函数
        """
        self._execution_callbacks.append(callback)

    def execute_signal(self, signal: Signal) -> ExecutionResult:
        """
        执行交易信号

        Args:
            signal: 交易信号

        Returns:
            ExecutionResult: 执行结果
        """
        # 前置风控检查
        risk_result = self._risk_check(signal)
        if not risk_result["passed"]:
            result = ExecutionResult(
                success=False,
                status="REJECTED",
                message=f"风控拒绝: {risk_result['reason']}"
            )
            self._notify_callbacks(result)
            return result

        # 信号转订单
        order = self._signal_to_order(signal)

        # 提交订单
        order_result = self.broker.place_order(order)

        if order_result.success:
            result = ExecutionResult(
                success=True,
                order_id=order.order_id,
                status="SUBMITTED",
                message="订单已提交"
            )
        else:
            result = ExecutionResult(
                success=False,
                status="REJECTED",
                message=order_result.message
            )

        self._notify_callbacks(result)
        return result

    def execute_buy(
        self,
        symbol: str,
        price: float,
        quantity: int = 0,
        confidence: float = 1.0,
        reason: str = ""
    ) -> ExecutionResult:
        """
        快捷买入

        Args:
            symbol: 股票代码
            price: 买入价格
            quantity: 数量（0表示自动计算）
            confidence: 置信度
            reason: 原因

        Returns:
            ExecutionResult: 执行结果
        """
        signal = Signal(
            symbol=symbol,
            signal_type=SignalType.BUY,
            price=price,
            quantity=quantity,
            confidence=confidence,
            reason=reason
        )
        return self.execute_signal(signal)

    def execute_sell(
        self,
        symbol: str,
        price: float,
        quantity: int = 0,
        confidence: float = 1.0,
        reason: str = ""
    ) -> ExecutionResult:
        """
        快捷卖出

        Args:
            symbol: 股票代码
            price: 卖出价格
            quantity: 数量（0表示全部）
            confidence: 置信度
            reason: 原因

        Returns:
            ExecutionResult: 执行结果
        """
        signal = Signal(
            symbol=symbol,
            signal_type=SignalType.SELL,
            price=price,
            quantity=quantity,
            confidence=confidence,
            reason=reason
        )
        return self.execute_signal(signal)

    def cancel_order(self, order_id: str) -> bool:
        """
        撤单

        Args:
            order_id: 订单ID

        Returns:
            是否成功
        """
        result = self.broker.cancel_order(order_id)
        return result.success

    def sync_positions(self):
        """同步持仓（启动时或收盘后调用）"""
        positions = self.broker.get_positions()
        for pos_data in positions:
            symbol = pos_data["symbol"]
            position = self.portfolio.get_or_create_position(symbol)
            position.quantity = pos_data["quantity"]
            position.avg_cost = pos_data["avg_cost"]
            position.last_price = pos_data.get("last_price", position.avg_cost)

    def get_portfolio_status(self) -> Dict[str, Any]:
        """
        获取组合状态快照

        Returns:
            状态字典
        """
        # 更新市值
        total_value = self.account.cash + self.portfolio.total_market_value
        self.account.market_value = self.portfolio.total_market_value

        # 计算浮动盈亏
        self.account.update_unrealized_pnl(self.portfolio.total_unrealized_pnl)

        return {
            "account": self.account.to_dict(),
            "portfolio": self.portfolio.to_dict(),
            "total_value": total_value,
            "position_ratio": self.portfolio.total_market_value / total_value if total_value > 0 else 0,
            "timestamp": datetime.now().isoformat(),
        }

    def get_pending_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """获取待成交订单"""
        if hasattr(self.broker, 'order_manager'):
            return self.broker.order_manager.get_pending_orders(symbol)
        return []

    def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        return self.broker.get_order_status(order_id)

    def _risk_check(self, signal: Signal) -> Dict:
        """
        风控前置检查

        Args:
            signal: 交易信号

        Returns:
            {"passed": bool, "reason": str}
        """
        # 日交易次数检查
        if hasattr(self.broker, 'order_manager'):
            if self.broker.order_manager.today_order_count >= self.max_orders_per_day:
                return {
                    "passed": False,
                    "reason": f"日交易次数 {self.max_orders_per_day} 达到上限"
                }

        # 日亏损检查（仅限制买入）
        if signal.signal_type == SignalType.BUY:
            daily_loss_ratio = abs(self.account.today_pnl) / self.initial_capital
            if daily_loss_ratio >= self.daily_loss_limit:
                return {
                    "passed": False,
                    "reason": f"日亏损 {daily_loss_ratio:.1%} 超过限制 {self.daily_loss_limit:.1%}"
                }

        # 资金/持仓检查
        total_value = self.account.cash + self.portfolio.total_market_value

        if signal.signal_type == SignalType.BUY:
            # 买入：检查资金和仓位
            order_value = signal.price * (signal.quantity if signal.quantity > 0 else 100)

            # 单股仓位检查
            new_position_value = self.portfolio.get_position(signal.symbol).market_value if self.portfolio.get_position(signal.symbol) else 0
            new_position_value += order_value
            position_ratio = new_position_value / total_value if total_value > 0 else 0

            if position_ratio > self.max_position_ratio:
                return {
                    "passed": False,
                    "reason": f"单股仓位 {position_ratio:.1%} 超过限制 {self.max_position_ratio:.1%}"
                }

            # 总仓位检查
            new_total_position = (self.portfolio.total_market_value + order_value) / total_value
            if new_total_position > self.max_total_position:
                return {
                    "passed": False,
                    "reason": f"总仓位 {new_total_position:.1%} 超过限制 {self.max_total_position:.1%}"
                }

            # 资金检查
            total_cost = order_value * 1.003  # 预估手续费
            if total_cost > self.account.available_cash:
                return {
                    "passed": False,
                    "reason": f"资金不足，需要 {total_cost:,.2f}，可用 {self.account.available_cash:,.2f}"
                }

        elif signal.signal_type == SignalType.SELL:
            # 卖出：检查持仓
            position = self.portfolio.get_position(signal.symbol)
            if not position:
                return {
                    "passed": False,
                    "reason": "无持仓"
                }

            sell_qty = signal.quantity if signal.quantity > 0 else position.available_quantity
            if sell_qty > position.available_quantity:
                return {
                    "passed": False,
                    "reason": f"可卖数量不足，需要 {sell_qty}，可卖 {position.available_quantity}"
                }

        return {"passed": True, "reason": ""}

    def _signal_to_order(self, signal: Signal) -> Order:
        """
        信号转订单

        Args:
            signal: 交易信号

        Returns:
            Order: 订单对象
        """
        # 确定数量
        quantity = signal.quantity
        if quantity == 0:
            # 自动计算：使用半仓或全部
            total_value = self.account.cash + self.portfolio.total_market_value

            if signal.signal_type == SignalType.BUY:
                # 买入：使用可用资金的 1/3（最多占组合 1/3）
                target_value = min(
                    self.account.available_cash * 0.95,  # 预留手续费
                    total_value * self.max_position_ratio - self.portfolio.get_position(signal.symbol).market_value
                )
                quantity = int(target_value / signal.price / 100) * 100  # 取整到百股
            else:
                # 卖出：全部
                position = self.portfolio.get_position(signal.symbol)
                quantity = position.available_quantity if position else 0

        # 确定方向和订单类型
        if signal.signal_type in {SignalType.BUY, SignalType.BUY_COVER}:
            side = OrderSide.BUY
            position_effect = PositionEffect.OPEN
        else:
            side = OrderSide.SELL
            position_effect = PositionEffect.CLOSE

        # 市价单用0价格，限价单用指定价格
        order_type = OrderType.MARKET if signal.confidence < 0.7 else OrderType.LIMIT
        price = 0.0 if order_type == OrderType.MARKET else signal.price

        return Order(
            symbol=signal.symbol,
            side=side,
            order_type=order_type,
            price=price,
            quantity=quantity,
            position_effect=position_effect,
            extras={
                "signal_type": signal.signal_type.value,
                "confidence": signal.confidence,
                "reason": signal.reason,
                "strategy_name": signal.strategy_name,
            }
        )

    def _notify_callbacks(self, result: ExecutionResult):
        """通知回调"""
        for callback in self._execution_callbacks:
            callback(result)

    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"TradingEngine(cash={self.account.cash:,.2f}, "
            f"equity={self.account.equity:,.2f}, "
            f"positions={self.portfolio.position_count})"
        )
