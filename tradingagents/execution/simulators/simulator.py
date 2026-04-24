# -*- coding: utf-8 -*-
"""
SimulatorBroker - 模拟交易券商

实现完整的模拟撮合引擎，支持：
- 市价单、限价单
- 涨跌停检查
- 滑点模拟
- 手续费计算（佣金+印花税）
- T+1 交易限制
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import threading
import time
import logging

logger = logging.getLogger(__name__)

from ..broker import (
    BrokerInterface, Order, OrderType, OrderSide,
    OrderStatus, PositionEffect, OrderResult, Trade, Quote
)
from ..account import Account
from ..portfolio import Portfolio, Position
from ..order_manager import OrderManager


class SimulatorBroker(BrokerInterface):
    """
    模拟交易券商

    特性：
    - 模拟订单撮合（基于行情）
    - 支持市价单、限价单
    - 涨跌停检查
    - 模拟滑点
    - 手续费计算
    """

    def __init__(
        self,
        account: Account = None,
        portfolio: Portfolio = None,
        commission_rate: float = 0.0003,      # 佣金万三
        stamp_tax: float = 0.001,              # 印花税千一（仅卖出）
        slippage: float = 0.001,               # 滑点 0.1%
        price_limit_ratio: float = 0.10,       # 涨跌停 10%
        min_commission: float = 5.0,          # 最低佣金
    ):
        """
        初始化模拟券商

        Args:
            account: 账户实例
            portfolio: 持仓实例
            commission_rate: 佣金费率
            stamp_tax: 印花税率
            slippage: 滑点率
            price_limit_ratio: 涨跌停比例
            min_commission: 最低佣金
        """
        super().__init__({
            "commission_rate": commission_rate,
            "stamp_tax": stamp_tax,
            "slippage": slippage,
            "price_limit_ratio": price_limit_ratio,
            "min_commission": min_commission,
        })

        self.account = account or Account()
        self.portfolio = portfolio or Portfolio()
        self.order_manager = OrderManager(self)

        self.commission_rate = commission_rate
        self.stamp_tax = stamp_tax
        self.slippage = slippage
        self.price_limit_ratio = price_limit_ratio
        self.min_commission = min_commission

        self._quotes: Dict[str, Quote] = {}  # 实时行情缓存
        self._prev_close: Dict[str, float] = {}  # 昨收价
        self._running = False
        self._match_thread: threading.Thread = None

    def connect(self) -> bool:
        """连接（模拟盘始终成功）"""
        self._connected = True
        self._running = True
        # 启动撮合线程
        self._match_thread = threading.Thread(target=self._match_loop, daemon=True)
        self._match_thread.start()
        return True

    def disconnect(self) -> bool:
        """断开连接"""
        self._running = False
        self._connected = False
        if self._match_thread:
            self._match_thread.join(timeout=1)
        return True

    def update_quote(self, symbol: str, quote: Quote):
        """
        更新行情（由外部数据源调用）

        Args:
            symbol: 股票代码
            quote: 行情对象
        """
        if symbol not in self._prev_close:
            self._prev_close[symbol] = quote.last_price
        self._quotes[symbol] = quote

        # 更新持仓价格
        self.portfolio.update_position_price(symbol, quote.last_price)

    def update_price(self, symbol: str, price: float):
        """
        快速更新价格（简化接口）

        Args:
            symbol: 股票代码
            price: 最新价
        """
        if symbol in self._quotes:
            self._quotes[symbol].last_price = price
        else:
            self._quotes[symbol] = Quote(symbol=symbol, last_price=price)

        # 更新持仓价格
        self.portfolio.update_position_price(symbol, price)

    def set_prev_close(self, symbol: str, prev_close: float):
        """
        设置昨收价

        Args:
            symbol: 股票代码
            prev_close: 昨收价
        """
        self._prev_close[symbol] = prev_close

    def place_order(self, order: Order) -> OrderResult:
        """
        下单

        Args:
            order: 订单对象

        Returns:
            OrderResult: 执行结果
        """
        if not self._connected:
            order.status = OrderStatus.REJECTED
            order.reject_reason = "broker not connected"
            return OrderResult(
                success=False,
                order_id=order.order_id,
                message="券商未连接",
                error_code="NOT_CONNECTED",
                order=order
            )

        # 订单验证
        validation = self._validate_order(order)
        if not validation["valid"]:
            order.status = OrderStatus.REJECTED
            order.reject_reason = validation["reason"]
            return OrderResult(
                success=False,
                order_id=order.order_id,
                message=validation["reason"],
                error_code="VALIDATION_FAILED",
                order=order
            )

        # 市价单：使用当前行情
        if order.order_type == OrderType.MARKET:
            quote = self._quotes.get(order.symbol)
            if not quote:
                order.status = OrderStatus.REJECTED
                order.reject_reason = "no quote available"
                return OrderResult(
                    success=False,
                    order_id=order.order_id,
                    message="无行情数据",
                    error_code="NO_QUOTE",
                    order=order
                )
            order.price = self._apply_slippage(quote.last_price, order.side)

        # 计算所需资金/股份
        order_value = order.price * order.quantity

        if order.side == OrderSide.BUY:
            # 买入：冻结资金
            total_cost = order_value * (1 + self.commission_rate)
            if self.account.available_cash < total_cost:
                order.status = OrderStatus.REJECTED
                order.reject_reason = "insufficient cash"
                return OrderResult(
                    success=False,
                    order_id=order.order_id,
                    message=f"资金不足，需要 {total_cost:,.2f}，可用 {self.account.available_cash:,.2f}",
                    error_code="INSUFFICIENT_CASH",
                    order=order
                )
            self.account.freeze_cash(total_cost)

        else:
            # 卖出：检查持仓
            position = self.portfolio.get_position(order.symbol)
            if not position or position.available_quantity < order.quantity:
                order.status = OrderStatus.REJECTED
                order.reject_reason = "insufficient position"
                available = position.available_quantity if position else 0
                return OrderResult(
                    success=False,
                    order_id=order.order_id,
                    message=f"持仓不足，需要 {order.quantity}，可卖 {available}",
                    error_code="INSUFFICIENT_POSITION",
                    order=order
                )
            position.freeze(order.quantity)

        # 提交订单
        order.status = OrderStatus.SUBMITTED
        order.updated_time = datetime.now()
        self.order_manager.pending_orders[order.order_id] = order

        return OrderResult(
            success=True,
            order_id=order.order_id,
            message="订单已提交",
            order=order
        )

    def cancel_order(self, order_id: str) -> OrderResult:
        """
        撤单

        Args:
            order_id: 订单ID

        Returns:
            OrderResult: 执行结果
        """
        order = self.order_manager.pending_orders.get(order_id)
        if not order:
            return OrderResult(
                success=False,
                order_id=order_id,
                message="订单不存在",
                error_code="ORDER_NOT_FOUND"
            )

        if order.status not in {OrderStatus.SUBMITTED, OrderStatus.PARTIAL}:
            return OrderResult(
                success=False,
                order_id=order_id,
                message=f"订单状态 {order.status.value} 不允许撤单",
                error_code="INVALID_STATUS"
            )

        # 解冻资金/持仓
        if order.side == OrderSide.BUY:
            unfreeze_amount = order.price * order.remaining_quantity * (1 + self.commission_rate)
            self.account.unfreeze_cash(unfreeze_amount)
        else:
            position = self.portfolio.get_position(order.symbol)
            if position:
                position.unfreeze(order.remaining_quantity)

        order.status = OrderStatus.CANCELLED
        order.cancel_time = datetime.now()
        self.order_manager._move_to_history(order)
        self.order_manager.pending_orders.pop(order_id, None)

        return OrderResult(
            success=True,
            order_id=order_id,
            message="撤单成功",
            order=order
        )

    def get_order_status(self, order_id: str) -> Optional[Order]:
        """查询订单状态"""
        return self.order_manager.get_order(order_id)

    def get_orders(self, symbol: Optional[str] = None,
                  status: Optional[OrderStatus] = None) -> List[Order]:
        """查询订单列表"""
        if status == OrderStatus.PENDING:
            return self.order_manager.get_pending_orders(symbol)
        return self.order_manager.get_history_orders(symbol, status)

    def get_trades(self, order_id: Optional[str] = None) -> List[Trade]:
        """查询成交记录"""
        return self.order_manager.get_trades(order_id)

    def get_positions(self) -> List[Dict[str, Any]]:
        """查询持仓"""
        positions = self.portfolio.get_all_positions()
        return [p.to_dict() for p in positions]

    def get_account(self) -> Dict[str, Any]:
        """查询账户信息"""
        return self.account.to_dict()

    def get_quote(self, symbol: str) -> Optional[Quote]:
        """获取行情"""
        return self._quotes.get(symbol)

    def _validate_order(self, order: Order) -> Dict:
        """
        订单验证

        Returns:
            {"valid": bool, "reason": str}
        """
        quote = self._quotes.get(order.symbol)

        # 检查行情
        if not quote:
            return {"valid": False, "reason": "无行情数据"}

        # 涨跌停检查
        prev_close = self._prev_close.get(order.symbol, quote.last_price)
        upper_limit = prev_close * (1 + self.price_limit_ratio)
        lower_limit = prev_close * (1 - self.price_limit_ratio)

        if order.side == OrderSide.BUY and order.price > upper_limit:
            return {"valid": False, "reason": f"买入价格超过涨停价 {upper_limit:.2f}"}

        if order.side == OrderSide.SELL and order.price < lower_limit:
            return {"valid": False, "reason": f"卖出价格低于跌停价 {lower_limit:.2f}"}

        # 数量检查（A股必须100股整数倍）
        if order.quantity % 100 != 0:
            return {"valid": False, "reason": "数量必须是100的整数倍"}

        return {"valid": True, "reason": ""}

    def _apply_slippage(self, price: float, side: OrderSide) -> float:
        """应用滑点"""
        if side == OrderSide.BUY:
            return price * (1 + self.slippage)
        else:
            return price * (1 - self.slippage)

    def _match_loop(self):
        """撮合循环（后台线程）"""
        while self._running:
            try:
                self._process_matches()
            except Exception as e:
                logger.error(f"Match loop error: {e}", exc_info=True)
            time.sleep(0.1)  # 100ms 撮合一次

    def _process_matches(self):
        """处理撮合"""
        for order in list(self.order_manager.pending_orders.values()):
            self._try_match(order)

    def _try_match(self, order: Order):
        """
        尝试撮合订单

        Args:
            order: 订单对象
        """
        quote = self._quotes.get(order.symbol)
        if not quote:
            return

        # 检查是否可成交
        can_match = False
        fill_price = order.price

        if order.order_type == OrderType.MARKET:
            can_match = True
            fill_price = self._apply_slippage(quote.last_price, order.side)

        elif order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.BUY and quote.last_price <= order.price:
                can_match = True
                fill_price = min(order.price, quote.last_price)
            elif order.side == OrderSide.SELL and quote.last_price >= order.price:
                can_match = True
                fill_price = max(order.price, quote.last_price)

        if not can_match:
            return

        # 成交
        self._execute_order(order, fill_price)

    def _execute_order(self, order: Order, fill_price: float):
        """
        执行订单成交

        Args:
            order: 订单对象
            fill_price: 成交价格
        """
        # 计算手续费
        trade_value = fill_price * order.quantity
        commission = max(trade_value * self.commission_rate, self.min_commission)
        stamp_tax = 0.0

        if order.side == OrderSide.SELL:
            stamp_tax = trade_value * self.stamp_tax

        total_cost = trade_value + commission + stamp_tax

        # 更新账户
        if order.side == OrderSide.BUY:
            self.account.deduct_cash(trade_value + commission)
            self.account.add_cash(0)  # 保持现金一致性

            # 更新持仓
            position = self.portfolio.get_or_create_position(order.symbol)
            position.add_position(order.quantity, fill_price)
            # 更新持仓价格
            position.last_price = fill_price

        else:
            self.account.add_cash(trade_value - commission - stamp_tax)

            # 更新持仓
            position = self.portfolio.get_position(order.symbol)
            if position:
                realized_pnl = position.reduce_position(order.quantity, fill_price)
                self.account.add_realized_pnl(realized_pnl)
                # 更新持仓价格
                position.last_price = fill_price

        self.account.add_commission(commission)
        if stamp_tax > 0:
            self.account.add_stamp_tax(stamp_tax)
        self.account.today_trades += 1

        # 创建成交记录
        trade = Trade(
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            price=fill_price,
            quantity=order.quantity,
            commission=commission + stamp_tax
        )
        self.order_manager.add_trade(trade)

        # 更新订单状态
        order.filled_quantity = order.quantity
        order.avg_fill_price = fill_price
        order.status = OrderStatus.FILLED
        self.order_manager.update_order_status(order.order_id, OrderStatus.FILLED)

    def get_portfolio_status(self) -> Dict:
        """
        获取组合状态快照

        Returns:
            状态字典
        """
        return {
            "account": self.get_account(),
            "portfolio": self.portfolio.to_dict(),
            "orders": self.order_manager.to_dict(),
        }
