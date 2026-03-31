# triggers/volume_triggers.py
"""
成交量相关触发器
"""

from typing import Any, Dict, Optional
from .base import AlertTrigger, TriggerResult, TriggerType, AlertLevel


class VolumeSpikeTrigger(AlertTrigger):
    """
    成交量放大触发器

    当成交量超过均量的指定倍数时触发

    使用方式:
    ```python
    trigger = VolumeSpikeTrigger(
        symbol="000001.SZ",
        multiplier=3.0,  # 超过3倍均量
        window=20       # 计算均量的窗口
    )
    result = trigger.check({
        'prices': {'000001.SZ': 10.0},
        'volumes': {'000001.SZ': 15000000},
        'avg_volumes': {'000001.SZ': 5000000}
    })
    ```
    """

    def __init__(
        self,
        symbol: str,
        multiplier: float = 2.0,
        window: int = 20,
        **kwargs
    ):
        super().__init__(
            name=f"volume_spike_{symbol}",
            trigger_type=TriggerType.VOLUME,
            level=AlertLevel.WARNING,
            **kwargs
        )
        self.symbol = symbol
        self.multiplier = multiplier
        self.window = window
        self._volume_history: list = []

    def _check_impl(self, context: Dict[str, Any]) -> TriggerResult:
        volumes = context.get('volumes', {})
        avg_volumes = context.get('avg_volumes', {})
        prices = context.get('prices', {})

        current_volume = volumes.get(self.symbol)
        avg_volume = avg_volumes.get(self.symbol)
        current_price = prices.get(self.symbol)

        if current_volume is None:
            return self.create_result(triggered=False, message="Volume not available")

        # 计算均量
        if avg_volume is None:
            self._volume_history.append(current_volume)
            if len(self._volume_history) <= self.window:
                return self.create_result(triggered=False, message="Collecting volume history")
            avg_volume = sum(self._volume_history[-self.window:]) / self.window
        else:
            self._volume_history.append(current_volume)

        # 判断是否放量
        ratio = current_volume / avg_volume if avg_volume > 0 else 0
        triggered = ratio >= self.multiplier

        symbol_name = context.get('symbols', {}).get(self.symbol, self.symbol)

        return self.create_result(
            triggered=triggered,
            title=f"{symbol_name} 成交量异动" if triggered else "",
            message=f"{symbol_name} 成交量放大 {ratio:.1f}倍 (当前: {current_volume/10000:.0f}万, 均量: {avg_volume/10000:.0f}万)",
            data={
                'symbol': self.symbol,
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'ratio': ratio,
                'threshold': self.multiplier,
            }
        )


class VolumeDrillTrigger(AlertTrigger):
    """
    成交量萎缩触发器

    当成交量低于均量的指定比例时触发（可能表示流动性枯竭）

    使用方式:
    ```python
    trigger = VolumeDrillTrigger(
        symbol="000001.SZ",
        threshold=0.3,  # 低于30%均量
        window=20
    )
    ```
    """

    def __init__(
        self,
        symbol: str,
        threshold: float = 0.5,   # 均量的比例
        window: int = 20,
        **kwargs
    ):
        super().__init__(
            name=f"volume_drill_{symbol}",
            trigger_type=TriggerType.VOLUME,
            level=AlertLevel.WARNING,
            **kwargs
        )
        self.symbol = symbol
        self.threshold = threshold
        self.window = window
        self._volume_history: list = []

    def _check_impl(self, context: Dict[str, Any]) -> TriggerResult:
        volumes = context.get('volumes', {})
        avg_volumes = context.get('avg_volumes', {})

        current_volume = volumes.get(self.symbol)
        avg_volume = avg_volumes.get(self.symbol)

        if current_volume is None:
            return self.create_result(triggered=False, message="Volume not available")

        # 计算均量
        if avg_volume is None:
            self._volume_history.append(current_volume)
            if len(self._volume_history) <= self.window:
                return self.create_result(triggered=False, message="Collecting volume history")
            avg_volume = sum(self._volume_history[-self.window:]) / self.window
        else:
            self._volume_history.append(current_volume)

        # 判断是否缩量
        ratio = current_volume / avg_volume if avg_volume > 0 else 0
        triggered = ratio <= self.threshold

        symbol_name = context.get('symbols', {}).get(self.symbol, self.symbol)

        return self.create_result(
            triggered=triggered,
            title=f"{symbol_name} 成交量萎缩" if triggered else "",
            message=f"{symbol_name} 成交量萎缩至 {ratio*100:.0f}% 均量 (当前: {current_volume/10000:.0f}万)",
            data={
                'symbol': self.symbol,
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'ratio': ratio,
                'threshold': self.threshold,
            }
        )
