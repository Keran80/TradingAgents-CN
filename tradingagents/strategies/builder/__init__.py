# -*- coding: utf-8 -*-
"""
TradingAgents-CN - Visual Strategy Builder
可视化策略构建器 Phase 8

提供零代码策略创建能力，通过拖拽组件构建交易策略。
"""

from .components import *
from .dsl import StrategyDSL, ComponentRegistry, list_templates, get_template
from .builder import VisualStrategyBuilder, save_builder_html

__all__ = [
    # 组件
    "ComponentRegistry",
    # DSL
    "StrategyDSL",
    "list_templates",
    "get_template",
    # 构建器
    "VisualStrategyBuilder",
    "save_builder_html",
]
