# triggers/time_triggers.py
"""
时间相关触发器
"""

from datetime import datetime, time
from typing import Any, Dict
from .base import AlertTrigger, TriggerResult, TriggerType, AlertLevel


class MarketOpenTrigger(AlertTrigger):
    """
    开盘触发器

    在交易时段开盘时触发（如9:30, 13:00）

    使用方式:
    ```python
    trigger = MarketOpenTrigger(session="morning")  # "morning" 或 "afternoon"
    ```
    """

    def __init__(
        self,
        session: str = "morning",    # "morning" 9:30, "afternoon" 13:00
        **kwargs
    ):
        name = f"market_open_{session}"
        super().__init__(
            name=name,
            trigger_type=TriggerType.TIME,
            level=AlertLevel.INFO,
            **kwargs
        )
        self.session = session
        self._triggered_today = False
        self._last_date: Any = None

    def _check_impl(self, context: Dict[str, Any]) -> TriggerResult:
        now = context.get('datetime', datetime.now())

        # 检查是否新的一天
        if self._last_date != now.date():
            self._last_date = now.date()
            self._triggered_today = False

        if self._triggered_today:
            return self.create_result(triggered=False)

        # 检查是否到达开盘时间
        target_time = time(9, 30) if self.session == "morning" else time(13, 0)
        current_time = now.time()

        triggered = current_time >= target_time

        if triggered:
            self._triggered_today = True
            session_name = "早盘" if self.session == "morning" else "午盘"

            return self.create_result(
                triggered=True,
                title=f"{session_name}开盘",
                message=f"市场{ session_name }开盘，当前时间 {now.strftime('%H:%M')}",
                data={
                    'session': self.session,
                    'current_time': current_time.isoformat(),
                }
            )

        return self.create_result(triggered=False)


class MarketCloseTrigger(AlertTrigger):
    """
    收盘触发器

    在交易时段收盘时触发（如15:00）

    使用方式:
    ```python
    trigger = MarketCloseTrigger()
    ```
    """

    def __init__(
        self,
        close_time: str = "15:00",
        **kwargs
    ):
        super().__init__(
            name="market_close",
            trigger_type=TriggerType.TIME,
            level=AlertLevel.INFO,
            **kwargs
        )
        self.close_time = datetime.strptime(close_time, "%H:%M").time()
        self._triggered_today = False
        self._last_date: Any = None

    def _check_impl(self, context: Dict[str, Any]) -> TriggerResult:
        now = context.get('datetime', datetime.now())

        # 检查是否新的一天
        if self._last_date != now.date():
            self._last_date = now.date()
            self._triggered_today = False

        if self._triggered_today:
            return self.create_result(triggered=False)

        current_time = now.time()
        triggered = current_time >= self.close_time

        if triggered:
            self._triggered_today = True
            return self.create_result(
                triggered=True,
                title="收盘",
                message=f"市场收盘，今日交易结束。当前时间 {now.strftime('%H:%M')}",
                data={
                    'close_time': self.close_time.isoformat(),
                    'current_time': current_time.isoformat(),
                }
            )

        return self.create_result(triggered=False)
