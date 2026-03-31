# -*- coding: utf-8 -*-
"""
策略 DSL - Domain Specific Language
=====================================

将可视化配置转换为可执行的策略代码。

DSL 配置示例：
{
    "name": "均线交叉策略",
    "symbols": ["000001.SZ"],
    "indicators": [
        {"name": "MA5", "type": "MA", "params": {"period": 5}},
        {"name": "MA20", "type": "MA", "params": {"period": 20}}
    ],
    "conditions": [
        {
            "name": "金叉买入",
            "type": "IndicatorCondition",
            "indicator_name": "MA5",
            "operator": "cross_up",
            "compare_indicator": "MA20"
        }
    ],
    "signals": {
        "buy": ["金叉买入"],
        "sell": ["死叉卖出"]
    }
}
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from .components import (
    ComponentRegistry,
    ComponentConfig,
    StrategyComponent,
    AndCondition,
    OrCondition,
    NotCondition
)

logger = logging.getLogger(__name__)


@dataclass
class IndicatorDefinition:
    """指标定义"""
    name: str
    component_type: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConditionDefinition:
    """条件定义"""
    name: str
    condition_type: str
    params: Dict[str, Any] = field(default_factory=dict)
    children: List["ConditionDefinition"] = field(default_factory=list)


@dataclass
class SignalDefinition:
    """信号定义"""
    signal_type: str  # buy/sell/hold
    conditions: List[str] = field(default_factory=list)  # 条件名称列表
    logic: str = "AND"  # 逻辑运算 AND/OR


@dataclass
class StrategyBlueprint:
    """
    策略蓝图

    保存可视化构建的策略配置
    """
    name: str = "UnnamedStrategy"
    symbols: List[str] = field(default_factory=lambda: ["000001.SZ"])
    initial_capital: float = 1000000.0
    commission_rate: float = 0.0003
    indicators: List[IndicatorDefinition] = field(default_factory=list)
    conditions: List[ConditionDefinition] = field(default_factory=list)
    buy_signals: List[SignalDefinition] = field(default_factory=list)
    sell_signals: List[SignalDefinition] = field(default_factory=list)
    position_size: float = 0.3  # 单股最大仓位比例
    stop_loss: float = 0.05  # 止损比例
    take_profit: float = 0.15  # 止盈比例

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "symbols": self.symbols,
            "initial_capital": self.initial_capital,
            "commission_rate": self.commission_rate,
            "indicators": [
                {"name": i.name, "type": i.component_type, "params": i.params}
                for i in self.indicators
            ],
            "conditions": [
                {
                    "name": c.name,
                    "type": c.condition_type,
                    "params": c.params,
                    "children": c.children
                }
                for c in self.conditions
            ],
            "buy_signals": [
                {"conditions": s.conditions, "logic": s.logic}
                for s in self.buy_signals
            ],
            "sell_signals": [
                {"conditions": s.conditions, "logic": s.logic}
                for s in self.sell_signals
            ],
            "position_size": self.position_size,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategyBlueprint":
        """从字典创建"""
        blueprint = cls()
        blueprint.name = data.get("name", "UnnamedStrategy")
        blueprint.symbols = data.get("symbols", ["000001.SZ"])
        blueprint.initial_capital = data.get("initial_capital", 1000000.0)
        blueprint.commission_rate = data.get("commission_rate", 0.0003)

        # 解析指标
        for ind in data.get("indicators", []):
            blueprint.indicators.append(IndicatorDefinition(
                name=ind["name"],
                component_type=ind["type"],
                params=ind.get("params", {})
            ))

        # 解析条件
        for cond in data.get("conditions", []):
            blueprint.conditions.append(ConditionDefinition(
                name=cond["name"],
                condition_type=cond["type"],
                params=cond.get("params", {}),
                children=[ConditionDefinition(**c) for c in cond.get("children", [])]
            ))

        # 解析买入信号
        for sig in data.get("buy_signals", []):
            blueprint.buy_signals.append(SignalDefinition(
                signal_type="buy",
                conditions=sig.get("conditions", []),
                logic=sig.get("logic", "AND")
            ))

        # 解析卖出信号
        for sig in data.get("sell_signals", []):
            blueprint.sell_signals.append(SignalDefinition(
                signal_type="sell",
                conditions=sig.get("conditions", []),
                logic=sig.get("logic", "AND")
            ))

        blueprint.position_size = data.get("position_size", 0.3)
        blueprint.stop_loss = data.get("stop_loss", 0.05)
        blueprint.take_profit = data.get("take_profit", 0.15)

        return blueprint


class StrategyDSL:
    """
    策略 DSL 解析器

    将策略蓝图编译为可执行的策略类
    """

    def __init__(self):
        self.registry = ComponentRegistry()
        self._indicators: Dict[str, StrategyComponent] = {}
        self._conditions: Dict[str, StrategyComponent] = {}
        self._buy_conditions: List[StrategyComponent] = []
        self._sell_conditions: List[StrategyComponent] = []

    def compile(self, blueprint: StrategyBlueprint) -> "CompiledStrategy":
        """
        编译策略蓝图为可执行策略

        Args:
            blueprint: 策略蓝图

        Returns:
            CompiledStrategy: 可编译策略
        """
        logger.info(f"Compiling strategy: {blueprint.name}")

        # 重置
        self._indicators.clear()
        self._conditions.clear()
        self._buy_conditions.clear()
        self._sell_conditions.clear()

        # 编译指标
        for ind_def in blueprint.indicators:
            indicator = self.registry.create_component(
                "indicator",
                ind_def.component_type,
                ind_def.params
            )
            if indicator:
                indicator.name = ind_def.name
                self._indicators[ind_def.name] = indicator
                logger.info(f"  Compiled indicator: {ind_def.name}")

        # 编译条件
        for cond_def in blueprint.conditions:
            condition = self._compile_condition(cond_def)
            if condition:
                self._conditions[cond_def.name] = condition
                logger.info(f"  Compiled condition: {cond_def.name}")

        # 编译买入信号
        for sig_def in blueprint.buy_signals:
            buy_conditions = self._build_signal_conditions(sig_def)
            self._buy_conditions.extend(buy_conditions)

        # 编译卖出信号
        for sig_def in blueprint.sell_signals:
            sell_conditions = self._build_signal_conditions(sig_def)
            self._sell_conditions.extend(sell_conditions)

        return CompiledStrategy(
            name=blueprint.name,
            symbols=blueprint.symbols,
            indicators=self._indicators,
            conditions=self._conditions,
            buy_conditions=self._buy_conditions,
            sell_conditions=self._sell_conditions,
            initial_capital=blueprint.initial_capital,
            commission_rate=blueprint.commission_rate,
            position_size=blueprint.position_size,
            stop_loss=blueprint.stop_loss,
            take_profit=blueprint.take_profit
        )

    def _compile_condition(self, cond_def: ConditionDefinition) -> Optional[StrategyComponent]:
        """编译单个条件"""
        params = cond_def.params.copy()

        # 处理子条件
        if cond_def.children:
            child_components = []
            for child in cond_def.children:
                child_comp = self._compile_condition(child)
                if child_comp:
                    child_components.append(child_comp)

            # 根据类型创建组合
            if cond_def.condition_type == "AND":
                config = ComponentConfig(name=cond_def.name, params=params)
                return AndCondition(config, child_components)
            elif cond_def.condition_type == "OR":
                config = ComponentConfig(name=cond_def.name, params=params)
                return OrCondition(config, child_components)
            elif cond_def.condition_type == "NOT":
                config = ComponentConfig(name=cond_def.name, params=params)
                return NotCondition(config, child_components[0] if child_components else None)
        else:
            # 创建基础条件组件
            component = self.registry.create_component(
                "condition",
                cond_def.condition_type,
                params
            )
            if component:
                component.name = cond_def.name
            return component

        return None

    def _build_signal_conditions(self, sig_def: SignalDefinition) -> List[StrategyComponent]:
        """构建信号条件"""
        conditions = []
        for cond_name in sig_def.conditions:
            cond = self._conditions.get(cond_name)
            if cond:
                conditions.append(cond)
        return conditions

    @staticmethod
    def validate_blueprint(blueprint: StrategyBlueprint) -> List[str]:
        """
        验证策略蓝图

        Args:
            blueprint: 策略蓝图

        Returns:
            错误列表，空列表表示验证通过
        """
        errors = []

        if not blueprint.name:
            errors.append("策略名称不能为空")

        if not blueprint.symbols:
            errors.append("至少需要选择一个股票")

        if not blueprint.indicators:
            errors.append("至少需要一个指标")

        if not blueprint.buy_signals and not blueprint.sell_signals:
            errors.append("至少需要一个买入或卖出条件")

        # 检查条件引用的指标是否存在
        condition_names = {c.name for c in blueprint.conditions}
        indicator_names = {i.name for i in blueprint.indicators}

        for sig in blueprint.buy_signals + blueprint.sell_signals:
            for cond_name in sig.conditions:
                if cond_name not in condition_names:
                    errors.append(f"条件 '{cond_name}' 未定义")

        return errors


@dataclass
class CompiledStrategy:
    """
    编译后的策略

    包含所有编译好的组件
    """
    name: str
    symbols: List[str]
    indicators: Dict[str, StrategyComponent]
    conditions: Dict[str, StrategyComponent]
    buy_conditions: List[StrategyComponent]
    sell_conditions: List[StrategyComponent]
    initial_capital: float = 1000000.0
    commission_rate: float = 0.0003
    position_size: float = 0.3
    stop_loss: float = 0.05
    take_profit: float = 0.15

    def generate_code(self) -> str:
        """
        生成 Python 策略代码

        Returns:
            可执行的策略代码字符串
        """
        code = f'''"""
{self.name} - 自动生成策略
Generated by Visual Strategy Builder
"""

from tradingagents.strategies.templates import StrategyTemplate, StrategyConfig


class {self.name.replace(" ", "").replace("-", "")}Strategy(StrategyTemplate):
    """
    {self.name}

    Indicators: {", ".join(self.indicators.keys())}
    Buy Conditions: {len(self.buy_conditions)}
    Sell Conditions: {len(self.sell_conditions)}
    """

    def __init__(self, config=None):
        super().__init__(config)
        self.name = "{self.name}"

        # 初始化指标
'''

        # 添加指标初始化代码
        for name, indicator in self.indicators.items():
            params_str = ", ".join(f"{k}={v!r}" for k, v in indicator.params.items())
            code += f'        self.indicators["{name}"] = {indicator.__class__.__name__}()\n'

        code += '''
    def on_bar(self, bar):
        """K线数据处理"""
        symbol = bar.symbol

        # 更新指标
        bar_data = {
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume
        }

        indicator_values = {{}}
        for name, indicator in self.indicators.items():
            output = indicator.compute(bar_data)
            indicator_values[name] = output.value
        bar_data["_indicators"] = indicator_values

        state = self.state[symbol]
'''

        # 生成买卖逻辑
        if self.buy_conditions:
            code += '''
        # 买入逻辑
        buy_signal = '''
            for i, cond in enumerate(self.buy_conditions):
                if i > 0:
                    code += " or "
                code += f"self.conditions['{cond.name}'].compute(bar_data).value"

            code += '''
        if buy_signal and state.position == 0:
            quantity = self._calculate_quantity(bar.close)
            if quantity > 0:
                self.buy(symbol, bar.close, quantity)
'''

        if self.sell_conditions:
            code += '''
        # 卖出逻辑
        sell_signal = '''
            for i, cond in enumerate(self.sell_conditions):
                if i > 0:
                    code += " or "
                code += f"self.conditions['{cond.name}'].compute(bar_data).value"

            code += '''
        if sell_signal and state.position > 0:
            self.sell(symbol, bar.close, state.position)
'''

        code += '''
    def _calculate_quantity(self, price):
        """计算买入数量"""
        if price <= 0:
            return 0
        max_value = self.config.initial_capital * self.position_size
        return max(0, int(max_value / price / 100) * 100)
'''

        return code

    def to_template_class(self) -> type:
        """
        转换为策略模板类

        Returns:
            策略模板类
        """
        code = self.generate_code()
        namespace = {"StrategyTemplate": StrategyTemplate, "StrategyConfig": StrategyConfig}
        exec(code, namespace)

        # 获取类名
        class_name = self.name.replace(" ", "").replace("-", "")
        return namespace.get(class_name)


# 预定义策略模板

MA_CROSSOVER_TEMPLATE = StrategyBlueprint(
    name="均线交叉策略",
    symbols=["000001.SZ"],
    indicators=[
        IndicatorDefinition(name="MA5", component_type="MA", params={"period": 5, "price_field": "close"}),
        IndicatorDefinition(name="MA20", component_type="MA", params={"period": 20, "price_field": "close"})
    ],
    conditions=[
        ConditionDefinition(
            name="金叉买入",
            condition_type="IndicatorCondition",
            params={"indicator_name": "MA5", "operator": "cross_up", "compare_indicator": "MA20"}
        ),
        ConditionDefinition(
            name="死叉卖出",
            condition_type="IndicatorCondition",
            params={"indicator_name": "MA5", "operator": "cross_down", "compare_indicator": "MA20"}
        )
    ],
    buy_signals=[SignalDefinition(signal_type="buy", conditions=["金叉买入"])],
    sell_signals=[SignalDefinition(signal_type="sell", conditions=["死叉卖出"])]
)

MACD_CROSSOVER_TEMPLATE = StrategyBlueprint(
    name="MACD 交叉策略",
    symbols=["000001.SZ"],
    indicators=[
        IndicatorDefinition(name="MACD", component_type="MACD", params={"fast_period": 12, "slow_period": 26, "signal_period": 9})
    ],
    conditions=[
        ConditionDefinition(
            name="MACD金叉",
            condition_type="MACDCross",
            params={"cross_type": "cross_up"}
        ),
        ConditionDefinition(
            name="MACD死叉",
            condition_type="MACDCross",
            params={"cross_type": "cross_down"}
        )
    ],
    buy_signals=[SignalDefinition(signal_type="buy", conditions=["MACD金叉"])],
    sell_signals=[SignalDefinition(signal_type="sell", conditions=["MACD死叉"])]
)

RSI_REVERSION_TEMPLATE = StrategyBlueprint(
    name="RSI 均值回归策略",
    symbols=["000001.SZ"],
    indicators=[
        IndicatorDefinition(name="RSI", component_type="RSI", params={"period": 14})
    ],
    conditions=[
        ConditionDefinition(
            name="RSI超卖买入",
            condition_type="IndicatorCondition",
            params={"indicator_name": "RSI", "operator": "lt", "compare_type": "value", "compare_value": 30}
        ),
        ConditionDefinition(
            name="RSI超买卖出",
            condition_type="IndicatorCondition",
            params={"indicator_name": "RSI", "operator": "gt", "compare_type": "value", "compare_value": 70}
        )
    ],
    buy_signals=[SignalDefinition(signal_type="buy", conditions=["RSI超卖买入"])],
    sell_signals=[SignalDefinition(signal_type="sell", conditions=["RSI超买卖出"])]
)

BOLL_BREAKOUT_TEMPLATE = StrategyBlueprint(
    name="布林带突破策略",
    symbols=["000001.SZ"],
    indicators=[
        IndicatorDefinition(name="BOLL", component_type="BOLL", params={"period": 20, "std_dev": 2})
    ],
    conditions=[
        ConditionDefinition(
            name="突破上轨",
            condition_type="PriceCondition",
            params={"operator": "gt", "compare_to": "indicator", "value": "BOLL_upper"}
        ),
        ConditionDefinition(
            name="跌破下轨",
            condition_type="PriceCondition",
            params={"operator": "lt", "compare_to": "indicator", "value": "BOLL_lower"}
        )
    ],
    buy_signals=[SignalDefinition(signal_type="buy", conditions=["突破上轨"])],
    sell_signals=[SignalDefinition(signal_type="sell", conditions=["跌破下轨"])]
)


# 预定义模板注册表
TEMPLATES = {
    "ma_crossover": MA_CROSSOVER_TEMPLATE,
    "macd_crossover": MACD_CROSSOVER_TEMPLATE,
    "rsi_reversion": RSI_REVERSION_TEMPLATE,
    "boll_breakout": BOLL_BREAKOUT_TEMPLATE
}


def get_template(name: str) -> Optional[StrategyBlueprint]:
    """获取预定义模板"""
    return TEMPLATES.get(name)


def list_templates() -> Dict[str, str]:
    """列出所有预定义模板"""
    return {name: template.name for name, template in TEMPLATES.items()}
