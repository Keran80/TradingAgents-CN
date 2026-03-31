# -*- coding: utf-8 -*-
"""
基金数据模块
"""

import akshare as ak
import pandas as pd
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class FundData:
    """基金数据处理器"""
    
    def __init__(self):
        self.cache: Dict[str, Any] = {}
    
    def get_nav(self, fund_code: str, date: Optional[str] = None) -> pd.DataFrame:
        """
        获取基金净值
        
        Args:
            fund_code: 基金代码，如 '000001'
            date: 指定日期，不指定则获取最新
        
        Returns:
            DataFrame: 包含净值数据
        """
        try:
            # 先获取全部基金列表，然后筛选
            df = ak.fund_open_fund_daily_em()
            
            if df.empty:
                return df
            
            # 筛选指定基金
            df = df[df['基金代码'] == fund_code]
            
            return df
            
        except Exception as e:
            logger.error(f"获取基金净值失败: {fund_code}, {e}")
            return pd.DataFrame()
    
    def get_list(self, fund_type: str = "all") -> List[Dict]:
        """
        获取基金列表
        
        Args:
            fund_type: 基金类型 ('all', 'stock', 'bond', 'mixed', 'index')
        
        Returns:
            List[Dict]: 基金列表
        """
        try:
            # 全部开放式基金列表
            df = ak.fund_open_fund_daily_em()
            
            # 去重获取基金列表
            df = df.drop_duplicates(subset=['基金代码'])
            
            return df.to_dict('records') if not df.empty else []
            
        except Exception as e:
            logger.error(f"获取基金列表失败: {e}")
            return []
    
    def get_holdings(self, fund_code: str, date: Optional[str] = None) -> pd.DataFrame:
        """
        获取基金持仓
        
        Args:
            fund_code: 基金代码
            date: 报告期
        
        Returns:
            DataFrame: 包含持仓明细
        """
        try:
            df = ak.fund_portfolio_em(fund=fund_code)
            return df
            
        except Exception as e:
            logger.error(f"获取基金持仓失败: {fund_code}, {e}")
            return pd.DataFrame()
    
    def get_etf_list(self) -> List[Dict]:
        """获取ETF列表"""
        try:
            df = ak.fund_etf_spot_em()
            return df.to_dict('records') if not df.empty else []
        except Exception as e:
            logger.error(f"获取ETF列表失败: {e}")
            return []
    
    def get_fund_manager(self, fund_code: str) -> pd.DataFrame:
        """获取基金经理信息"""
        try:
            df = ak.fund_manager_sina(fund=fund_code)
            return df
        except Exception as e:
            logger.error(f"获取基金经理信息失败: {fund_code}, {e}")
            return pd.DataFrame()
    
    def get_fund_company(self) -> pd.DataFrame:
        """获取基金公司列表"""
        try:
            df = ak.fund_company_sina()
            return df
        except Exception as e:
            logger.error(f"获取基金公司列表失败: {e}")
            return pd.DataFrame()