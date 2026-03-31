# -*- coding: utf-8 -*-
"""
A股数据模块
"""

import akshare as ak
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AStockData:
    """A股数据处理器"""
    
    def __init__(self):
        self.cache: Dict[str, Any] = {}
    
    def get_daily(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取A股日线数据
        
        Args:
            symbol: 股票代码，如 '000001'
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
            adjust: 复权类型
        
        Returns:
            DataFrame: 包含 Open, High, Low, Close, Volume
        """
        try:
            # 转换日期格式
            start_str = start_date.replace('-', '')
            end_str = end_date.replace('-', '')
            
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_str,
                end_date=end_str,
                adjust=adjust
            )
            
            if df.empty:
                return df
            
            # 标准化列名
            df = df.rename(columns={
                '日期': 'Date',
                '开盘': 'Open',
                '收盘': 'Close',
                '最高': 'High',
                '最低': 'Low',
                '成交量': 'Volume',
                '成交额': 'Amount',
                '振幅': 'Amplitude',
                '涨跌幅': 'Pct_Change',
                '涨跌额': 'Change',
                '换手率': 'Turnover'
            })
            
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date')
            df['Adj Close'] = df['Close']
            
            return df
            
        except Exception as e:
            logger.error(f"获取A股日线数据失败: {symbol}, {e}")
            return pd.DataFrame()
    
    def get_info(self, symbol: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        try:
            df = ak.stock_individual_info_em(symbol=symbol)
            
            if df.empty:
                return {}
            
            info = {}
            for _, row in df.iterrows():
                info[row['item']] = row['value']
            
            return {
                'symbol': symbol,
                'name': info.get('股票简称', ''),
                'industry': info.get('行业', ''),
                'sector': info.get('行业', ''),
                'total_shares': info.get('总股本', 0),
                'circulating_shares': info.get('流通股', 0),
                'total_market_cap': info.get('总市值', 0),
                'circulating_market_cap': info.get('流通市值', 0),
                'listing_date': info.get('上市时间', ''),
            }
            
        except Exception as e:
            logger.error(f"获取股票信息失败: {symbol}, {e}")
            return {}
    
    def get_realtime(self, symbol: str) -> Dict[str, Any]:
        """获取实时行情"""
        try:
            df = ak.stock_zh_a_spot_em()
            
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
                'amount': row.get('成交额', 0),
                'amplitude': row.get('振幅', 0),
                'high': row.get('最高', 0),
                'low': row.get('最低', 0),
                'open': row.get('今开', 0),
                'close': row.get('昨收', 0),
                'turnover': row.get('换手率', 0),
            }
            
        except Exception as e:
            logger.error(f"获取实时行情失败: {symbol}, {e}")
            return {}
    
    def get_list(self, market: str = "a") -> List[Dict]:
        """
        获取股票列表
        
        Args:
            market: 市场类型 ('a', '科创板', '北交所')
        """
        try:
            df = ak.stock_zh_a_spot_em()
            
            # 过滤市场
            if market == "a":
                pass  # 返回全部
            elif market == "科创板":
                df = df[df['代码'].str.startswith('688')]
            elif market == "北交所":
                df = df[df['代码'].str.startswith('8')]
            
            # 转换为 dict 列表
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    def get_limit_list(self, date: Optional[str] = None) -> List[Dict]:
        """获取涨跌停列表"""
        try:
            if date:
                df = ak.stock_zt_pool_em(date=date)
            else:
                df = ak.stock_zt_pool_em()
            
            return df.to_dict('records') if not df.empty else []
            
        except Exception as e:
            logger.error(f"获取涨跌停列表失败: {e}")
            return []
    
    def get_moneyflow_hsgt(self) -> pd.DataFrame:
        """获取北向资金流向"""
        try:
            df = ak.moneyflow_hsgt()
            return df
        except Exception as e:
            logger.error(f"获取北向资金流向失败: {e}")
            return pd.DataFrame()
    
    def get_top_list(self) -> List[Dict]:
        """获取龙虎榜"""
        try:
            df = ak.top_list()
            return df.to_dict('records') if not df.empty else []
        except Exception as e:
            logger.error(f"获取龙虎榜失败: {e}")
            return []