# -*- coding: utf-8 -*-
"""
A股技术分析指标计算模块
用于替代 stockstats_utils
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# 中文列名到英文列名的映射
CHINESE_TO_ENGLISH = {
    '日期': 'date',
    '股票代码': 'ts_code',
    '股票简称': 'name',
    '开盘': 'open',
    '收盘': 'close',
    '最高': 'high',
    '最低': 'low',
    '成交量': 'volume',
    '成交额': 'amount',
    '振幅': 'amplitude',
    '涨跌幅': 'pct_change',
    '涨跌额': 'change',
    '换手率': 'turnover',
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    将中文列名转换为英文列名
    
    Args:
        df: 包含中文列名的DataFrame
        
    Returns:
        列名已转换的DataFrame
    """
    if df.empty:
        return df
    
    # 创建副本避免修改原数据
    result = df.copy()
    
    # 重命名列
    rename_map = {}
    for col in result.columns:
        if col in CHINESE_TO_ENGLISH:
            rename_map[col] = CHINESE_TO_ENGLISH[col]
    
    if rename_map:
        result = result.rename(columns=rename_map)
    
    return result


class AStockTechnical:
    """A股技术指标计算类"""
    
    @staticmethod
    def calculate_ma(df: pd.DataFrame, periods: list = [5, 10, 20, 30, 60, 120, 250]) -> pd.DataFrame:
        """
        计算移动平均线
        
        Args:
            df: 包含收盘价的DataFrame，需要有 'close' 列
            periods: 周期列表
        
        Returns:
            添加了MA列的DataFrame
        """
        result = df.copy()
        
        for period in periods:
            result[f'ma{period}'] = result['close'].rolling(window=period).mean()
        
        return result
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, periods: list = [12, 26]) -> pd.DataFrame:
        """计算指数移动平均线"""
        result = df.copy()
        
        for period in periods:
            result[f'ema{period}'] = result['close'].ewm(span=period, adjust=False).mean()
        
        return result
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, 
                       signal: int = 9) -> pd.DataFrame:
        """
        计算MACD指标
        
        Returns:
            添加了 macd, macds, macdh 列的DataFrame
        """
        result = df.copy()
        
        # 计算EMA
        ema_fast = result['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = result['close'].ewm(span=slow, adjust=False).mean()
        
        # MACD线
        result['macd'] = ema_fast - ema_slow
        
        # Signal线
        result['macds'] = result['macd'].ewm(span=signal, adjust=False).mean()
        
        # 柱状图
        result['macdh'] = (result['macd'] - result['macds']) * 2
        
        return result
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, periods: list = [6, 12, 24]) -> pd.DataFrame:
        """
        计算RSI指标
        
        Args:
            periods: RSI周期列表
        
        Returns:
            添加了RSI列的DataFrame
        """
        result = df.copy()
        
        for period in periods:
            delta = result['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            result[f'rsi{period}'] = 100 - (100 / (1 + rs))
        
        # 默认RSI(14)
        delta = result['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        result['rsi'] = 100 - (100 / (1 + rs))
        
        return result
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, 
                                  period: int = 20, 
                                  std_dev: float = 2.0) -> pd.DataFrame:
        """计算布林带"""
        result = df.copy()
        
        result['boll_mid'] = result['close'].rolling(window=period).mean()
        std = result['close'].rolling(window=period).std()
        result['boll_upper'] = result['boll_mid'] + (std * std_dev)
        result['boll_lower'] = result['boll_mid'] - (std * std_dev)
        
        return result
    
    @staticmethod
    def calculate_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
        """计算KDJ指标"""
        result = df.copy()
        
        low_n = result['low'].rolling(window=n).min()
        high_n = result['high'].rolling(window=n).max()
        
        rsv = (result['close'] - low_n) / (high_n - low_n) * 100
        rsv = rsv.fillna(50)
        
        result['kdj_k'] = rsv.ewm(com=m1-1, adjust=False).mean()
        result['kdj_d'] = result['kdj_k'].ewm(com=m2-1, adjust=False).mean()
        result['kdj_j'] = 3 * result['kdj_k'] - 2 * result['kdj_d']
        
        return result
    
    @staticmethod
    def calculate_bias(df: pd.DataFrame, periods: list = [5, 10, 30]) -> pd.DataFrame:
        """计算乖离率"""
        result = df.copy()
        
        for period in periods:
            ma = result['close'].rolling(window=period).mean()
            result[f'bias{period}'] = (result['close'] - ma) / ma * 100
        
        return result
    
    @staticmethod
    def calculate_cci(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算CCI指标"""
        result = df.copy()
        
        tp = (result['high'] + result['low'] + result['close']) / 3
        sma = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
        
        result['cci'] = (tp - sma) / (0.015 * mad)
        
        return result
    
    @staticmethod
    def calculate_wr(df: pd.DataFrame, periods: list = [6, 10]) -> pd.DataFrame:
        """计算威廉指标"""
        result = df.copy()
        
        for period in periods:
            high_n = result['high'].rolling(window=period).max()
            low_n = result['low'].rolling(window=period).min()
            result[f'wr{period}'] = (high_n - result['close']) / (high_n - low_n) * 100
        
        return result
    
    @staticmethod
    def calculate_obv(df: pd.DataFrame) -> pd.DataFrame:
        """计算OBV能量潮"""
        result = df.copy()
        
        result['obv'] = (np.sign(result['close'].diff()) * result['volume']).fillna(0).cumsum()
        
        return result
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算ATR真实波幅"""
        result = df.copy()
        
        high_low = result['high'] - result['low']
        high_close = np.abs(result['high'] - result['close'].shift())
        low_close = np.abs(result['low'] - result['close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        result['atr'] = tr.rolling(window=period).mean()
        
        return result
    
    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        """计算所有常用技术指标"""
        result = df.copy()
        
        # 均线
        result = AStockTechnical.calculate_ma(result)
        
        # MACD
        result = AStockTechnical.calculate_macd(result)
        
        # RSI
        result = AStockTechnical.calculate_rsi(result)
        
        # 布林带
        result = AStockTechnical.calculate_bollinger_bands(result)
        
        # KDJ
        result = AStockTechnical.calculate_kdj(result)
        
        # ATR
        result = AStockTechnical.calculate_atr(result)
        
        return result
    
    @staticmethod
    def get_latest_indicators(df: pd.DataFrame) -> Dict:
        """获取最新技术指标值"""
        if df.empty or len(df) < 2:
            return {}
        
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        indicators = {}
        
        # 均线
        for col in ['ma5', 'ma10', 'ma20', 'ma30', 'ma60']:
            if col in df.columns:
                indicators[col] = round(latest[col], 2) if pd.notna(latest[col]) else None
        
        # MACD
        if 'macd' in df.columns:
            indicators['macd'] = round(latest['macd'], 4) if pd.notna(latest['macd']) else None
            indicators['macds'] = round(latest['macds'], 4) if pd.notna(latest['macds']) else None
            indicators['macdh'] = round(latest['macdh'], 4) if pd.notna(latest['macdh']) else None
        
        # RSI
        if 'rsi' in df.columns:
            indicators['rsi'] = round(latest['rsi'], 2) if pd.notna(latest['rsi']) else None
        
        # KDJ
        for col in ['kdj_k', 'kdj_d', 'kdj_j']:
            if col in df.columns:
                indicators[col] = round(latest[col], 2) if pd.notna(latest[col]) else None
        
        # 布林带
        for col in ['boll_upper', 'boll_mid', 'boll_lower']:
            if col in df.columns:
                indicators[col] = round(latest[col], 2) if pd.notna(latest[col]) else None
        
        # 收盘价和成交量
        indicators['close'] = round(latest['close'], 2) if pd.notna(latest['close']) else None
        indicators['volume'] = int(latest['volume']) if pd.notna(latest.get('volume')) else None
        
        return indicators


def get_stock_technical_indicators(ticker: str, period: str = "daily",
                                    days: int = 60) -> Dict:
    """
    获取股票技术指标
    
    Args:
        ticker: 股票代码
        period: 周期 'daily'/'weekly'/'monthly'
        days: 获取天数
    
    Returns:
        Dict: 技术指标数据
    """
    from .astock_utils import AStockData
    
    # 计算日期范围
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
    
    # 获取日线数据
    df = AStockData.get_daily(ticker, start_date, end_date)
    
    if df.empty:
        return {'error': f'无法获取 {ticker} 的数据'}
    
    # 转换列名：中文 -> 英文
    df = normalize_columns(df)
    
    # 计算技术指标
    df = AStockTechnical.calculate_all(df)
    
    # 获取最新值
    latest = AStockTechnical.get_latest_indicators(df)
    
    # 添加基本信息
    latest['ticker'] = ticker
    # 支持中英文列名
    latest['name'] = df.iloc[-1].get('name', df.iloc[-1].get('股票简称', ticker))
    latest['date'] = df.iloc[-1].get('date', df.iloc[-1].get('日期', datetime.now().strftime('%Y-%m-%d')))
    
    return latest


# 便捷函数
def get_stockstats_indicator(ticker: str, indicator: str, 
                              curr_date: str, online: bool = True) -> str:
    """获取技术指标（兼容原接口）"""
    from .astock_utils import AStockData
    
    # 计算日期范围
    end_date = curr_date.replace('-', '')
    start_date = (datetime.strptime(curr_date, '%Y-%m-%d') - timedelta(days=60)).strftime('%Y%m%d')
    
    # 获取数据
    df = AStockData.get_daily(ticker, start_date, end_date)
    
    if df.empty:
        return ""
    
    # 转换列名：中文 -> 英文
    df = normalize_columns(df)
    
    # 计算指标
    if indicator == 'rsi':
        df = AStockTechnical.calculate_rsi(df)
        return str(round(df['rsi'].iloc[-1], 2)) if 'rsi' in df.columns else ""
    
    elif indicator in ['macd', 'macds', 'macdh']:
        df = AStockTechnical.calculate_macd(df)
        return str(round(df[indicator].iloc[-1], 4)) if indicator in df.columns else ""
    
    elif 'ma' in indicator:
        period = int(indicator.replace('ma', ''))
        df = AStockTechnical.calculate_ma(df, [period])
        return str(round(df[f'ma{period}'].iloc[-1], 2)) if f'ma{period}' in df.columns else ""
    
    elif indicator == 'boll':
        df = AStockTechnical.calculate_bollinger_bands(df)
        return str(round(df['boll_mid'].iloc[-1], 2)) if 'boll_mid' in df.columns else ""
    
    elif indicator == 'boll_ub':
        df = AStockTechnical.calculate_bollinger_bands(df)
        return str(round(df['boll_upper'].iloc[-1], 2)) if 'boll_upper' in df.columns else ""
    
    elif indicator == 'boll_lb':
        df = AStockTechnical.calculate_bollinger_bands(df)
        return str(round(df['boll_lower'].iloc[-1], 2)) if 'boll_lower' in df.columns else ""
    
    return ""
