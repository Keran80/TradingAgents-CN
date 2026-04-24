# -*- coding: utf-8 -*-
"""
策略组件库 - 兼容性层
=======================

此文件为向后兼容的导出层，所有实际实现已移至 components/ 包中。
新代码应直接从 components 包导入：
    from .components import ComponentRegistry, MAIndicator, ...
"""

from .components import (
    ComponentType,
    ComponentOutput,
    ComponentConfig,
    StrategyComponent,
    IndicatorComponent,
    ConditionComponent,
    SignalComponent,
    LogicComponent,
    MAIndicator,
    MACDIndicator,
    RSIIndicator,
    KDJIndicator,
    BOLLIndicator,
    VolumeIndicator,
    PriceCondition,
    IndicatorCondition,
    MACDCrossCondition,
    VolumeCondition,
    AndCondition,
    OrCondition,
    NotCondition,
    BuySignal,
    SellSignal,
    ComponentRegistry,
)

__all__ = [
    "ComponentType",
    "ComponentOutput",
    "ComponentConfig",
    "StrategyComponent",
    "IndicatorComponent",
    "ConditionComponent",
    "SignalComponent",
    "LogicComponent",
    "MAIndicator",
    "MACDIndicator",
    "RSIIndicator",
    "KDJIndicator",
    "BOLLIndicator",
    "VolumeIndicator",
    "PriceCondition",
    "IndicatorCondition",
    "MACDCrossCondition",
    "VolumeCondition",
    "AndCondition",
    "OrCondition",
    "NotCondition",
    "BuySignal",
    "SellSignal",
    "ComponentRegistry",
]
