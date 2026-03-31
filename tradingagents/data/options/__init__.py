# -*- coding: utf-8 -*-
"""
期权数据模块

支持获取：
- 50ETF期权
- 300ETF期权
- 商品期权
- 期权希腊字母计算

Usage:
    from tradingagents.data.options import OptionsDataManager, OptionsCalculator
    
    manager = OptionsDataManager()
    calculator = OptionsCalculator()
    
    # 获取期权列表
    options = manager.get_options_chain("510300.XSHG")
    
    # 计算希腊字母
    greeks = calculator.calc_greeks(S, K, T, r, sigma, option_type="call")
"""

from .manager import OptionsDataManager, OptionType, ExerciseType
from .calculator import OptionsCalculator, OptionContract, Greeks

__all__ = [
    "OptionsDataManager",
    "OptionsCalculator",
    "OptionType",
    "ExerciseType",
    "OptionContract",
    "Greeks",
]
