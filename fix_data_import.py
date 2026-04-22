#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复数据层导入问题

问题原因：循环导入
- data/__init__.py 从 dashboard 导入 HeatmapGenerator
- dashboard/__init__.py 可能从 data 导入某些内容
- 导致互相依赖，导入失败

解决方案：
1. 移除 data/__init__.py 中对 dashboard 的导入
2. HeatmapGenerator 应该在 dashboard 中使用，而不是 data
3. 保持模块职责清晰：data 负责数据，dashboard 负责可视化
"""

import os
import shutil

# 备份原文件
print("备份原文件...")
shutil.copy("tradingagents/data/__init__.py", "tradingagents/data/__init__.py.bak")

# 创建修复后的 data/__init__.py
print("创建修复后的 data/__init__.py...")

fixed_data_init = '''# -*- coding: utf-8 -*-
"""
TradingAgents-CN Data Module

数据层模块，支持：
- 历史数据 (AkShare/Tushare)
- 实时行情 (AkShare/pytdx/WebSocket)
- 期货数据
- 期权数据
- 全市场数据 (A 股/港股/美股/基金/宏观/债券)
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

# 注意：Dashboard 相关导入已移除，避免循环导入
# 如需使用 Dashboard，请直接导入：
# from tradingagents.dashboard import HeatmapGenerator, DashboardState

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
    
    # Dashboard 相关已移除，避免循环导入
    # "DashboardState",
    # "run_dashboard",
    # "HeatmapGenerator",
    # "PortfolioHeatmap",
    # "ChartGenerator",
    # "MetricsCalculator",
]
'''

with open("tradingagents/data/__init__.py", "w", encoding="utf-8") as f:
    f.write(fixed_data_init)

print("✅ data/__init__.py 修复完成")

# 清理缓存
print("清理 Python 缓存...")
import subprocess
subprocess.run(["find", "tradingagents/", "-type", "d", "-name", "__pycache__", "-exec", "rm", "-rf", "{}", ";"], 
               capture_output=True)

print("✅ 缓存清理完成")

# 验证修复
print("\n验证修复...")
import sys
sys.path.insert(0, '/tmp/TradingAgents-CN')

try:
    from tradingagents.data import RealtimeDataManager, MarketDataHub
    print("✅ 数据层核心模块导入成功")
except Exception as e:
    print(f"❌ 数据层导入失败：{e}")

try:
    from tradingagents.dashboard import HeatmapGenerator, DashboardState
    print("✅ Dashboard 模块导入成功")
except Exception as e:
    print(f"❌ Dashboard 导入失败：{e}")

try:
    import tradingagents
    from tradingagents.event_engine import EventEngine
    from tradingagents.backtest import BacktestEngine
    print("✅ 所有核心模块导入成功")
except Exception as e:
    print(f"❌ 核心模块导入失败：{e}")

print("\n=== 修复完成 ===")
