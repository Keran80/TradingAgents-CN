# -*- coding: utf-8 -*-
"""
TradingAgents-CN Data Module

数据层模块，支持：
- 历史数据 (AkShare/Tushare)
- 实时行情 (AkShare/pytdx/WebSocket)
- 期货数据
- 期权数据
"""

from .realtime import (
    RealtimeDataManager,
    MarketType,
    BarSize,
)

from .realtime.manager import TickData, BarData

from .futures import (
    FuturesDataManager,
    FuturesCategory,
    FuturesCalculator,
)

from .options import (
    OptionsDataManager,
    OptionsCalculator,
    OptionType,
    ExerciseType,
    OptionContract,
    Greeks,
)

__all__ = [
    # 实时行情
    "RealtimeDataManager",
    "MarketType",
    "BarSize",
    "TickData",
    "BarData",
    
    # 期货数据
    "FuturesDataManager",
    "FuturesCategory",
    "FuturesCalculator",
    
    # 期权数据
    "OptionsDataManager",
    "OptionsCalculator",
    "OptionType",
    "ExerciseType",
    "OptionContract",
    "Greeks",
]
