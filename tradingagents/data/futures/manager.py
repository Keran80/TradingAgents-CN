# -*- coding: utf-8 -*-
"""
期货数据管理器

提供期货数据的获取、解析和管理功能
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import pandas as pd

logger = logging.getLogger(__name__)


class FuturesCategory(Enum):
    """期货分类"""
    # 国内商品期货
    METALS = "metals"           # 金属（铜、铝、锌、镍等）
    ENERGY = "energy"           # 能源（原油、煤炭、天然气）
    CHEMICALS = "chemicals"     # 化工（塑料、PP、PVC、甲醇）
    AGRICULTURE = "agriculture" # 农产品（豆粕、玉米、棉花、白糖）
    BLACK = "black"             # 黑色系（螺纹钢、铁矿石、焦煤焦炭）
    
    # 金融期货
    INDEX = "index"             # 股指期货（IF、IH、IC、IM）
    TREASURY = "treasury"       # 国债期货（TS、TF、T、TL）
    
    # 国际期货
    INTERNATIONAL = "international"  # 国际期货


class FuturesDataManager:
    """
    期货数据管理器
    
    支持：
    - 期货合约列表查询
    - 实时行情获取
    - K线历史数据
    - 持仓/仓单数据
    """
    
    # 主力合约映射
    MAIN_CONTRACT_MAP = {
        "CU": "cu2405",   # 沪铜
        "AL": "al2405",   # 沪铝
        "ZN": "zn2405",   # 沪锌
        "NI": "ni2405",   # 沪镍
        "AU": "au2406",   # 沪金
        "AG": "ag2406",   # 沪银
        "RB": "rb2405",   # 螺纹钢
        "HC": "hc2405",   # 热轧卷板
        "I": "i2405",     # 铁矿石
        "J": "j2405",     # 焦炭
        "JM": "jm2405",   # 焦煤
        "原油": "sc2405", # 原油
        "FU": "fu2405",   # 燃料油
        "RU": "ru2405",   # 橡胶
        "IF": "IF2404",   # 沪深300股指
        "IH": "IH2404",   # 上证50股指
        "IC": "IC2404",   # 中证500股指
        "IM": "IM2404",   # 中证1000股指
    }
    
    def __init__(self):
        """初始化管理器"""
        self._ak = None
        
    def _ensure_akshare(self):
        """确保 AkShare 已导入"""
        if self._ak is None:
            import akshare as ak
            self._ak = ak
            
    def get_contracts(
        self,
        category: str = "futures",
        exchange: Optional[str] = None,
    ) -> List[Dict]:
        """
        获取期货合约列表
        
        Args:
            category: 分类 ("futures", "options", "spot")
            exchange: 交易所代码 (如 "CFFEX", "DCE", "CZCE", "SHFE", "INE")
            
        Returns:
            合约列表
        """
        self._ensure_akshare()
        
        try:
            if category == "futures":
                df = self._ak.futures_zh_contract_sina()
            elif category == "options":
                df = self._ak.option_daily_50etf()
            else:
                df = self._ak.futures_spot供求关系()
                
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Failed to get contracts: {e}")
            return []
            
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """
        获取期货实时行情
        
        Args:
            symbol: 合约代码（如 "IF2404"）
            
        Returns:
            行情数据
        """
        self._ensure_akshare()
        
        try:
            # 去掉后缀获取合约代码
            contract = symbol.replace(".SF", "").replace(".DF", "")
            
            df = self._ak.futures_zh_real_time_sina(symbol=contract)
            
            if not df.empty:
                row = df.iloc[0]
                return {
                    "symbol": symbol,
                    "name": row.get('品种名称', ''),
                    "price": float(row.get('今开', 0)),
                    "open": float(row.get('今开', 0)),
                    "high": float(row.get('最高', 0)),
                    "low": float(row.get('最低', 0)),
                    "volume": float(row.get('成交量', 0)),
                    "turnover": float(row.get('成交额', 0)),
                    "position": float(row.get('持仓量', 0)),
                    "settlement": float(row.get('结算价', 0)),
                    "pre_close": float(row.get('昨收', 0)),
                    "pre_settlement": float(row.get('昨结算', 0)),
                    "change": float(row.get('涨跌额', 0)),
                    "change_pct": float(row.get('涨跌幅', 0)),
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
        return None
        
    def get_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        批量获取期货行情
        
        Args:
            symbols: 合约代码列表
            
        Returns:
            行情字典
        """
        results = {}
        for symbol in symbols:
            quote = self.get_quote(symbol)
            if quote:
                results[symbol] = quote
        return results
        
    def get_bars(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "daily",
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """
        获取期货K线数据
        
        Args:
            symbol: 合约代码（如 "IF2404"）
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            period: 周期 ("daily", "weekly", "monthly", "60min", "30min", "15min", "5min")
            adjust: 复权类型 ("qfq", "hfq", "None")
            
        Returns:
            K线数据 DataFrame
        """
        self._ensure_akshare()
        
        try:
            # 去掉后缀
            contract = symbol.replace(".SF", "").replace(".DF", "")
            
            df = self._ak.futures_zh_daily_sina(
                symbol=contract,
            )
            
            if not df.empty:
                # 标准化列名
                df = df.rename(columns={
                    '品种代码': 'symbol',
                    '品种名称': 'name',
                    '开盘价': 'open',
                    '最高价': 'high',
                    '最低价': 'low',
                    ' '

'收盘价': 'close',
                    '成交量': 'volume',
                    '成交额': 'turnover',
                    '持仓量': 'position',
                    '结算价': 'settlement',
                    '昨结算': 'pre_settlement',
                    '涨跌额': 'change',
                    '涨跌幅': 'change_pct',
                    '交易日': 'date',
                })
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                
                return df
                
        except Exception as e:
            logger.error(f"Failed to get bars for {symbol}: {e}")
        return pd.DataFrame()
        
    def get_main_contract(self, product: str) -> Optional[str]:
        """
        获取主力合约代码
        
        Args:
            product: 品种代码（如 "IF", "CU", "AU"）
            
        Returns:
            主力合约代码
        """
        return self.MAIN_CONTRACT_MAP.get(product.upper())
        
    def get_position_rank(self, date: str = None) -> List[Dict]:
        """
        获取持仓排名
        
        Args:
            date: 日期 (YYYYMMDD)，默认今天
            
        Returns:
            持仓排名数据
        """
        self._ensure_akshare()
        
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
            
        try:
            df = self._ak.futures_position_rank_cfmmc(date=date)
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Failed to get position rank: {e}")
            return []
            
    def get_warehouse_receipt(self, symbol: str) -> List[Dict]:
        """
        获取仓单数据
        
        Args:
            symbol: 品种代码（如 "CU"）
            
        Returns:
            仓单数据
        """
        self._ensure_akshare()
        
        try:
            df = self._ak.futures_warehouse_receipt(symbol=symbol)
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Failed to get warehouse receipt: {e}")
            return []
            
    def calculate_margin(
        self,
        symbol: str,
        price: float,
        direction: str = "long",
    ) -> Dict[str, float]:
        """
        计算保证金
        
        Args:
            symbol: 合约代码
            price: 当前价格
            direction: 方向 ("long", "short")
            
        Returns:
            保证金信息
        """
        # 默认保证金率（实际需从交易所获取）
        MARGIN_RATES = {
            "IF": 0.12,  # 12%
            "IH": 0.12,
            "IC": 0.12,
            "IM": 0.12,
            "T": 0.02,   # 2%
            "TF": 0.02,
            "TS": 0.02,
            "TL": 0.02,
            "AU": 0.08,  # 8%
            "AG": 0.08,
            "CU": 0.10,
            "AL": 0.10,
            "ZN": 0.10,
            "NI": 0.12,
            "RB": 0.11,
            "HC": 0.11,
            "I": 0.12,
            "J": 0.12,
            "JM": 0.12,
        }
        
        # 合约乘数
        MULTIPLIERS = {
            "IF": 300.0,
            "IH": 300.0,
            "IC": 200.0,
            "IM": 200.0,
            "T": 10000.0,
            "TF": 10000.0,
            "TS": 10000.0,
            "TL": 10000.0,
            "AU": 1000.0,
            "AG": 15000.0,
            "CU": 5.0,
            "AL": 5.0,
            "ZN": 5.0,
            "NI": 1.0,
            "RB": 10.0,
            "HC": 10.0,
            "I": 100.0,
        }
        
        product = symbol[:2].upper()
        rate = MARGIN_RATES.get(product, 0.10)
        multiplier = MULTIPLIERS.get(product, 10.0)
        
        margin = price * multiplier * rate
        commission = price * multiplier * 0.00005  # 假设万分之0.5
        
        return {
            "symbol": symbol,
            "price": price,
            "direction": direction,
            "margin_rate": rate,
            "margin": margin,
            "commission": commission,
            "multiplier": multiplier,
        }
