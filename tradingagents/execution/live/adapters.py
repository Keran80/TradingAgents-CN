# -*- coding: utf-8 -*-
"""
券商适配器

实现各种券商的具体对接
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict
import random
import time

from .broker import (
    LiveBroker, Order, Position, Account,
    OrderStatus, OrderType, Side
)

logger = logging.getLogger(__name__)


class SimulatorAdapter(LiveBroker):
    """
    模拟交易适配器
    
    用于测试和回测，支持：
    - 模拟下单/撤单
    - 模拟成交
    - 持仓管理
    - 账户资金管理
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 模拟账户
        initial_cash = config.get("initial_cash", 1000000)
        self._account = Account(
            account_id="SIM001",
            cash=initial_cash,
            total_assets=initial_cash,
        )
        
        # 模拟持仓
        self._positions: Dict[str, Position] = {}
        
        # 模拟订单
        self._orders: Dict[str, Order] = {}
        
        # 模拟行情
        self._quotes: Dict[str, float] = defaultdict(lambda: 10.0)
        
        # 成交模拟设置
        self._fill_ratio = config.get("fill_ratio", 1.0)  # 成交比例
        self._fill_delay = config.get("fill_delay", 0)    # 成交延迟(秒)
        
        self._connected = True
        
    def connect(self) -> bool:
        self._connected = True
        logger.info("Simulator connected")
        return True
        
    def disconnect(self):
        self._connected = False
        logger.info("Simulator disconnected")
        
    def get_account(self) -> Account:
        """获取账户信息"""
        # 更新市值
        market_value = sum(p.market_value for p in self._positions.values())
        self._account.market_value = market_value
        self._account.total_assets = self._account.cash + market_value
        return self._account
        
    def get_positions(self) -> List[Position]:
        """获取持仓"""
        return list(self._positions.values())
        
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取指定持仓"""
        return self._positions.get(symbol)
        
    def send_order(
        self,
        symbol: str,
        side: Side,
        order_type: OrderType,
        price: float,
        quantity: int,
    ) -> Order:
        """发送订单"""
        # 检查资金/持仓
        if side == Side.BUY:
            required = price * quantity * 1.0003  # 考虑手续费
            if self._account.cash < required:
                raise ValueError(f"Insufficient cash: {self._account.cash} < {required}")
        else:
            pos = self._positions.get(symbol)
            if not pos or pos.available < quantity:
                raise ValueError(f"Insufficient position: {pos.available if pos else 0} < {quantity}")
                
        # 创建订单
        order_id = f"SIM{int(time.time()*1000)}{random.randint(100,999)}"
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            price=price,
            quantity=quantity,
            status=OrderStatus.SUBMITTED,
        )
        
        self._orders[order_id] = order
        
        # 模拟成交
        self._simulate_fill(order)
        
        return order
        
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        order = self._orders.get(order_id)
        if not order:
            return False
            
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            return False
            
        order.status = OrderStatus.CANCELLED
        order.update_time = datetime.now()
        return True
        
    def get_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        """获取订单列表"""
        orders = list(self._orders.values())
        if status:
            orders = [o for o in orders if o.status == status]
        return orders
        
    def get_trades(self, order_id: Optional[str] = None) -> List[Dict]:
        """获取成交记录"""
        trades = []
        for order in self._orders.values():
            if order.status == OrderStatus.FILLED:
                if order_id is None or order.order_id == order_id:
                    trades.append({
                        "order_id": order.order_id,
                        "symbol": order.symbol,
                        "side": order.side.value,
                        "price": order.avg_fill_price,
                        "quantity": order.filled_quantity,
                        "time": order.update_time.isoformat(),
                    })
        return trades
        
    def set_quote(self, symbol: str, price: float):
        """设置行情价格"""
        self._quotes[symbol] = price
        
    def _simulate_fill(self, order: Order):
        """模拟成交"""
        if self._fill_delay > 0:
            time.sleep(self._fill_delay)
            
        # 按成交比例决定是否成交
        if random.random() > self._fill_ratio:
            return
            
        # 更新订单
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.avg_fill_price = order.price * (1 + random.uniform(-0.001, 0.001))
        order.update_time = datetime.now()
        
        # 更新持仓
        if order.side == Side.BUY:
            self._update_position_buy(order)
        else:
            self._update_position_sell(order)
            
    def _update_position_buy(self, order: Order):
        """更新买入持仓"""
        symbol = order.symbol
        
        if symbol in self._positions:
            pos = self._positions[symbol]
            total_cost = pos.avg_cost * pos.quantity + order.avg_fill_price * order.quantity
            pos.quantity += order.quantity
            pos.available += order.quantity
            pos.avg_cost = total_cost / pos.quantity
        else:
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=order.quantity,
                available=order.quantity,
                avg_cost=order.avg_fill_price,
            )
            
        # 扣除资金
        cost = order.avg_fill_price * order.quantity * 1.0003
        self._account.cash -= cost
        
    def _update_position_sell(self, order: Order):
        """更新卖出持仓"""
        symbol = order.symbol
        pos = self._positions.get(symbol)
        
        if pos:
            pos.quantity -= order.quantity
            pos.available -= order.quantity
            
            if pos.quantity <= 0:
                del self._positions[symbol]
                
        # 收回资金
        revenue = order.avg_fill_price * order.quantity * 0.9997
        self._account.cash += revenue


class TigerAdapter(LiveBroker):
    """
    老虎证券适配器
    
    对接 Tiger Trade API
    需要安装: pip install tigeropen
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        self._account_id = config.get("account")
        self._token = config.get("token")
        self._api = None
        
    def connect(self) -> bool:
        try:
            from tigeropen import TigerOpen
            from tigeropen.common.const import Language
            
            self._api = TigerOpen(
                lang=Language.zh_CN,
            )
            self._api.set_token(self._token)
            
            self._connected = True
            logger.info("Tiger connected")
            return True
            
        except ImportError:
            logger.error("tigeropen not installed")
            return False
        except Exception as e:
            logger.error(f"Tiger connect failed: {e}")
            return False
            
    def disconnect(self):
        self._connected = False
        logger.info("Tiger disconnected")
        
    def get_account(self) -> Account:
        """获取账户"""
        try:
            account_info = self._api.get_account()
            return Account(
                account_id=account_info.account_id,
                cash=account_info.cash,
                total_assets=account_info.total_assets,
            )
        except Exception as e:
            logger.error(f"Get account failed: {e}")
            return Account(account_id="", cash=0)
            
    def get_positions(self) -> List[Position]:
        """获取持仓"""
        try:
            positions = self._api.get_positions()
            return [
                Position(
                    symbol=p.symbol,
                    quantity=p.quantity,
                    available=p.available,
                    avg_cost=p.avg_cost,
                    last_price=p.last_price,
                )
                for p in positions
            ]
        except Exception as e:
            logger.error(f"Get positions failed: {e}")
            return []
            
    def send_order(
        self,
        symbol: str,
        side: Side,
        order_type: OrderType,
        price: float,
        quantity: int,
    ) -> Order:
        """下单"""
        try:
            result = self._api.place_order(
                symbol=symbol,
                side=side.value.upper(),
                order_type=order_type.value.upper(),
                price=price,
                quantity=quantity,
            )
            
            return Order(
                order_id=result.order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                price=price,
                quantity=quantity,
                status=OrderStatus.SUBMITTED,
            )
            
        except Exception as e:
            logger.error(f"Send order failed: {e}")
            raise
            
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        try:
            return self._api.cancel_order(order_id)
        except Exception as e:
            logger.error(f"Cancel order failed: {e}")
            return False
            
    def get_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        """获取订单"""
        try:
            orders = self._api.get_orders()
            return [self._convert_order(o) for o in orders]
        except Exception as e:
            logger.error(f"Get orders failed: {e}")
            return []
            
    def get_trades(self, order_id: Optional[str] = None) -> List[Dict]:
        """获取成交"""
        try:
            return self._api.get_trades(order_id)
        except Exception as e:
            logger.error(f"Get trades failed: {e}")
            return []
            
    def _convert_order(self, data: Dict) -> Order:
        """转换订单"""
        return Order(
            order_id=data["order_id"],
            symbol=data["symbol"],
            side=Side(data["side"].lower()),
            order_type=OrderType(data["type"].lower()),
            price=data["price"],
            quantity=data["quantity"],
            filled_quantity=data.get("filled", 0),
            avg_fill_price=data.get("avg_fill_price", 0),
            status=OrderStatus(data["status"]),
        )


class FutuAdapter(LiveBroker):
    """
    富途证券适配器
    
    对接 Futu OpenD API
    需要安装: pip install futu-api
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        self._host = config.get("host", "127.0.0.1")
        self._port = config.get("port", 11111)
        self._api = None
        
    def connect(self) -> bool:
        try:
            from futu import OpenQuoteContext, OpenTradeContext
            
            self._quote_ctx = OpenQuoteContext(host=self._host, port=self._port)
            self._trade_ctx = OpenTradeContext(host=self._host, port=self._port)
            
            self._connected = True
            logger.info("Futu connected")
            return True
            
        except ImportError:
            logger.error("futu-api not installed")
            return False
        except Exception as e:
            logger.error(f"Futu connect failed: {e}")
            return False
            
    def disconnect(self):
        if hasattr(self, "_quote_ctx"):
            self._quote_ctx.close()
        if hasattr(self, "_trade_ctx"):
            self._trade_ctx.close()
        self._connected = False
        logger.info("Futu disconnected")
        
    def get_account(self) -> Account:
        """获取账户"""
        try:
            ret, data = self._trade_ctx.get_account_list()
            if ret == 0 and not data.empty:
                acc = data.iloc[0]
                return Account(
                    account_id=str(acc['account_id']),
                    cash=float(acc['cash']),
                    total_assets=float(acc['total_assets']),
                )
        except Exception as e:
            logger.error(f"Get account failed: {e}")
        return Account(account_id="", cash=0)
        
    def get_positions(self) -> List[Position]:
        """获取持仓"""
        try:
            ret, data = self._trade_ctx.get_position_list()
            if ret == 0 and not data.empty:
                return [
                    Position(
                        symbol=str(row['code']),
                        quantity=int(row['qty']),
                        available=int(row['can_sell_qty']),
                        avg_cost=float(row['cost']),
                        last_price=float(row['close_price']),
                    )
                    for _, row in data.iterrows()
                ]
        except Exception as e:
            logger.error(f"Get positions failed: {e}")
        return []
        
    def send_order(
        self,
        symbol: str,
        side: Side,
        order_type: OrderType,
        price: float,
        quantity: int,
    ) -> Order:
        """下单"""
        try:
            # 转换买卖方向
            trade_side = 1 if side == Side.BUY else 2
            
            # 转换订单类型
            if order_type == OrderType.MARKET:
                price_type = 5  # 市价
            else:
                price_type = 0  # 限价
                
            ret, data = self._trade_ctx.place_order(
                code=symbol,
                price=price,
                qty=quantity,
                trade_side=trade_side,
                price_type=price_type,
            )
            
            if ret == 0:
                order_id = str(data.iloc[0]['order_id'])
                return Order(
                    order_id=order_id,
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    price=price,
                    quantity=quantity,
                    status=OrderStatus.SUBMITTED,
                )
            else:
                raise ValueError(f"Place order failed: {data}")
                
        except Exception as e:
            logger.error(f"Send order failed: {e}")
            raise
            
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        try:
            ret, data = self._trade_ctx.cancel_order(order_id)
            return ret == 0
        except Exception as e:
            logger.error(f"Cancel order failed: {e}")
            return False
            
    def get_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        """获取订单"""
        try:
            ret, data = self._trade_ctx.get_order_list()
            if ret == 0 and not data.empty:
                orders = []
                for _, row in data.iterrows():
                    order = Order(
                        order_id=str(row['order_id']),
                        symbol=str(row['code']),
                        side=Side.BUY if row['trade_side'] == 1 else Side.SELL,
                        order_type=OrderType.LIMIT if row['price_type'] == 0 else OrderType.MARKET,
                        price=float(row['price']),
                        quantity=int(row['qty']),
                        filled_quantity=int(row['dealt_qty']),
                        status=self._convert_status(row['order_status']),
                    )
                    orders.append(order)
                return orders
        except Exception as e:
            logger.error(f"Get orders failed: {e}")
        return []
        
    def _convert_status(self, status: int) -> OrderStatus:
        """转换订单状态"""
        mapping = {
            0: OrderStatus.SUBMITTED,
            1: OrderStatus.FILLED,
            2: OrderStatus.CANCELLED,
            3: OrderStatus.REJECTED,
        }
        return mapping.get(status, OrderStatus.PENDING)


class JoinQuantAdapter(LiveBroker):
    """
    聚宽适配器
    
    对接 JoinQuant API
    需要安装: pip install jqdatasdk
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        self._username = config.get("username")
        self._password = config.get("password")
        
    def connect(self) -> bool:
        try:
            import jqdatasdk as jq
            
            jq.auth(self._username, self._password)
            
            self._jq = jq
            self._connected = True
            logger.info("JoinQuant connected")
            return True
            
        except ImportError:
            logger.error("jqdatasdk not installed")
            return False
        except Exception as e:
            logger.error(f"JoinQuant connect failed: {e}")
            return False
            
    def disconnect(self):
        if hasattr(self, "_jq"):
            self._jq.logout()
        self._connected = False
        logger.info("JoinQuant disconnected")
        
    def get_account(self) -> Account:
        """获取账户"""
        try:
            cash = self._jq.get_cash()
            return Account(
                account_id="JQ",
                cash=float(cash),
                total_assets=float(cash),
            )
        except Exception as e:
            logger.error(f"Get account failed: {e}")
            return Account(account_id="", cash=0)
            
    def get_positions(self) -> List[Position]:
        """获取持仓"""
        try:
            positions = self._jq.get_positions()
            return [
                Position(
                    symbol=p['security'],
                    quantity=int(p['amount']),
                    available=int(p['available_amount']),
                    avg_cost=float(p['avg_cost']),
                    last_price=float(p['last_price']),
                )
                for p in positions
            ]
        except Exception as e:
            logger.error(f"Get positions failed: {e}")
            return []
            
    def send_order(
        self,
        symbol: str,
        side: Side,
        order_type: OrderType,
        price: float,
        quantity: int,
    ) -> Order:
        """下单"""
        try:
            if order_type == OrderType.MARKET:
                order_id = self._jq.order_shares(
                    symbol, quantity, side.value, 'market'
                )
            else:
                order_id = self._jq.order_shares(
                    symbol, quantity, side.value, 'limit', price
                )
                
            return Order(
                order_id=str(order_id),
                symbol=symbol,
                side=side,
                order_type=order_type,
                price=price,
                quantity=quantity,
                status=OrderStatus.SUBMITTED,
            )
            
        except Exception as e:
            logger.error(f"Send order failed: {e}")
            raise
            
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        try:
            self._jq.cancel_order(int(order_id))
            return True
        except Exception as e:
            logger.error(f"Cancel order failed: {e}")
            return False
            
    def get_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        """获取订单"""
        try:
            orders = self._jq.get_orders()
            return [
                Order(
                    order_id=str(o.id),
                    symbol=o.security,
                    side=Side.BUY if o.side.value == 'buy' else Side.SELL,
                    order_type=OrderType.LIMIT if o.type.value == 'limit' else OrderType.MARKET,
                    price=float(o.price),
                    quantity=int(o.amount),
                    filled_quantity=int(o.filled_amount),
                    status=self._convert_status(o.status),
                )
                for o in orders
            ]
        except Exception as e:
            logger.error(f"Get orders failed: {e}")
            return []
            
    def _convert_status(self, status: str) -> OrderStatus:
        """转换状态"""
        mapping = {
            'open': OrderStatus.SUBMITTED,
            'filled': OrderStatus.FILLED,
            'cancelled': OrderStatus.CANCELLED,
            'rejected': OrderStatus.REJECTED,
        }
        return mapping.get(status, OrderStatus.PENDING)
