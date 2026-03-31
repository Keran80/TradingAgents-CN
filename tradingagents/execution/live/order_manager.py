# -*- coding: utf-8 -*-
"""
实盘订单管理器

管理实盘交易订单的发送、撤销、查询
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import defaultdict
import threading
import time

from .broker import LiveBroker, Order, OrderStatus, Side, OrderType

logger = logging.getLogger(__name__)


@dataclass
class OrderRequest:
    """订单请求"""
    symbol: str
    side: Side
    order_type: OrderType
    price: float
    quantity: int
    stop_price: float = 0.0  # 止损价
    time_condition: str = "GFD"  # GFD=当日有效, GTC=取消前有效, IOC=立即成交或取消
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "side": self.side.value,
            "type": self.order_type.value,
            "price": self.price,
            "quantity": self.quantity,
            "stop_price": self.stop_price,
            "time_condition": self.time_condition,
        }


@dataclass
class OrderResult:
    """订单结果"""
    success: bool
    order: Optional[Order] = None
    message: str = ""
    error_code: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "order": self.order.to_dict() if self.order else None,
            "message": self.message,
            "error_code": self.error_code,
        }


class LiveOrderManager:
    """
    实盘订单管理器
    
    功能：
    - 订单发送与跟踪
    - 自动撤单
    - 订单状态监控
    - 成交推送
    """
    
    def __init__(
        self,
        broker: LiveBroker,
        auto_cancel_interval: int = 300,
        check_interval: float = 1.0,
    ):
        """
        初始化管理器
        
        Args:
            broker: 券商接口
            auto_cancel_interval: 自动撤单间隔（秒），0表示不自动撤单
            check_interval: 订单状态检查间隔（秒）
        """
        self.broker = broker
        self.auto_cancel_interval = auto_cancel_interval
        self.check_interval = check_interval
        
        # 本地订单缓存
        self._orders: Dict[str, Order] = {}
        self._pending_orders: Dict[str, Order] = {}
        
        # 回调函数
        self._on_order_update: Optional[Callable] = None
        self._on_trade: Optional[Callable] = None
        self._on_error: Optional[Callable] = None
        
        # 运行状态
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        
        # 重试队列
        self._retry_queue: List[Dict] = []
        
    def set_callbacks(
        self,
        on_order_update: Optional[Callable] = None,
        on_trade: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ):
        """
        设置回调函数
        
        Args:
            on_order_update: 订单更新回调 (order: Order)
            on_trade: 成交回调 (order: Order, trade: Dict)
            on_error: 错误回调 (order: Order, error: str)
        """
        self._on_order_update = on_order_update
        self._on_trade = on_trade
        self._on_error = on_error
        
    def send_order(self, request: OrderRequest) -> OrderResult:
        """
        发送订单
        
        Args:
            request: 订单请求
            
        Returns:
            订单结果
        """
        try:
            # 调用券商接口下单
            order = self.broker.send_order(
                symbol=request.symbol,
                side=request.side,
                order_type=request.order_type,
                price=request.price,
                quantity=request.quantity,
            )
            
            # 缓存订单
            with self._lock:
                self._orders[order.order_id] = order
                self._pending_orders[order.order_id] = order
                
            logger.info(f"Order sent: {order.order_id} {request.side.value} {request.symbol}")
            
            # 回调
            if self._on_order_update:
                self._on_order_update(order)
                
            return OrderResult(success=True, order=order)
            
        except Exception as e:
            logger.error(f"Failed to send order: {e}")
            return OrderResult(
                success=False,
                message=str(e),
                error_code="SEND_FAILED",
            )
            
    def cancel_order(self, order_id: str) -> OrderResult:
        """
        撤销订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            撤销结果
        """
        try:
            # 检查订单状态
            with self._lock:
                order = self._orders.get(order_id)
                
            if not order:
                return OrderResult(
                    success=False,
                    message=f"Order not found: {order_id}",
                    error_code="ORDER_NOT_FOUND",
                )
                
            if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
                return OrderResult(
                    success=False,
                    message=f"Cannot cancel order with status: {order.status.value}",
                    error_code="INVALID_STATUS",
                )
                
            # 调用券商接口撤单
            success = self.broker.cancel_order(order_id)
            
            if success:
                with self._lock:
                    if order_id in self._pending_orders:
                        del self._pending_orders[order_id]
                    order.status = OrderStatus.CANCELLED
                    order.update_time = datetime.now()
                    
                logger.info(f"Order cancelled: {order_id}")
                
                if self._on_order_update:
                    self._on_order_update(order)
                    
                return OrderResult(success=True, order=order)
            else:
                return OrderResult(
                    success=False,
                    message="Cancel failed",
                    error_code="CANCEL_FAILED",
                )
                
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return OrderResult(
                success=False,
                message=str(e),
                error_code="CANCEL_ERROR",
            )
            
    def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        with self._lock:
            return self._orders.get(order_id)
            
    def get_orders(
        self,
        status: Optional[OrderStatus] = None,
    ) -> List[Order]:
        """
        获取订单列表
        
        Args:
            status: 筛选状态，为None返回所有
            
        Returns:
            订单列表
        """
        with self._lock:
            orders = list(self._orders.values())
            
        if status:
            orders = [o for o in orders if o.status == status]
            
        return orders
        
    def get_pending_orders(self) -> List[Order]:
        """获取待成交订单"""
        with self._lock:
            return list(self._pending_orders.values())
            
    def start(self):
        """启动订单监控"""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("LiveOrderManager started")
        
    def stop(self):
        """停止订单监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("LiveOrderManager stopped")
        
    def _run_loop(self):
        """订单监控循环"""
        while self._running:
            try:
                self._check_orders()
                self._auto_cancel()
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                
            time.sleep(self.check_interval)
            
    def _check_orders(self):
        """检查订单状态"""
        with self._lock:
            pending_ids = list(self._pending_orders.keys())
            
        for order_id in pending_ids:
            try:
                orders = self.broker.get_orders()
                order_data = next((o for o in orders if o.order_id == order_id), None)
                
                if order_data:
                    with self._lock:
                        order = self._orders.get(order_id)
                        if order:
                            old_status = order.status
                            order.status = order_data.status
                            order.filled_quantity = order_data.filled_quantity
                            order.avg_fill_price = order_data.avg_fill_price
                            order.update_time = datetime.now()
                            
                            # 状态变化
                            if old_status != order.status:
                                if order.status == OrderStatus.FILLED:
                                    self._on_fill(order)
                                elif order.status == OrderStatus.CANCELLED:
                                    self._on_cancel(order)
                                elif order.status == OrderStatus.REJECTED:
                                    self._on_reject(order)
                                    
                                if self._on_order_update:
                                    self._on_order_update(order)
                                    
            except Exception as e:
                logger.error(f"Failed to check order {order_id}: {e}")
                
    def _auto_cancel(self):
        """自动撤单"""
        if self.auto_cancel_interval <= 0:
            return
            
        now = datetime.now()
        expired_ids = []
        
        with self._lock:
            for order_id, order in self._pending_orders.items():
                elapsed = (now - order.create_time).total_seconds()
                if elapsed >= self.auto_cancel_interval:
                    expired_ids.append(order_id)
                    
        for order_id in expired_ids:
            logger.info(f"Auto-cancel expired order: {order_id}")
            self.cancel_order(order_id)
            
    def _on_fill(self, order: Order):
        """成交处理"""
        logger.info(f"Order filled: {order.order_id}")
        
    def _on_cancel(self, order: Order):
        """撤单处理"""
        logger.info(f"Order cancelled: {order.order_id}")
        with self._lock:
            if order.order_id in self._pending_orders:
                del self._pending_orders[order.order_id]
                
    def _on_reject(self, order: Order):
        """拒单处理"""
        logger.warning(f"Order rejected: {order.order_id}")
        with self._lock:
            if order.order_id in self._pending_orders:
                del self._pending_orders[order.order_id]
                
        if self._on_error:
            self._on_error(order, "Order rejected")
            
    # 便捷方法
    def buy_limit(
        self,
        symbol: str,
        price: float,
        quantity: int,
    ) -> OrderResult:
        """买入限价单"""
        return self.send_order(OrderRequest(
            symbol=symbol,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=price,
            quantity=quantity,
        ))
        
    def sell_limit(
        self,
        symbol: str,
        price: float,
        quantity: int,
    ) -> OrderResult:
        """卖出限价单"""
        return self.send_order(OrderRequest(
            symbol=symbol,
            side=Side.SELL,
            order_type=OrderType.LIMIT,
            price=price,
            quantity=quantity,
        ))
        
    def buy_market(
        self,
        symbol: str,
        quantity: int,
    ) -> OrderResult:
        """买入市价单"""
        return self.send_order(OrderRequest(
            symbol=symbol,
            side=Side.BUY,
            order_type=OrderType.MARKET,
            price=0,  # 市价单价格填0
            quantity=quantity,
        ))
        
    def sell_market(
        self,
        symbol: str,
        quantity: int,
    ) -> OrderResult:
        """卖出市价单"""
        return self.send_order(OrderRequest(
            symbol=symbol,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=0,
            quantity=quantity,
        ))
