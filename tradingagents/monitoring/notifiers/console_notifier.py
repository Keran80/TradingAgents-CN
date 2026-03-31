# notifiers/console_notifier.py
"""
控制台通知器
将告警输出到控制台/日志
"""

from ..triggers.base import TriggerResult
from .base import AlertNotifier, NotificationResult


class ConsoleNotifier(AlertNotifier):
    """
    控制台通知器

    将告警信息打印到控制台，支持彩色输出

    使用方式:
    ```python
    notifier = ConsoleNotifier(
        name="console",
        min_level=AlertLevel.WARNING,  # 只通知 WARNING 及以上
        use_color=True
    )
    notifier.notify(trigger_result)
    ```
    """

    def __init__(
        self,
        name: str = "console",
        use_color: bool = True,
        **kwargs
    ):
        super().__init__(name=name, **kwargs)
        self.use_color = use_color

    def _send_impl(self, result: TriggerResult) -> NotificationResult:
        """发送控制台通知"""
        message = self._format_message(result)

        if self.use_color:
            message = self._add_color(message, result.alert_level)

        # 输出到控制台
        print(message)

        return self._create_result(
            success=True,
            message="Sent to console"
        )

    def _add_color(self, message: str, level) -> str:
        """添加ANSI颜色码"""
        colors = {
            'info': '\033[94m',      # 蓝色
            'warning': '\033[93m',   # 黄色
            'critical': '\033[91m',  # 红色
            'urgent': '\033[95m',    # 紫色闪烁
        }
        color = colors.get(level.value, '\033[0m')
        reset = '\033[0m'
        return f"{color}{message}{reset}"
