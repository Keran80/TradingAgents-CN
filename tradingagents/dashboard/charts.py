# -*- coding: utf-8 -*-
"""
Dashboard 可视化组件
生成图表数据
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass


@dataclass
class ChartData:
    """图表数据容器"""
    labels: List[str]
    datasets: List[Dict[str, Any]]


class ChartGenerator:
    """图表生成器"""
    
    @staticmethod
    def generate_equity_curve(
        equity_data: List[Dict[str, float]],
        benchmark: Optional[List[float]] = None
    ) -> ChartData:
        """
        生成资金曲线图
        
        Args:
            equity_data: 资金数据 [{date, value}]
            benchmark: 基准数据
        
        Returns:
            ChartData: 图表数据
        """
        if not equity_data:
            return ChartData(labels=[], datasets=[])
        
        labels = [e['date'] for e in equity_data]
        values = [e['value'] for e in equity_data]
        
        datasets = [
            {
                'label': '组合收益',
                'data': values,
                'borderColor': '#34d399',
                'backgroundColor': 'rgba(52, 211, 153, 0.1)',
                'fill': True,
                'tension': 0.4
            }
        ]
        
        if benchmark:
            datasets.append({
                'label': '基准收益',
                'data': benchmark,
                'borderColor': '#60a5fa',
                'borderDash': [5, 5],
                'fill': False,
                'tension': 0.4
            })
        
        return ChartData(labels=labels, datasets=datasets)
    
    @staticmethod
    def generate_drawdown_chart(equity_data: List[Dict[str, float]]) -> ChartData:
        """
        生成回撤图
        
        Args:
            equity_data: 资金数据
        
        Returns:
            ChartData: 图表数据
        """
        if not equity_data:
            return ChartData(labels=[], datasets=[])
        
        values = [e['value'] for e in equity_data]
        labels = [e['date'] for e in equity_data]
        
        # 计算回撤
        peak = values[0]
        drawdowns = []
        
        for v in values:
            if v > peak:
                peak = v
            dd = (v - peak) / peak * 100 if peak > 0 else 0
            drawdowns.append(dd)
        
        return ChartData(
            labels=labels,
            datasets=[{
                'label': '回撤%',
                'data': drawdowns,
                'borderColor': '#f87171',
                'backgroundColor': 'rgba(248, 113, 113, 0.3)',
                'fill': True,
                'tension': 0.4
            }]
        )
    
    @staticmethod
    def generate_position_distribution(positions: List[Dict]) -> ChartData:
        """
        生成持仓分布图（饼图）
        
        Args:
            positions: 持仓列表
        
        Returns:
            ChartData: 图表数据
        """
        if not positions:
            return ChartData(labels=[], datasets=[])
        
        labels = [p.get('name', p.get('symbol')) for p in positions]
        values = [p.get('market_value', 0) for p in positions]
        
        colors = [
            '#60a5fa', '#34d399', '#fbbf24', '#f87171', 
            '#a78bfa', '#fb923c', '#2dd4bf', '#818cf8'
        ]
        
        return ChartData(
            labels=labels,
            datasets=[{
                'data': values,
                'backgroundColor': colors[:len(values)],
                'borderWidth': 0
            }]
        )
    
    @staticmethod
    def generate_monthly_returns(returns: List[float], dates: List[str]) -> ChartData:
        """
        生成月度收益图
        
        Args:
            returns: 收益列表
            dates: 日期列表
        
        Returns:
            ChartData: 图表数据
        """
        if not returns:
            return ChartData(labels=[], datasets=[])
        
        # 按月聚合
        df = pd.DataFrame({'date': dates, 'return': returns})
        df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
        monthly = df.groupby('month')['return'].sum()
        
        labels = [str(m) for m in monthly.index]
        values = monthly.values.tolist()
        
        # 颜色基于正负
        colors = ['#34d399' if v >= 0 else '#f87171' for v in values]
        
        return ChartData(
            labels=labels,
            datasets=[{
                'label': '月度收益%',
                'data': values,
                'backgroundColor': colors
            }]
        )
    
    @staticmethod
    def generate_trade_distribution(trades: List[Dict]) -> ChartData:
        """
        生成交易分布图
        
        Args:
            trades: 交易列表
        
        Returns:
            ChartData: 图表数据
        """
        if not trades:
            return ChartData(labels=[], datasets=[])
        
        # 按行业统计
        sector_trades = {}
        for t in trades:
            sector = t.get('sector', '未知')
            if sector not in sector_trades:
                sector_trades[sector] = {'count': 0, 'profit': 0}
            sector_trades[sector]['count'] += 1
            sector_trades[sector]['profit'] += t.get('profit', 0)
        
        labels = list(sector_trades.keys())
        counts = [v['count'] for v in sector_trades.values()]
        
        return ChartData(
            labels=labels,
            datasets=[{
                'label': '交易次数',
                'data': counts,
                'backgroundColor': '#60a5fa'
            }]
        )


class MetricsCalculator:
    """指标计算器"""
    
    @staticmethod
    def calculate_metrics(
        equity_data: List[Dict[str, float]],
        trades: Optional[List[Dict]] = None
    ) -> Dict[str, float]:
        """
        计算绩效指标
        
        Args:
            equity_data: 资金曲线
            trades: 交易记录
        
        Returns:
            Dict: 指标数据
        """
        if not equity_data:
            return {}
        
        values = [e['value'] for e in equity_data]
        dates = [e['date'] for e in equity_data]
        
        # 基本指标
        total_return = (values[-1] - values[0]) / values[0] * 100 if values[0] > 0 else 0
        
        # 日收益率
        returns = np.diff(values) / values[:-1] * 100
        
        # 年化收益
        days = len(dates)
        annual_return = ((1 + total_return / 100) ** (365 / days) - 1) * 100 if days > 0 else 0
        
        # 夏普比率 (假设无风险利率 3%)
        if len(returns) > 0 and np.std(returns) > 0:
            sharpe = (np.mean(returns) - 3 / 252) / np.std(returns) * np.sqrt(252)
        else:
            sharpe = 0
        
        # 最大回撤
        peak = values[0]
        max_dd = 0
        for v in values:
            if v > peak:
                peak = v
            dd = (v - peak) / peak * 100 if peak > 0 else 0
            if dd < max_dd:
                max_dd = dd
        
        # 胜率
        win_rate = 0
        if trades:
            wins = sum(1 for t in trades if t.get('profit', 0) > 0)
            win_rate = wins / len(trades) * 100 if trades else 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'total_trades': len(trades) if trades else 0,
            'avg_win': np.mean([t['profit'] for t in trades if t.get('profit', 0) > 0]) if trades else 0,
            'avg_loss': np.mean([t['profit'] for t in trades if t.get('profit', 0) < 0]) if trades else 0,
            'profit_factor': abs(np.sum([t['profit'] for t in trades if t.get('profit', 0) > 0]) / 
                                np.sum([t['profit'] for t in trades if t.get('profit', 0) < 0])) if trades and 
                                np.sum([t['profit'] for t in trades if t.get('profit', 0) < 0]) != 0 else 0
        }
    
    @staticmethod
    def calculate_var(returns: List[float], confidence: float = 0.95) -> float:
        """
        计算VaR
        
        Args:
            returns: 收益序列
            confidence: 置信度
        
        Returns:
            float: VaR值
        """
        if not returns:
            return 0
        return np.percentile(returns, (1 - confidence) * 100)


__all__ = ['ChartData', 'ChartGenerator', 'MetricsCalculator']