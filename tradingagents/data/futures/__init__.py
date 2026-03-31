# -*- coding: utf-8 -*-
"""
期货数据模块

支持获取：
- 国内期货（商品期货、金融期货）
- 国际期货（原油、黄金等）
- 期货实时行情
- 期货持仓/仓单数据

Usage:
    from tradingagents.data.futures import FuturesDataManager
    
    manager = FuturesDataManager()
    
    # 获取期货合约列表
    contracts = manager.get_contracts("futures")
    
    # 获取实时行情
    quote = manager.get_quote("IF2404")
    
    # 获取K线数据
    bars = manager.get_bars("IF2404", count=100)
"""

from .manager import FuturesDataManager, FuturesCategory
from .calculator import FuturesCalculator

__all__ = [
    "FuturesDataManager",
    "FuturesCategory",
    "FuturesCalculator",
]
