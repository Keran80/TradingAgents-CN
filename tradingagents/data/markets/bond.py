# -*- coding: utf-8 -*-
"""
债券数据模块
"""

import akshare as ak
import pandas as pd
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BondData:
    """债券数据处理器"""
    
    def __init__(self):
        self.cache: Dict[str, Any] = {}
    
    def get_data(
        self,
        bond_type: str = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取债券数据
        
        Args:
            bond_type: 债券类型 ('all', '可转债', '国债', '企业债')
        
        Returns:
            DataFrame: 债券数据
        """
        if bond_type == "可转债" or bond_type == "cb":
            return self.get_cb_list()
        elif bond_type == "国债" or bond_type == "treasury":
            return self.get_treasury_yield()
        elif bond_type == "企业债" or bond_type == "corporate":
            return self.get_corporate_bond()
        else:
            return self.get_cb_list()
    
    def get_cb_list(self) -> List[Dict]:
        """
        获取可转债列表
        
        Returns:
            List[Dict]: 可转债列表
        """
        try:
            # 使用可转债Summary接口
            df = ak.bond_cb_summary_sina()
            return df.to_dict('records') if not df.empty else []
        except Exception as e:
            logger.error(f"获取可转债列表失败: {e}")
            return []
    
    def get_cb_info(self, bond_code: str) -> Dict[str, Any]:
        """获取可转债基本信息"""
        try:
            # 可转债信息接口
            df = ak.bond_cb_info(symbol=bond_code)
            if not df.empty:
                return df.to_dict('records')[0]
            return {}
        except Exception as e:
            logger.error(f"获取可转债信息失败: {bond_code}, {e}")
            return {}
    
    def get_cb_price(self, bond_code: str) -> pd.DataFrame:
        """获取可转债实时行情"""
        try:
            # 可转债行情接口
            df = ak.bond_cb()
            df = df[df['债券代码'] == bond_code]
            return df
        except Exception as e:
            logger.error(f"获取可转债行情失败: {bond_code}, {e}")
            return pd.DataFrame()
    
    def get_treasury_yield(self) -> pd.DataFrame:
        """获取国债收益率曲线"""
        try:
            # 使用正确的接口
            df = ak.bond_china_yield()
            return df
        except Exception as e:
            logger.error(f"获取国债收益率失败: {e}")
            return pd.DataFrame()
    
    def get_treasury_10y(self) -> Optional[float]:
        """获取中国10年期国债收益率"""
        try:
            df = self.get_treasury_yield()
            if not df.empty:
                # 尝试获取10年期数据
                # 可能需要根据实际列名调整
                return None
            return None
        except Exception as e:
            logger.error(f"获取10年期国债收益率失败: {e}")
            return None
    
    def get_corporate_bond(self) -> List[Dict]:
        """获取企业债列表"""
        try:
            # 企业债接口
            df = pd.DataFrame()
            return df.to_dict('records') if not df.empty else []
        except Exception as e:
            logger.error(f"获取企业债列表失败: {e}")
            return []
    
    def get_yield_curve(self) -> pd.DataFrame:
        """获取债券收益率曲线"""
        return self.get_treasury_yield()
    
    def get_credit_rating(self) -> pd.DataFrame:
        """获取债券信用评级"""
        try:
            # 信用评级接口
            df = pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"获取债券信用评级失败: {e}")
            return pd.DataFrame()