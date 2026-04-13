# -*- coding: utf-8 -*-
"""
Dashboard 指标计算组件
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np


class MetricsCalculator:
    """指标计算器"""
    
    @staticmethod
    def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
        """
        计算夏普比率
        
        Args:
            returns: 收益率列表
            risk_free_rate: 无风险利率
        
        Returns:
            夏普比率
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - risk_free_rate / 252  # 日化无风险利率
        
        if np.std(excess_returns) == 0:
            return 0.0
        
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)  # 年化
        return float(sharpe)
    
    @staticmethod
    def calculate_max_drawdown(returns: List[float]) -> float:
        """
        计算最大回撤
        
        Args:
            returns: 收益率列表
        
        Returns:
            最大回撤 (负值)
        """
        if not returns:
            return 0.0
        
        # 计算累计收益
        cumulative = np.cumprod(1 + np.array(returns))
        
        # 计算running maximum
        running_max = np.maximum.accumulate(cumulative)
        
        # 计算回撤
        drawdown = (cumulative - running_max) / running_max
        
        return float(np.min(drawdown))
    
    @staticmethod
    def calculate_win_rate(trades: List[Dict[str, Any]]) -> float:
        """
        计算胜率
        
        Args:
            trades: 交易记录列表
        
        Returns:
            胜率 (0-100)
        """
        if not trades:
            return 0.0
        
        winning_trades = sum(1 for t in trades if t.get('profit_loss', 0) > 0)
        return (winning_trades / len(trades)) * 100
    
    @staticmethod
    def calculate_total_return(initial_value: float, final_value: float) -> float:
        """
        计算总收益率
        
        Args:
            initial_value: 初始值
            final_value: 最终值
        
        Returns:
            总收益率
        """
        if initial_value == 0:
            return 0.0
        
        return ((final_value - initial_value) / initial_value) * 100
    
    @staticmethod
    def calculate_volatility(returns: List[float], periods: int = 252) -> float:
        """
        计算波动率
        
        Args:
            returns: 收益率列表
            periods: 年化因子 (日线=252)
        
        Returns:
            波动率
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        return float(np.std(returns) * np.sqrt(periods))
    
    @staticmethod
    def calculate_sortino_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
        """
        计算索提诺比率
        
        Args:
            returns: 收益率列表
            risk_free_rate: 无风险利率
        
        Returns:
            索提诺比率
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - risk_free_rate / 252
        
        # 只考虑下行波动
        downside_returns = returns_array[returns_array < 0]
        if len(downside_returns) == 0:
            return float('inf')
        
        downside_std = np.std(downside_returns)
        if downside_std == 0:
            return 0.0
        
        sortino = np.mean(excess_returns) / downside_std * np.sqrt(252)
        return float(sortino)
    
    @staticmethod
    def calculate_calmar_ratio(returns: List[float], max_drawdown: float) -> float:
        """
        计算卡玛比率
        
        Args:
            returns: 收益率列表
            max_drawdown: 最大回撤 (绝对值)
        
        Returns:
            卡玛比率
        """
        if max_drawdown == 0 or max_drawdown == 0.0:
            return 0.0
        
        annual_return = np.mean(returns) * 252
        
        return float(annual_return / abs(max_drawdown))


# 导出类
__all__ = ["MetricsCalculator"]
