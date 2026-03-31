# -*- coding: utf-8 -*-
"""
实盘券商接口

提供统一的券商接口规范，支持多种券商对接
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import time

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"       # 待报
    SUBMITTED = "submitted"   # 已提交
    PARTIAL = "partial"      # 部分成交
    FILLED = "filled"        # 完全成交
    CANCELLED = "cancelled"  # 已撤销
    REJECTED = "rejected"    # 已拒绝


class OrderType(Enum):
    """订单类型"""
    LIMIT = "limit"          # 限价
    MARKET = "market"        # 市价
    STOP = "stop"            # 止损
    STOP_LIMIT = "stop_limit" # 止损限价


class Side(Enum):
    """买卖方向"""
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """订单"""
    order_id: str
    symbol: str
    side: Side
    order_type: OrderType
    price: float
    quantity: int
    filled_quantity: int = 0
    avg_fill_price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    create_time: datetime = field(default_factory=datetime.now)
    update_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "type": self.order_type.value,
            "price": self.price,
            "quantity": self.quantity,
            "filled": self.filled_quantity,
            "avg_price": self.avg_fill_price,
            "status": self.status.value,
            "create_time": self.create_time.isoformat(),
            "update_time": self.update_time.isoformat(),
        }


@dataclass
class Position:
    """持仓"""
    symbol: str
    quantity: int
    available: int
    avg_cost: float
    last_price: float = 0.0
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.last_price
        
    @property
    def unrealized_pnl(self) -> float:
        return (self.last_price - self.avg_cost) * self.quantity


@dataclass
class Account:
    """账户"""
    account_id: str
    cash: float
    frozen_cash: float = 0.0
    market_value: float = 0.0
    total_assets: float = 0.0
    
    @property
    def available_cash(self) -> float:
        return self.cash - self.frozen_cash


class LiveBroker(ABC):
    """
    实盘券商接口基类
    
    定义券商接口规范，子类实现具体券商的对接
    """
    
    # 支持的券商类型
    SUPPORTED_BROKERS = {
        "simulator": "模拟交易",
        "tiger": "老虎证券",
        "futu": "富途证券",
        "joinquant": "聚宽",
        "snowball": "雪球",
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化券商接口
        
        Args:
            config: 券商配置
        """
        self.config = config
        self._connected = False
        self._account: Optional[Account] = None
        
    @abstractmethod
    def connect(self) -> bool:
        """连接券商"""
        pass
        
    @abstractmethod
    def disconnect(self):
        """断开连接"""
        pass
        
    @abstractmethod
    def get_account(self) -> Account:
        """获取账户信息"""
        pass
        
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """获取持仓"""
        pass
        
    @abstractmethod
    def send_order(
        self,
        symbol: str,
        side: Side,
        order_type: OrderType,
        price: float,
        quantity: int,
    ) -> Order:
        """下单"""
        pass
        
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        pass
        
    @abstractmethod
    def get_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        """获取订单列表"""
        pass
        
    @abstractmethod
    def get_trades(self, order_id: Optional[str] = None) -> List[Dict]:
        """获取成交记录"""
        pass
        
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """获取行情（可选实现）"""
        return None
        
    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected
        
    @classmethod
    def create(
        cls,
        broker_type: str,
        **kwargs,
    ) -> "LiveBroker":
        """
        工厂方法：创建券商接口
        
        Args:
            broker_type: 券商类型
            **kwargs: 券商配置参数
            
        Returns:
            券商接口实例
        """
        if broker_type == "simulator":
            from .adapters import SimulatorAdapter
            return SimulatorAdapter(kwargs)
        elif broker_type == "tiger":
            from .adapters import TigerAdapter
            return TigerAdapter(kwargs)
        elif broker_type == "futu":
            from .adapters import FutuAdapter
            return FutuAdapter(kwargs)
        elif broker_type == "joinquant":
            from .adapters import JoinQuantAdapter
            return JoinQuantAdapter(kwargs)
        else:
            raise ValueError(f"Unsupported broker type: {broker_type}")
