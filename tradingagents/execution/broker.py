# -*- coding: utf-8 -*-
"""
Broker Interface - 券商适配器基类

定义所有券商接口必须实现的抽象方法
支持：模拟交易、通达信、东方财富等
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import uuid4


class OrderType(Enum):
    """订单类型"""
    MARKET = "MARKET"           # 市价单
    LIMIT = "LIMIT"            # 限价单
    STOP = "STOP"              # 止损单
    STOP_LIMIT = "STOP_LIMIT"  # 止损限价单


class OrderSide(Enum):
    """交易方向"""
    BUY = "BUY"                # 买入
    SELL = "SELL"              # 卖出


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "PENDING"        # 待提交
    SUBMITTED = "SUBMITTED"    # 已提交
    PARTIAL = "PARTIAL"        # 部分成交
    FILLED = "FILLED"          # 全部成交
    CANCELLED = "CANCELLED"    # 已撤销
    REJECTED = "REJECTED"      # 已拒绝
    EXPIRED = "EXPIRED"        # 已过期


class PositionEffect(Enum):
    """持仓效应（用于区分开平仓）"""
    OPEN = "OPEN"              # 开仓
    CLOSE = "CLOSE"            # 平仓
    CLOSE_TODAY = "CLOSE_TODAY"    # 平今
    CLOSE_YESTERDAY = "CLOSE_YESTERDAY"  # 平昨


@dataclass
class Order:
    """
    订单数据类

    Attributes:
        symbol: 股票代码，如 "000001.SZ"
        side: 买卖方向
        order_type: 订单类型
        price: 订单价格（限价单/止损单用）
        quantity: 数量（正数）
        stop_price: 止损价格
        position_effect: 开平仓标识
        order_id: 订单ID（系统生成）
        status: 订单状态
        filled_quantity: 已成交数量
        avg_fill_price: 成交均价
        created_time: 创建时间
        updated_time: 更新时间
        cancel_time: 撤销时间
        reject_reason: 拒绝原因
    """
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: float = 0.0
    stop_price: float = 0.0
    position_effect: PositionEffect = PositionEffect.OPEN
    order_id: str = field(default_factory=lambda: str(uuid4()))
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    avg_fill_price: float = 0.0
    created_time: datetime = field(default_factory=datetime.now)
    updated_time: datetime = field(default_factory=datetime.now)
    cancel_time: Optional[datetime] = None
    reject_reason: Optional[str] = None
    extras: Dict[str, Any] = field(default_factory=dict)

    @property
    def remaining_quantity(self) -> int:
        """剩余未成交数量"""
        return self.quantity - self.filled_quantity

    @property
    def is_active(self) -> bool:
        """订单是否处于活跃状态"""
        return self.status in {
            OrderStatus.PENDING,
            OrderStatus.SUBMITTED,
            OrderStatus.PARTIAL
        }

    @property
    def order_value(self) -> float:
        """订单金额（基于指定价格）"""
        return self.price * self.quantity

    def __post_init__(self):
        """参数校验"""
        if self.quantity <= 0:
            raise ValueError(f"quantity must be positive, got {self.quantity}")
        if self.order_type == OrderType.LIMIT and self.price <= 0:
            raise ValueError("LIMIT order requires positive price")


@dataclass
class Trade:
    """
    成交数据类

    Attributes:
        trade_id: 成交ID
        order_id: 关联订单ID
        symbol: 股票代码
        side: 买卖方向
        price: 成交价格
        quantity: 成交数量
        commission: 手续费
        trade_time: 成交时间
    """
    trade_id: str = field(default_factory=lambda: str(uuid4()))
    order_id: str = ""
    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    price: float = 0.0
    quantity: int = 0
    commission: float = 0.0
    trade_time: datetime = field(default_factory=datetime.now)

    @property
    def trade_value(self) -> float:
        """成交金额"""
        return self.price * self.quantity


@dataclass
class Quote:
    """
    行情数据类

    Attributes:
        symbol: 股票代码
        last_price: 最新价
        open_price: 开盘价
        high_price: 最高价
        low_price: 最低价
        volume: 成交量
        turnover: 成交额
        bid_price_1~5: 买1~买5价
        ask_price_1~5: 卖1~卖5价
        timestamp: 时间戳
    """
    symbol: str
    last_price: float = 0.0
    open_price: float = 0.0
    high_price: float = 0.0
    low_price: float = 0.0
    volume: int = 0
    turnover: float = 0.0
    bid_price_1: float = 0.0
    bid_price_2: float = 0.0
    bid_price_3: float = 0.0
    bid_price_4: float = 0.0
    bid_price_5: float = 0.0
    ask_price_1: float = 0.0
    ask_price_2: float = 0.0
    ask_price_3: float = 0.0
    ask_price_4: float = 0.0
    ask_price_5: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def upper_limit(self) -> float:
        """涨停价（A股10%涨跌停限制）"""
        return self.last_price * 1.10 if self.last_price > 0 else 0.0

    @property
    def lower_limit(self) -> float:
        """跌停价"""
        return self.last_price * 0.90 if self.last_price > 0 else 0.0

    def is_limit_up(self, prev_close: float) -> bool:
        """是否涨停"""
        if prev_close <= 0:
            return False
        return self.last_price >= prev_close * 1.0999

    def is_limit_down(self, prev_close: float) -> bool:
        """是否跌停"""
        if prev_close <= 0:
            return False
        return self.last_price <= prev_close * 0.9001


@dataclass
class OrderResult:
    """
    订单执行结果

    Attributes:
        success: 是否成功
        order_id: 订单ID
        message: 结果消息
        error_code: 错误码
        order: 关联的订单对象
    """
    success: bool
    order_id: str = ""
    message: str = ""
    error_code: str = ""
    order: Optional[Order] = None


class BrokerInterface(ABC):
    """
    券商适配器抽象基类

    所有券商接口必须继承此类并实现以下方法：
    - connect: 连接券商
    - disconnect: 断开连接
    - is_connected: 检查连接状态
    - place_order: 下单
    - cancel_order: 撤单
    - get_order_status: 查询订单状态
    - get_positions: 查询持仓
    - get_account: 查询账户信息
    - get_quote: 获取行情
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化券商适配器

        Args:
            config: 券商配置（如服务器地址、账号等）
        """
        self.config = config or {}
        self._connected = False

    @abstractmethod
    def connect(self) -> bool:
        """
        连接券商

        Returns:
            是否连接成功
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        断开连接

        Returns:
            是否断开成功
        """
        pass

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected

    @abstractmethod
    def place_order(self, order: Order) -> OrderResult:
        """
        下单

        Args:
            order: 订单对象

        Returns:
            OrderResult: 执行结果
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> OrderResult:
        """
        撤单

        Args:
            order_id: 订单ID

        Returns:
            OrderResult: 执行结果
        """
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """
        查询订单状态

        Args:
            order_id: 订单ID

        Returns:
            Order对象或None
        """
        pass

    @abstractmethod
    def get_orders(self, symbol: Optional[str] = None,
                   status: Optional[OrderStatus] = None) -> List[Order]:
        """
        查询订单列表

        Args:
            symbol: 股票代码过滤（可选）
            status: 订单状态过滤（可选）

        Returns:
            订单列表
        """
        pass

    @abstractmethod
    def get_trades(self, order_id: Optional[str] = None) -> List[Trade]:
        """
        查询成交记录

        Args:
            order_id: 订单ID过滤（可选）

        Returns:
            成交列表
        """
        pass

    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        查询持仓

        Returns:
            持仓列表，每项包含:
            - symbol: 股票代码
            - quantity: 持仓数量
            - avg_cost: 成本价
            - market_value: 市值
            - unrealized_pnl: 浮动盈亏
        """
        pass

    @abstractmethod
    def get_account(self) -> Dict[str, Any]:
        """
        查询账户信息

        Returns:
            账户信息字典，包含:
            - account_id: 账户ID
            - cash: 可用资金
            - frozen_cash: 冻结资金
            - total_assets: 总资产
            - market_value: 持仓市值
            - equity: 账户净值
        """
        pass

    @abstractmethod
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """
        获取行情

        Args:
            symbol: 股票代码

        Returns:
            Quote对象或None
        """
        pass

    def get_required_fields(self) -> List[str]:
        """
        返回券商需要的配置字段

        子类可重写此方法，返回必填配置项列表
        """
        return []


class SimulatorBrokerConfig:
    """模拟券商配置"""

    def __init__(
        self,
        commission_rate: float = 0.0003,      # 佣金万三（0.03%）
        stamp_tax: float = 0.001,               # 印花税千一（仅卖出）
        slippage: float = 0.001,               # 滑点 0.1%
        price_limit_ratio: float = 0.10,       # 涨跌停 10%
        min_commission: float = 5.0,            # 最低佣金
    ):
        self.commission_rate = commission_rate
        self.stamp_tax = stamp_tax
        self.slippage = slippage
        self.price_limit_ratio = price_limit_ratio
        self.min_commission = min_commission
