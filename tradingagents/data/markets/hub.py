# -*- coding: utf-8 -*-
"""
全市场数据统一入口 - MarketDataHub
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .stock_a import AStockData
from .stock_hk import HKStockData
from .stock_us import USStockData
from .fund import FundData
from .macro import MacroData
from .bond import BondData

logger = logging.getLogger(__name__)


class MarketDataHub:
    """
    全市场数据统一入口
    
    提供统一的接口访问 A股、港股、美股、基金、期货、宏观经济、债券数据
    """
    
    def __init__(self):
        """初始化各市场数据处理器"""
        self.astock = AStockData()
        self.hkstock = HKStockData()
        self.usstock = USStockData()
        self.fund = FundData()
        self.macro = MacroData()
        self.bond = BondData()
        logger.info("MarketDataHub initialized")
    
    # ==================== A股数据 ====================
    
    def get_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq"
    ):
        """
        获取A股日线数据
        
        Args:
            symbol: 股票代码，如 '000001'
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
            adjust: 复权类型 ('qfq' 前复权, 'hfq' 后复权, '' 不复权)
        
        Returns:
            DataFrame: 包含 Open, High, Low, Close, Volume
        """
        return self.astock.get_daily(symbol, start_date, end_date, adjust)
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """获取A股股票基本信息"""
        return self.astock.get_info(symbol)
    
    def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """获取A股实时行情"""
        return self.astock.get_realtime(symbol)
    
    def get_stock_list(self, market: str = "a") -> List[Dict]:
        """获取股票列表"""
        return self.astock.get_list(market)
    
    # ==================== 港股数据 ====================
    
    def get_hk_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ):
        """
        获取港股日线数据
        
        Args:
            symbol: 港股代码，如 '00700' (腾讯控股)
            start_date: 开始日期
            end_date: 结束日期
        """
        return self.hkstock.get_daily(symbol, start_date, end_date)
    
    def get_hk_stock_info(self, symbol: str) -> Dict[str, Any]:
        """获取港股股票基本信息"""
        return self.hkstock.get_info(symbol)
    
    def get_hk_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """获取港股实时行情"""
        return self.hkstock.get_realtime(symbol)
    
    # ==================== 美股数据 ====================
    
    def get_us_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ):
        """
        获取美股日线数据
        
        Args:
            symbol: 美股代码，如 'AAPL', 'MSFT'
            start_date: 开始日期
            end_date: 结束日期
        """
        return self.usstock.get_daily(symbol, start_date, end_date)
    
    def get_us_stock_info(self, symbol: str) -> Dict[str, Any]:
        """获取美股股票基本信息"""
        return self.usstock.get_info(symbol)
    
    def get_us_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """获取美股实时行情"""
        return self.usstock.get_realtime(symbol)
    
    # ==================== 基金数据 ====================
    
    def get_fund_nav(self, fund_code: str, date: Optional[str] = None):
        """
        获取基金净值
        
        Args:
            fund_code: 基金代码
            date: 指定日期，不指定则获取最新
        """
        return self.fund.get_nav(fund_code, date)
    
    def get_fund_list(self, fund_type: str = "all") -> List[Dict]:
        """
        获取基金列表
        
        Args:
            fund_type: 基金类型 ('all', 'stock', 'bond', 'mixed', 'index')
        """
        return self.fund.get_list(fund_type)
    
    def get_fund_holdings(self, fund_code: str, date: Optional[str] = None):
        """获取基金持仓"""
        return self.fund.get_holdings(fund_code, date)
    
    # ==================== 宏观经济数据 ====================
    
    def get_macro_data(
        self,
        data_type: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """
        获取宏观经济数据
        
        Args:
            data_type: 数据类型 ('gdp', 'cpi', 'pmi', 'm2', 'shibor', 'lpr', '社融', '信贷')
            start_date: 开始日期
            end_date: 结束日期
        """
        return self.macro.get_data(data_type, start_date, end_date)
    
    def get_gdp(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """获取GDP数据"""
        return self.macro.get_gdp(start_date, end_date)
    
    def get_cpi(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """获取CPI数据"""
        return self.macro.get_cpi(start_date, end_date)
    
    def get_pmi(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """获取PMI数据"""
        return self.macro.get_pmi(start_date, end_date)
    
    # ==================== 债券数据 ====================
    
    def get_bond_data(
        self,
        bond_type: str = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """
        获取债券数据
        
        Args:
            bond_type: 债券类型 ('all', '可转债', '国债', '企业债')
            start_date: 开始日期
            end_date: 结束日期
        """
        return self.bond.get_data(bond_type, start_date, end_date)
    
    def get_cb_list(self):
        """获取可转债列表"""
        return self.bond.get_cb_list()
    
    def get_treasury_yield(self):
        """获取国债收益率"""
        return self.bond.get_treasury_yield()