# -*- coding: utf-8 -*-
"""
全市场数据统一入口

支持：
- A股市场 (stock_zh_a)
- 港股市场 (stock_hk)
- 美股市场 (stock_us)
- 基金数据 (fund)
- 期货数据 (futures)
- 宏观经济 (macro)
- 债券数据 (bond)

Usage:
    from tradingagents.data.markets import MarketDataHub
    
    hub = MarketDataHub()
    
    # A股数据
    df = hub.get_stock_data("000001", "2024-01-01", "2024-12-31")
    
    # 港股数据
    df = hub.get_hk_stock_data("00700", "2024-01-01", "2024-12-31")
    
    # 美股数据
    df = hub.get_us_stock_data("AAPL", "2024-01-01", "2024-12-31")
    
    # 基金数据
    nav = hub.get_fund_nav("000001")
    
    # 宏观经济
    gdp = hub.get_macro_data("gdp")
    
    # 债券数据
    bond = hub.get_bond_data("2024")
"""

from .hub import MarketDataHub
from .stock_a import AStockData
from .stock_hk import HKStockData
from .stock_us import USStockData
from .fund import FundData
from .macro import MacroData
from .bond import BondData

__all__ = [
    "MarketDataHub",
    "AStockData",
    "HKStockData",
    "USStockData",
    "FundData",
    "MacroData",
    "BondData",
]