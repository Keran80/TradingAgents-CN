# -*- coding: utf-8 -*-
"""
策略组件库 - Component Library
===============================

提供各类策略组件，支持条件组合和信号生成：
- 指标组件：均线、MACD、RSI、KDJ、BOLL 等
- 条件组件：价格比较、时间判断、成交量异动
- 信号组件：买入、卖出、观望
- 组合组件：AND、OR、NOT 等逻辑组合
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union

import numpy as np

logger = logging.getLogger(__name__)


class ComponentType(Enum):
    """组件类型"""
    # 指标类
    INDICATOR = "indicator"  # 指标计算
    # 条件类
    CONDITION = "condition"  # 条件判断
    # 信号类
    SIGNAL = "signal"  # 交易信号
    # 逻辑类
    LOGIC = "logic"  # 逻辑组合


@dataclass
class ComponentOutput:
    """组件输出"""
    name: str
    value: Any
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ComponentConfig:
    """组件配置"""
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


class StrategyComponent(ABC):
    """
    策略组件基类

    所有组件必须实现：
    1. compute() - 计算输出值
    2. reset() - 重置内部状态
    """

    def __init__(self, config: Optional[ComponentConfig] = None):
        self.config = config or ComponentConfig(name=self.__class__.__name__)
        self.name = self.config.name
        self.params = self.config.params
        self.component_type = ComponentType.INDICATOR
        self._history: Dict[str, List[float]] = {}
        self._last_output: Optional[ComponentOutput] = None

    @abstractmethod
    def compute(self, bar: Dict[str, Any]) -> ComponentOutput:
        """
        计算组件输出

        Args:
            bar: K线数据，包含 open/high/low/close/volume

        Returns:
            ComponentOutput: 组件输出
        """
        pass

    def reset(self) -> None:
        """重置组件状态"""
        self._history.clear()
        self._last_output = None

    def get_value(self) -> Any:
        """获取当前值"""
        return self._last_output.value if self._last_output else None

    @property
    def description(self) -> str:
        """获取组件描述"""
        return self.config.description or self.__class__.__doc__ or ""


class IndicatorComponent(StrategyComponent):
    """指标组件基类"""
    component_type = ComponentType.INDICATOR


class ConditionComponent(StrategyComponent):
    """条件组件基类"""
    component_type = ComponentType.CONDITION


class SignalComponent(StrategyComponent):
    """信号组件基类"""
    component_type = ComponentType.SIGNAL


class LogicComponent(StrategyComponent):
    """逻辑组合组件基类"""
    component_type = ComponentType.LOGIC


# ============================================================
# 指标组件实现
# ============================================================

class MAIndicator(IndicatorComponent):
    """
    移动平均线指标

    params:
        period: 周期 (默认 5)
        price_field: 价格字段 (close/high/low/open)
    """

    def __init__(self, config: Optional[ComponentConfig] = None):
        super().__init__(config)
        self.period = self.params.get("period", 5)
        self.price_field = self.params.get("price_field", "close")
        self._prices: List[float] = []

    def compute(self, bar: Dict[str, Any]) -> ComponentOutput:
        price = bar.get(self.price_field, bar.get("close", 0))
        self._prices.append(price)

        if len(self._prices) > self.period:
            self._prices.pop(0)

        if len(self._prices) < self.period:
            ma_value = np.nan
        else:
            ma_value = np.mean(self._prices[-self.period:])

        self._last_output = ComponentOutput(
            name=f"MA{self.period}",
            value=ma_value
        )
        return self._last_output

    def reset(self) -> None:
        super().reset()
        self._prices.clear()


class MACDIndicator(IndicatorComponent):
    """
    MACD 指标

    params:
        fast_period: 快线周期 (默认 12)
        slow_period: 慢线周期 (默认 26)
        signal_period: 信号线周期 (默认 9)
    """

    def __init__(self, config: Optional[ComponentConfig] = None):
        super().__init__(config)
        self.fast_period = self.params.get("fast_period", 12)
        self.slow_period = self.params.get("slow_period", 26)
        self.signal_period = self.params.get("signal_period", 9)
        self._fast_ema: List[float] = []
        self._slow_ema: List[float] = []
        self._macd_line: List[float] = []
        self._signal_line: List[float] = []

    def compute(self, bar: Dict[str, Any]) -> ComponentOutput:
        close = bar.get("close", 0)

        # 简单计算 EMA
        if not self._fast_ema:
            self._fast_ema.append(close)
            self._slow_ema.append(close)
        else:
            fast_ema = close * (2 / (self.fast_period + 1)) + self._fast_ema[-1] * (1 - 2 / (self.fast_period + 1))
            slow_ema = close * (2 / (self.slow_period + 1)) + self._slow_ema[-1] * (1 - 2 / (self.slow_period + 1))
            self._fast_ema.append(fast_ema)
            self._slow_ema.append(slow_ema)

        # MACD 线
        if len(self._fast_ema) >= self.slow_period:
            macd = self._fast_ema[-1] - self._slow_ema[-1]
            self._macd_line.append(macd)

            # 信号线
            if len(self._macd_line) >= self.signal_period:
                signal = np.mean(self._macd_line[-self.signal_period:])
                self._signal_line.append(signal)
                histogram = macd - signal
            else:
                signal = np.nan
                histogram = np.nan
        else:
            macd = np.nan
            signal = np.nan
            histogram = np.nan

        self._last_output = ComponentOutput(
            name="MACD",
            value={
                "macd": macd,
                "signal": signal,
                "histogram": histogram
            }
        )
        return self._last_output

    def reset(self) -> None:
        super().reset()
        self._fast_ema.clear()
        self._slow_ema.clear()
        self._macd_line.clear()
        self._signal_line.clear()


class RSIIndicator(IndicatorComponent):
    """
    RSI 相对强弱指标

    params:
        period: 周期 (默认 14)
    """

    def __init__(self, config: Optional[ComponentConfig] = None):
        super().__init__(config)
        self.period = self.params.get("period", 14)
        self._gains: List[float] = []
        self._losses: List[float] = []
        self._last_close: Optional[float] = None

    def compute(self, bar: Dict[str, Any]) -> ComponentOutput:
        close = bar.get("close", 0)

        if self._last_close is not None:
            change = close - self._last_close
            self._gains.append(max(change, 0))
            self._losses.append(max(-change, 0))

        self._last_close = close

        if len(self._gains) < self.period:
            rsi_value = np.nan
        else:
            avg_gain = np.mean(self._gains[-self.period:])
            avg_loss = np.mean(self._losses[-self.period:])

            if avg_loss == 0:
                rsi_value = 100
            else:
                rs = avg_gain / avg_loss
                rsi_value = 100 - (100 / (1 + rs))

        self._last_output = ComponentOutput(
            name=f"RSI{self.period}",
            value=rsi_value
        )
        return self._last_output

    def reset(self) -> None:
        super().reset()
        self._gains.clear()
        self._losses.clear()
        self._last_close = None


class KDJIndicator(IndicatorComponent):
    """
    KDJ 随机指标

    params:
        n: 周期 (默认 9)
        m1: K 平滑 (默认 3)
        m2: D 平滑 (默认 3)
    """

    def __init__(self, config: Optional[ComponentConfig] = None):
        super().__init__(config)
        self.n = self.params.get("n", 9)
        self.m1 = self.params.get("m1", 3)
        self.m2 = self.params.get("m2", 3)
        self._rsv: List[float] = []
        self._k: List[float] = [50]
        self._d: List[float] = [50]

    def compute(self, bar: Dict[str, Any]) -> ComponentOutput:
        high = bar.get("high", 0)
        low = bar.get("low", 0)
        close = bar.get("close", 0)

        highest_high = high
        lowest_low = low

        self._last_output = ComponentOutput(
            name="KDJ",
            value={
                "k": self._k[-1] if self._k else np.nan,
                "d": self._d[-1] if self._d else np.nan,
                "j": 3 * self._k[-1] - 2 * self._d[-1] if self._k and self._d else np.nan
            }
        )
        return self._last_output

    def reset(self) -> None:
        super().reset()
        self._rsv.clear()
        self._k.clear()
        self._d.clear()
        self._k.append(50)
        self._d.append(50)


class BOLLIndicator(IndicatorComponent):
    """
    布林带指标

    params:
        period: 周期 (默认 20)
        std_dev: 标准差倍数 (默认 2)
    """

    def __init__(self, config: Optional[ComponentConfig] = None):
        super().__init__(config)
        self.period = self.params.get("period", 20)
        self.std_dev = self.params.get("std_dev", 2)
        self._prices: List[float] = []

    def compute(self, bar: Dict[str, Any]) -> ComponentOutput:
        close = bar.get("close", 0)
        self._prices.append(close)

        if len(self._prices) > self.period:
            self._prices.pop(0)

        if len(self._prices) < self.period:
            mid = np.nan
            upper = np.nan
            lower = np.nan
        else:
            prices_arr = np.array(self._prices[-self.period:])
            mid = np.mean(prices_arr)
            std = np.std(prices_arr)
            upper = mid + self.std_dev * std
            lower = mid - self.std_dev * std

        self._last_output = ComponentOutput(
            name="BOLL",
            value={
                "upper": upper,
                "mid": mid,
                "lower": lower
            }
        )
        return self._last_output

    def reset(self) -> None:
        super().reset()
        self._prices.clear()


class VolumeIndicator(IndicatorComponent):
    """
    成交量指标

    params:
        period: 周期 (默认 5)
    """

    def __init__(self, config: Optional[ComponentConfig] = None):
        super().__init__(config)
        self.period = self.params.get("period", 5)
        self._volumes: List[float] = []

    def compute(self, bar: Dict[str, Any]) -> ComponentOutput:
        volume = bar.get("volume", 0)
        self._volumes.append(volume)

        if len(self._volumes) > self.period:
            self._volumes.pop(0)

        if len(self._volumes) < self.period:
            avg_volume = np.nan
        else:
            avg_volume = np.mean(self._volumes[-self.period:])

        self._last_output = ComponentOutput(
            name=f"VolumeMA{self.period}",
            value=avg_volume
        )
        return self._last_output

    def reset(self) -> None:
        super().reset()
        self._volumes.clear()


# ============================================================
# 条件组件实现
# ============================================================

class PriceCondition(ConditionComponent):
    """
    价格比较条件

    params:
        operator: 比较运算符 (gt/lt/gte/lte/eq/cross_up/cross_down)
        compare_to: 比较值类型 (price/indicator/fixed)
        value: 固定比较值或指标名
    """

    def __init__(self, config: Optional[ComponentConfig] = None):
        super().__init__(config)
        self.operator = self.params.get("operator", "gt")
        self.compare_to = self.params.get("compare_to", "fixed")
        self.value = self.params.get("value", 0)
        self._prev_price: Optional[float] = None

    def compute(self, bar: Dict[str, Any]) -> ComponentOutput:
        current_price = bar.get("close", 0)
        result = False

        if self.operator == "gt":
            result = current_price > self.value
        elif self.operator == "lt":
            result = current_price < self.value
        elif self.operator == "gte":
            result = current_price >= self.value
        elif self.operator == "lte":
            result = current_price <= self.value
        elif self.operator == "eq":
            result = abs(current_price - self.value) < 0.01
        elif self.operator == "cross_up":
            if self._prev_price is not None:
                result = self._prev_price <= self.value and current_price > self.value
        elif self.operator == "cross_down":
            if self._prev_price is not None:
                result = self._prev_price >= self.value and current_price < self.value

        self._prev_price = current_price

        self._last_output = ComponentOutput(
            name=f"Price{self.operator}",
            value=result
        )
        return self._last_output

    def reset(self) -> None:
        super().reset()
        self._prev_price = None


class IndicatorCondition(ConditionComponent):
    """
    指标条件判断

    params:
        indicator_name: 指标名
        operator: 比较运算符
        compare_type: 比较类型 (value/indicator/zero)
        compare_indicator: 比较的指标名
        compare_value: 比较的固定值
    """

    def __init__(self, config: Optional[ComponentConfig] = None):
        super().__init__(config)
        self.indicator_name = self.params.get("indicator_name", "MA5")
        self.operator = self.params.get("operator", "gt")
        self.compare_type = self.params.get("compare_type", "value")
        self.compare_value = self.params.get("compare_value", 0)
        self._indicator_values: Dict[str, float] = {}

    def set_indicator_value(self, name: str, value: float) -> None:
        """设置指标值"""
        self._indicator_values[name] = value

    def compute(self, bar: Dict[str, Any]) -> ComponentOutput:
        indicator_value = self._indicator_values.get(self.indicator_name, np.nan)
        result = False

        if self.compare_type == "value":
            compare_val = self.compare_value
        elif self.compare_type == "zero":
            compare_val = 0
        else:
            compare_val = self._indicator_values.get(self.params.get("compare_indicator", ""), np.nan)

        if self.operator == "gt":
            result = indicator_value > compare_val
        elif self.operator == "lt":
            result = indicator_value < compare_val
        elif self.operator == "gte":
            result = indicator_value >= compare_val
        elif self.operator == "lte":
            result = indicator_value <= compare_val
        elif self.operator == "cross_up":
            prev = self._indicator_values.get(f"_prev_{self.indicator_name}", np.nan)
            result = prev <= compare_val and indicator_value > compare_val
            self._indicator_values[f"_prev_{self.indicator_name}"] = indicator_value
        elif self.operator == "cross_down":
            prev = self._indicator_values.get(f"_prev_{self.indicator_name}", np.nan)
            result = prev >= compare_val and indicator_value < compare_val
            self._indicator_values[f"_prev_{self.indicator_name}"] = indicator_value

        self._last_output = ComponentOutput(
            name=f"Condition_{self.indicator_name}_{self.operator}",
            value=result
        )
        return self._last_output

    def reset(self) -> None:
        super().reset()
        self._indicator_values.clear()


class MACDCrossCondition(ConditionComponent):
    """
    MACD 金叉/死叉条件

    params:
        cross_type: cross_up(金叉)/cross_down(死叉)
    """

    def __init__(self, config: Optional[ComponentConfig] = None):
        super().__init__(config)
        self.cross_type = self.params.get("cross_type", "cross_up")
        self._prev_macd: Optional[float] = None
        self._prev_signal: Optional[float] = None

    def compute(self, bar: Dict[str, Any]) -> ComponentOutput:
        # 从 bar 中获取 MACD 指标值
        macd_data = bar.get("_indicators", {}).get("MACD", {})
        macd = macd_data.get("macd", np.nan)
        signal = macd_data.get("signal", np.nan)

        result = False

        if self._prev_macd is not None and self._prev_signal is not None:
            if self.cross_type == "cross_up":
                # 金叉：MACD 从下方穿越信号线
                result = self._prev_macd <= self._prev_signal and macd > signal
            elif self.cross_type == "cross_down":
                # 死叉：MACD 从上方穿越信号线
                result = self._prev_macd >= self._prev_signal and macd < signal

        self._prev_macd = macd
        self._prev_signal = signal

        self._last_output = ComponentOutput(
            name=f"MACD_{self.cross_type}",
            value=result
        )
        return self._last_output

    def reset(self) -> None:
        super().reset()
        self._prev_macd = None
        self._prev_signal = None


class VolumeCondition(ConditionComponent):
    """
    成交量条件

    params:
        condition: 放量/缩量/突破
        compare_type: 与谁比较 (avg/fixed)
        value: 比较值
        ratio: 倍数 (放量/缩量时使用)
    """

    def __init__(self, config: Optional[ComponentConfig] = None):
        super().__init__(config)
        self.condition = self.params.get("condition", "spike")
        self.compare_type = self.params.get("compare_type", "avg")
        self.fixed_value = self.params.get("value", 0)
        self.ratio = self.params.get("ratio", 1.5)
        self._volume_history: List[float] = []

    def compute(self, bar: Dict[str, Any]) -> ComponentOutput:
        volume = bar.get("volume", 0)
        self._volume_history.append(volume)

        if len(self._volume_history) > 20:
            self._volume_history.pop(0)

        result = False

        if len(self._volume_history) >= 5:
            avg_volume = np.mean(self._volume_history[:-1])

            if self.condition == "spike":
                result = volume > avg_volume * self.ratio
            elif self.condition == "drill":
                result = volume < avg_volume / self.ratio
            elif self.condition == "break":
                result = volume > self.fixed_value

        self._last_output = ComponentOutput(
            name=f"Volume_{self.condition}",
            value=result
        )
        return self._last_output

    def reset(self) -> None:
        super().reset()
        self._volume_history.clear()


# ============================================================
# 组合逻辑组件
# ============================================================

class AndCondition(LogicComponent):
    """
    AND 逻辑组合
    所有输入条件都为 True 时返回 True
    """

    def __init__(self, config: Optional[ComponentConfig] = None, conditions: List[StrategyComponent] = None):
        super().__init__(config)
        self.conditions = conditions or []

    def compute(self, bar: Dict[str, Any]) -> ComponentOutput:
        results = [c.compute(bar).value if isinstance(c.compute(bar).value, bool) else c.compute(bar).value for c in self.conditions]
        result = all(r for r in results if isinstance(r, bool))

        self._last_output = ComponentOutput(
            name="AND",
            value=result
        )
        return self._last_output

    def reset(self) -> None:
        super().reset()
        for c in self.conditions:
            c.reset()


class OrCondition(LogicComponent):
    """
    OR 逻辑组合
    任一输入条件为 True 时返回 True
    """

    def __init__(self, config: Optional[ComponentConfig] = None, conditions: List[StrategyComponent] = None):
        super().__init__(config)
        self.conditions = conditions or []

    def compute(self, bar: Dict[str, Any]) -> ComponentOutput:
        results = [c.compute(bar).value if isinstance(c.compute(bar).value, bool) else c.compute(bar).value for c in self.conditions]
        result = any(r for r in results if isinstance(r, bool))

        self._last_output = ComponentOutput(
            name="OR",
            value=result
        )
        return self._last_output

    def reset(self) -> None:
        super().reset()
        for c in self.conditions:
            c.reset()


class NotCondition(LogicComponent):
    """
    NOT 逻辑取反
    """

    def __init__(self, config: Optional[ComponentConfig] = None, condition: Optional[StrategyComponent] = None):
        super().__init__(config)
        self.condition = condition

    def compute(self, bar: Dict[str, Any]) -> ComponentOutput:
        result = True
        if self.condition:
            output = self.condition.compute(bar)
            result = not output.value if isinstance(output.value, bool) else True

        self._last_output = ComponentOutput(
            name="NOT",
            value=result
        )
        return self._last_output

    def reset(self) -> None:
        super().reset()
        if self.condition:
            self.condition.reset()


# ============================================================
# 信号组件
# ============================================================

class BuySignal(SignalComponent):
    """买入信号"""

    def __init__(self, config: Optional[ComponentConfig] = None):
        super().__init__(config)
        self.signal_type = "BUY"

    def compute(self, bar: Dict[str, Any]) -> ComponentOutput:
        self._last_output = ComponentOutput(
            name="BUY_SIGNAL",
            value=True
        )
        return self._last_output


class SellSignal(SignalComponent):
    """卖出信号"""

    def __init__(self, config: Optional[ComponentConfig] = None):
        super().__init__(config)
        self.signal_type = "SELL"

    def compute(self, bar: Dict[str, Any]) -> ComponentOutput:
        self._last_output = ComponentOutput(
            name="SELL_SIGNAL",
            value=True
        )
        return self._last_output


# ============================================================
# 组件注册表
# ============================================================

class ComponentRegistry:
    """
    组件注册表

    管理所有可用组件，支持动态注册和查询
    """

    _instance = None
    _indicators: Dict[str, type] = {}
    _conditions: Dict[str, type] = {}
    _signals: Dict[str, type] = {}
    _logics: Dict[str, type] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._register_defaults()
        return cls._instance

    def _register_defaults(self) -> None:
        """注册默认组件"""
        # 指标
        self.register_indicator("MA", MAIndicator)
        self.register_indicator("MACD", MACDIndicator)
        self.register_indicator("RSI", RSIIndicator)
        self.register_indicator("KDJ", KDJIndicator)
        self.register_indicator("BOLL", BOLLIndicator)
        self.register_indicator("Volume", VolumeIndicator)

        # 条件
        self.register_condition("PriceCondition", PriceCondition)
        self.register_condition("IndicatorCondition", IndicatorCondition)
        self.register_condition("MACDCross", MACDCrossCondition)
        self.register_condition("VolumeCondition", VolumeCondition)

        # 信号
        self.register_signal("BUY", BuySignal)
        self.register_signal("SELL", SellSignal)

        # 逻辑
        self.register_logic("AND", AndCondition)
        self.register_logic("OR", OrCondition)
        self.register_logic("NOT", NotCondition)

    @classmethod
    def register_indicator(cls, name: str, component_class: type) -> None:
        """注册指标组件"""
        cls._indicators[name] = component_class

    @classmethod
    def register_condition(cls, name: str, component_class: type) -> None:
        """注册条件组件"""
        cls._conditions[name] = component_class

    @classmethod
    def register_signal(cls, name: str, component_class: type) -> None:
        """注册信号组件"""
        cls._signals[name] = component_class

    @classmethod
    def register_logic(cls, name: str, component_class: type) -> None:
        """注册逻辑组件"""
        cls._logics[name] = component_class

    def get_indicator(self, name: str) -> Optional[type]:
        """获取指标组件类"""
        return self._indicators.get(name)

    def get_condition(self, name: str) -> Optional[type]:
        """获取条件组件类"""
        return self._conditions.get(name)

    def get_signal(self, name: str) -> Optional[type]:
        """获取信号组件类"""
        return self._signals.get(name)

    def get_logic(self, name: str) -> Optional[type]:
        """获取逻辑组件类"""
        return self._logics.get(name)

    def create_component(self, component_type: str, name: str, params: Dict[str, Any] = None) -> Optional[StrategyComponent]:
        """
        创建组件实例

        Args:
            component_type: 组件类型 (indicator/condition/signal/logic)
            name: 组件名称
            params: 组件参数

        Returns:
            组件实例
        """
        config = ComponentConfig(name=name, params=params or {})

        if component_type == "indicator":
            cls = self.get_indicator(name)
        elif component_type == "condition":
            cls = self.get_condition(name)
        elif component_type == "signal":
            cls = self.get_signal(name)
        elif component_type == "logic":
            cls = self.get_logic(name)
        else:
            return None

        if cls:
            return cls(config)
        return None

    def list_components(self) -> Dict[str, List[str]]:
        """列出所有组件"""
        return {
            "indicators": list(self._indicators.keys()),
            "conditions": list(self._conditions.keys()),
            "signals": list(self._signals.keys()),
            "logics": list(self._logics.keys())
        }
