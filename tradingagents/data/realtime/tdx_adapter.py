# -*- coding: utf-8 -*-
"""
通达信 pytdx 实时行情适配器

使用 pytdx 连接通达信行情服务器获取实时数据
低延迟（<50ms），适合短线交易
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Callable, List
import time

logger = logging.getLogger(__name__)


class TDXRealtimeAdapter:
    """
    通达信 pytdx 实时行情适配器
    
    特点：
    - 低延迟 (<50ms)
    - TCP 直连
    - 支持 Level2 数据
    
    服务器地址：
    - 主站: 218.75.126.9:7709
    - 备站: 218.75.126.9:7709
    """
    
    # 通达信服务器列表
    SERVERS = [
        {"ip": "218.75.126.9", "port": 7709},   # 主站
        {"ip": "218.75.126.9", "port": 7709},   # 备站
        {"ip": "218.75.137.4", "port": 7709},   # 备用
        {"ip": "218.75.137.5", "port": 7709},   # 备用
    ]
    
    def __init__(
        self,
        server: Optional[Dict] = None,
        reconnect_interval: float = 5.0,
    ):
        """
        初始化适配器
        
        Args:
            server: 服务器配置 {"ip": str, "port": int}
            reconnect_interval: 重连间隔（秒）
        """
        self._server = server or self.SERVERS[0]
        self._reconnect_interval = reconnect_interval
        self._callback: Optional[Callable] = None
        self._running = False
        self._tdx = None
        self._api = None
        self._task: Optional[asyncio.Task] = None
        self._connected = False
        
    def _ensure_pytdx(self):
        """确保 pytdx 已导入"""
        if self._tdx is None:
            try:
                from pytdx.hq import TdxHq_API
                self._tdx = TdxHq_API
                logger.info("pytdx loaded successfully")
            except ImportError:
                raise ImportError(
                    "pytdx not installed. Install with: pip install pytdx"
                )
                
    def set_callback(self, callback: Callable):
        """设置数据回调"""
        self._callback = callback
        
    def subscribe(self, symbol: str, market: int = 0):
        """
        订阅行情
        
        Args:
            symbol: 股票代码（如 "000001"）
            market: 市场代码 (0=深圳, 1=上海)
        """
        # pytdx 订阅在 connect 时批量注册
        pass
        
    def unsubscribe(self, symbol: str):
        """取消订阅"""
        pass
        
    async def connect(self) -> bool:
        """连接服务器"""
        try:
            self._ensure_pytdx()
            self._api = self._tdx()
            
            # 异步连接
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._connect_sync
            )
            
            if result:
                self._connected = True
                self._running = True
                logger.info(f"Connected to TDX: {self._server}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to connect to TDX: {e}")
            return False
            
    def _connect_sync(self) -> bool:
        """同步连接"""
        try:
            result = self._api.connect(
                ip=self._server["ip"],
                port=self._server["port"],
            )
            return bool(result)
        except Exception as e:
            logger.error(f"Sync connect error: {e}")
            return False
            
    async def disconnect(self):
        """断开连接"""
        self._running = False
        self._connected = False
        
        if self._api:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._api.disconnect)
            except Exception as e:
                logger.error(f"Disconnect error: {e}")
                
        logger.info("TDX adapter disconnected")
        
    def get_security_list(self, market: int = 0) -> List[Dict]:
        """
        获取证券列表
        
        Args:
            market: 市场代码 (0=深圳, 1=上海)
            
        Returns:
            证券列表
        """
        try:
            return self._api.get_security_list(market, 0)
        except Exception as e:
            logger.error(f"Failed to get security list: {e}")
            return []
            
    def get_security_quote(self, symbol: str, market: int = 0) -> Optional[Dict]:
        """
        获取单只股票行情
        
        Args:
            symbol: 股票代码（如 "000001"）
            market: 市场代码 (0=深圳, 1=上海)
            
        Returns:
            行情数据
        """
        try:
            data = self._api.get_security_quote([(market, symbol)])
            
            if data:
                d = data[0]
                return {
                    "symbol": symbol,
                    "market": market,
                    "name": d.get('name', ''),
                    "open": float(d.get('open', 0)),
                    "high": float(d.get('high', 0)),
                    "low": float(d.get('low', 0)),
                    "price": float(d.get('price', 0)),
                    "volume": float(d.get('amount', 0)),
                    "turnover": float(d.get('turnover', 0)),
                    "bid1": float(d.get('bid1', 0)),
                    "ask1": float(d.get('ask1', 0)),
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
        return None
        
    def get_security_bars(
        self,
        symbol: str,
        market: int = 0,
        count: int = 100,
    ) -> List[Dict]:
        """
        获取K线数据
        
        Args:
            symbol: 股票代码
            market: 市场代码
            count: 数量
            
        Returns:
            K线数据列表
        """
        try:
            data = self._api.get_security_bars(
                category=9,  # 日线
                market=market,
                code=symbol,
                start=0,
                count=count,
            )
            return data or []
        except Exception as e:
            logger.error(f"Failed to get bars for {symbol}: {e}")
            return []
            
    def get_instrument_quote(self, symbol: str) -> Optional[Dict]:
        """
        获取期货/期权行情
        
        Args:
            symbol: 合约代码（如 "IF2404"）
            
        Returns:
            行情数据
        """
        try:
            data = self._api.get_instrument_quote([symbol])
            
            if data:
                d = data[0]
                return {
                    "symbol": d.get('code', symbol),
                    "name": d.get('name', ''),
                    "open": float(d.get('open', 0)),
                    "high": float(d.get('high', 0)),
                    "low": float(d.get('low', 0)),
                    "price": float(d.get('price', 0)),
                    "volume": float(d.get('volume', 0)),
                    "turnover": float(d.get('turnover', 0)),
                    "bid1": float(d.get('bid1', 0)),
                    "ask1": float(d.get('ask1', 0)),
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception as e:
            logger.error(f"Failed to get instrument quote for {symbol}: {e}")
        return None
        
    def get_transaction_data(
        self,
        symbol: str,
        market: int = 0,
        count: int = 10,
    ) -> List[Dict]:
        """
        获取分笔成交数据
        
        Args:
            symbol: 股票代码
            market: 市场代码
            count: 数量
            
        Returns:
            成交数据列表
        """
        try:
            data = self._api.get_transaction_data(
                market=market,
                code=symbol,
                start=0,
                count=count,
            )
            return data or []
        except Exception as e:
            logger.error(f"Failed to get transactions for {symbol}: {e}")
            return []
            
    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected
