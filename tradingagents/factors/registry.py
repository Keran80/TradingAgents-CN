# -*- coding: utf-8 -*-
"""
TradingAgents-CN - Factor Registry
因子注册表实现
"""

from typing import Dict, Optional
from .base import FactorRegistry, BaseFactor, FactorCategory


class _FactorRegistry(FactorRegistry):
    """因子注册表的具体实现"""
    pass


# 导出供外部使用
__all__ = ["FactorRegistry", "get_registry"]


def get_registry() -> FactorRegistry:
    """获取全局因子注册表实例"""
    reg = _FactorRegistry()
    if not reg._initialized:
        reg.initialize()
    return reg
