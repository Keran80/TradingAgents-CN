# -*- coding: utf-8 -*-
"""
TradingAgents-CN - Momentum Factors
动量因子模块

包含：
- 价格动量
- 换手率动量
- 波动率因子
- 趋势因子
"""

from typing import Dict
import pandas as pd
import numpy as np
from ..base import BaseFactor, FactorCategory, FactorType, FactorRegistry


# 注册所有动量因子
_registry_registered = False


def _register_factors():
    global _registry_registered
    if _registry_registered:
        return
    
    # 价格动量
    FactorRegistry.register(Return_1M)
    FactorRegistry.register(Return_3M)
    FactorRegistry.register(Return_6M)
    FactorRegistry.register(Return_12M)
    FactorRegistry.register(Return_MaxDrawdown)
    
    # 换手率动量
    FactorRegistry.register(Turnover_Rate_1M)
    FactorRegistry.register(Turnover_Rate_3M_Avg)
    FactorRegistry.register(Turnover_Rate_Variation)
    
    # 波动率
    FactorRegistry.register(Volatility_1M)
    FactorRegistry.register(Volatility_3M)
    FactorRegistry.register(Volatility_6M)
    
    # 趋势
    FactorRegistry.register(Price_Momentum_12_1)
    FactorRegistry.register(Price_Momentum_6_1)
    FactorRegistry.register(Price_Range_20D)
    
    _registry_registered = True


# ============== 价格动量因子 ==============

class Return_1M(BaseFactor):
    """月度收益率 (过去1个月)"""
    name = "Return_1M"
    category = FactorCategory.MOMENTUM
    factor_type = FactorType.TECHNICAL
    description = "过去1个月收益率"
    formula = "Return_1M = (Price_End - Price_Start) / Price_Start"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        result = daily.groupby('ts_code').apply(
            lambda x: x['close'].pct_change(periods=21).iloc[-1] if len(x) > 21 else np.nan
        )
        return result


class Return_3M(BaseFactor):
    """季度收益率 (过去3个月)"""
    name = "Return_3M"
    category = FactorCategory.MOMENTUM
    factor_type = FactorType.TECHNICAL
    description = "过去3个月收益率"
    formula = "Return_3M = (Price_End - Price_Start) / Price_Start"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        result = daily.groupby('ts_code').apply(
            lambda x: x['close'].pct_change(periods=63).iloc[-1] if len(x) > 63 else np.nan
        )
        return result


class Return_6M(BaseFactor):
    """半年度收益率 (过去6个月)"""
    name = "Return_6M"
    category = FactorCategory.MOMENTUM
    factor_type = FactorType.TECHNICAL
    description = "过去6个月收益率"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        result = daily.groupby('ts_code').apply(
            lambda x: x['close'].pct_change(periods=126).iloc[-1] if len(x) > 126 else np.nan
        )
        return result


class Return_12M(BaseFactor):
    """年度收益率 (过去12个月)"""
    name = "Return_12M"
    category = FactorCategory.MOMENTUM
    factor_type = FactorType.TECHNICAL
    description = "过去12个月收益率"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        result = daily.groupby('ts_code').apply(
            lambda x: x['close'].pct_change(periods=252).iloc[-1] if len(x) > 252 else np.nan
        )
        return result


class Return_MaxDrawdown(BaseFactor):
    """最大回撤"""
    name = "Return_MaxDrawdown"
    category = FactorCategory.MOMENTUM
    factor_type = FactorType.TECHNICAL
    description = "过去252个交易日的最大回撤"
    formula = "MaxDD = (Peak - Valley) / Peak"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        def calc_maxdd(group):
            prices = group['close'].values
            if len(prices) < 20:
                return np.nan
            
            peak = prices[0]
            maxdd = 0
            for p in prices:
                if p > peak:
                    peak = p
                dd = (peak - p) / peak
                if dd > maxdd:
                    maxdd = dd
            return maxdd
        
        return daily.groupby('ts_code').apply(calc_maxdd)


# ============== 换手率因子 ==============

class Turnover_Rate_1M(BaseFactor):
    """月度平均换手率"""
    name = "Turnover_Rate_1M"
    category = FactorCategory.MOMENTUM
    factor_type = FactorType.TECHNICAL
    description = "过去1个月日均换手率"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'turnover_rate' not in daily.columns:
            return pd.Series(dtype=float)
        
        recent = daily.groupby('ts_code').tail(21)
        return recent.groupby('ts_code')['turnover_rate'].mean()


class Turnover_Rate_3M_Avg(BaseFactor):
    """季度平均换手率"""
    name = "Turnover_Rate_3M_Avg"
    category = FactorCategory.MOMENTUM
    factor_type = FactorType.TECHNICAL
    description = "过去3个月日均换手率均值"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'turnover_rate' not in daily.columns:
            return pd.Series(dtype=float)
        
        recent = daily.groupby('ts_code').tail(63)
        return recent.groupby('ts_code')['turnover_rate'].mean()


class Turnover_Rate_Variation(BaseFactor):
    """换手率波动率"""
    name = "Turnover_Rate_Variation"
    category = FactorCategory.MOMENTUM
    factor_type = FactorType.TECHNICAL
    description = "过去3个月换手率标准差"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'turnover_rate' not in daily.columns:
            return pd.Series(dtype=float)
        
        recent = daily.groupby('ts_code').tail(63)
        return recent.groupby('ts_code')['turnover_rate'].std()


# ============== 波动率因子 ==============

class Volatility_1M(BaseFactor):
    """月度波动率"""
    name = "Volatility_1M"
    category = FactorCategory.MOMENTUM
    factor_type = FactorType.TECHNICAL
    description = "过去1个月日收益率标准差 (年化)"
    formula = "Vol_1M = Std(Returns) * sqrt(252)"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        recent = daily.groupby('ts_code').tail(21)
        vol = recent.groupby('ts_code')['close'].pct_change().std() * np.sqrt(252)
        return vol


class Volatility_3M(BaseFactor):
    """季度波动率"""
    name = "Volatility_3M"
    category = FactorCategory.MOMENTUM
    factor_type = FactorType.TECHNICAL
    description = "过去3个月日收益率标准差 (年化)"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        recent = daily.groupby('ts_code').tail(63)
        vol = recent.groupby('ts_code')['close'].pct_change().std() * np.sqrt(252)
        return vol


class Volatility_6M(BaseFactor):
    """半年度波动率"""
    name = "Volatility_6M"
    category = FactorCategory.MOMENTUM
    factor_type = FactorType.TECHNICAL
    description = "过去6个月日收益率标准差 (年化)"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        recent = daily.groupby('ts_code').tail(126)
        vol = recent.groupby('ts_code')['close'].pct_change().std() * np.sqrt(252)
        return vol


# ============== 趋势因子 ==============

class Price_Momentum_12_1(BaseFactor):
    """12-1 动量因子 (过去12个月收益减去过去1个月收益)"""
    name = "Price_Momentum_12_1"
    category = FactorCategory.MOMENTUM
    factor_type = FactorType.TECHNICAL
    description = "12-1 动量,规避短期反转"
    formula = "Mom_12_1 = Return_12M - Return_1M"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        # 计算 12 个月收益
        ret_12m = daily.groupby('ts_code').apply(
            lambda x: x['close'].pct_change(periods=252).iloc[-1] if len(x) > 252 else np.nan
        )
        # 计算 1 个月收益
        ret_1m = daily.groupby('ts_code').apply(
            lambda x: x['close'].pct_change(periods=21).iloc[-1] if len(x) > 21 else np.nan
        )
        
        return ret_12m - ret_1m


class Price_Momentum_6_1(BaseFactor):
    """6-1 动量因子"""
    name = "Price_Momentum_6_1"
    category = FactorCategory.MOMENTUM
    factor_type = FactorType.TECHNICAL
    description = "6-1 动量"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        ret_6m = daily.groupby('ts_code').apply(
            lambda x: x['close'].pct_change(periods=126).iloc[-1] if len(x) > 126 else np.nan
        )
        ret_1m = daily.groupby('ts_code').apply(
            lambda x: x['close'].pct_change(periods=21).iloc[-1] if len(x) > 21 else np.nan
        )
        
        return ret_6m - ret_1m


class Price_Range_20D(BaseFactor):
    """20日价格波动范围"""
    name = "Price_Range_20D"
    category = FactorCategory.MOMENTUM
    factor_type = FactorType.TECHNICAL
    description = "过去20个交易日最高价与最低价的比率"
    formula = "Range = (High_20D - Low_20D) / Low_20D"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        def calc_range(group):
            recent = group.tail(20)
            if len(recent) < 20:
                return np.nan
            high = recent['high'].max()
            low = recent['low'].min()
            if low == 0:
                return np.nan
            return (high - low) / low
        
        return daily.groupby('ts_code').apply(calc_range)


# 导出
__all__ = [
    # 价格动量
    "Return_1M", "Return_3M", "Return_6M", "Return_12M",
    "Return_MaxDrawdown",
    # 换手率
    "Turnover_Rate_1M", "Turnover_Rate_3M_Avg", "Turnover_Rate_Variation",
    # 波动率
    "Volatility_1M", "Volatility_3M", "Volatility_6M",
    # 趋势
    "Price_Momentum_12_1", "Price_Momentum_6_1", "Price_Range_20D",
]

_register_factors()