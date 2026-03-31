# -*- coding: utf-8 -*-
"""
实时行情管理器

统一管理多个实时数据源，提供订阅、取消订阅、数据推送等功能
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import threading
import time

logger = logging.getLogger(__name__)


class MarketType(Enum):
    """市场类型"""
    A_STOCK = "A"      # A股
    HK_STOCK = "HK"    # 港股
    US_STOCK = "US"    # 美股
    FUTURES = "FUT"    # 期货
    OPTIONS = "OPT"    # 期权
    CRYPTO = "CRYPTO"  # 加密货币


class BarSize(Enum):
    """K线周期"""
    TICK = "tick"      # 分笔
    MIN_1 = "1m"       # 1分钟
    MIN_5 = "5m"       # 5分钟
    MIN_15 = "15m"     # 15分钟
    MIN_30 = "30m"     # 30分钟
    HOUR_1 = "1h"      # 1小时
    HOUR_4 = "4h"      # 4小时
    DAILY = "1d"       # 日线
    WEEKLY = "1w"      # 周线


@dataclass
class TickData:
    """分笔数据"""
    symbol: str
    timestamp: datetime
    last_price: float
    open: float
    high: float
    low: float
    volume: float
    turnover: float
    bid_price: List[float] = field(default_factory=list)
    bid_volume: List[int] = field(default_factory=list)
    ask_price: List[float] = field(default_factory=list)
    ask_volume: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "last_price": self.last_price,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "volume": self.volume,
            "turnover": self.turnover,
            "bid": list(zip(self.bid_price, self.bid_volume)),
            "ask": list(zip(self.ask_price, self.ask_volume)),
        }


@dataclass
class BarData:
    """K线数据"""
    symbol: str
    timestamp: datetime
    interval: BarSize
    open: float
    high: float
    low: float
    close: float
    volume: float
    turnover: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "interval": self.interval.value,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "turnover": self.turnover,
        }


class RealtimeDataManager:
    """
    实时行情管理器
    
    统一管理实时数据订阅，支持：
    - 多个数据源（AkShare、pytdx、WebSocket）
    - 多个订阅者
    - 自动重连
    - 数据缓存
    """
    
    def __init__(
        self,
        primary_source: str = "akshare",
        use_websocket: bool = False,
        cache_size: int = 1000,
    ):
        """
        初始化管理器
        
        Args:
            primary_source: 主数据源 ("akshare", "tdx", "websocket")
            use_websocket: 是否使用WebSocket
            cache_size: 缓存大小
        """
        self.primary_source = primary_source
        self.use_websocket = use_websocket
        self.cache_size = cache_size
        
        # 数据源适配器
        self._adapters: Dict[str, Any] = {}
        self._active_adapter = None
        
        # 订阅管理
        self._subscriptions: Dict[str, List[Callable]] = defaultdict(list)
        self._symbols: set = set()
        
        # 数据缓存
        self._tick_cache: Dict[str, TickData] = {}
        self._bar_cache: Dict[str, Dict[BarSize, BarData]] = defaultdict(dict)
        
        # 状态
        self._running = False
        self._loop = None
        self._thread = None
        
        # 初始化适配器
        self._init_adapters()
        
    def _init_adapters(self):
        """初始化数据源适配器"""
        try:
            from .akshare_adapter import AkShareRealtimeAdapter
            self._adapters["akshare"] = AkShareRealtimeAdapter()
            logger.info("AkShare adapter initialized")
        except Exception as e:
            logger.warning(f"Failed to init AkShare adapter: {e}")
            
        try:
            from .tdx_adapter import TDXRealtimeAdapter
            self._adapters["tdx"] = TDXRealtimeAdapter()
            logger.info("TDX adapter initialized")
        except Exception as e:
            logger.warning(f"Failed to init TDX adapter: {e}")
            
        if self.use_websocket:
            self._adapters["websocket"] = WebSocketClient()
            
        # 选择主适配器
        if self.primary_source in self._adapters:
            self._active_adapter = self._adapters[self.primary_source]
        elif self._adapters:
            self._active_adapter = next(iter(self._adapters.values()))
        else:
            raise RuntimeError("No data adapter available")
            
    def subscribe(
        self,
        symbol: str,
        callback: Callable[[TickData], None],
        market: MarketType = MarketType.A_STOCK,
    ):
        """
        订阅实时行情
        
        Args:
            symbol: 股票代码 (如 "000001.SZ")
            callback: 数据回调函数
            market: 市场类型
        """
        self._subscriptions[symbol].append(callback)
        self._symbols.add(symbol)
        
        if self._active_adapter:
            self._active_adapter.subscribe(symbol, market)
            
        logger.info(f"Subscribed: {symbol}")
        
    def unsubscribe(self, symbol: str, callback: Optional[Callable] = None):
        """
        取消订阅
        
        Args:
            symbol: 股票代码
            callback: 指定的回调函数，为None则取消所有该symbol的回调
        """
        if callback:
            if callback in self._subscriptions[symbol]:
                self._subscriptions[symbol].remove(callback)
        else:
            self._subscriptions[symbol].clear()
            
        if not self._subscriptions[symbol]:
            self._symbols.discard(symbol)
            if self._active_adapter:
                self._active_adapter.unsubscribe(symbol)
                
        logger.info(f"Unsubscribed: {symbol}")
        
    def get_tick(self, symbol: str) -> Optional[TickData]:
        """获取最新分笔数据"""
        return self._tick_cache.get(symbol)
        
    def get_bar(
        self,
        symbol: str,
        interval: BarSize = BarSize.MIN_1,
    ) -> Optional[BarData]:
        """获取最新K线数据"""
        return self._bar_cache.get(symbol, {}).get(interval)
        
    def _on_tick(self, tick: TickData):
        """收到分笔数据"""
        self._tick_cache[tick.symbol] = tick
        
        # 限制缓存大小
        if len(self._tick_cache) > self.cache_size:
            oldest = next(iter(self._tick_cache))
            del self._tick_cache[oldest]
            
        # 推送数据
        for callback in self._subscriptions[tick.symbol]:
            try:
                callback(tick)
            except Exception as e:
                logger.error(f"Callback error for {tick.symbol}: {e}")
                
    def _on_bar(self, bar: BarData):
        """收到K线数据"""
        if bar.symbol not in self._bar_cache:
            self._bar_cache[bar.symbol] = {}
        self._bar_cache[bar.symbol][bar.interval] = bar
        
    async def start_async(self):
        """异步启动"""
        if self._running:
            return
            
        self._running = True
        self._loop = asyncio.get_event_loop()
        
        if self._active_adapter:
            self._active_adapter.set_callback(self._on_tick)
            await self._active_adapter.connect()
            
    def start(self):
        """同步启动（在独立线程中运行）"""
        if self._running:
            return
            
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("RealtimeDataManager started")
        
    def _run_loop(self):
        """运行事件循环"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        if self._active_adapter:
            self._active_adapter.set_callback(self._on_tick)
            self._loop.run_until_complete(self._active_adapter.connect())
            
        self._running = True
        
        try:
            self._loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self._loop.close()
            
    async def stop_async(self):
        """异步停止"""
        self._running = False
        if self._active_adapter:
            await self._active_adapter.disconnect()
            
    def stop(self):
        """同步停止"""
        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        logger.info("RealtimeDataManager stopped")
        
    @property
    def is_running(self) -> bool:
        """是否运行中"""
        return self._running
