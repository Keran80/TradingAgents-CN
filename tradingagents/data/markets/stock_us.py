# -*- coding: utf-8 -*-
"""
美股数据模块
"""

import akshare as ak
import pandas as pd
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class USStockData:
    """美股数据处理器"""
    
    def __init__(self):
        self.cache: Dict[str, Any] = {}
    
    def get_daily(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        获取美股日线数据
        
        Args:
            symbol: 美股代码，如 'AAPL'
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
        """
        try:
            # 转换日期格式
            start_str = start_date.replace('-', '')
            end_str = end_date.replace('-', '')
            
            df = ak.stock_us_daily(symbol=symbol, adjust="qfq")
            
            if df.empty:
                return df
            
            # 筛选日期范围
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            
            # 标准化列名
            df = df.rename(columns={
                'date': 'Date',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume',
            })
            
            df = df.set_index('Date')
            df['Adj Close'] = df['Close']
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            logger.error(f"获取美股日线数据失败: {symbol}, {e}")
            return pd.DataFrame()
    
    def get_info(self, symbol: str) -> Dict[str, Any]:
        """获取美股基本信息"""
        try:
            # 美股基本信息接口
            df = ak.stock_us_spot_em()
            
            # 筛选目标股票
            row = df[df['代码'] == symbol]
            
            if row.empty:
                return {}
            
            row = row.iloc[0]
            return {
                'symbol': symbol,
                'name': row.get('名称', ''),
                'price': row.get('最新价', 0),
                'change': row.get('涨跌幅', 0),
                'volume': row.get('成交量', 0),
                'market_cap': row.get('市值', ''),
                'pe': row.get('市盈率', 0),
            }
            
        except Exception as e:
            logger.error(f"获取美股信息失败: {symbol}, {e}")
            return {}
    
    def get_realtime(self, symbol: str) -> Dict[str, Any]:
        """获取美股实时行情"""
        try:
            df = ak.stock_us_spot_em()
            
            row = df[df['代码'] == symbol]
            
            if row.empty:
                return {}
            
            row = row.iloc[0]
            return {
                'symbol': symbol,
                'name': row.get('名称', ''),
                'price': row.get('最新价', 0),
                'change': row.get('涨跌幅', 0),
                'change_amount': row.get('涨跌额', 0),
                'volume': row.get('成交量', 0),
                'high': row.get('最高', 0),
                'low': row.get('最低', 0),
                'open': row.get('今开', 0),
                'close': row.get('昨收', 0),
            }
            
        except Exception as e:
            logger.error(f"获取美股实时行情失败: {symbol}, {e}")
            return {}
    
    def get_spot_list(self) -> List[Dict]:
        """获取美股实时行情列表"""
        try:
            df = ak.stock_us_spot_em()
            return df.to_dict('records') if not df.empty else []
        except Exception as e:
            logger.error(f"获取美股列表失败: {e}")
            return []
    
    def get_us_stock_name(self, symbol: str) -> Optional[str]:
        """获取美股名称"""
        try:
            df = ak.stock_us_spot_em()
            row = df[df['代码'] == symbol]
            if not row.empty:
                return row.iloc[0].get('名称', '')
            return None
        except Exception as e:
            logger.error(f"获取美股名称失败: {symbol}, {e}")
            return None
    
    def get_kline(self, symbol: str, period: str = "daily") -> pd.DataFrame:
        """获取美股K线数据"""
        return self.get_daily(symbol, "1900-01-01", "2030-12-31")