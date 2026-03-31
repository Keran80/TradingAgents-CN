# -*- coding: utf-8 -*-
"""
AkShare 股票数据接口 - 替代 yfinance
提供与 yfin_utils 类似的功能接口，但使用 AkShare 获取数据
适用于A股市场
"""

import akshare as ak
import pandas as pd
from typing import Annotated, Callable, Any, Optional, List, Dict, Tuple, Union
from datetime import datetime, timedelta
from functools import wraps
import logging
import time
import hashlib
import os

# 导入缓存模块
from .cache import (
    cached, retry, get_cache, set_cache, _generate_cache_key,
    RateLimiter, get_rate_limiter
)

logger = logging.getLogger(__name__)

# 缓存配置
STOCK_DATA_CACHE_TTL = 3600  # 股票数据缓存 1 小时
STOCK_INFO_CACHE_TTL = 300   # 股票信息缓存 5 分钟

# 限流器配置（AkShare 较宽容，设置较高限制）
_stock_rate_limiter = RateLimiter(calls=30, period=60.0)  # 每分钟最多 30 次


def init_akshare_ticker(func: Callable) -> Callable:
    """装饰器：转换股票代码格式"""
    @wraps(func)
    def wrapper(symbol: Annotated[str, "ticker symbol"], *args, **kwargs):
        # 转换股票代码为 AkShare 格式
        akshare_symbol = convert_to_akshare_format(symbol)
        return func(akshare_symbol, *args, **kwargs)
    return wrapper


@init_akshare_ticker
class AkShareUtils:
    """使用 AkShare 获取A股数据的工具类"""

    @staticmethod
    @retry(max_attempts=3, delay=1.0, backoff=2.0)
    def get_stock_data(
        symbol: Annotated[str, "ticker symbol"],
        start_date: Annotated[str, "start date YYYY-mm-dd"],
        end_date: Annotated[str, "end date YYYY-mm-dd"],
        save_path: Optional[str] = None,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        获取股票日线数据（带缓存和重试机制）
        
        Args:
            symbol: 股票代码，如 '000001'
            start_date: 开始日期
            end_date: 结束日期
            save_path: 保存路径（可选）
            use_cache: 是否使用缓存
        
        Returns:
            pd.DataFrame: 包含 Open, High, Low, Close, Volume
        """
        # 生成缓存键
        cache_key = _generate_cache_key("akshare_stock_data", symbol, start_date, end_date)
        
        # 尝试从缓存获取
        if use_cache:
            cached_data = get_cache(cache_key, STOCK_DATA_CACHE_TTL)
            if cached_data is not None:
                logger.debug(f"缓存命中: {symbol} {start_date}-{end_date}")
                if save_path:
                    cached_data.to_csv(save_path)
                return cached_data
        
        try:
            # 限流检查（每分钟最多 30 次 API 调用）
            if not _stock_rate_limiter.wait_and_acquire(f"stock_data_{symbol}", timeout=30.0):
                logger.warning(f"API 请求频率超限: {symbol}")
                raise RuntimeError(f"Rate limit exceeded for stock data: {symbol}")
            
            # 转换日期格式
            start_str = start_date.replace('-', '')
            end_str = end_date.replace('-', '')
            
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_str,
                end_date=end_str,
                adjust="qfq"
            )
            
            if df.empty:
                return df
            
            # 转换为与 yfinance 相同的列名格式
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
            
            # 设置日期索引
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date')
            
            # 添加 Adj Close（与 Close 相同）
            df['Adj Close'] = df['Close']
            
            # 保存到缓存
            if use_cache:
                set_cache(cache_key, df)
            
            if save_path:
                df.to_csv(save_path)
            
            return df
            
        except Exception as e:
            logger.error(f"获取股票数据失败: {e}")
            return pd.DataFrame()

    @staticmethod
    @retry(max_attempts=3, delay=0.5, backoff=2.0)
    def get_stock_info(symbol: Annotated[str, "ticker symbol"], use_cache: bool = True) -> Dict[str, Any]:
        """
        获取股票基本信息（带缓存和重试机制）
        
        Args:
            symbol: 股票代码
            use_cache: 是否使用缓存
        
        Returns:
            Dict[str, Any]: 包含股票基本信息
        """
        # 生成缓存键
        cache_key = _generate_cache_key("akshare_stock_info", symbol)
        
        # 尝试从缓存获取
        if use_cache:
            cached_data = get_cache(cache_key, STOCK_INFO_CACHE_TTL)
            if cached_data is not None:
                logger.debug(f"缓存命中: {symbol} info")
                return cached_data
        
        try:
            # 限流检查
            if not _stock_rate_limiter.wait_and_acquire(f"stock_info_{symbol}", timeout=30.0):
                logger.warning(f"API 请求频率超限: {symbol}")
                raise RuntimeError(f"Rate limit exceeded for stock info: {symbol}")
            
            # 使用单只股票信息接口（更快）
            df = ak.stock_individual_info_em(symbol=symbol)
            
            if df.empty:
                return {}
            
            # 转换为 dict
            info: Dict[str, Any] = {}
            for _, row in df.iterrows():
                info[row['item']] = row['value']
            
            result: Dict[str, Any] = {
                'shortName': info.get('股票简称', ''),
                'industry': info.get('行业', ''),
                'sector': info.get('行业', ''),
                'totalShares': info.get('总股本', 0),
                'circulatingShares': info.get('流通股', 0),
                'totalMarketCap': info.get('总市值', 0),
                'circulatingMarketCap': info.get('流通市值', 0),
                'listingDate': info.get('上市时间', ''),
            }
            
            # 保存到缓存
            if use_cache:
                set_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return {}

    @staticmethod
    def get_company_info(
        symbol: Annotated[str, "ticker symbol"],
        save_path: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取公司信息
        
        Args:
            symbol: 股票代码
            save_path: 保存路径（可选）
        
        Returns:
            DataFrame 包含公司信息
        """
        try:
            info = AkShareUtils.get_stock_info(symbol)
            
            company_info = {
                "Company Name": info.get("shortName", "N/A"),
                "Industry": info.get("industry", "N/A"),
                "Sector": info.get("sector", "N/A"),
                "Market": info.get("market", "N/A"),
            }
            
            company_df = pd.DataFrame([company_info])
            
            if save_path:
                company_df.to_csv(save_path, index=False)
                print(f"Company info for {symbol} saved to {save_path}")
            
            return company_df
            
        except Exception as e:
            logger.error(f"获取公司信息失败: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_stock_dividends(
        symbol: Annotated[str, "ticker symbol"],
        save_path: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取股票分红送转数据
        
        Args:
            symbol: 股票代码
            save_path: 保存路径（可选）
        
        Returns:
            DataFrame 包含分红数据
        """
        try:
            # AkShare 分红数据接口
            df = ak.stock_dividend_flow_em(symbol=symbol)
            
            if df.empty:
                return pd.DataFrame()
            
            if save_path:
                df.to_csv(save_path, index=False)
                print(f"Dividends for {symbol} saved to {save_path}")
            
            return df
            
        except Exception as e:
            logger.error(f"获取分红数据失败: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_income_stmt(symbol: Annotated[str, "ticker symbol"]) -> pd.DataFrame:
        """
        获取利润表数据
        
        Args:
            symbol: 股票代码
        
        Returns:
            DataFrame 包含利润表
        """
        try:
            df = ak.stock_financial_analysis_indicator(symbol=symbol)
            return df
            
        except Exception as e:
            logger.error(f"获取利润表失败: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_balance_sheet(symbol: Annotated[str, "ticker symbol"]) -> pd.DataFrame:
        """
        获取资产负债表数据
        
        Args:
            symbol: 股票代码
        
        Returns:
            DataFrame 包含资产负债表
        """
        try:
            # 使用资产负债表接口
            df = ak.stock_balance_sheet_em(symbol=symbol)
            return df
            
        except Exception as e:
            logger.error(f"获取资产负债表失败: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_cash_flow(symbol: Annotated[str, "ticker symbol"]) -> pd.DataFrame:
        """
        获取现金流量表数据
        
        Args:
            symbol: 股票代码
        
        Returns:
            DataFrame 包含现金流量表
        """
        try:
            df = ak.stock_cash_flow_em(symbol=symbol)
            return df
            
        except Exception as e:
            logger.error(f"获取现金流量表失败: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_analyst_recommendations(symbol: Annotated[str, "ticker symbol"]) -> tuple:
        """
        获取分析师建议
        
        Args:
            symbol: 股票代码
        
        Returns:
            tuple: (推荐评级, 评级数量)
        """
        try:
            # 使用机构评级接口
            df = ak.stock_zh_a_report_rc_em(symbol=symbol)
            
            if df.empty:
                return None, 0
            
            # 获取最新评级
            latest = df.iloc[0]
            recommendation = latest.get('评级类别', 'N/A')
            count = 1
            
            return recommendation, count
            
        except Exception as e:
            logger.error(f"获取分析师建议失败: {e}")
            return None, 0


def convert_to_akshare_format(symbol: str) -> str:
    """
    将股票代码转换为 AkShare 格式
    
    Args:
        symbol: 原始股票代码
    
    Returns:
        str: AkShare 格式的股票代码
    """
    # 如果已经是纯数字格式，直接返回
    if symbol.isdigit():
        return symbol
    
    # 去除可能的后缀（如 .SH, .SZ）
    symbol = symbol.split('.')[0]
    
    return symbol


# 创建便捷函数（替代 yfinance 的调用方式）
def get_stock_data(symbol, start_date, end_date, save_path=None):
    """获取股票日线数据"""
    return AkShareUtils.get_stock_data(symbol, start_date, end_date, save_path)

def get_stock_info(symbol):
    """获取股票信息"""
    return AkShareUtils.get_stock_info(symbol)

def get_company_info(symbol, save_path=None):
    """获取公司信息"""
    return AkShareUtils.get_company_info(symbol, save_path)

def get_stock_dividends(symbol, save_path=None):
    """获取分红数据"""
    return AkShareUtils.get_stock_dividends(symbol, save_path)

def get_income_stmt(symbol):
    """获取利润表"""
    return AkShareUtils.get_income_stmt(symbol)

def get_balance_sheet(symbol):
    """获取资产负债表"""
    return AkShareUtils.get_balance_sheet(symbol)

def get_cash_flow(symbol):
    """获取现金流量表"""
    return AkShareUtils.get_cash_flow(symbol)

def get_analyst_recommendations(symbol):
    """获取分析师建议"""
    return AkShareUtils.get_analyst_recommendations(symbol)

# 创建便捷实例
class _AkShareHelper:
    """便捷调用类"""
    
    def get_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        save_path: Optional[str] = None,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """获取股票日线数据"""
        return AkShareUtils.get_stock_data(symbol, start_date, end_date, save_path, use_cache)
    
    def get_stock_info(self, symbol: str, use_cache: bool = True) -> Dict[str, Any]:
        """获取股票信息"""
        return AkShareUtils.get_stock_info(symbol, use_cache)
    
    def get_company_info(self, symbol: str, save_path: Optional[str] = None) -> pd.DataFrame:
        """获取公司信息"""
        return AkShareUtils.get_company_info(symbol, save_path)
    
    def get_stock_dividends(self, symbol: str, save_path: Optional[str] = None) -> pd.DataFrame:
        """获取分红数据"""
        return AkShareUtils.get_stock_dividends(symbol, save_path)
    
    def get_income_stmt(self, symbol: str) -> pd.DataFrame:
        """获取利润表"""
        return AkShareUtils.get_income_stmt(symbol)
    
    def get_balance_sheet(self, symbol: str) -> pd.DataFrame:
        """获取资产负债表"""
        return AkShareUtils.get_balance_sheet(symbol)
    
    def get_cash_flow(self, symbol: str) -> pd.DataFrame:
        """获取现金流量表"""
        return AkShareUtils.get_cash_flow(symbol)
    
    def get_analyst_recommendations(self, symbol: str) -> Tuple[Optional[str], int]:
        """获取分析师建议"""
        return AkShareUtils.get_analyst_recommendations(symbol)

aks = _AkShareHelper()
