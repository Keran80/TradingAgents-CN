# TradingAgents-CN Backtest Module
"""
回测引擎与绩效分析模块

提供完整的策略回测框架和绩效评估功能：
- 回测引擎：支持事件驱动和向量化双模式
- 绩效分析：收益率、风险指标、夏普比率等
- 报告生成：HTML/JSON格式回测报告
"""

from .engine import BacktestEngine, BacktestConfig, BacktestResult, BacktestMode
from .performance import PerformanceAnalyzer, PerformanceMetrics
from .report import ReportGenerator, ReportConfig

__all__ = [
    "BacktestEngine",
    "BacktestConfig", 
    "BacktestResult",
    "BacktestMode",
    "PerformanceAnalyzer",
    "PerformanceMetrics",
    "ReportGenerator",
    "ReportConfig",
]
