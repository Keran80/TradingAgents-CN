# triggers/position_triggers.py
"""
持仓相关触发器
"""

from typing import Any, Dict, Optional
from .base import AlertTrigger, TriggerResult, TriggerType, AlertLevel


class PositionChangeTrigger(AlertTrigger):
    """
    持仓变动触发器

    当持仓数量或市值变动超过阈值时触发

    使用方式:
    ```python
    trigger = PositionChangeTrigger(
        symbol="000001.SZ",
        change_threshold=10.0,  # 变动超过10%
    )
    result = trigger.check({'positions': {...}})
    ```
    """

    def __init__(
        self,
        symbol: str,
        change_threshold: float = 5.0,
        **kwargs
    ):
        super().__init__(
            name=f"position_change_{symbol}",
            trigger_type=TriggerType.POSITION,
            level=AlertLevel.WARNING,
            **kwargs
        )
        self.symbol = symbol
        self.change_threshold = change_threshold
        self._last_quantity: Optional[int] = None

    def _check_impl(self, context: Dict[str, Any]) -> TriggerResult:
        positions = context.get('positions', {})
        position = positions.get(self.symbol, {})

        current_quantity = position.get('quantity', 0)

        if self._last_quantity is None:
            self._last_quantity = current_quantity
            return self.create_result(triggered=False)

        if current_quantity == 0 and self._last_quantity == 0:
            return self.create_result(triggered=False)

        if self._last_quantity == 0:
            change_pct = 100.0
        else:
            change_pct = abs(current_quantity - self._last_quantity) / self._last_quantity * 100

        triggered = change_pct >= self.change_threshold

        self._last_quantity = current_quantity

        symbol_name = context.get('symbols', {}).get(self.symbol, self.symbol)
        direction = "增加" if current_quantity > self._last_quantity else "减少"

        return self.create_result(
            triggered=triggered,
            title=f"{symbol_name} 持仓{direction}" if triggered else "",
            message=f"{symbol_name} 持仓{direction} {change_pct:.1f}% (从 {self._last_quantity} 到 {current_quantity})",
            data={
                'symbol': self.symbol,
                'last_quantity': self._last_quantity,
                'current_quantity': current_quantity,
                'change_pct': change_pct,
            }
        )


class PnLThresholdTrigger(AlertTrigger):
    """
    盈亏阈值触发器

    当持仓盈亏达到指定阈值时触发

    使用方式:
    ```python
    # 盈利超过20%或亏损超过10%时告警
    trigger = PnLThresholdTrigger(
        symbol="000001.SZ",
        profit_threshold=20.0,   # 盈利阈值(%)
        loss_threshold=-10.0,    # 亏损阈值(%)
    )
    ```
    """

    def __init__(
        self,
        symbol: str,
        profit_threshold: float = 20.0,
        loss_threshold: float = -10.0,
        **kwargs
    ):
        super().__init__(
            name=f"pnl_{symbol}",
            trigger_type=TriggerType.POSITION,
            level=AlertLevel.CRITICAL,
            **kwargs
        )
        self.symbol = symbol
        self.profit_threshold = profit_threshold
        self.loss_threshold = loss_threshold

    def _check_impl(self, context: Dict[str, Any]) -> TriggerResult:
        positions = context.get('positions', {})
        position = positions.get(self.symbol, {})

        pnl_pct = position.get('pnl_pct', 0)

        # 检查是否触发
        triggered = pnl_pct >= self.profit_threshold or pnl_pct <= self.loss_threshold

        if not triggered:
            return self.create_result(triggered=False)

        symbol_name = context.get('symbols', {}).get(self.symbol, self.symbol)
        is_profit = pnl_pct > 0
        level = AlertLevel.CRITICAL if not is_profit else AlertLevel.WARNING

        return self.create_result(
            triggered=True,
            title=f"{symbol_name} 盈亏预警" if is_profit else f"{symbol_name} 亏损预警",
            message=f"{symbol_name} 收益率 {pnl_pct:+.2f}% ({'盈利' if is_profit else '亏损'})",
            data={
                'symbol': self.symbol,
                'pnl_pct': pnl_pct,
                'profit_threshold': self.profit_threshold,
                'loss_threshold': self.loss_threshold,
            }
        )


class DrawdownTrigger(AlertTrigger):
    """
    回撤触发器

    当账户回撤超过指定阈值时触发

    使用方式:
    ```python
    trigger = DrawdownTrigger(drawdown_threshold=15.0)
    result = trigger.check({'portfolio': {...}})
    ```
    """

    def __init__(
        self,
        drawdown_threshold: float = 15.0,
        **kwargs
    ):
        super().__init__(
            name="portfolio_drawdown",
            trigger_type=TriggerType.POSITION,
            level=AlertLevel.CRITICAL,
            **kwargs
        )
        self.drawdown_threshold = drawdown_threshold
        self._peak_value: Optional[float] = None

    def _check_impl(self, context: Dict[str, Any]) -> TriggerResult:
        portfolio = context.get('portfolio', {})
        current_value = portfolio.get('total_value', 0)
        high_water_mark = portfolio.get('high_water_mark')

        if current_value <= 0:
            return self.create_result(triggered=False, message="Invalid portfolio value")

        # 更新峰值
        if self._peak_value is None:
            self._peak_value = current_value
            return self.create_result(triggered=False)

        if high_water_mark is not None:
            self._peak_value = high_water_mark

        if current_value > self._peak_value:
            self._peak_value = current_value

        # 计算回撤
        drawdown = (self._peak_value - current_value) / self._peak_value * 100
        triggered = drawdown >= self.drawdown_threshold

        return self.create_result(
            triggered=triggered,
            title="账户回撤预警" if triggered else "",
            message=f"账户回撤 {drawdown:.2f}% (峰值: {self._peak_value:.2f}, 当前: {current_value:.2f})",
            data={
                'current_value': current_value,
                'peak_value': self._peak_value,
                'drawdown': drawdown,
                'threshold': self.drawdown_threshold,
            }
        )
