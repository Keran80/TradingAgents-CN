# -*- coding: utf-8 -*-
"""
TradingAgents-CN - Growth Factors
成长因子模块

包含：
- 营收增长率
- 利润增长率
- 资产增长率
- 订单增长率
"""

from typing import Dict
import pandas as pd
from ..base import BaseFactor, FactorCategory, FactorType, FactorRegistry


# 注册所有成长因子
_registry_registered = False


def _register_factors():
    global _registry_registered
    if _registry_registered:
        return
    
    FactorRegistry.register(Revenue_Growth_YOY)
    FactorRegistry.register(Profit_Growth_YOY)
    FactorRegistry.register(GrossProfit_Growth_YOY)
    FactorRegistry.register(Asset_Growth_YOY)
    FactorRegistry.register(Equity_Growth_YOY)
    FactorRegistry.register(OCF_Growth_YOY)
    FactorRegistry.register(Order_Growth_YOY)
    FactorRegistry.register(EPS_Growth_YOY)
    FactorRegistry.register(BVPS_Growth_YOY)
    
    _registry_registered = True


class Revenue_Growth_YOY(BaseFactor):
    """营收同比增长率"""
    name = "Revenue_Growth_YOY"
    category = FactorCategory.GROWTH
    factor_type = FactorType.FUNDAMENTAL
    description = "营业收入同比增长率"
    formula = "Revenue_Growth = (Revenue_Current - Revenue_LY) / Revenue_LY"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        financial = data.get('financial')
        
        if financial is None:
            return pd.Series(dtype=float)
        
        if 'revenue' in financial.columns:
            return financial.groupby('ts_code')['revenue'].pct_change(periods=4)
        return pd.Series(dtype=float)


class Profit_Growth_YOY(BaseFactor):
    """净利润同比增长率"""
    name = "Profit_Growth_YOY"
    category = FactorCategory.GROWTH
    factor_type = FactorType.FUNDAMENTAL
    description = "净利润同比增长率"
    formula = "Profit_Growth = (Profit_Current - Profit_LY) / Profit_LY"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'net_profit' not in financial.columns:
            return pd.Series(dtype=float)
        return financial.groupby('ts_code')['net_profit'].pct_change(periods=4)


class GrossProfit_Growth_YOY(BaseFactor):
    """毛利同比增长率"""
    name = "GrossProfit_Growth_YOY"
    category = FactorCategory.GROWTH
    factor_type = FactorType.FUNDAMENTAL
    description = "毛利润同比增长率"
    formula = "GrossProfit_Growth = (GP_Current - GP_LY) / GP_LY"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'gross_profit' not in financial.columns:
            return pd.Series(dtype=float)
        return financial.groupby('ts_code')['gross_profit'].pct_change(periods=4)


class Asset_Growth_YOY(BaseFactor):
    """总资产同比增长率"""
    name = "Asset_Growth_YOY"
    category = FactorCategory.GROWTH
    factor_type = FactorType.FUNDAMENTAL
    description = "总资产同比增长率"
    formula = "Asset_Growth = (Asset_Current - Asset_LY) / Asset_LY"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'total_assets' not in financial.columns:
            return pd.Series(dtype=float)
        return financial.groupby('ts_code')['total_assets'].pct_change(periods=4)


class Equity_Growth_YOY(BaseFactor):
    """净资产同比增长率"""
    name = "Equity_Growth_YOY"
    category = FactorCategory.GROWTH
    factor_type = FactorType.FUNDAMENTAL
    description = "归属于母公司净资产同比增长率"
    formula = "Equity_Growth = (Equity_Current - Equity_LY) / Equity_LY"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'total_equity' not in financial.columns:
            return pd.Series(dtype=float)
        return financial.groupby('ts_code')['total_equity'].pct_change(periods=4)


class OCF_Growth_YOY(BaseFactor):
    """经营现金流同比增长率"""
    name = "OCF_Growth_YOY"
    category = FactorCategory.GROWTH
    factor_type = FactorType.FUNDAMENTAL
    description = "经营活动现金流同比增长率"
    formula = "OCF_Growth = (OCF_Current - OCF_LY) / OCF_LY"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'operating_cf' not in financial.columns:
            return pd.Series(dtype=float)
        return financial.groupby('ts_code')['operating_cf'].pct_change(periods=4)


class Order_Growth_YOY(BaseFactor):
    """订单同比增长率"""
    name = "Order_Growth_YOY"
    category = FactorCategory.GROWTH
    factor_type = FactorType.FUNDAMENTAL
    description = "订单金额同比增长率"
    formula = "Order_Growth = (Order_Current - Order_LY) / Order_LY"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        financial = data.get('financial')
        if financial is None or 'order_revenue' not in financial.columns:
            return pd.Series(dtype=float)
        return financial.groupby('ts_code')['order_revenue'].pct_change(periods=4)


class EPS_Growth_YOY(BaseFactor):
    """EPS同比增长率"""
    name = "EPS_Growth_YOY"
    category = FactorCategory.GROWTH
    factor_type = FactorType.FUNDAMENTAL
    description = "每股收益同比增长率"
    formula = "EPS_Growth = (EPS_Current - EPS_LY) / EPS_LY"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            return pd.Series(dtype=float)
        # 简化：使用收盘价变化作为代理
        return daily.groupby('ts_code')['close'].pct_change(periods=252)


class BVPS_Growth_YOY(BaseFactor):
    """每股净资产同比增长率"""
    name = "BVPS_Growth_YOY"
    category = FactorCategory.GROWTH
    factor_type = FactorType.FUNDAMENTAL
    description = "每股净资产同比增长率"
    formula = "BVPS_Growth = (BVPS_Current - BVPS_LY) / BVPS_LY"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            return pd.Series(dtype=float)
        return daily.groupby('ts_code')['close'].pct_change(periods=252)


# 导出
__all__ = [
    "Revenue_Growth_YOY",
    "Profit_Growth_YOY", 
    "GrossProfit_Growth_YOY",
    "Asset_Growth_YOY",
    "Equity_Growth_YOY",
    "OCF_Growth_YOY",
    "Order_Growth_YOY",
    "EPS_Growth_YOY",
    "BVPS_Growth_YOY",
]

_register_factors()