# -*- coding: utf-8 -*-
"""
港股数据模块
"""

import akshare as ak
import pandas as pd
from typing import Dict, Any, Optional
import logging
import time

logger = logging.getLogger(__name__)


def retry_on_error(max_attempts=3, delay=1.0):
    """重试装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_attempts - 1:
                        logger.warning(f"尝试 {attempt+1} 失败，重试中...: {e}")
                        time.sleep(delay)
                    else:
                        raise e
        return wrapper
    return decorator


class HKStockData:
    """港股数据处理器"""
    
    def __init__(self):
        self.cache: Dict[str, Any] = {}
    
    def get_daily(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        获取港股日线数据
        
        Args:
            symbol: 港股代码，如 '00700'
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
        """
        try:
            # 使用 stock_hk_hist 获取历史数据
            df = ak.stock_hk_hist(symbol=symbol, period="daily")
            
            if df.empty:
                return df
            
            # 转换日期格式筛选
            df['日期'] = pd.to_datetime(df['日期'])
            df = df[(df['日期'] >= start_date) & (df['日期'] <= end_date)]
            
            # 标准化列名
            df = df.rename(columns={
                '日期': 'Date',
                '开盘': 'Open',
                '收盘': 'Close',
                '最高': 'High',
                '最低': 'Low',
                '成交量': 'Volume',
                '成交额': 'Amount',
            })
            
            df = df.set_index('Date')
            df['Adj Close'] = df['Close']
            
            return df
            
        except Exception as e:
            logger.error(f"获取港股日线数据失败: {symbol}, {e}")
            return pd.DataFrame()
    
    def get_info(self, symbol: str) -> Dict[str, Any]:
        """获取港股基本信息"""
        try:
            # 港股基本信息接口
            df = ak.stock_hk_spot_em()
            
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
            }
            
        except Exception as e:
            logger.error(f"获取港股信息失败: {symbol}, {e}")
            return {}
    
    def get_realtime(self, symbol: str) -> Dict[str, Any]:
        """获取港股实时行情"""
        try:
            df = ak.stock_hk_spot_em()
            
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
                'amount': row.get('成交额', 0),
                'high': row.get('最高', 0),
                'low': row.get('最低', 0),
                'open': row.get('今开', 0),
                'close': row.get('昨收', 0),
                'turnover': row.get('换手率', 0),
            }
            
        except Exception as e:
            logger.error(f"获取港股实时行情失败: {symbol}, {e}")
            return {}
    
    def get_spot_list(self) -> list:
        """获取港股实时行情列表"""
        try:
            df = ak.stock_hk_spot_em()
            return df.to_dict('records') if not df.empty else []
        except Exception as e:
            logger.error(f"获取港股列表失败: {e}")
            return []
    
    def get_hsgt_daily(self) -> pd.DataFrame:
        """获取沪深港通每日数据"""
        try:
            df = ak.stock_hsgt_detail_em()
            return df
        except Exception as e:
            logger.error(f"获取沪深港通数据失败: {e}")
            return pd.DataFrame()
    
    def get_stock_basic(self) -> pd.DataFrame:
        """获取港股基本信息列表"""
        try:
            df = ak.stock_hk_spot_em()
            return df
        except Exception as e:
            logger.error(f"获取港股基本信息失败: {e}")
            return pd.DataFrame()