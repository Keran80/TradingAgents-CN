# -*- coding: utf-8 -*-
"""
实盘交易模块

支持多种券商API对接：
- 模拟交易
- 老虎证券
- 富途证券
- 雪球
- 聚宽

Usage:
    from tradingagents.execution.live import LiveBroker, LiveOrderManager, AccountSync
    
    # 创建券商接口
    broker = LiveBroker.create("simulator")
    # 或: LiveBroker.create("tiger", account="xxx", secret="xxx")
    
    # 创建订单管理器
    manager = LiveOrderManager(broker)
    
    # 下单
    order = manager.send_order(
        symbol="000001.SZ",
        side="BUY",
        quantity=100,
        price=10.5,
    )
"""

from .broker import LiveBroker
from .order_manager import LiveOrderManager
from .account_sync import AccountSync
from .adapters import (
    SimulatorAdapter,
    TigerAdapter,
    FutuAdapter,
    JoinQuantAdapter,
)

__all__ = [
    "LiveBroker",
    "LiveOrderManager",
    "AccountSync",
    "SimulatorAdapter",
    "TigerAdapter",
    "FutuAdapter",
    "JoinQuantAdapter",
]
