# -*- coding: utf-8 -*-
"""
Dashboard 热力图组件
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np


class HeatmapGenerator:
    """热力图生成器"""
    
    def __init__(self):
        self.sector_map = {
            '银行': ['000001.SZ', '601398.SH', '601939.SH'],
            '白酒': ['600519.SH', '000858.SZ', '000568.SZ'],
            '新能源': ['300750.SZ', '002594.SZ', '002466.SZ'],
            '医药': ['600276.SH', '000538.SZ', '300003.SZ'],
            '科技': ['600036.SH', '000333.SZ', '601012.SH'],
            '消费': ['000651.SZ', '603259.SH', '603288.SH'],
        }
    
    def generate_sector_heatmap(self, positions: List[Dict]) -> Dict[str, float]:
        """
        生成行业热力图
        
        Args:
            positions: 持仓列表
        
        Returns:
            Dict[sector, weight]: 行业权重
        """
        total_value = sum(p.get('market_value', 0) for p in positions)
        if total_value == 0:
            return {}
        
        sector_weights = {}
        
        for sector, codes in self.sector_map.items():
            sector_value = sum(
                p.get('market_value', 0) 
                for p in positions 
                if p.get('symbol') in codes
            )
            if sector_value > 0:
                sector_weights[sector] = (sector_value / total_value) * 100
        
        return sector_weights
    
    def generate_return_calendar(
        self, 
        returns: List[float], 
        dates: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        生成收益日历
        
        Args:
            returns: 每日收益列表
            dates: 日期列表
        
        Returns:
            Dict: 日历数据
        """
        if dates is None:
            end_date = datetime.now()
            dates = [
                (end_date - timedelta(days=i)).strftime('%Y-%m-%d')
                for i in range(len(returns)-1, -1, -1)
            ]
        
        calendar_data = []
        for i, (date, ret) in enumerate(zip(dates, returns)):
            calendar_data.append({
                'date': date,
                'return': ret,
                'color': self._get_return_color(ret)
            })
        
        return {
            'data': calendar_data,
            'total_days': len(returns),
            'positive_days': sum(1 for r in returns if r > 0),
            'negative_days': sum(1 for r in returns if r < 0),
            'avg_return': np.mean(returns) if returns else 0
        }
    
    def _get_return_color(self, return_val: float) -> str:
        """根据收益获取颜色"""
        if return_val > 2:
            return '#34d399'  # 强阳
        elif return_val > 0:
            return '#86efac'  # 小阳
        elif return_val == 0:
            return '#6b7280'  # 平
        elif return_val > -2:
            return '#fca5a5'  # 小阴
        else:
            return '#f87171'  # 强阴
    
    def generate_correlation_matrix(
        self, 
        prices: pd.DataFrame
    ) -> pd.DataFrame:
        """
        生成相关性矩阵
        
        Args:
            prices: 价格DataFrame
        
        Returns:
            DataFrame: 相关性矩阵
        """
        returns = prices.pct_change().dropna()
        return returns.corr()
    
    def generate_volume_heatmap(
        self, 
        symbol: str,
        volume_data: List[Dict]
    ) -> Dict[str, Any]:
        """
        生成成交量热力图
        
        Args:
            symbol: 股票代码
            volume_data: 成交量数据
        
        Returns:
            Dict: 成交量热力图数据
        """
        if not volume_data:
            return {}
        
        # 按时间段聚合
        time_buckets = {
            '09:30-10:30': [],
            '10:30-11:30': [],
            '13:00-14:00': [],
            '14:00-15:00': []
        }
        
        for v in volume_data:
            time = v.get('time', '')
            volume = v.get('volume', 0)
            
            if '09:30' <= time < '10:30':
                time_buckets['09:30-10:30'].append(volume)
            elif '10:30' <= time < '11:30':
                time_buckets['10:30-11:30'].append(volume)
            elif '13:00' <= time < '14:00':
                time_buckets['13:00-14:00'].append(volume)
            elif '14:00' <= time <= '15:00':
                time_buckets['14:00-15:00'].append(volume)
        
        return {
            'symbol': symbol,
            'time_buckets': {
                k: {
                    'avg': np.mean(v) if v else 0,
                    'max': np.max(v) if v else 0,
                    'total': np.sum(v) if v else 0
                }
                for k, v in time_buckets.items()
            }
        }


class PortfolioHeatmap:
    """组合热力图视图"""
    
    def __init__(self):
        self.generator = HeatmapGenerator()
    
    def generate_overview(
        self,
        positions: List[Dict],
        historical_returns: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        生成组合概览热力图
        
        Args:
            positions: 持仓列表
            historical_returns: 历史收益
        
        Returns:
            Dict: 热力图概览数据
        """
        # 行业分布
        sector_weights = self.generator.generate_sector_heatmap(positions)
        
        # 收益日历
        calendar_data = {}
        if historical_returns:
            calendar_data = self.generator.generate_return_calendar(historical_returns)
        
        return {
            'sector_weights': sector_weights,
            'calendar': calendar_data,
            'total_positions': len(positions),
            'total_value': sum(p.get('market_value', 0) for p in positions)
        }
    
    def generate_position_heatmap(
        self,
        positions: List[Dict]
    ) -> List[Dict]:
        """
        生成持仓热力图（按盈亏排序）
        
        Args:
            positions: 持仓列表
        
        Returns:
            List[Dict]: 持仓热力图数据
        """
        # 按盈亏排序
        sorted_positions = sorted(
            positions,
            key=lambda x: x.get('profit_pct', 0),
            reverse=True
        )
        
        heatmap = []
        for i, p in enumerate(sorted_positions):
            profit_pct = p.get('profit_pct', 0)
            heatmap.append({
                'rank': i + 1,
                'symbol': p.get('symbol'),
                'name': p.get('name', p.get('symbol')),
                'weight': p.get('weight', 0),
                'profit_pct': profit_pct,
                'color': self.generator._get_return_color(profit_pct),
                'intensity': min(abs(profit_pct) / 10, 1)  # 归一化强度
            })
        
        return heatmap


__all__ = ['HeatmapGenerator', 'PortfolioHeatmap']