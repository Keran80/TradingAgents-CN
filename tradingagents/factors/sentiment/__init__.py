# -*- coding: utf-8 -*-
"""
TradingAgents-CN - Sentiment Factors
情绪因子模块

包含：
- 资金流向 (北向资金/主力资金)
- 龙虎榜数据
- 分析师情绪
- 舆情因子
"""

from typing import Dict
import pandas as pd
import numpy as np
from ..base import BaseFactor, FactorCategory, FactorType, FactorRegistry


_registry_registered = False


def _register_factors():
    global _registry_registered
    if _registry_registered:
        return
    
    # 资金流向
    FactorRegistry.register(Northbound_Flow_Ratio)
    FactorRegistry.register(Major_Fund_Flow_5D)
    FactorRegistry.register(Major_Fund_Flow_10D)
    FactorRegistry.register(Retail_Fund_Flow_5D)
    FactorRegistry.register(Net_Buy_Ratio_Inst)
    
    # 龙虎榜
    FactorRegistry.register(Dragon_Tiger_Count_1M)
    FactorRegistry.register(Dragon_Tiger_Buy_1M)
    FactorRegistry.register(Dragon_Tiger_Sell_1M)
    FactorRegistry.register(Institutional_Holding_Change)
    
    # 分析师
    FactorRegistry.register(Analyst_Rating)
    FactorRegistry.register(Target_Price_Upside)
    FactorRegistry.register(EPS_Change_Ratio)
    FactorRegistry.register(Consensus_Growth_Rate)
    
    # 舆情
    FactorRegistry.register(News_Sentiment_Score)
    FactorRegistry.register(Social_Media_Heat)
    FactorRegistry.register(Insider_Buy_Ratio)
    FactorRegistry.register(Insider_Sell_Ratio)
    
    _registry_registered = True


# ============== 资金流向因子 ==============

class Northbound_Flow_Ratio(BaseFactor):
    """北向资金持股占比"""
    name = "Northbound_Flow_Ratio"
    category = FactorCategory.SENTIMENT
    factor_type = FactorType.MARKET
    description = "北向资金持股占流通股本比例"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'northbound_hold_ratio' not in daily.columns:
            return pd.Series(dtype=float)
        return daily.groupby('ts_code')['northbound_hold_ratio'].last()


class Major_Fund_Flow_5D(BaseFactor):
    """5日主力资金净流入"""
    name = "Major_Fund_Flow_5D"
    category = FactorCategory.SENTIMENT
    factor_type = FactorType.MARKET
    description = "过去5个交易日主力资金净流入"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'main_fund_flow' not in daily.columns:
            return pd.Series(dtype=float)
        
        recent = daily.groupby('ts_code').tail(5)
        return recent.groupby('ts_code')['main_fund_flow'].sum()


class Major_Fund_Flow_10D(BaseFactor):
    """10日主力资金净流入"""
    name = "Major_Fund_Form_10D"
    category = FactorCategory.SENTIMENT
    factor_type = FactorType.MARKET
    description = "过去10个交易日主力资金净流入"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'main_fund_flow' not in daily.columns:
            return pd.Series(dtype=float)
        
        recent = daily.groupby('ts_code').tail(10)
        return recent.groupby('ts_code')['main_fund_flow'].sum()


class Retail_Fund_Flow_5D(BaseFactor):
    """5日散户资金净流入"""
    name = "Retail_Fund_Flow_5D"
    category = FactorCategory.SENTIMENT
    factor_type = FactorType.MARKET
    description = "过去5个交易日散户资金净流入"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'retail_fund_flow' not in daily.columns:
            return pd.Series(dtype=float)
        
        recent = daily.groupby('ts_code').tail(5)
        return recent.groupby('ts_code')['retail_fund_flow'].sum()


class Net_Buy_Ratio_Inst(BaseFactor):
    """机构净买入占比"""
    name = "Net_Buy_Ratio_Inst"
    category = FactorCategory.SENTIMENT
    factor_type = FactorType.MARKET
    description = "机构净买入金额占总成交额比例"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'inst_net_buy' not in daily.columns or 'amount' not in daily.columns:
            return pd.Series(dtype=float)
        
        recent = daily.groupby('ts_code').tail(5)
        result = recent.groupby('ts_code').apply(
            lambda x: x['inst_net_buy'].sum() / x['amount'].sum() if x['amount'].sum() != 0 else 0
        )
        return result


# ============== 龙虎榜因子 ==============

class Dragon_Tiger_Count_1M(BaseFactor):
    """月度登榜次数"""
    name = "Dragon_Tiger_Count_1M"
    category = FactorCategory.SENTIMENT
    factor_type = FactorType.MARKET
    description = "过去1个月登录龙虎榜次数"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'dragon_tiger_count' not in daily.columns:
            return pd.Series(dtype=float)
        
        recent = daily.groupby('ts_code').tail(21)
        return recent.groupby('ts_code')['dragon_tiger_count'].sum()


class Dragon_Tiger_Buy_1M(BaseFactor):
    """月度龙虎榜买入金额"""
    name = "Dragon_Tiger_Buy_1M"
    category = FactorCategory.SENTIMENT
    factor_type = FactorType.MARKET
    description = "过去1个月龙虎榜买入金额"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'dragon_tiger_buy' not in daily.columns:
            return pd.Series(dtype=float)
        
        recent = daily.groupby('ts_code').tail(21)
        return recent.groupby('ts_code')['dragon_tiger_buy'].sum()


class Dragon_Tiger_Sell_1M(BaseFactor):
    """月度龙虎榜卖出金额"""
    name = "Dragon_Tiger_Sell_1M"
    category = FactorCategory.SENTIMENT
    factor_type = FactorType.MARKET
    description = "过去1个月龙虎榜卖出金额"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'dragon_tiger_sell' not in daily.columns:
            return pd.Series(dtype=float)
        
        recent = daily.groupby('ts_code').tail(21)
        return recent.groupby('ts_code')['dragon_tiger_sell'].sum()


class Institutional_Holding_Change(BaseFactor):
    """机构持股变化"""
    name = "Institutional_Holding_Change"
    category = FactorCategory.SENTIMENT
    factor_type = FactorType.MARKET
    description = "机构持股比例变化"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'inst_holding' not in daily.columns:
            return pd.Series(dtype=float)
        
        def calc_change(group):
            if len(group) < 60:
                return np.nan
            current = group['inst_holding'].iloc[-1]
            old = group['inst_holding'].iloc[-60]
            if old == 0:
                return np.nan
            return (current - old) / old
        
        return daily.groupby('ts_code').apply(calc_change)


# ============== 分析师因子 ==============

class Analyst_Rating(BaseFactor):
    """分析师评级 (1-5, 5最高)"""
    name = "Analyst_Rating"
    category = FactorCategory.SENTIMENT
    factor_type = FactorType.FUNDAMENTAL
    description = "分析师综合评级"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'analyst_rating' not in daily.columns:
            return pd.Series(dtype=float)
        return daily.groupby('ts_code')['analyst_rating'].last()


class Target_Price_Upside(BaseFactor):
    """目标价上涨空间"""
    name = "Target_Price_Upside"
    category = FactorCategory.SENTIMENT
    factor_type = FactorType.FUNDAMENTAL
    description = "目标价相对当前价的上涨空间"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'target_price' not in daily.columns or 'close' not in daily.columns:
            return pd.Series(dtype=float)
        
        def calc_upside(group):
            target = group['target_price'].iloc[-1]
            current = group['close'].iloc[-1]
            if current == 0 or pd.isna(target):
                return np.nan
            return (target - current) / current
        
        return daily.groupby('ts_code').apply(calc_upside)


class EPS_Change_Ratio(BaseFactor):
    """分析师EPS上调比例"""
    name = "EPS_Change_Ratio"
    category = FactorCategory.SENTIMENT
    factor_type = FactorType.FUNDAMENTAL
    description = "近1个月上调EPS的分析师占比"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'eps_up_count' not in daily.columns or 'eps_total_count' not in daily.columns:
            return pd.Series(dtype=float)
        
        def calc_ratio(group):
            up = group['eps_up_count'].sum()
            total = group['eps_total_count'].sum()
            if total == 0:
                return np.nan
            return up / total
        
        recent = daily.groupby('ts_code').tail(21)
        return recent.groupby('ts_code').apply(calc_ratio)


class Consensus_Growth_Rate(BaseFactor):
    """一致预期增长率"""
    name = "Consensus_Growth_Rate"
    category = FactorCategory.SENTIMENT
    factor_type = FactorType.FUNDAMENTAL
    description = "分析师一致预期净利润增长率"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'consensus_growth' not in daily.columns:
            return pd.Series(dtype=float)
        return daily.groupby('ts_code')['consensus_growth'].last()


# ============== 舆情因子 ==============

class News_Sentiment_Score(BaseFactor):
    """新闻情绪得分 (-1到1)"""
    name = "News_Sentiment_Score"
    category = FactorCategory.SENTIMENT
    factor_type = FactorType.MARKET
    description = "新闻情绪得分,负负面,正正面"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'news_sentiment' not in daily.columns:
            return pd.Series(dtype=float)
        
        recent = daily.groupby('ts_code').tail(5)
        return recent.groupby('ts_code')['news_sentiment'].mean()


class Social_Media_Heat(BaseFactor):
    """社交媒体热度"""
    name = "Social_Media_Heat"
    category = FactorCategory.SENTIMENT
    factor_type = FactorType.MARKET
    description = "社交媒体讨论热度"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'social_heat' not in daily.columns:
            return pd.Series(dtype=float)
        return daily.groupby('ts_code')['social_heat'].last()


class Insider_Buy_Ratio(BaseFactor):
    """高管增持比例"""
    name = "Insider_Buy_Ratio"
    category = FactorCategory.SENTIMENT
    factor_type = FactorType.FUNDAMENTAL
    description = "近1个月高管增持股份占流通股本比例"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'insider_buy' not in daily.columns:
            return pd.Series(dtype=float)
        return daily.groupby('ts_code')['insider_buy'].last()


class Insider_Sell_Ratio(BaseFactor):
    """高管减持比例"""
    name = "Insider_Sell_Ratio"
    category = FactorCategory.SENTIMENT
    factor_type = FactorType.FUNDAMENTAL
    description = "近1个月高管减持股份占流通股本比例"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'insider_sell' not in daily.columns:
            return pd.Series(dtype=float)
        return daily.groupby('ts_code')['insider_sell'].last()


# 导出
__all__ = [
    # 资金流向
    "Northbound_Flow_Ratio",
    "Major_Fund_Flow_5D", "Major_Fund_Flow_10D",
    "Retail_Fund_Flow_5D",
    "Net_Buy_Ratio_Inst",
    # 龙虎榜
    "Dragon_Tiger_Count_1M", "Dragon_Tiger_Buy_1M", "Dragon_Tiger_Sell_1M",
    "Institutional_Holding_Change",
    # 分析师
    "Analyst_Rating", "Target_Price_Upside", "EPS_Change_Ratio", "Consensus_Growth_Rate",
    # 舆情
    "News_Sentiment_Score", "Social_Media_Heat",
    "Insider_Buy_Ratio", "Insider_Sell_Ratio",
]

_register_factors()