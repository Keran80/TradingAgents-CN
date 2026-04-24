# -*- coding: utf-8 -*-
"""
宏观经济数据模块
"""

import akshare as ak
import pandas as pd
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MacroData:
    """宏观经济数据处理器"""
    
    def __init__(self):
        self.cache: Dict[str, Any] = {}
    
    def get_data(
        self,
        data_type: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取宏观经济数据
        
        Args:
            data_type: 数据类型 ('gdp', 'cpi', 'pmi', 'm2', 'shibor', 'lpr', '社融', '信贷')
        
        Returns:
            DataFrame: 宏观经济数据
        """
        data_type = data_type.lower()
        
        if data_type == "gdp":
            return self.get_gdp()
        elif data_type == "cpi":
            return self.get_cpi()
        elif data_type == "pmi":
            return self.get_pmi()
        elif data_type == "m2":
            return self.get_m2()
        elif data_type == "shibor":
            return self.get_shibor()
        elif data_type == "lpr":
            return self.get_lpr()
        elif data_type in ["社融", "social_finance"]:
            return self.get_social_finance()
        elif data_type in ["信贷", "credit"]:
            return self.get_credit()
        else:
            logger.warning(f"不支持的数据类型: {data_type}")
            return pd.DataFrame()
    
    def get_gdp(self) -> pd.DataFrame:
        """获取GDP数据"""
        try:
            # 尝试多种GDP接口
            try:
                df = ak.gdp_china()
            except Exception:
                df = ak.macro_china_gdp()
            return df
        except Exception as e:
            logger.error(f"获取GDP数据失败: {e}")
            return pd.DataFrame()
    
    def get_cpi(self) -> pd.DataFrame:
        """获取CPI数据"""
        try:
            try:
                df = ak.cpi_china()
            except Exception:
                df = ak.macro_china_cpi()
            return df
        except Exception as e:
            logger.error(f"获取CPI数据失败: {e}")
            return pd.DataFrame()
    
    def get_pmi(self) -> pd.DataFrame:
        """获取PMI数据"""
        try:
            try:
                df = ak.pmi_china()
            except Exception:
                df = ak.macro_china_pmi()
            return df
        except Exception as e:
            logger.error(f"获取PMI数据失败: {e}")
            return pd.DataFrame()
    
    def get_m2(self) -> pd.DataFrame:
        """获取M2货币供应量数据"""
        try:
            try:
                df = ak.m2_china()
            except Exception:
                df = ak.macro_china_m2()
            return df
        except Exception as e:
            logger.error(f"获取M2数据失败: {e}")
            return pd.DataFrame()
    
    def get_shibor(self) -> pd.DataFrame:
        """获取Shibor利率数据"""
        try:
            df = ak.macro_china_shibor_all()
            return df
        except Exception as e:
            logger.error(f"获取Shibor数据失败: {e}")
            return pd.DataFrame()
    
    def get_lpr(self) -> pd.DataFrame:
        """获取LPR利率数据"""
        try:
            df = ak.macro_china_lpr()
            return df
        except Exception as e:
            logger.error(f"获取LPR数据失败: {e}")
            return pd.DataFrame()
    
    def get_social_finance(self) -> pd.DataFrame:
        """获取社融数据"""
        try:
            # 社融数据
            df = pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"获取社融数据失败: {e}")
            return pd.DataFrame()
    
    def get_credit(self) -> pd.DataFrame:
        """获取信贷数据"""
        try:
            # 信贷数据
            df = pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"获取信贷数据失败: {e}")
            return pd.DataFrame()
    
    def get_trading_economics(self) -> pd.DataFrame:
        """获取Trading Economics数据"""
        try:
            df = pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"获取Trading Economics数据失败: {e}")
            return pd.DataFrame()
    
    def get_import_export(self) -> pd.DataFrame:
        """获取进出口数据"""
        try:
            df = pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"获取进出口数据失败: {e}")
            return pd.DataFrame()
    
    def get_freight_index(self) -> pd.DataFrame:
        """获取货运指数"""
        try:
            df = pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"获取货运指数失败: {e}")
            return pd.DataFrame()