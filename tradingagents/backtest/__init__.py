# TradingAgents-CN Backtest Module
"""
回测引擎与绩效分析模块

提供完整的策略回测框架和绩效评估功能：
- 回测引擎：支持事件驱动和向量化双模式
- 绩效分析：收益率、风险指标、夏普比率等
- 报告生成：HTML/JSON格式回测报告
- 策略库：预置策略函数
"""

# 核心引擎类 (从 engine 导入，engine 从 config/result 导入)
from .engine import BacktestEngine
from .config import BacktestConfig, BacktestMode
from .result import BacktestResult, TradeRecord

# 策略函数
from .strategies import moving_average_crossover_strategy, Signal

# 绩效分析
from .performance import PerformanceAnalyzer, PerformanceMetrics
from .report import ReportGenerator, ReportConfig

__all__ = [
    # 引擎
    "BacktestEngine",
    "BacktestConfig",
    "BacktestResult",
    "BacktestMode",
    "TradeRecord",
    # 策略
    "moving_average_crossover_strategy",
    "Signal",
    # 绩效
    "PerformanceAnalyzer",
    "PerformanceMetrics",
    "ReportGenerator",
    "ReportConfig",
]
