# -*- coding: utf-8 -*-
"""
TradingAgents-CN - 交易执行层
券商适配器基类和统一接口

Author: Keran (AI Assistant)
Date: 2026-03-30
"""

from .broker import BrokerInterface, Order, OrderType, OrderSide, OrderStatus
from .account import Account
from .portfolio import Portfolio, Position
from .order_manager import OrderManager
from .simulators.simulator import SimulatorBroker
from .trading_engine import TradingEngine, Signal, SignalType, ExecutionResult

__all__ = [
    # 核心接口
    "BrokerInterface",
    "Order",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    # 账户与持仓
    "Account",
    "Portfolio",
    "Position",
    # 订单管理
    "OrderManager",
    # 模拟交易
    "SimulatorBroker",
    # 交易引擎
    "TradingEngine",
    "Signal",
    "SignalType",
    "ExecutionResult",
]
