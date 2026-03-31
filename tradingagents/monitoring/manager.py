# monitoring/manager.py
"""
监控管理器
统一管理告警触发和通知
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
import logging

from .triggers.base import AlertTrigger, TriggerResult
from .notifiers.base import AlertNotifier, NotificationResult
from .dashboard import MonitorDashboard


class MonitorManager:
    """
    监控管理器

    统一管理触发器、通知器和监控面板

    使用方式:
    ```python
    from tradingagents.monitoring import MonitorManager, MonitorDashboard
    from tradingagents.monitoring.triggers import PriceChangeTrigger
    from tradingagents.monitoring.notifiers import ConsoleNotifier

    # 创建管理器
    manager = MonitorManager(name="my_monitor")

    # 添加触发器
    manager.add_trigger(PriceChangeTrigger(
        symbol="000001.SZ",
        threshold=-5.0,
        level=AlertLevel.WARNING
    ))

    # 添加通知器
    manager.add_notifier(ConsoleNotifier(min_level=AlertLevel.WARNING))

    # 创建监控面板
    dashboard = MonitorDashboard()
    manager.set_dashboard(dashboard)

    # 执行监控检查
    context = {
        'prices': {'000001.SZ': 9.0},
        'positions': {...},
        'portfolio': {...},
        'datetime': datetime.now()
    }
    manager.check(context)

    # 获取报告
    print(manager.get_report())
    ```
    """

    def __init__(
        self,
        name: str = "main",
        auto_start: bool = False,
        check_interval: int = 60  # 秒
    ):
        self.name = name
        self.check_interval = check_interval
        self.logger = logging.getLogger(f"monitoring.manager.{name}")

        self.triggers: List[AlertTrigger] = []
        self.notifiers: List[AlertNotifier] = []
        self.dashboard: Optional[MonitorDashboard] = None
        self.enabled = True

        # 回调函数
        self._on_alert_callbacks: List[Callable[[TriggerResult], None]] = []

        # 统计
        self._total_checks = 0
        self._triggered_count = 0

    def add_trigger(self, trigger: AlertTrigger) -> 'MonitorManager':
        """添加触发器"""
        self.triggers.append(trigger)
        self.logger.info(f"Added trigger: {trigger.name}")
        return self

    def remove_trigger(self, trigger_name: str) -> bool:
        """移除触发器"""
        for i, t in enumerate(self.triggers):
            if t.name == trigger_name:
                self.triggers.pop(i)
                self.logger.info(f"Removed trigger: {trigger_name}")
                return True
        return False

    def add_notifier(self, notifier: AlertNotifier) -> 'MonitorManager':
        """添加通知器"""
        self.notifiers.append(notifier)
        self.logger.info(f"Added notifier: {notifier.name}")
        return self

    def remove_notifier(self, notifier_name: str) -> bool:
        """移除通知器"""
        for i, n in enumerate(self.notifiers):
            if n.name == notifier_name:
                self.notifiers.pop(i)
                self.logger.info(f"Removed notifier: {notifier_name}")
                return True
        return False

    def set_dashboard(self, dashboard: MonitorDashboard) -> 'MonitorManager':
        """设置监控面板"""
        self.dashboard = dashboard
        return self

    def on_alert(self, callback: Callable[[TriggerResult], None]) -> 'MonitorManager':
        """注册告警回调"""
        self._on_alert_callbacks.append(callback)
        return self

    def check(self, context: Dict[str, Any]) -> List[TriggerResult]:
        """
        执行监控检查

        Args:
            context: 监控上下文字典
                   - prices: Dict[str, float] 当前价格
                   - positions: Dict[str, Dict] 持仓信息
                   - portfolio: Dict 投资组合信息
                   - volumes: Dict[str, float] 成交量
                   - avg_volumes: Dict[str, float] 平均成交量
                   - datetime: datetime 当前时间

        Returns:
            List[TriggerResult]: 所有触发结果
        """
        if not self.enabled:
            return []

        self._total_checks += 1
        triggered_results: List[TriggerResult] = []

        # 添加时间到上下文
        if 'datetime' not in context:
            context['datetime'] = datetime.now()

        # 遍历所有触发器
        for trigger in self.triggers:
            if not trigger.enabled:
                continue

            try:
                result = trigger.check(context)
                if result.triggered:
                    triggered_results.append(result)
                    self._triggered_count += 1
                    self.logger.warning(f"Alert triggered: {result.title}")

                    # 发送通知
                    self._notify(result)

                    # 添加到面板
                    if self.dashboard:
                        self.dashboard.add_alert(result)

                    # 执行回调
                    for callback in self._on_alert_callbacks:
                        try:
                            callback(result)
                        except Exception as e:
                            self.logger.error(f"Callback error: {e}")

            except Exception as e:
                self.logger.error(f"Trigger {trigger.name} error: {e}")

        return triggered_results

    def _notify(self, result: TriggerResult):
        """发送通知"""
        for notifier in self.notifiers:
            if not notifier.enabled:
                continue
            try:
                notifier.notify(result)
            except Exception as e:
                self.logger.error(f"Notifier {notifier.name} error: {e}")

    def get_triggers(self) -> List[Dict[str, Any]]:
        """获取触发器列表"""
        return [t.stats for t in self.triggers]

    def get_notifiers(self) -> List[Dict[str, Any]]:
        """获取通知器列表"""
        return [n.stats for n in self.notifiers]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_checks': self._total_checks,
            'triggered_count': self._triggered_count,
            'trigger_rate': self._triggered_count / max(1, self._total_checks),
            'triggers': len(self.triggers),
            'notifiers': len(self.notifiers),
            'enabled': self.enabled,
        }

    def get_report(self) -> str:
        """生成监控报告"""
        lines = [
            "=" * 50,
            f"  监控管理器报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 50,
            "",
            f"名称: {self.name}",
            f"状态: {'运行中' if self.enabled else '已暂停'}",
            f"检查次数: {self._total_checks}",
            f"触发次数: {self._triggered_count}",
            "",
            "触发器列表:",
        ]

        for t in self.triggers:
            status = "启用" if t.enabled else "禁用"
            lines.append(f"  [{status}] {t.name} ({t.trigger_type.value}) - 触发 {t._trigger_count} 次")

        lines.extend(["", "通知器列表:"])
        for n in self.notifiers:
            status = "启用" if n.enabled else "禁用"
            lines.append(f"  [{status}] {n.name} - 发送 {n._sent_count}, 失败 {n._failed_count}")

        if self.dashboard:
            lines.extend(["", "监控面板:"])
            lines.append(self.dashboard.generate_report())

        lines.append("=" * 50)

        return "\n".join(lines)

    def reset(self):
        """重置管理器"""
        for trigger in self.triggers:
            trigger.reset()
        self._total_checks = 0
        self._triggered_count = 0
        self.logger.info("Monitor manager reset")


def create_default_monitor_manager(
    symbols: List[str],
    risk_level: str = "normal"
) -> MonitorManager:
    """
    创建默认监控管理器

    根据风险级别预设触发器和通知器

    Args:
        symbols: 监控的股票代码列表
        risk_level: 风险级别 "low"/"normal"/"high"

    Returns:
        MonitorManager: 配置好的监控管理器
    """
    from .triggers.base import AlertLevel
    from .notifiers import ConsoleNotifier

    manager = MonitorManager(name=f"monitor_{risk_level}")

    # 根据风险级别配置阈值
    thresholds = {
        'low': {'price_change': 10.0, 'profit': 30.0, 'loss': -15.0, 'drawdown': 20.0},
        'normal': {'price_change': 5.0, 'profit': 20.0, 'loss': -10.0, 'drawdown': 15.0},
        'high': {'price_change': 3.0, 'profit': 15.0, 'loss': -5.0, 'drawdown': 10.0},
    }
    t = thresholds.get(risk_level, thresholds['normal'])

    # 添加价格变动触发器
    for symbol in symbols:
        manager.add_trigger(
            AlertTrigger(
                name=f"price_change_{symbol}",
                trigger_type=1,  # PRICE
                level=AlertLevel.WARNING,
                enabled=True
            )
        )

    # 添加涨停跌停触发器
    for symbol in symbols:
        manager.add_trigger(
            AlertTrigger(
                name=f"limit_{symbol}",
                trigger_type=1,  # PRICE
                level=AlertLevel.CRITICAL,
                enabled=True
            )
        )

    # 添加回撤触发器
    manager.add_trigger(
        AlertTrigger(
            name="portfolio_drawdown",
            trigger_type=2,  # POSITION
            level=AlertLevel.CRITICAL,
            enabled=True
        )
    )

    # 添加控制台通知器
    manager.add_notifier(
        ConsoleNotifier(
            name="console",
            min_level=AlertLevel.WARNING,
            enabled=True
        )
    )

    # 添加监控面板
    manager.set_dashboard(MonitorDashboard(name=f"dashboard_{risk_level}"))

    return manager
