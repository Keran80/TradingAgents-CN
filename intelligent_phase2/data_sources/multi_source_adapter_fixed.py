#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多数据源适配器
支持从多个数据源获取股票数据
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StockData:
    """股票数据类"""
    symbol: str
    data: pd.DataFrame
    source: str
    fetch_time: datetime
    data_type: str = "daily"  # daily, minute, tick
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'data': self.data.to_dict('records'),
            'source': self.source,
            'fetch_time': self.fetch_time.isoformat(),
            'data_type': self.data_type
        }

class MultiSourceAdapter:
    """多数据源适配器"""
    
    def __init__(self, preferred_source: str = "akshare"):
        """
        初始化适配器
        
        Args:
            preferred_source: 首选数据源
        """
        self.preferred_source = preferred_source
        self.sources = {
            "akshare": self._fetch_from_akshare,
            "tushare": self._fetch_from_tushare,
            "yfinance": self._fetch_from_yfinance,
            "baostock": self._fetch_from_baostock,
            "joinquant": self._fetch_from_joinquant
        }
        
    async def fetch_stock_data(self, symbol: str, start_date: str, end_date: str, 
                              data_type: str = "daily", source: Optional[str] = None) -> StockData:
        """
        获取股票数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            data_type: 数据类型 (daily, minute, tick)
            source: 数据源，如果为None则使用首选数据源
            
        Returns:
            StockData: 股票数据对象
        """
        source = source or self.preferred_source
        
        if source not in self.sources:
            raise ValueError(f"不支持的数据源: {source}")
        
        logger.info(f"从 {source} 获取 {symbol} 数据 ({start_date} 到 {end_date})")
        
        try:
            # 调用对应的数据源方法
            fetch_func = self.sources[source]
            data = await fetch_func(symbol, start_date, end_date, data_type)
            
            # 确保数据有正确的列
            if 'date' in data.columns and 'datetime' not in data.columns:
                data['datetime'] = pd.to_datetime(data['date'].astype(str) + ' ' + data.get('time', '00:00:00').astype(str))
            
            # 设置索引
            if 'datetime' in data.columns:
                data = data.set_index('datetime')
            
            stock_data = StockData(
                symbol=symbol,
                data=data,
                source=source,
                fetch_time=datetime.now(),
                data_type=data_type
            )
            
            logger.info(f"成功获取 {symbol} 数据，共 {len(data)} 条记录")
            return stock_data
            
        except Exception as e:
            logger.error(f"从 {source} 获取 {symbol} 数据失败: {e}")
            raise
    
    async def _fetch_from_akshare(self, symbol: str, start_date: str, end_date: str, data_type: str) -> pd.DataFrame:
        """从 akshare 获取数据"""
        try:
            import akshare as ak
            
            if data_type == "daily":
                # 获取日线数据
                df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
                # 重命名列以标准化
                df = df.rename(columns={
                    '日期': 'date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '振幅': 'amplitude',
                    '涨跌幅': 'pct_change',
                    '涨跌额': 'change',
                    '换手率': 'turnover'
                })
            elif data_type == "minute":
                # 获取分钟数据
                df = ak.stock_zh_a_minute(symbol=symbol, period="1", adjust="qfq")
                df = df.rename(columns={
                    '时间': 'datetime',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount'
                })
            else:
                raise ValueError(f"akshare 不支持的数据类型: {data_type}")
            
            return df
            
        except ImportError:
            logger.warning("akshare 未安装，使用模拟数据")
            return self._generate_mock_data(symbol, start_date, end_date, data_type)
    
    async def _fetch_from_tushare(self, symbol: str, start_date: str, end_date: str, data_type: str) -> pd.DataFrame:
        """从 tushare 获取数据"""
        try:
            import tushare as ts
            
            # 设置 token（需要在环境中配置）
            ts.set_token('your_tushare_token')
            pro = ts.pro_api()
            
            if data_type == "daily":
                df = pro.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
                df = df.rename(columns={
                    'trade_date': 'date',
                    'open': 'open',
                    'close': 'close',
                    'high': 'high',
                    'low': 'low',
                    'vol': 'volume',
                    'amount': 'amount',
                    'pct_chg': 'pct_change'
                })
            else:
                raise ValueError(f"tushare 不支持的数据类型: {data_type}")
            
            return df
            
        except ImportError:
            logger.warning("tushare 未安装，使用模拟数据")
            return self._generate_mock_data(symbol, start_date, end_date, data_type)
    
    async def _fetch_from_yfinance(self, symbol: str, start_date: str, end_date: str, data_type: str) -> pd.DataFrame:
        """从 yfinance 获取数据（主要用于美股）"""
        try:
            import yfinance as yf
            
            # 添加 .SS 或 .SZ 后缀
            if symbol.startswith('6'):
                yf_symbol = symbol + '.SS'
            elif symbol.startswith('0') or symbol.startswith('3'):
                yf_symbol = symbol + '.SZ'
            else:
                yf_symbol = symbol
            
            ticker = yf.Ticker(yf_symbol)
            
            if data_type == "daily":
                df = ticker.history(start=start_date, end=end_date)
                df = df.reset_index()
                df = df.rename(columns={
                    'Date': 'date',
                    'Open': 'open',
                    'Close': 'close',
                    'High': 'high',
                    'Low': 'low',
                    'Volume': 'volume'
                })
            else:
                raise ValueError(f"yfinance 不支持的数据类型: {data_type}")
            
            return df
            
        except ImportError:
            logger.warning("yfinance 未安装，使用模拟数据")
            return self._generate_mock_data(symbol, start_date, end_date, data_type)
    
    async def _fetch_from_baostock(self, symbol: str, start_date: str, end_date: str, data_type: str) -> pd.DataFrame:
        """从 baostock 获取数据"""
        try:
            import baostock as bs
            
            # 登录
            lg = bs.login()
            
            if data_type == "daily":
                # 查询日线数据
                rs = bs.query_history_k_data_plus(
                    symbol,
                    "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                    start_date=start_date, end_date=end_date,
                    frequency="d", adjustflag="3"
                )
                
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                
                df = pd.DataFrame(data_list, columns=rs.fields)
                df = df.rename(columns={
                    'date': 'date',
                    'open': 'open',
                    'close': 'close',
                    'high': 'high',
                    'low': 'low',
                    'volume': 'volume',
                    'amount': 'amount',
                    'pctChg': 'pct_change'
                })
                
                # 登出
                bs.logout()
                
                return df
            else:
                raise ValueError(f"baostock 不支持的数据类型: {data_type}")
            
        except ImportError:
            logger.warning("baostock 未安装，使用模拟数据")
            return self._generate_mock_data(symbol, start_date, end_date, data_type)
    
    async def _fetch_from_joinquant(self, symbol: str, start_date: str, end_date: str, data_type: str) -> pd.DataFrame:
        """从 JoinQuant 获取数据"""
        try:
            import jqdatasdk
            
            # 登录（需要在环境中配置）
            jqdatasdk.auth('your_username', 'your_password')
            
            if data_type == "daily":
                df = jqdatasdk.get_price(symbol, start_date=start_date, end_date=end_date, frequency='daily')
                df = df.reset_index()
                df = df.rename(columns={
                    'index': 'date',
                    'open': 'open',
                    'close': 'close',
                    'high': 'high',
                    'low': 'low',
                    'volume': 'volume',
                    'money': 'amount'
                })
            else:
                raise ValueError(f"JoinQuant 不支持的数据类型: {data_type}")
            
            return df
            
        except ImportError:
            logger.warning("JoinQuant 未安装，使用模拟数据")
            return self._generate_mock_data(symbol, start_date, end_date, data_type)
    
    def _generate_mock_data(self, symbol: str, start_date: str, end_date: str, data_type: str) -> pd.DataFrame:
        """生成模拟数据（当数据源不可用时）"""
        logger.info(f"为 {symbol} 生成模拟数据 ({start_date} 到 {end_date})")
        
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        if data_type == "daily":
            dates = pd.date_range(start=start_dt, end=end_dt, freq='D')
        elif data_type == "minute":
            dates = pd.date_range(start=start_dt, end=end_dt, freq='1min')
        else:
            dates = pd.date_range(start=start_dt, end=end_dt, freq='D')
        
        n = len(dates)
        
        # 生成随机价格数据
        np.random.seed(hash(symbol) % 10000)
        base_price = 100 + np.random.randn() * 20
        
        returns = np.random.randn(n) * 0.02
        prices = base_price * (1 + np.cumsum(returns))
        
        df = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'open': prices * (1 + np.random.randn(n) * 0.005),
            'close': prices,
            'high': prices * (1 + np.abs(np.random.randn(n)) * 0.01),
            'low': prices * (1 - np.abs(np.random.randn(n)) * 0.01),
            'volume': np.random.randint(1000000, 10000000, n),
            'amount': np.random.randint(10000000, 100000000, n),
            'pct_change': returns * 100,
            'symbol': symbol
        })
        
        if data_type == "minute":
            df['time'] = dates.strftime('%H:%M:%S')
            df['datetime'] = dates
        
        return df
    
    async def fetch_multiple_stocks(self, symbols: List[str], start_date: str, end_date: str, 
                                   data_type: str = "daily", source: Optional[str] = None) -> Dict[str, StockData]:
        """
        获取多个股票的数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            data_type: 数据类型
            source: 数据源
            
        Returns:
            Dict[str, StockData]: 股票数据字典
        """
        results = {}
        
        tasks = []
        for symbol in symbols:
            task = self.fetch_stock_data(symbol, start_date, end_date, data_type, source)
            tasks.append(task)
        
        # 并发获取数据
        stock_data_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, data in zip(symbols, stock_data_list):
            if isinstance(data, Exception):
                logger.error(f"获取 {symbol} 数据失败: {data}")
            else:
                results[symbol] = data
        
        return results

# 示例使用
async def main():
    """示例主函数"""
    adapter = MultiSourceAdapter(preferred_source="akshare")
    
    # 获取单个股票数据
    try:
        stock_data = await adapter.fetch_stock_data(
            symbol="000001",
            start_date="2024-01-01",
            end_date="2024-01-31",
            data_type="daily"
        )
        
        print(f"获取到 {stock_data.symbol} 数据:")
        print(f"数据源: {stock_data.source}")
        print(f"数据条数: {len(stock_data.data)}")
        print(f"数据列: {stock_data.data.columns.tolist()}")
        print(f"前5条数据:\n{stock_data.data.head()}")
        
    except Exception as e:
        print(f"获取数据失败: {e}")
    
    # 获取多个股票数据
    try:
        multiple_data = await adapter.fetch_multiple_stocks(
            symbols=["000001", "600519", "300750"],
            start_date="2024-01-01",
            end_date="2024-01-10",
            data_type="daily"
        )
        
        print(f"\n获取到 {len(multiple_data)} 个股票的数据")
        for symbol, data in multiple_data.items():
            print(f"{symbol}: {len(data.data)} 条记录")
            
    except Exception as e:
        print(f"批量获取数据失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())