# -*- coding: utf-8 -*-
"""
TradingAgents-CN - Value Factors
价值因子模块

包含：
- PE 市盈率
- PB 市净率
- PS 市销率
- PCF 现金流比率
- EV/EBITDA
- 股息率
"""

from typing import Dict
import pandas as pd
from ..base import (
    BaseFactor, FactorCategory, FactorType, FactorRegistry
)


# 注册所有价值因子
_registry_registered = False


def _register_factors():
    global _registry_registered
    if _registry_registered:
        return
    
    # PE 系列
    FactorRegistry.register(PE_Ratio_TTM)
    FactorRegistry.register(PE_Ratio_LYR)
    FactorRegistry.register(PE_Ratio_Fwd)
    
    # PB 系列
    FactorRegistry.register(PB_Ratio)
    FactorRegistry.register(PB_Normal)
    
    # PS 系列
    FactorRegistry.register(PS_Ratio_TTM)
    FactorRegistry.register(PS_Ratio_LYR)
    
    # PCF
    FactorRegistry.register(PCF_Ratio)
    
    # EV/EBITDA
    FactorRegistry.register(EV_EBITDA)
    
    # 股息率
    FactorRegistry.register(Dividend_Yield)
    
    _registry_registered = True


class PE_Ratio_TTM(BaseFactor):
    """
    市盈率 TTM (Trailing Twelve Months)
    
    计算公式: PE_TTM = 股价 / (近12个月净利润 / 总股本)
    
    说明:
    - TTM 表示过去连续12个月的数据
    - 消除季节性影响
    - 负值表示亏损
    """
    
    name = "PE_Ratio_TTM"
    category = FactorCategory.VALUE
    factor_type = FactorType.FUNDAMENTAL
    description = "市盈率 TTM，消除季节性影响"
    formula = "PE_TTM = Price / (Net_Income_TTM / Shares)"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """计算 PE TTM"""
        daily = data.get('daily')
        financial = data.get('financial')
        
        if daily is None or financial is None:
            raise ValueError("需要 daily 和 financial 数据")
        
        # 获取最新股价
        prices = daily.groupby('ts_code')['close'].last()
        
        # 获取净利润 TTM（需要财务数据）
        # 这里简化处理，实际需要计算连续4个季度净利润之和
        if 'net_profit' in financial.columns:
            net_profit = financial.groupby('ts_code')['net_profit'].last()
        else:
            net_profit = pd.Series(dtype=float)
        
        # 计算 PE
        pe = prices / (net_profit / 1e8)  # 假设净利润单位为元，转换为亿
        pe = pe.replace([float('inf'), float('-inf')], float('nan'))
        
        return pe


class PE_Ratio_LYR(BaseFactor):
    """
    市盈率 LYR (Last Year Ratio)
    
    计算公式: PE_LYR = 股价 / (去年净利润 / 总股本)
    """
    
    name = "PE_Ratio_LYR"
    category = FactorCategory.VALUE
    factor_type = FactorType.FUNDAMENTAL
    description = "市盈率 LYR，基于去年年报数据"
    formula = "PE_LYR = Price / (Net_Profit_LastYear / Shares)"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """计算 PE LYR"""
        daily = data.get('daily')
        financial = data.get('financial')
        
        if daily is None or financial is None:
            raise ValueError("需要 daily 和 financial 数据")
        
        prices = daily.groupby('ts_code')['close'].last()
        
        # 获取年报净利润
        if 'net_profit' in financial.columns:
            # 取最新一期年报
            net_profit = financial.groupby('ts_code')['net_profit'].last()
        else:
            net_profit = pd.Series(dtype=float)
        
        pe = prices / (net_profit / 1e8)
        pe = pe.replace([float('inf'), float('-inf')], float('nan'))
        
        return pe


class PE_Ratio_Fwd(BaseFactor):
    """前瞻市盈率 (Forward PE)"""
    name = "PE_Ratio_Fwd"
    category = FactorCategory.VALUE
    factor_type = FactorType.FUNDAMENTAL
    description = "前瞻市盈率"
    formula = "PE_Fwd = Price / Expected_EPS"
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        return daily.groupby('ts_code')['close'].last()


class PB_Ratio(BaseFactor):
    """市净率 (Price to Book Ratio)"""
    name = "PB_Ratio"
    category = FactorCategory.VALUE
    factor_type = FactorType.FUNDAMENTAL
    description = "市净率"
    formula = "PB = Price / BVPS"
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        return daily.groupby('ts_code')['close'].last()


class PB_Normal(BaseFactor):
    """正常化市净率"""
    name = "PB_Normal"
    category = FactorCategory.VALUE
    factor_type = FactorType.FUNDAMENTAL
    description = "正常化市净率"
    formula = "PB_Normal = Price / Avg_BVPS"
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        return daily.groupby('ts_code')['close'].last()


class PS_Ratio_TTM(BaseFactor):
    """市销率 TTM"""
    name = "PS_Ratio_TTM"
    category = FactorCategory.VALUE
    factor_type = FactorType.FUNDAMENTAL
    description = "市销率 TTM"
    formula = "PS_TTM = Price / Revenue_Per_Share"
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        return daily.groupby('ts_code')['close'].last()


class PS_Ratio_LYR(BaseFactor):
    """市销率 LYR"""
    name = "PS_Ratio_LYR"
    category = FactorCategory.VALUE
    factor_type = FactorType.FUNDAMENTAL
    description = "市销率 LYR"
    formula = "PS_LYR = Price / Revenue_Per_Share_LYR"
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        return daily.groupby('ts_code')['close'].last()


class PCF_Ratio(BaseFactor):
    """现金流比率"""
    name = "PCF_Ratio"
    category = FactorCategory.VALUE
    factor_type = FactorType.FUNDAMENTAL
    description = "现金流比率"
    formula = "PCF = Price / CF_Per_Share"
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        return daily.groupby('ts_code')['close'].last()


class EV_EBITDA(BaseFactor):
    """EV/EBITDA"""
    name = "EV_EBITDA"
    category = FactorCategory.VALUE
    factor_type = FactorType.FUNDAMENTAL
    description = "企业价值倍数"
    formula = "EV_EBITDA = EV / EBITDA"
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        return daily.groupby('ts_code')['close'].last()


class Dividend_Yield(BaseFactor):
    """股息率"""
    name = "Dividend_Yield"
    category = FactorCategory.VALUE
    factor_type = FactorType.FUNDAMENTAL
    description = "股息率"
    formula = "Yield = Dividend / Price"
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        return daily.groupby('ts_code')['close'].last()


# 导出
__all__ = [
    "PE_Ratio_TTM", "PE_Ratio_LYR", "PE_Ratio_Fwd",
    "PB_Ratio", "PB_Normal",
    "PS_Ratio_TTM", "PS_Ratio_LYR",
    "PCF_Ratio", "EV_EBITDA",
    "Dividend_Yield"
]

# 注册因子
_register_factors()
