# -*- coding: utf-8 -*-
"""
TradingAgents-CN - Quality Factors
质量因子模块

包含：
- 盈利能力 (ROE/ROA/毛利率)
- 运营效率 (资产周转率)
- 财务结构 (资产负债率)
- 现金流质量
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
    
    # 盈利能力
    FactorRegistry.register(ROE)
    FactorRegistry.register(ROA)
    FactorRegistry.register(ROIC)
    FactorRegistry.register(Gross_Margin)
    FactorRegistry.register(Net_Margin)
    FactorRegistry.register(Operating_Margin)
    FactorRegistry.register(EBITDA_Margin)
    
    # 运营效率
    FactorRegistry.register(Asset_Turnover)
    FactorRegistry.register(Inventory_Turnover)
    FactorRegistry.register(Receivables_Turnover)
    FactorRegistry.register(Working_Capital_Turnover)
    
    # 财务结构
    FactorRegistry.register(Debt_to_Asset)
    FactorRegistry.register(Debt_to_Equity)
    FactorRegistry.register(Current_Ratio)
    FactorRegistry.register(Quick_Ratio)
    FactorRegistry.register(Equity_To_Asset)
    
    # 现金流
    FactorRegistry.register(OCF_to_Revenue)
    FactorRegistry.register(OCF_to_NetProfit)
    FactorRegistry.register(FCF_to_OCF)
    
    _registry_registered = True


# ============== 盈利能力因子 ==============

class ROE(BaseFactor):
    """净资产收益率 (Return on Equity)"""
    name = "ROE"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "净资产收益率,衡量股东权益回报"
    formula = "ROE = Net_Profit / Average_Equity"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None:
            return pd.Series(dtype=float)
        
        if 'net_profit' in financial.columns and 'total_equity' in financial.columns:
            result = financial.groupby('ts_code').apply(
                lambda x: x['net_profit'].sum() / x['total_equity'].mean() if x['total_equity'].mean() != 0 else np.nan
            )
            return result
        return pd.Series(dtype=float)


class ROA(BaseFactor):
    """总资产收益率 (Return on Assets)"""
    name = "ROA"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "总资产收益率,衡量资产利用效率"
    formula = "ROA = Net_Profit / Average_Total_Assets"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None:
            return pd.Series(dtype=float)
        
        if 'net_profit' in financial.columns and 'total_assets' in financial.columns:
            return financial.groupby('ts_code').apply(
                lambda x: x['net_profit'].sum() / x['total_assets'].mean() if x['total_assets'].mean() != 0 else np.nan
            )
        return pd.Series(dtype=float)


class ROIC(BaseFactor):
    """投资资本回报率 (Return on Invested Capital)"""
    name = "ROIC"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "投资资本回报率"
    formula = "ROIC = EBIT / (Equity + Debt)"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None:
            return pd.Series(dtype=float)
        
        if 'ebit' in financial.columns and 'total_equity' in financial.columns and 'total_liabilities' in financial.columns:
            return financial.groupby('ts_code').apply(
                lambda x: x['ebit'].sum() / (x['total_equity'].mean() + x['total_liabilities'].mean()) if (x['total_equity'].mean() + x['total_liabilities'].mean()) != 0 else np.nan
            )
        return pd.Series(dtype=float)


class Gross_Margin(BaseFactor):
    """毛利率"""
    name = "Gross_Margin"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "毛利率,衡量产品盈利能力"
    formula = "Gross_Margin = (Revenue - COGS) / Revenue"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'gross_profit' not in financial.columns or 'revenue' not in financial.columns:
            return pd.Series(dtype=float)
        
        return financial.groupby('ts_code').apply(
            lambda x: x['gross_profit'].sum() / x['revenue'].sum() if x['revenue'].sum() != 0 else np.nan
        )


class Net_Margin(BaseFactor):
    """净利率"""
    name = "Net_Margin"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "净利润率"
    formula = "Net_Margin = Net_Profit / Revenue"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'net_profit' not in financial.columns or 'revenue' not in financial.columns:
            return pd.Series(dtype=float)
        
        return financial.groupby('ts_code').apply(
            lambda x: x['net_profit'].sum() / x['revenue'].sum() if x['revenue'].sum() != 0 else np.nan
        )


class Operating_Margin(BaseFactor):
    """营业利润率"""
    name = "Operating_Margin"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "营业利润率"
    formula = "Operating_Margin = Operating_Profit / Revenue"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'operating_profit' not in financial.columns or 'revenue' not in financial.columns:
            return pd.Series(dtype=float)
        
        return financial.groupby('ts_code').apply(
            lambda x: x['operating_profit'].sum() / x['revenue'].sum() if x['revenue'].sum() != 0 else np.nan
        )


class EBITDA_Margin(BaseFactor):
    """EBITDA利润率"""
    name = "EBITDA_Margin"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "EBITDA利润率"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'ebitda' not in financial.columns or 'revenue' not in financial.columns:
            return pd.Series(dtype=float)
        
        return financial.groupby('ts_code').apply(
            lambda x: x['ebitda'].sum() / x['revenue'].sum() if x['revenue'].sum() != 0 else np.nan
        )


# ============== 运营效率因子 ==============

class Asset_Turnover(BaseFactor):
    """资产周转率"""
    name = "Asset_Turnover"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "总资产周转率"
    formula = "Asset_Turnover = Revenue / Average_Assets"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'revenue' not in financial.columns or 'total_assets' not in financial.columns:
            return pd.Series(dtype=float)
        
        return financial.groupby('ts_code').apply(
            lambda x: x['revenue'].sum() / x['total_assets'].mean() if x['total_assets'].mean() != 0 else np.nan
        )


class Inventory_Turnover(BaseFactor):
    """存货周转率"""
    name = "Inventory_Turnover"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "存货周转率"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'cost_of_goods' not in financial.columns or 'inventory' not in financial.columns:
            return pd.Series(dtype=float)
        
        return financial.groupby('ts_code').apply(
            lambda x: x['cost_of_goods'].sum() / x['inventory'].mean() if x['inventory'].mean() != 0 else np.nan
        )


class Receivables_Turnover(BaseFactor):
    """应收账款周转率"""
    name = "Receivables_Turnover"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "应收账款周转率"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'revenue' not in financial.columns or 'accounts_receivable' not in financial.columns:
            return pd.Series(dtype=float)
        
        return financial.groupby('ts_code').apply(
            lambda x: x['revenue'].sum() / x['accounts_receivable'].mean() if x['accounts_receivable'].mean() != 0 else np.nan
        )


class Working_Capital_Turnover(BaseFactor):
    """营运资本周转率"""
    name = "Working_Capital_Turnover"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "营运资本周转率"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'revenue' not in financial.columns or 'working_capital' not in financial.columns:
            return pd.Series(dtype=float)
        
        return financial.groupby('ts_code').apply(
            lambda x: x['revenue'].sum() / x['working_capital'].mean() if x['working_capital'].mean() != 0 else np.nan
        )


# ============== 财务结构因子 ==============

class Debt_to_Asset(BaseFactor):
    """资产负债率"""
    name = "Debt_to_Asset"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "资产负债率,衡量财务杠杆"
    formula = "Debt_to_Asset = Total_Liabilities / Total_Assets"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'total_liabilities' not in financial.columns or 'total_assets' not in financial.columns:
            return pd.Series(dtype=float)
        
        return financial.groupby('ts_code').apply(
            lambda x: x['total_liabilities'].sum() / x['total_assets'].sum() if x['total_assets'].sum() != 0 else np.nan
        )


class Debt_to_Equity(BaseFactor):
    """产权比率 (Debt to Equity)"""
    name = "Debt_to_Equity"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "产权比率"
    formula = "D_E = Total_Liabilities / Total_Equity"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'total_liabilities' not in financial.columns or 'total_equity' not in financial.columns:
            return pd.Series(dtype=float)
        
        return financial.groupby('ts_code').apply(
            lambda x: x['total_liabilities'].sum() / x['total_equity'].sum() if x['total_equity'].sum() != 0 else np.nan
        )


class Current_Ratio(BaseFactor):
    """流动比率"""
    name = "Current_Ratio"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "流动比率,衡量短期偿债能力"
    formula = "Current_Ratio = Current_Assets / Current_Liabilities"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'current_assets' not in financial.columns or 'current_liabilities' not in financial.columns:
            return pd.Series(dtype=float)
        
        return financial.groupby('ts_code').apply(
            lambda x: x['current_assets'].last() / x['current_liabilities'].last() if x['current_liabilities'].last() != 0 else np.nan
        )


class Quick_Ratio(BaseFactor):
    """速动比率"""
    name = "Quick_Ratio"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "速动比率,剔除存货后的短期偿债能力"
    formula = "Quick_Ratio = (Current_Assets - Inventory) / Current_Liabilities"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'current_assets' not in financial.columns or 'inventory' not in financial.columns or 'current_liabilities' not in financial.columns:
            return pd.Series(dtype=float)
        
        return financial.groupby('ts_code').apply(
            lambda x: (x['current_assets'].last() - x['inventory'].last()) / x['current_liabilities'].last() if x['current_liabilities'].last() != 0 else np.nan
        )


class Equity_To_Asset(BaseFactor):
    """净资产占比"""
    name = "Equity_To_Asset"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "净资产占总资产比例"
    formula = "Equity_to_Asset = Total_Equity / Total_Assets"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'total_equity' not in financial.columns or 'total_assets' not in financial.columns:
            return pd.Series(dtype=float)
        
        return financial.groupby('ts_code').apply(
            lambda x: x['total_equity'].sum() / x['total_assets'].sum() if x['total_assets'].sum() != 0 else np.nan
        )


# ============== 现金流因子 ==============

class OCF_to_Revenue(BaseFactor):
    """经营现金流/营收"""
    name = "OCF_to_Revenue"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "经营现金流占营业收入比例"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'operating_cf' not in financial.columns or 'revenue' not in financial.columns:
            return pd.Series(dtype=float)
        
        return financial.groupby('ts_code').apply(
            lambda x: x['operating_cf'].sum() / x['revenue'].sum() if x['revenue'].sum() != 0 else np.nan
        )


class OCF_to_NetProfit(BaseFactor):
    """经营现金流/净利润"""
    name = "OCF_to_NetProfit"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "经营现金流占净利润比例,衡量盈利质量"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'operating_cf' not in financial.columns or 'net_profit' not in financial.columns:
            return pd.Series(dtype=float)
        
        return financial.groupby('ts_code').apply(
            lambda x: x['operating_cf'].sum() / x['net_profit'].sum() if x['net_profit'].sum() != 0 else np.nan
        )


class FCF_to_OCF(BaseFactor):
    """自由现金流/经营现金流"""
    name = "FCF_to_OCF"
    category = FactorCategory.QUALITY
    factor_type = FactorType.FUNDAMENTAL
    description = "自由现金流占经营现金流比例"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'free_cf' not in financial.columns or 'operating_cf' not in financial.columns:
            return pd.Series(dtype=float)
        
        return financial.groupby('ts_code').apply(
            lambda x: x['free_cf'].sum() / x['operating_cf'].sum() if x['operating_cf'].sum() != 0 else np.nan
        )


# 导出
__all__ = [
    # 盈利能力
    "ROE", "ROA", "ROIC",
    "Gross_Margin", "Net_Margin", "Operating_Margin", "EBITDA_Margin",
    # 运营效率
    "Asset_Turnover", "Inventory_Turnover", "Receivables_Turnover", "Working_Capital_Turnover",
    # 财务结构
    "Debt_to_Asset", "Debt_to_Equity", "Current_Ratio", "Quick_Ratio", "Equity_To_Asset",
    # 现金流
    "OCF_to_Revenue", "OCF_to_NetProfit", "FCF_to_OCF",
]

_register_factors()