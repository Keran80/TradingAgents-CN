# triggers/price_triggers.py
"""
价格相关触发器
"""

from typing import Any, Dict, Optional
from .base import AlertTrigger, TriggerResult, TriggerType, AlertLevel


class PriceChangeTrigger(AlertTrigger):
    """
    价格变动触发器

    当股票价格变动超过指定百分比时触发

    使用方式:
    ```python
    # 股价下跌超过5%时告警
    trigger = PriceChangeTrigger(
        symbol="000001.SZ",
        threshold=-5.0,  # 百分比，负数表示下跌
        reference_price=10.0  # 参考价，不提供则用context中的价格
    )
    result = trigger.check({'prices': {'000001.SZ': 9.4}})
    ```
    """

    def __init__(
        self,
        symbol: str,
        threshold: float,           # 变动百分比(%)，正数上涨，负数下跌
        reference_price: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            name=f"price_change_{symbol}",
            trigger_type=TriggerType.PRICE,
            **kwargs
        )
        self.symbol = symbol
        self.threshold = threshold
        self.reference_price = reference_price
        self._last_price: Optional[float] = None

    def _check_impl(self, context: Dict[str, Any]) -> TriggerResult:
        prices = context.get('prices', {})
        current_price = prices.get(self.symbol)

        if current_price is None:
            return self.create_result(triggered=False, message="Price not available")

        # 使用参考价或上次价格
        ref_price = self.reference_price or self._last_price

        if ref_price is None:
            self._last_price = current_price
            return self.create_result(triggered=False, message="No reference price")

        # 计算变动百分比
        change_pct = ((current_price - ref_price) / ref_price) * 100

        # 更新上次价格
        self._last_price = current_price

        # 判断是否触发
        if self.threshold >= 0:
            triggered = change_pct >= self.threshold
        else:
            triggered = change_pct <= self.threshold

        direction = "上涨" if change_pct > 0 else "下跌"
        symbol_name = context.get('symbols', {}).get(self.symbol, self.symbol)

        return self.create_result(
            triggered=triggered,
            title=f"{symbol_name} 价格异动" if triggered else "",
            message=f"{symbol_name} {direction} {abs(change_pct):.2f}% (阈值: {self.threshold}%)",
            data={
                'symbol': self.symbol,
                'current_price': current_price,
                'reference_price': ref_price,
                'change_pct': change_pct,
            }
        )


class PriceCrossTrigger(AlertTrigger):
    """
    价格穿越触发器

    当价格向上或向下穿越指定价格时触发

    使用方式:
    ```python
    trigger = PriceCrossTrigger(
        symbol="000001.SZ",
        trigger_price=10.0,
        direction="up"  # "up" 或 "down"
    )
    ```
    """

    def __init__(
        self,
        symbol: str,
        trigger_price: float,
        direction: str = "up",    # "up" 向上穿越, "down" 向下穿越
        **kwargs
    ):
        super().__init__(
            name=f"price_cross_{symbol}",
            trigger_type=TriggerType.PRICE,
            **kwargs
        )
        self.symbol = symbol
        self.trigger_price = trigger_price
        self.direction = direction.lower()
        self._last_above: Optional[bool] = None

    def _check_impl(self, context: Dict[str, Any]) -> TriggerResult:
        prices = context.get('prices', {})
        current_price = prices.get(self.symbol)

        if current_price is None:
            return self.create_result(triggered=False, message="Price not available")

        current_above = current_price >= self.trigger_price

        if self._last_above is None:
            self._last_above = current_above
            return self.create_result(triggered=False)

        # 检测穿越
        triggered = False
        if self.direction == "up":
            triggered = current_above and not self._last_above
        else:
            triggered = not current_above and self._last_above

        self._last_above = current_above

        symbol_name = context.get('symbols', {}).get(self.symbol, self.symbol)
        direction_text = "向上穿越" if self.direction == "up" else "向下穿越"

        return self.create_result(
            triggered=triggered,
            title=f"{symbol_name} 价格{direction_text}" if triggered else "",
            message=f"{symbol_name} {direction_text} {self.trigger_price:.2f} (当前: {current_price:.2f})",
            data={
                'symbol': self.symbol,
                'trigger_price': self.trigger_price,
                'current_price': current_price,
                'direction': self.direction,
            }
        )


class UpperLimitTrigger(AlertTrigger):
    """
    涨停触发器

    当股票达到涨停价时触发（A股特有）

    使用方式:
    ```python
    trigger = UpperLimitTrigger(symbol="000001.SZ")
    result = trigger.check({'prices': {'000001.SZ': 11.0}})
    ```
    """

    def __init__(
        self,
        symbol: str,
        limit_up_ratio: float = 10.0,  # 涨停比例(%)，默认10%
        reference_price: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            name=f"upper_limit_{symbol}",
            trigger_type=TriggerType.PRICE,
            level=AlertLevel.CRITICAL,
            **kwargs
        )
        self.symbol = symbol
        self.limit_up_ratio = limit_up_ratio
        self.reference_price = reference_price
        self._base_price: Optional[float] = None

    def _check_impl(self, context: Dict[str, Any]) -> TriggerResult:
        prices = context.get('prices', {})
        current_price = prices.get(self.symbol)

        if current_price is None:
            return self.create_result(triggered=False)

        # 计算涨停价
        if self.reference_price:
            base_price = self.reference_price
        elif self._base_price is None:
            self._base_price = current_price
            return self.create_result(triggered=False)
        else:
            base_price = self._base_price

        limit_up_price = base_price * (1 + self.limit_up_ratio / 100)
        is_at_limit = abs(current_price - limit_up_price) < 0.01

        if is_at_limit and self._base_price is not None:
            symbol_name = context.get('symbols', {}).get(self.symbol, self.symbol)
            return self.create_result(
                triggered=True,
                title=f"{symbol_name} 涨停",
                message=f"{symbol_name} 达到涨停价 {limit_up_price:.2f}",
                data={
                    'symbol': self.symbol,
                    'current_price': current_price,
                    'limit_up_price': limit_up_price,
                    'base_price': base_price,
                }
            )

        return self.create_result(triggered=False)


class LowerLimitTrigger(AlertTrigger):
    """
    跌停触发器

    当股票达到跌停价时触发（A股特有）

    使用方式:
    ```python
    trigger = LowerLimitTrigger(symbol="000001.SZ")
    result = trigger.check({'prices': {'000001.SZ': 9.0}})
    ```
    """

    def __init__(
        self,
        symbol: str,
        limit_down_ratio: float = 10.0,  # 跌停比例(%)，默认10%
        reference_price: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            name=f"lower_limit_{symbol}",
            trigger_type=TriggerType.PRICE,
            level=AlertLevel.CRITICAL,
            **kwargs
        )
        self.symbol = symbol
        self.limit_down_ratio = limit_down_ratio
        self.reference_price = reference_price
        self._base_price: Optional[float] = None

    def _check_impl(self, context: Dict[str, Any]) -> TriggerResult:
        prices = context.get('prices', {})
        current_price = prices.get(self.symbol)

        if current_price is None:
            return self.create_result(triggered=False)

        # 计算跌停价
        if self.reference_price:
            base_price = self.reference_price
        elif self._base_price is None:
            self._base_price = current_price
            return self.create_result(triggered=False)
        else:
            base_price = self._base_price

        limit_down_price = base_price * (1 - self.limit_down_ratio / 100)
        is_at_limit = abs(current_price - limit_down_price) < 0.01

        if is_at_limit and self._base_price is not None:
            symbol_name = context.get('symbols', {}).get(self.symbol, self.symbol)
            return self.create_result(
                triggered=True,
                title=f"{symbol_name} 跌停",
                message=f"{symbol_name} 达到跌停价 {limit_down_price:.2f}",
                data={
                    'symbol': self.symbol,
                    'current_price': current_price,
                    'limit_down_price': limit_down_price,
                    'base_price': base_price,
                }
            )

        return self.create_result(triggered=False)
