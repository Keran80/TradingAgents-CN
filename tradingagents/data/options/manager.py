# -*- coding: utf-8 -*-
"""
期权数据管理器

提供期权数据的获取和管理功能
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class OptionType(Enum):
    """期权类型"""
    CALL = "call"      # 认购期权（看涨）
    PUT = "put"        # 认沽期权（看跌）


class ExerciseType(Enum):
    """行权方式"""
    EUROPEAN = "european"  # 欧式
    AMERICAN = "american"  # 美式


class OptionsDataManager:
    """
    期权数据管理器
    
    支持：
    - 期权合约列表
    - 期权链数据
    - 实时行情
    - 历史数据
    """
    
    # 支持的标的
    UNDERLYINGS = {
        "510050.XSHG": {"name": "50ETF", "exchange": "CFFEX"},
        "510300.XSHG": {"name": "300ETF", "exchange": "CFFEX"},
        "159919.XSHE": {"name": "300ETF", "exchange": "CFFEX"},
        "510500.XSHG": {"name": "500ETF", "exchange": "CFFEX"},
        "159915.XSHE": {"name": "创业板ETF", "exchange": "CFFEX"},
        "159919.XSHE": {"name": "300ETF", "exchange": "CFFEX"},
    }
    
    def __init__(self):
        """初始化管理器"""
        self._ak = None
        
    def _ensure_akshare(self):
        """确保 AkShare 已导入"""
        if self._ak is None:
            import akshare as ak
            self._ak = ak
            
    def get_options_chain(
        self,
        underlying: str,
        expiration: Optional[str] = None,
    ) -> List[Dict]:
        """
        获取期权链
        
        Args:
            underlying: 标的代码（如 "510050.XSHG"）
            expiration: 到期日（YYYY-MM-DD），为None则获取所有
            
        Returns:
            期权链列表
        """
        self._ensure_akshare()
        
        try:
            if "50" in underlying or "510050" in underlying:
                df = self._ak.option_daily_50etf()
            elif "300" in underlying or "510300" in underlying or "159919" in underlying:
                df = self._ak.option_daily_hs300()
            else:
                logger.error(f"Unsupported underlying: {underlying}")
                return []
                
            # 转换列名
            df = df.rename(columns={
                '合约代码': 'symbol',
                '标的代码': 'underlying',
                '到期日': 'expiration',
                '行权价': 'strike',
                '合约类型': 'type',
                '前收盘价': 'pre_close',
                '前结算价': 'pre_settlement',
                '开盘价': 'open',
                '最高价': 'high',
                '最低价': 'low',
                '收盘价': 'close',
                '结算价': 'settlement',
                '成交量': 'volume',
                '成交额': 'turnover',
                '持仓量': 'open_interest',
                '行权量': 'exercise_volume',
            })
            
            # 过滤到期日
            if expiration:
                df = df[df['expiration'] == expiration]
                
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Failed to get options chain: {e}")
            return []
            
    def get_option_quote(self, symbol: str) -> Optional[Dict]:
        """
        获取期权实时行情
        
        Args:
            symbol: 期权合约代码
            
        Returns:
            行情数据
        """
        self._ensure_akshare()
        
        try:
            # 解析合约代码
            df = self._ak.option_daily_50etf()
            row = df[df['合约代码'] == symbol]
            
            if not row.empty:
                r = row.iloc[0]
                return {
                    "symbol": symbol,
                    "underlying": r.get('标的代码', ''),
                    "strike": float(r.get('行权价', 0)),
                    "type": r.get('合约类型', ''),
                    "expiration": r.get('到期日', ''),
                    "price": float(r.get('收盘价', 0)),
                    "open": float(r.get('开盘价', 0)),
                    "high": float(r.get('最高价', 0)),
                    "low": float(r.get('最低价', 0)),
                    "settlement": float(r.get('结算价', 0)),
                    "volume": float(r.get('成交量', 0)),
                    "turnover": float(r.get('成交额', 0)),
                    "open_interest": float(r.get('持仓量', 0)),
                    "change": float(r.get('涨跌幅', 0)) if '涨跌幅' in r else 0,
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
        return None
        
    def get_expiration_dates(
        self,
        underlying: str,
    ) -> List[str]:
        """
        获取某标的的所有到期日
        
        Args:
            underlying: 标的代码
            
        Returns:
            到期日列表
        """
        chain = self.get_options_chain(underlying)
        expirations = list(set([opt['expiration'] for opt in chain]))
        return sorted(expirations)
        
    def get_spot_price(self, underlying: str) -> Optional[float]:
        """
        获取标的现货价格
        
        Args:
            underlying: 标的代码
            
        Returns:
            现货价格
        """
        self._ensure_akshare()
        
        try:
            # 去除交易所后缀
            code = underlying.split(".")[0]
            
            df = self._ak.stock_zh_a_spot_em()
            row = df[df['代码'] == code]
            
            if not row.empty:
                return float(row.iloc[0].get('最新价', 0))
        except Exception as e:
            logger.error(f"Failed to get spot price for {underlying}: {e}")
        return None
        
    def get_implied_volatility(
        self,
        option_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: str,
    ) -> Optional[float]:
        """
        计算隐含波动率
        
        使用牛顿法迭代求解
        """
        from .calculator import OptionsCalculator
        
        calc = OptionsCalculator()
        return calc.calc_implied_volatility(
            option_price, S, K, T, r, option_type
        )
