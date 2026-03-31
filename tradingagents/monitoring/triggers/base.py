# triggers/base.py
"""
告警触发器基类
所有触发器需继承 AlertTrigger 并实现 check 方法
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class TriggerType(Enum):
    """触发器类型"""
    PRICE = "price"                    # 价格相关
    VOLUME = "volume"                  # 成交量相关
    POSITION = "position"              # 持仓相关
    TIME = "time"                      # 时间相关
    CUSTOM = "custom"                  # 自定义


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"                     # 信息
    WARNING = "warning"                # 警告
    CRITICAL = "critical"              # 严重
    URGENT = "urgent"                  # 紧急


@dataclass
class TriggerResult:
    """触发结果"""
    triggered: bool = False            # 是否触发
    trigger_name: str = ""             # 触发器名称
    alert_level: AlertLevel = AlertLevel.INFO  # 告警级别
    title: str = ""                    # 告警标题
    message: str = ""                  # 告警消息
    data: Dict[str, Any] = field(default_factory=dict)  # 附加数据
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'triggered': self.triggered,
            'trigger_name': self.trigger_name,
            'alert_level': self.alert_level.value,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
        }


class AlertTrigger(ABC):
    """
    告警触发器基类

    使用方式:
    ```python
    class MyTrigger(AlertTrigger):
        def __init__(self):
            super().__init__(
                name="my_trigger",
                trigger_type=TriggerType.PRICE,
                level=AlertLevel.WARNING
            )

        def check(self, context: Dict[str, Any]) -> TriggerResult:
            # 实现触发逻辑
            if condition_met:
                return self.create_result(
                    triggered=True,
                    title="Title",
                    message="Message",
                    data={'key': 'value'}
                )
            return self.create_result(triggered=False)

    trigger = MyTrigger()
    result = trigger.check(context)
    ```
    """

    def __init__(
        self,
        name: str,
        trigger_type: TriggerType,
        level: AlertLevel = AlertLevel.INFO,
        enabled: bool = True,
        cooldown_seconds: int = 0,      # 冷却时间(秒)
        description: str = ""
    ):
        self.name = name
        self.trigger_type = trigger_type
        self.level = level
        self.enabled = enabled
        self.cooldown_seconds = cooldown_seconds
        self.description = description
        self._last_triggered: Optional[datetime] = None
        self._trigger_count: int = 0

    def check(self, context: Dict[str, Any]) -> TriggerResult:
        """
        检查是否触发告警

        Args:
            context: 包含市场数据的上下文字典
                   - prices: Dict[str, float] 当前价格
                   - positions: Dict[str, Dict] 持仓信息
                   - portfolio: Dict 投资组合信息
                   - datetime: datetime 当前时间

        Returns:
            TriggerResult: 触发结果
        """
        if not self.enabled:
            return self.create_result(triggered=False)

        # 检查冷却时间
        if self._is_in_cooldown():
            return self.create_result(triggered=False)

        # 执行子类检查逻辑
        result = self._check_impl(context)

        # 更新触发状态
        if result.triggered:
            self._last_triggered = datetime.now()
            self._trigger_count += 1
            result.alert_level = self.level

        return result

    @abstractmethod
    def _check_impl(self, context: Dict[str, Any]) -> TriggerResult:
        """子类实现具体的检查逻辑"""
        pass

    def _is_in_cooldown(self) -> bool:
        """检查是否在冷却时间内"""
        if self._last_triggered is None or self.cooldown_seconds <= 0:
            return False
        elapsed = (datetime.now() - self._last_triggered).total_seconds()
        return elapsed < self.cooldown_seconds

    def create_result(
        self,
        triggered: bool,
        title: str = "",
        message: str = "",
        data: Optional[Dict[str, Any]] = None
    ) -> TriggerResult:
        """创建触发结果"""
        return TriggerResult(
            triggered=triggered,
            trigger_name=self.name,
            alert_level=self.level,
            title=title or self.name,
            message=message,
            data=data or {},
            timestamp=datetime.now()
        )

    def reset(self):
        """重置触发器状态"""
        self._last_triggered = None
        self._trigger_count = 0

    @property
    def stats(self) -> Dict[str, Any]:
        """获取触发器统计信息"""
        return {
            'name': self.name,
            'type': self.trigger_type.value,
            'level': self.level.value,
            'enabled': self.enabled,
            'trigger_count': self._trigger_count,
            'last_triggered': self._last_triggered.isoformat() if self._last_triggered else None,
        }


class CompositeTrigger(AlertTrigger):
    """
    组合触发器
    多个触发器的逻辑组合
    """

    def __init__(
        self,
        name: str,
        triggers: List[AlertTrigger],
        operator: str = "AND",  # AND / OR / ANY
        level: AlertLevel = AlertLevel.INFO
    ):
        super().__init__(
            name=name,
            trigger_type=TriggerType.CUSTOM,
            level=level
        )
        self.triggers = triggers
        self.operator = operator.upper()

    def _check_impl(self, context: Dict[str, Any]) -> TriggerResult:
        results = [t.check(context) for t in self.triggers if t.enabled]

        if not results:
            return self.create_result(triggered=False)

        if self.operator == "AND":
            triggered = all(r.triggered for r in results)
        elif self.operator == "OR":
            triggered = any(r.triggered for r in results)
        else:  # ANY
            triggered = any(r.triggered for r in results)

        triggered_results = [r for r in results if r.triggered]
        messages = [r.message for r in triggered_results]

        return self.create_result(
            triggered=triggered,
            title=f"{self.name} ({self.operator})",
            message="; ".join(messages) if messages else "",
            data={'sub_results': [r.to_dict() for r in results]}
        )
