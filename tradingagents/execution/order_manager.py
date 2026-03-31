# -*- coding: utf-8 -*-
"""
OrderManager - 订单生命周期管理

管理订单的创建、提交、成交、撤销等全生命周期
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Callable
from .broker import Order, OrderStatus, OrderResult, Trade, BrokerInterface


class OrderManager:
    """
    订单管理器

    负责：
    - 订单预处理（验证、合并）
    - 订单提交到broker
    - 订单状态跟踪
    - 成交撮合（模拟盘）
    - 历史订单记录
    """

    def __init__(self, broker: BrokerInterface):
        """
        初始化订单管理器

        Args:
            broker: 券商适配器实例
        """
        self.broker = broker
        self.pending_orders: Dict[str, Order] = {}  # 待成交订单
        self.history_orders: List[Order] = []         # 历史订单
        self.history_trades: List[Trade] = []        # 历史成交
        self._order_callbacks: List[Callable] = []  # 订单回调
        self._trade_callbacks: List[Callable] = []  # 成交回调

    def register_order_callback(self, callback: Callable[[Order], None]):
        """
        注册订单状态变化回调

        Args:
            callback: 回调函数，签名为 func(order: Order)
        """
        self._order_callbacks.append(callback)

    def register_trade_callback(self, callback: Callable[[Trade], None]):
        """
        注册成交回调

        Args:
            callback: 回调函数，签名为 func(trade: Trade)
        """
        self._trade_callbacks.append(callback)

    def place_order(self, order: Order) -> OrderResult:
        """
        下单

        Args:
            order: 订单对象

        Returns:
            OrderResult: 执行结果
        """
        # 订单预处理
        if order.status != OrderStatus.PENDING:
            return OrderResult(
                success=False,
                order_id=order.order_id,
                message="订单状态不是PENDING",
                error_code="INVALID_ORDER_STATUS"
            )

        # 提交到broker
        result = self.broker.place_order(order)

        if result.success:
            # 跟踪订单
            order.status = OrderStatus.SUBMITTED
            self.pending_orders[order.order_id] = order

        return result

    def cancel_order(self, order_id: str) -> OrderResult:
        """
        撤单

        Args:
            order_id: 订单ID

        Returns:
            OrderResult: 执行结果
        """
        if order_id not in self.pending_orders:
            return OrderResult(
                success=False,
                order_id=order_id,
                message="订单不存在或已结束",
                error_code="ORDER_NOT_FOUND"
            )

        order = self.pending_orders[order_id]
        result = self.broker.cancel_order(order_id)

        if result.success:
            order.status = OrderStatus.CANCELLED
            order.cancel_time = datetime.now()
            self._move_to_history(order)
            self.pending_orders.pop(order_id, None)

        return result

    def get_order(self, order_id: str) -> Optional[Order]:
        """
        获取订单

        Args:
            order_id: 订单ID

        Returns:
            Order对象或None
        """
        return self.pending_orders.get(order_id)

    def get_pending_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        获取待成交订单

        Args:
            symbol: 股票代码过滤（可选）

        Returns:
            订单列表
        """
        orders = list(self.pending_orders.values())
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        return orders

    def get_history_orders(self, symbol: Optional[str] = None,
                          status: Optional[OrderStatus] = None) -> List[Order]:
        """
        获取历史订单

        Args:
            symbol: 股票代码过滤（可选）
            status: 订单状态过滤（可选）

        Returns:
            订单列表
        """
        orders = self.history_orders
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        if status:
            orders = [o for o in orders if o.status == status]
        return orders

    def get_trades(self, order_id: Optional[str] = None) -> List[Trade]:
        """
        获取成交记录

        Args:
            order_id: 订单ID过滤（可选）

        Returns:
            成交列表
        """
        if order_id:
            return [t for t in self.history_trades if t.order_id == order_id]
        return self.history_trades

    def update_order_status(self, order_id: str, status: OrderStatus,
                           filled_qty: int = 0, avg_price: float = 0.0):
        """
        更新订单状态（由撮合引擎调用）

        Args:
            order_id: 订单ID
            status: 新状态
            filled_qty: 成交数量
            avg_price: 成交均价
        """
        if order_id not in self.pending_orders:
            return

        order = self.pending_orders[order_id]
        order.status = status
        order.updated_time = datetime.now()

        if filled_qty > 0:
            order.filled_quantity = filled_qty
            order.avg_fill_price = avg_price

        if status in {OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED}:
            self._move_to_history(order)
            self.pending_orders.pop(order_id, None)

        # 触发回调
        for callback in self._order_callbacks:
            callback(order)

    def add_trade(self, trade: Trade):
        """
        添加成交记录（由撮合引擎调用）

        Args:
            trade: 成交记录
        """
        self.history_trades.append(trade)

        # 触发回调
        for callback in self._trade_callbacks:
            callback(trade)

    def _move_to_history(self, order: Order):
        """移动订单到历史"""
        self.history_orders.append(order)

    @property
    def pending_count(self) -> int:
        """待成交订单数"""
        return len(self.pending_orders)

    @property
    def today_order_count(self) -> int:
        """今日订单总数"""
        today = datetime.now().date()
        return len([
            o for o in self.history_orders
            if o.created_time.date() == today
        ])

    @property
    def today_trade_count(self) -> int:
        """今日成交总数"""
        today = datetime.now().date()
        return len([
            t for t in self.history_trades
            if t.trade_time.date() == today
        ])

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "pending_count": self.pending_count,
            "today_order_count": self.today_order_count,
            "today_trade_count": self.today_trade_count,
            "total_trades": len(self.history_trades),
        }
