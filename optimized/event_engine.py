"""
事件驱动引擎 - TradingAgents-CN
===============================

核心组件：
- Event: 事件基类
- TickEvent: 行情事件
- BarEvent: K线事件
- OrderEvent: 订单事件
- TradeEvent: 成交事件
- SignalEvent: 信号事件
- EventEngine: 事件分发引擎
"""

from __future__ import annotations

import threading
import queue
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any
from .error_handling import TradingException, handle_data_errors Dict, List, Callable, Type, Any, Optional
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型枚举"""
    TICK = "tick"           # 行情tick
    BAR = "bar"             # K线数据
    ORDER = "order"         # 订单事件
    TRADE = "trade"         # 成交事件
    SIGNAL = "signal"        # 交易信号
    POSITION = "position"    # 持仓变化
    ACCOUNT = "account"      # 账户变化
    RISK = "risk"           # 风控事件
    TIMER = "timer"          # 定时事件
    CUSTOM = "custom"        # 自定义事件


@dataclass
class Event:
    """事件基类"""
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: EventType = EventType.CUSTOM
    source: str = ""  # 事件来源标识

    def __post_init__(*args, **kwargs) -> Any:
    """
      Post Init  
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        Any: 返回值
        
    Note:
        基于 Claude Code 规范自动添加
    """
if not isinstance(self.timestamp, datetime):
            self.timestamp = datetime.now()


@dataclass
class TickEvent(Event):
    """Tick行情事件"""
    symbol: str = ""
    last_price: float = 0.0
    open_price: float = 0.0
    high_price: float = 0.0
    low_price: float = 0.0
    volume: int = 0
    turnover: float = 0.0
    bid_price1: float = 0.0
    bid_volume1: int = 0
    ask_price1: float = 0.0
    ask_volume1: int = 0

    def __post_init__(*args, **kwargs) -> Any:
    """
      Post Init  
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        Any: 返回值
        
    Note:
        基于 Claude Code 规范自动添加
    """
super().__post_init__()
        self.event_type = EventType.TICK


@dataclass
class BarEvent(Event):
    """K线数据事件"""
    symbol: str = ""
    interval: str = "1d"  # K线周期: 1m, 5m, 15m, 1h, 1d
    open_price: float = 0.0
    high_price: float = 0.0
    low_price: float = 0.0
    close_price: float = 0.0
    volume: int = 0
    turnover: float = 0.0
    datetime: datetime = field(default_factory=datetime.now)

    def __post_init__(*args, **kwargs) -> Any:
    """
      Post Init  
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        Any: 返回值
        
    Note:
        基于 Claude Code 规范自动添加
    """
super().__post_init__()
        self.event_type = EventType.BAR

    @property
    def open(self) -> float:
        return self.open_price

    @property
    def high(self) -> float:
        return self.high_price

    @property
    def low(self) -> float:
        return self.low_price

    @property
    def close(self) -> float:
        return self.close_price


@dataclass
class OrderEventData:
    """订单事件数据"""
    class Status(Enum):
        NEW = "new"              # 新订单
        SUBMITTED = "submitted"  # 已提交
        PARTIAL = "partial"     # 部分成交
        FILLED = "filled"       # 全部成交
        CANCELLED = "cancelled" # 已撤销
        REJECTED = "rejected"   # 已拒绝

    order_id: str = ""
    symbol: str = ""
    side: str = ""  # BUY/SELL
    order_type: str = ""  # MARKET/LIMIT/STOP
    price: float = 0.0
    quantity: int = 0
    filled_quantity: int = 0
    status: Status = Status.NEW
    reason: str = ""


@dataclass
class OrderEvent(Event):
    """订单事件"""
    order_data: OrderEventData = field(default_factory=OrderEventData)

    def __post_init__(*args, **kwargs) -> Any:
    """
      Post Init  
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        Any: 返回值
        
    Note:
        基于 Claude Code 规范自动添加
    """
super().__post_init__()
        self.event_type = EventType.ORDER


@dataclass
class TradeEventData:
    """成交事件数据"""
    trade_id: str = ""
    order_id: str = ""
    symbol: str = ""
    side: str = ""  # BUY/SELL
    price: float = 0.0
    quantity: int = 0
    commission: float = 0.0
    turnover: float = 0.0


@dataclass
class TradeEvent(Event):
    """成交事件"""
    trade_data: TradeEventData = field(default_factory=TradeEventData)

    def __post_init__(*args, **kwargs) -> Any:
    """
      Post Init  
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        Any: 返回值
        
    Note:
        基于 Claude Code 规范自动添加
    """
super().__post_init__()
        self.event_type = EventType.TRADE


@dataclass
class SignalEventData:
    """信号事件数据"""
    class SignalType(Enum):
        BUY = "buy"
        SELL = "sell"
        CLOSE = "close"
        SHORT = "short"
        COVER = "cover"

    symbol: str = ""
    signal_type: SignalType = SignalType.BUY
    price: float = 0.0
    quantity: int = 0
    confidence: float = 1.0  # 信号置信度 0-1
    reason: str = ""


@dataclass
class SignalEvent(Event):
    """交易信号事件"""
    signal_data: SignalEventData = field(default_factory=SignalEventData)

    def __post_init__(*args, **kwargs) -> Any:
    """
      Post Init  
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        Any: 返回值
        
    Note:
        基于 Claude Code 规范自动添加
    """
super().__post_init__()
        self.event_type = EventType.SIGNAL


@dataclass
class PositionEvent(Event):
    """持仓变化事件"""
    symbol: str = ""
    quantity: int = 0
    avg_cost: float = 0.0
    last_price: float = 0.0
    change_type: str = ""  # ADD/REDUCE/CLEAR

    def __post_init__(*args, **kwargs) -> Any:
    """
      Post Init  
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        Any: 返回值
        
    Note:
        基于 Claude Code 规范自动添加
    """
super().__post_init__()
        self.event_type = EventType.POSITION


@dataclass
class AccountEvent(Event):
    """账户变化事件"""
    cash: float = 0.0
    frozen_cash: float = 0.0
    market_value: float = 0.0
    total_assets: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    today_pnl: float = 0.0

    def __post_init__(*args, **kwargs) -> Any:
    """
      Post Init  
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        Any: 返回值
        
    Note:
        基于 Claude Code 规范自动添加
    """
super().__post_init__()
        self.event_type = EventType.ACCOUNT


@dataclass
class RiskEvent(Event):
    """风控事件"""
    class RiskLevel(Enum):
        INFO = "info"
        WARNING = "warning"
        ERROR = "error"
        CRITICAL = "critical"

    risk_type: str = ""  # 风险类型
    level: RiskLevel = RiskLevel.INFO
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(*args, **kwargs) -> Any:
    """
      Post Init  
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        Any: 返回值
        
    Note:
        基于 Claude Code 规范自动添加
    """
super().__post_init__()
        self.event_type = EventType.RISK


@dataclass
class TimerEvent(Event):
    """定时事件"""
    interval: int = 0  # 触发间隔（秒）
    count: int = 0     # 触发次数

    def __post_init__(*args, **kwargs) -> Any:
    """
      Post Init  
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        Any: 返回值
        
    Note:
        基于 Claude Code 规范自动添加
    """
super().__post_init__()
        self.event_type = EventType.TIMER


class EventHandler:
    """事件处理器接口"""

    def handle(self, event: Event) -> None:
        """处理事件 - 子类实现"""
        raise NotImplementedError


class EventEngine:
    """
    事件驱动引擎
    ============

    核心功能：
    - 事件队列管理
    - 事件处理器注册/注销
    - 事件分发
    - 支持同步/异步模式

    使用示例：
    ```python
    engine = EventEngine()

    # 注册处理器
    def on_tick(*args, **kwargs) -> Any:
    """
    On Tick
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        Any: 返回值
        
    Note:
        基于 Claude Code 规范自动添加
    """
print(f"Tick: {event.symbol} @ {event.last_price}")

    engine.register(TickEvent, on_tick)

    # 启动引擎
    engine.start()

    # 发送事件
    engine.put(TickEvent(symbol="000001.SZ", last_price=12.50))

    # 停止引擎
    engine.stop()
    ```
    """

    def __init__(self, async_mode: bool = False) -> Any:"""
        初始化事件引擎

        Args:
            async_mode: 是否异步模式（使用线程）
        """
        self.async_mode = async_mode
        self.queue: queue.Queue = queue.Queue()
        self.handlers: Dict[Type[Event], List[Callable]] = defaultdict(list)
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        logger.info(f"EventEngine initialized (async={async_mode})")

    def register(self, event_type: Type[Event], handler: Callable) -> None:
        """
        注册事件处理器

        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        with self._lock:
            self.handlers[event_type].append(handler)
            logger.debug(f"Registered handler for {event_type.__name__}: {handler.__name__}")

    def unregister(self, event_type: Type[Event], handler: Callable) -> None:
        """
        注销事件处理器

        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        with self._lock:
            if handler in self.handlers[event_type]:
                self.handlers[event_type].remove(handler)
                logger.debug(f"Unregistered handler for {event_type.__name__}")

    def put(self, event: Event) -> None:
        """
        放入事件到队列

        Args:
            event: 事件对象
        """
        self.queue.put(event)
        logger.debug(f"Event queued: {event.event_type.value} from {event.source}")

    def start(self) -> None:
        """启动事件引擎"""
        if self.running:
            logger.warning("EventEngine already running")
            return

        self.running = True

        if self.async_mode:
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            logger.info("EventEngine started in async mode")
        else:
            logger.info("EventEngine started in sync mode")

    def stop(self) -> None:
        """停止事件引擎"""
        if not self.running:
            return

        self.running = False

        if self.async_mode and self.thread:
            self.thread.join(timeout=5)
            logger.info("EventEngine stopped")

    def _run(self) -> None:
        """事件循环（异步模式）"""
        while self.running:
            try:
                event = self.queue.get(timeout=1)
                self._dispatch(event)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Event loop error: {e}", exc_info=True)

    def process(self) -> int:
        """
        处理队列中的所有事件（同步模式）

        Returns:
            处理的事件数量
        """
        count = 0
        while not self.queue.empty():
            try:
                event = self.queue.get_nowait()
                self._dispatch(event)
                count += 1
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Process error: {e}", exc_info=True)
        return count

    def _dispatch(self, event: Event) -> None:
        """
        分发事件到处理器

        Args:
            event: 事件对象
        """
        event_type = type(event)
        handlers = self.handlers.get(event_type, [])

        if not handlers:
            return

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"Handler error for {event_type.__name__}: {e}",
                    exc_info=True
                )

    def clear(self) -> None:
        """清空事件队列"""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break
        logger.debug("Event queue cleared")

    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self.queue.qsize()


class EventBus:
    """
    事件总线 - 单例模式全局事件管理
    """

    _instance: Optional[EventBus] = None
    _lock = threading.Lock()

    def __new__(*args, **kwargs) -> Any:
    """
      New  
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        Any: 返回值
        
    Note:
        基于 Claude Code 规范自动添加
    """
if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(*args, **kwargs) -> Any:
    """
      Init  
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        Any: 返回值
        
    Note:
        基于 Claude Code 规范自动添加
    """
if self._initialized:
            return
        self._initialized = True
        self.engine = EventEngine(async_mode=False)
        logger.info("EventBus initialized (singleton)")

    def register(self, event_type: Type[Event], handler: Callable) -> None:
        """注册事件处理器"""
        self.engine.register(event_type, handler)

    def unregister(self, event_type: Type[Event], handler: Callable) -> None:
        """注销事件处理器"""
        self.engine.unregister(event_type, handler)

    def emit(self, event: Event) -> None:
        """发送事件"""
        self.engine.put(event)

    def process(self) -> int:
        """处理事件"""
        return self.engine.process()


# 全局事件总线实例
event_bus = EventBus()
