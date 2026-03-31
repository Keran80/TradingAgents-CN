# notifiers/base.py
"""
通知器基类
所有通知器需继承 AlertNotifier 并实现 send 方法
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

from ..triggers.base import TriggerResult, AlertLevel


@dataclass
class NotificationResult:
    """通知结果"""
    success: bool = False
    notifier_name: str = ""
    message: str = ""
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'notifier_name': self.notifier_name,
            'message': self.message,
            'error': self.error,
            'timestamp': self.timestamp.isoformat(),
        }


class AlertNotifier(ABC):
    """
    告警通知器基类

    使用方式:
    ```python
    class MyNotifier(AlertNotifier):
        def __init__(self):
            super().__init__(name="my_notifier")

        def _send_impl(self, result: TriggerResult) -> NotificationResult:
            # 发送通知
            return NotificationResult(success=True, message="Sent")

    notifier = MyNotifier()
    result = notifier.notify(trigger_result)
    ```
    """

    def __init__(
        self,
        name: str,
        min_level: AlertLevel = AlertLevel.INFO,
        enabled: bool = True,
        template: Optional[str] = None,
        **kwargs
    ):
        self.name = name
        self.min_level = min_level
        self.enabled = enabled
        self.template = template or self._default_template()
        self.logger = logging.getLogger(f"monitoring.notifier.{name}")
        self._sent_count: int = 0
        self._failed_count: int = 0

    def notify(self, result: TriggerResult) -> NotificationResult:
        """
        发送通知

        Args:
            result: 触发结果

        Returns:
            NotificationResult: 通知结果
        """
        if not self.enabled:
            return NotificationResult(
                success=True,
                notifier_name=self.name,
                message="Notifier disabled"
            )

        # 检查告警级别
        if not self._should_notify(result.alert_level):
            return NotificationResult(
                success=True,
                notifier_name=self.name,
                message=f"Alert level {result.alert_level.value} below minimum"
            )

        try:
            notification_result = self._send_impl(result)
            if notification_result.success:
                self._sent_count += 1
            else:
                self._failed_count += 1
            return notification_result
        except Exception as e:
            self._failed_count += 1
            self.logger.error(f"Notifier {self.name} failed: {e}")
            return NotificationResult(
                success=False,
                notifier_name=self.name,
                error=str(e)
            )

    def notify_batch(self, results: List[TriggerResult]) -> List[NotificationResult]:
        """批量发送通知"""
        return [self.notify(r) for r in results]

    def _should_notify(self, level: AlertLevel) -> bool:
        """检查是否应该通知"""
        level_order = {
            AlertLevel.INFO: 0,
            AlertLevel.WARNING: 1,
            AlertLevel.CRITICAL: 2,
            AlertLevel.URGENT: 3,
        }
        return level_order.get(level, 0) >= level_order.get(self.min_level, 0)

    def _default_template(self) -> str:
        """默认消息模板"""
        return "[{level}] {title}\n{message}\n时间: {timestamp}"

    def _format_message(self, result: TriggerResult) -> str:
        """格式化消息"""
        template = self.template
        return template.format(
            level=result.alert_level.value.upper(),
            title=result.title,
            message=result.message,
            timestamp=result.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            trigger_name=result.trigger_name,
            data=result.data
        )

    @abstractmethod
    def _send_impl(self, result: TriggerResult) -> NotificationResult:
        """子类实现具体的发送逻辑"""
        pass

    def _create_result(
        self,
        success: bool,
        message: str = "",
        error: Optional[str] = None
    ) -> NotificationResult:
        """创建通知结果"""
        return NotificationResult(
            success=success,
            notifier_name=self.name,
            message=message,
            error=error
        )

    @property
    def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'min_level': self.min_level.value,
            'sent_count': self._sent_count,
            'failed_count': self._failed_count,
        }
