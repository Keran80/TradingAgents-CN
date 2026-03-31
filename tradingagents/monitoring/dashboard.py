# monitoring/dashboard.py
"""
监控面板
提供实时监控状态概览
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json


@dataclass
class AlertRecord:
    """告警记录"""
    id: str
    trigger_name: str
    alert_level: str
    title: str
    message: str
    data: Dict[str, Any]
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'trigger_name': self.trigger_name,
            'alert_level': self.alert_level,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class MonitorDashboard:
    """
    监控面板

    汇总所有监控状态，提供告警历史和统计

    使用方式:
    ```python
    dashboard = MonitorDashboard()

    # 添加告警记录
    dashboard.add_alert(result)

    # 获取概览
    overview = dashboard.get_overview()

    # 生成报告
    report = dashboard.generate_report()
    ```
    """

    def __init__(
        self,
        name: str = "main",
        max_history: int = 1000,
        retention_hours: int = 24
    ):
        self.name = name
        self.max_history = max_history
        self.retention_hours = retention_hours
        self.alerts: List[AlertRecord] = []
        self.alert_counts: Dict[str, int] = {}
        self._alert_id = 0

    def add_alert(self, result) -> str:
        """添加告警记录"""
        self._alert_id += 1
        record = AlertRecord(
            id=f"alert_{self._alert_id}",
            trigger_name=result.trigger_name,
            alert_level=result.alert_level.value,
            title=result.title,
            message=result.message,
            data=result.data,
            timestamp=result.timestamp
        )
        self.alerts.append(record)

        # 更新计数
        key = f"{result.trigger_name}:{result.alert_level.value}"
        self.alert_counts[key] = self.alert_counts.get(key, 0) + 1

        # 清理过期记录
        self._cleanup()

        return record.id

    def _cleanup(self):
        """清理过期记录"""
        # 清理超过最大数量的记录
        if len(self.alerts) > self.max_history:
            self.alerts = self.alerts[-self.max_history:]

        # 清理超时记录
        cutoff = datetime.now() - timedelta(hours=self.retention_hours)
        self.alerts = [a for a in self.alerts if a.timestamp > cutoff]

    def get_overview(self) -> Dict[str, Any]:
        """获取监控概览"""
        now = datetime.now()
        cutoff = now - timedelta(hours=self.retention_hours)

        # 过滤最近24小时的告警
        recent = [a for a in self.alerts if a.timestamp > cutoff]

        # 统计各级别告警数
        level_counts = {'info': 0, 'warning': 0, 'critical': 0, 'urgent': 0}
        for a in recent:
            level_counts[a.alert_level] = level_counts.get(a.alert_level, 0) + 1

        # 获取最近告警
        recent_alerts = [a.to_dict() for a in recent[-10:]]

        return {
            'name': self.name,
            'total_alerts': len(self.alerts),
            'recent_alerts': len(recent),
            'level_counts': level_counts,
            'recent_alerts_list': recent_alerts,
            'last_alert_time': recent[-1].timestamp.isoformat() if recent else None,
            'uptime': (now - self.alerts[0].timestamp).total_seconds() if self.alerts else 0,
        }

    def get_alerts(
        self,
        level: Optional[str] = None,
        trigger: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取告警列表"""
        filtered = self.alerts

        if level:
            filtered = [a for a in filtered if a.alert_level == level]
        if trigger:
            filtered = [a for a in filtered if a.trigger_name == trigger]
        if since:
            filtered = [a for a in filtered if a.timestamp > since]

        return [a.to_dict() for a in filtered[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据"""
        if not self.alerts:
            return {'total': 0, 'by_level': {}, 'by_trigger': {}}

        # 按级别统计
        by_level = {}
        for a in self.alerts:
            by_level[a.alert_level] = by_level.get(a.alert_level, 0) + 1

        # 按触发器统计
        by_trigger = {}
        for a in self.alerts:
            by_trigger[a.trigger_name] = by_trigger.get(a.trigger_name, 0) + 1

        return {
            'total': len(self.alerts),
            'by_level': by_level,
            'by_trigger': by_trigger,
            'top_triggers': sorted(by_trigger.items(), key=lambda x: -x[1])[:5],
        }

    def generate_report(self) -> str:
        """生成监控报告"""
        overview = self.get_overview()
        stats = self.get_stats()

        lines = [
            "=" * 50,
            f"  监控面板报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 50,
            "",
            "概览:",
            f"  总告警数: {overview['total_alerts']}",
            f"  最近告警: {overview['recent_alerts']}",
            f"  最后告警: {overview['last_alert_time'] or 'N/A'}",
            "",
            "告警统计:",
            f"  INFO:     {overview['level_counts'].get('info', 0)}",
            f"  WARNING:  {overview['level_counts'].get('warning', 0)}",
            f"  CRITICAL: {overview['level_counts'].get('critical', 0)}",
            f"  URGENT:   {overview['level_counts'].get('urgent', 0)}",
            "",
            "Top 触发器:",
        ]

        for trigger, count in stats.get('top_triggers', []):
            lines.append(f"  {trigger}: {count}")

        lines.extend(["", "=" * 50])

        return "\n".join(lines)

    def export_json(self) -> str:
        """导出为JSON"""
        return json.dumps({
            'overview': self.get_overview(),
            'stats': self.get_stats(),
            'alerts': [a.to_dict() for a in self.alerts[-100:]]
        }, indent=2, ensure_ascii=False)
