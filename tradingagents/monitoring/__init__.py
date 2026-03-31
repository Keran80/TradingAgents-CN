# monitoring/__init__.py
"""
TradingAgents-CN 监控告警模块
提供持仓监控、异动预警、事件驱动跟踪功能
"""

from .manager import MonitorManager, create_default_monitor_manager
from .dashboard import MonitorDashboard

__all__ = [
    'MonitorManager',
    'MonitorDashboard',
    'create_default_monitor_manager',
]
