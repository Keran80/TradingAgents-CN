# -*- coding: utf-8 -*-
"""
WebSocket 实时行情客户端

支持多种 WebSocket 数据源：
- 东方财富 WebSocket
- 新浪财经 WebSocket
- 自定义 WebSocket 服务器
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Callable, List
import websockets
import threading

logger = logging.getLogger(__name__)


class WebSocketClient:
    """
    WebSocket 实时行情客户端
    
    支持：
    - 自动重连
    - 心跳保活
    - 批量订阅
    - 数据解析
    """
    
    def __init__(
        self,
        url: str = "wss://push2.eastmoney.com",
        reconnect_delay: float = 5.0,
        heartbeat_interval: float = 30.0,
    ):
        """
        初始化客户端
        
        Args:
            url: WebSocket 服务器地址
            reconnect_delay: 重连延迟（秒）
            heartbeat_interval: 心跳间隔（秒）
        """
        self.url = url
        self.reconnect_delay = reconnect_delay
        self.heartbeat_interval = heartbeat_interval
        
        self._callback: Optional[Callable] = None
        self._running = False
        self._ws = None
        self._thread = None
        self._loop = None
        self._subscriptions: set = set()
        
    def set_callback(self, callback: Callable):
        """设置数据回调"""
        self._callback = callback
        
    def subscribe(self, symbol: str, market: str = "stock"):
        """
        订阅行情
        
        Args:
            symbol: 股票代码
            market: 市场类型
        """
        full_symbol = f"{symbol}.{market.upper()}"
        self._subscriptions.add(full_symbol)
        
        if self._ws and self._running:
            asyncio.run_coroutine_threadsafe(
                self._send_subscribe([full_symbol]),
                self._loop
            )
            
    def unsubscribe(self, symbol: str):
        """取消订阅"""
        self._subscriptions.discard(symbol)
        
    async def _send_subscribe(self, symbols: List[str]):
        """发送订阅请求"""
        if self._ws:
            try:
                # 东方财富格式
                msg = {
                    "cmd": "subscribe",
                    "args": symbols,
                }
                await self._ws.send(json.dumps(msg))
                logger.debug(f"Subscribed: {symbols}")
            except Exception as e:
                logger.error(f"Subscribe error: {e}")
                
    async def connect(self):
        """连接服务器"""
        self._running = True
        self._loop = asyncio.get_event_loop()
        
        while self._running:
            try:
                async with websockets.connect(self.url) as ws:
                    self._ws = ws
                    logger.info(f"Connected to {self.url}")
                    
                    # 订阅所有股票
                    if self._subscriptions:
                        await self._send_subscribe(list(self._subscriptions))
                        
                    # 启动心跳
                    heartbeat_task = asyncio.create_task(self._heartbeat())
                    
                    # 接收消息
                    async for msg in ws:
                        await self._on_message(msg)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Connection error: {e}")
                
            if self._running:
                await asyncio.sleep(self.reconnect_delay)
                
    async def _heartbeat(self):
        """心跳保活"""
        while self._running:
            await asyncio.sleep(self.heartbeat_interval)
            if self._ws:
                try:
                    await self._ws.send(json.dumps({"cmd": "ping"}))
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")
                    break
                    
    async def _on_message(self, msg: str):
        """处理消息"""
        try:
            data = json.loads(msg)
            
            # 解析行情数据
            if "data" in data:
                for item in data["data"]:
                    tick = self._parse_tick(item)
                    if tick and self._callback:
                        self._callback(tick)
                        
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON: {msg[:100]}")
        except Exception as e:
            logger.error(f"Parse error: {e}")
            
    def _parse_tick(self, item: Dict) -> Optional[Dict]:
        """解析分笔数据"""
        from .manager import TickData
        
        try:
            return TickData(
                symbol=item.get("symbol", ""),
                timestamp=datetime.fromtimestamp(item.get("timestamp", 0)),
                last_price=float(item.get("price", 0)),
                open=float(item.get("open", 0)),
                high=float(item.get("high", 0)),
                low=float(item.get("low", 0)),
                volume=float(item.get("volume", 0)),
                turnover=float(item.get("turnover", 0)),
            )
        except Exception as e:
            logger.error(f"Parse tick error: {e}")
            return None
            
    async def disconnect(self):
        """断开连接"""
        self._running = False
        if self._ws:
            await self._ws.close()
        logger.info("WebSocket disconnected")
        
    def start(self):
        """启动客户端（在独立线程中）"""
        if self._thread and self._thread.is_alive():
            return
            
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        
    def _run(self):
        """运行事件循环"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self.connect())
        
    def stop(self):
        """停止客户端"""
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
