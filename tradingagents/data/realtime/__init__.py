# -*- coding: utf-8 -*-
"""
实时行情数据模块

支持多种实时数据源：
- AkShare 实时行情
- 通达信 pytdx
- WebSocket 实时推送

Usage:
    from tradingagents.data.realtime import RealtimeDataManager
    
    manager = RealtimeDataManager()
    await manager.subscribe("000001.SZ", callback=on_tick)
    await manager.start()
"""

from .manager import RealtimeDataManager, MarketType, BarSize
from .websocket_client import WebSocketClient
from .akshare_adapter import AkShareRealtimeAdapter
from .tdx_adapter import TDXRealtimeAdapter

__all__ = [
    "RealtimeDataManager",
    "MarketType",
    "BarSize",
    "WebSocketClient",
    "AkShareRealtimeAdapter",
    "TDXRealtimeAdapter",
]
