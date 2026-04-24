"""
回测配置模块

包含回测模式和配置数据类。
"""

from dataclasses import dataclass
from enum import Enum


class BacktestMode(Enum):
    """回测模式"""
    EVENT_DRIVEN = "event"  # 事件驱动
    VECTORIZED = "vector"  # 向量化


@dataclass
class BacktestConfig:
    """回测配置"""
    # 数据配置
    start_date: str = "2024-01-01"
    end_date: str = "2024-12-31"
    initial_cash: float = 1000000.0

    # 回测模式
    mode: BacktestMode = BacktestMode.EVENT_DRIVEN

    # 手续费配置
    commission_rate: float = 0.0003  # 万三
    slippage_rate: float = 0.0001   # 万一滑点

    # 风控配置
    enable_risk: bool = True
    max_position_ratio: float = 0.3  # 最大持仓比例

    # 监控配置
    enable_monitoring: bool = True

    # 数据源
    data_source: str = "akshare"  # akshare / tdx / csv
