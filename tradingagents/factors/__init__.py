# -*- coding: utf-8 -*-
"""
TradingAgents-CN - Factor Module
因子研究与 Alpha 挖掘模块 Phase 9

提供五大类因子库：
- 价值因子 (Value): PE、PB、PS、PCF、EV/EBITDA 等
- 成长因子 (Growth): 营收增长、利润增长、资产增长等
- 动量因子 (Momentum): 价格动量、换手率动量、波动率等
- 质量因子 (Quality): ROE、ROA、毛利率、资产负债率等
- 情绪因子 (Sentiment): 资金流向、龙虎榜、分析师情绪等
"""

from .registry import FactorRegistry, get_registry
from .base import BaseFactor, FactorCategory, FactorType
from .value import *
from .growth import *
from .momentum import *
from .quality import *
from .sentiment import *
from .technical import *
from .research import FactorResearcher

__all__ = [
    # 核心类
    "BaseFactor",
    "FactorCategory",
    "FactorType", 
    "FactorRegistry",
    "get_registry",
    "FactorResearcher",
]
