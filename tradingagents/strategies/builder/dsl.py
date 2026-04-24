# -*- coding: utf-8 -*-
"""
策略 DSL - 兼容性层
=====================

此文件为向后兼容的导出层，所有实际实现已移至 dsl/ 包中。
新代码应直接从 dsl 包导入：
    from .dsl import StrategyDSL, CompiledStrategy, ...
"""

from .dsl import (
    IndicatorDefinition,
    ConditionDefinition,
    SignalDefinition,
    StrategyBlueprint,
    BlueprintParser,
    BlueprintValidator,
    StrategyDSL,
    CompiledStrategy,
    MA_CROSSOVER_TEMPLATE,
    MACD_CROSSOVER_TEMPLATE,
    RSI_REVERSION_TEMPLATE,
    BOLL_BREAKOUT_TEMPLATE,
    TEMPLATES,
    get_template,
    list_templates,
)

# 保持与原 from_dict 方法的兼容
@classmethod
def _blueprint_from_dict(cls, data):
    """从字典创建 - 兼容原接口"""
    return BlueprintParser.parse(data)

StrategyBlueprint.from_dict = _blueprint_from_dict

# 保持与原 validate_blueprint 方法的兼容
def _validate_blueprint(blueprint):
    """验证策略蓝图 - 兼容原接口"""
    return BlueprintValidator.validate(blueprint)

StrategyDSL.validate_blueprint = staticmethod(_validate_blueprint)

__all__ = [
    "IndicatorDefinition",
    "ConditionDefinition",
    "SignalDefinition",
    "StrategyBlueprint",
    "BlueprintParser",
    "BlueprintValidator",
    "StrategyDSL",
    "CompiledStrategy",
    "MA_CROSSOVER_TEMPLATE",
    "MACD_CROSSOVER_TEMPLATE",
    "RSI_REVERSION_TEMPLATE",
    "BOLL_BREAKOUT_TEMPLATE",
    "TEMPLATES",
    "get_template",
    "list_templates",
]
