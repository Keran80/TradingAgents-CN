# -*- coding: utf-8 -*-
"""
TradingAgents-CN Data Module

数据层模块，支持：
- 历史数据 (AkShare/Tushare)
- 实时行情 (AkShare/pytdx/WebSocket)
- 期货数据
- 期权数据
- 全市场数据 (A股/港股/美股/基金/宏观/债券)
- Dashboard 可视化
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

# 全市场数据
from .markets import (
    MarketDataHub,
    AStockData,
    HKStockData,
    USStockData,
    FundData,
    MacroData,
    BondData,
)

# Dashboard
from ..dashboard import (
    DashboardState,
    run_dashboard,
    HeatmapGenerator,
    PortfolioHeatmap,
    ChartGenerator,
    MetricsCalculator,
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
    
    # 全市场数据
    "MarketDataHub",
    "AStockData",
    "HKStockData",
    "USStockData",
    "FundData",
    "MacroData",
    "BondData",
    
    # Dashboard
    "DashboardState",
    "run_dashboard",
    "HeatmapGenerator",
    "PortfolioHeatmap",
    "ChartGenerator",
    "MetricsCalculator",
]
