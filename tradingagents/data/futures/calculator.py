# -*- coding: utf-8 -*-
"""
期货专用计算器

提供期货相关的计算功能：
- 保证金计算
- 盈亏计算
- 合约价值计算
- 风险度计算
"""

import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FuturesContract:
    """期货合约信息"""
    symbol: str           # 合约代码
    name: str             # 合约名称
    exchange: str         # 交易所
    multiplier: float     # 合约乘数
    tick_size: float      # 最小变动价位
    contract_size: float  # 合约规模
    margin_rate: float    # 保证金率
    
    
@dataclass
class FuturesPosition:
    """期货持仓"""
    symbol: str
    direction: str          # "long" 或 "short"
    entry_price: float     # 开仓价
    current_price: float   # 当前价
    quantity: int          # 持仓量（手）
    entry_date: datetime   # 开仓日期
    
    
class FuturesCalculator:
    """
    期货计算器
    
    提供期货交易相关的计算功能
    """
    
    # 交易所信息
    EXCHANGES = {
        "SHFE": "上海期货交易所",
        "DCE": "大连商品交易所",
        "CZCE": "郑州商品交易所",
        "CFFEX": "中国金融期货交易所",
        "INE": "上海国际能源交易中心",
    }
    
    # 品种配置
    PRODUCTS = {
        # 金融期货
        "IF": {"name": "沪深300股指", "exchange": "CFFEX", "multiplier": 300.0, "tick": 0.2},
        "IH": {"name": "上证50股指", "exchange": "CFFEX", "multiplier": 300.0, "tick": 0.2},
        "IC": {"name": "中证500股指", "exchange": "CFFEX", "multiplier": 200.0, "tick": 0.2},
        "IM": {"name": "中证1000股指", "exchange": "CFFEX", "multiplier": 200.0, "tick": 0.2},
        "T": {"name": "10年期国债", "exchange": "CFFEX", "multiplier": 10000.0, "tick": 0.005},
        "TF": {"name": "5年期国债", "exchange": "CFFEX", "multiplier": 10000.0, "tick": 0.005},
        "TS": {"name": "2年期国债", "exchange": "CFFEX", "multiplier": 10000.0, "tick": 0.005},
        "TL": {"name": "30年期国债", "exchange": "CFFEX", "multiplier": 10000.0, "tick": 0.01},
        
        # 贵金属
        "AU": {"name": "黄金", "exchange": "SHFE", "multiplier": 1000.0, "tick": 0.02},
        "AG": {"name": "白银", "exchange": "SHFE", "multiplier": 15000.0, "tick": 1.0},
        
        # 基本金属
        "CU": {"name": "铜", "exchange": "SHFE", "multiplier": 5.0, "tick": 10.0},
        "AL": {"name": "铝", "exchange": "SHFE", "multiplier": 5.0, "tick": 5.0},
        "ZN": {"name": "锌", "exchange": "SHFE", "multiplier": 5.0, "tick": 5.0},
        "PB": {"name": "铅", "exchange": "SHFE", "multiplier": 5.0, "tick": 5.0},
        "NI": {"name": "镍", "exchange": "SHFE", "multiplier": 1.0, "tick": 10.0},
        "SN": {"name": "锡", "exchange": "SHFE", "multiplier": 1.0, "tick": 10.0},
        "BC": {"name": "国际铜", "exchange": "INE", "multiplier": 5.0, "tick": 10.0},
        
        # 黑色金属
        "RB": {"name": "螺纹钢", "exchange": "SHFE", "multiplier": 10.0, "tick": 1.0},
        "HC": {"name": "热轧卷板", "exchange": "SHFE", "multiplier": 10.0, "tick": 1.0},
        "WR": {"name": "线材", "exchange": "SHFE", "multiplier": 10.0, "tick": 1.0},
        "I": {"name": "铁矿石", "exchange": "DCE", "multiplier": 100.0, "tick": 0.5},
        
        # 焦煤焦炭
        "JM": {"name": "焦煤", "exchange": "DCE", "multiplier": 60.0, "tick": 0.5},
        "J": {"name": "焦炭", "exchange": "DCE", "multiplier": 100.0, "tick": 0.5},
        
        # 能源化工
        "SC": {"name": "原油", "exchange": "INE", "multiplier": 1000.0, "tick": 0.1},
        "FU": {"name": "燃料油", "exchange": "SHFE", "multiplier": 50.0, "tick": 1.0},
        "LU": {"name": "低硫燃料油", "exchange": "INE", "multiplier": 50.0, "tick": 1.0},
        "BU": {"name": "沥青", "exchange": "SHFE", "multiplier": 10.0, "tick": 1.0},
        "RU": {"name": "天然橡胶", "exchange": "SHFE", "multiplier": 10.0, "tick": 5.0},
        "NR": {"name": "20号胶", "exchange": "INE", "multiplier": 10.0, "tick": 5.0},
        
        # 化工品
        "L": {"name": "聚乙烯", "exchange": "DCE", "multiplier": 5.0, "tick": 5.0},
        "PP": {"name": "聚丙烯", "exchange": "DCE", "multiplier": 5.0, "tick": 1.0},
        "PVC": {"name": "聚氯乙烯", "exchange": "DCE", "multiplier": 5.0, "tick": 5.0},
        "MA": {"name": "甲醇", "exchange": "CZCE", "multiplier": 10.0, "tick": 1.0},
        "EG": {"name": "乙二醇", "exchange": "DCE", "multiplier": 10.0, "tick": 1.0},
        "EB": {"name": "苯乙烯", "exchange": "DCE", "multiplier": 5.0, "tick": 1.0},
        "PG": {"name": "液化石油气", "exchange": "DCE", "multiplier": 20.0, "tick": 1.0},
        
        # 农产品
        "豆粕": {"name": "豆粕", "exchange": "DCE", "multiplier": 10.0, "tick": 1.0},
        "豆油": {"name": "豆油", "exchange": "DCE", "multiplier": 10.0, "tick": 2.0},
        "豆一": {"name": "黄大豆1号", "exchange": "DCE", "multiplier": 10.0, "tick": 1.0},
        "豆二": {"name": "黄大豆2号", "exchange": "DCE", "multiplier": 10.0, "tick": 1.0},
        "玉米": {"name": "玉米", "exchange": "DCE", "multiplier": 10.0, "tick": 1.0},
        "玉米淀粉": {"name": "玉米淀粉", "exchange": "DCE", "multiplier": 10.0, "tick": 1.0},
        "棕榈油": {"name": "棕榈油", "exchange": "DCE", "multiplier": 10.0, "tick": 2.0},
        "菜粕": {"name": "菜粕", "exchange": "CZCE", "multiplier": 10.0, "tick": 1.0},
        "菜油": {"name": "菜油", "exchange": "CZCE", "multiplier": 10.0, "tick": 1.0},
        "菜籽": {"name": "油菜籽", "exchange": "CZCE", "multiplier": 10.0, "tick": 1.0},
        "白糖": {"name": "白糖", "exchange": "CZCE", "multiplier": 10.0, "tick": 1.0},
        "棉花": {"name": "棉花", "exchange": "CZCE", "multiplier": 5.0, "tick": 5.0},
        "棉纱": {"name": "棉纱", "exchange": "CZCE", "multiplier": 5.0, "tick": 5.0},
        "苹果": {"name": "苹果", "exchange": "CZCE", "multiplier": 10.0, "tick": 1.0},
        "红枣": {"name": "红枣", "exchange": "CZCE", "multiplier": 5.0, "tick": 5.0},
        "花生": {"name": "花生", "exchange": "CZCE", "multiplier": 5.0, "tick": 2.0},
        "粳稻": {"name": "粳稻", "exchange": "CZCE", "multiplier": 20.0, "tick": 1.0},
        "早籼稻": {"name": "早籼稻", "exchange": "CZCE", "multiplier": 20.0, "tick": 1.0},
        "晚籼稻": {"name": "晚籼稻", "exchange": "CZCE", "multiplier": 20.0, "tick": 1.0},
        "小麦": {"name": "强麦", "exchange": "CZCE", "multiplier": 20.0, "tick": 1.0},
    }
    
    # 默认保证金率
    DEFAULT_MARGIN_RATES = {
        "CFFEX": 0.12,
        "SHFE": 0.10,
        "DCE": 0.10,
        "CZCE": 0.08,
        "INE": 0.10,
    }
    
    def get_product_info(self, product_code: str) -> Optional[Dict]:
        """获取品种信息"""
        return self.PRODUCTS.get(product_code.upper())
        
    def calculate_contract_value(
        self,
        symbol: str,
        price: float,
    ) -> float:
        """
        计算合约价值
        
        Args:
            symbol: 合约代码
            price: 价格
            
        Returns:
            合约价值
        """
        product = self._extract_product(symbol)
        info = self.get_product_info(product)
        
        if info:
            return price * info["multiplier"]
        return price * 10.0  # 默认乘数
        
    def calculate_margin(
        self,
        symbol: str,
        price: float,
        margin_rate: Optional[float] = None,
    ) -> float:
        """
        计算保证金
        
        Args:
            symbol: 合约代码
            price: 价格
            margin_rate: 保证金率，为None时使用默认值
            
        Returns:
            所需保证金
        """
        value = self.calculate_contract_value(symbol, price)
        
        if margin_rate is None:
            product = self._extract_product(symbol)
            info = self.get_product_info(product)
            exchange = info.get("exchange", "SHFE") if info else "SHFE"
            margin_rate = self.DEFAULT_MARGIN_RATES.get(exchange, 0.10)
            
        return value * margin_rate
        
    def calculate_profit(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        exit_price: float,
        quantity: int = 1,
    ) -> float:
        """
        计算盈亏
        
        Args:
            symbol: 合约代码
            direction: 方向 ("long" 或 "short")
            entry_price: 开仓价
            exit_price: 平仓价
            quantity: 持仓量（手）
            
        Returns:
            盈亏金额
        """
        product = self._extract_product(symbol)
        info = self.get_product_info(product)
        multiplier = info["multiplier"] if info else 10.0
        
        price_diff = exit_price - entry_price
        
        if direction.lower() == "short":
            price_diff = -price_diff
            
        return price_diff * multiplier * quantity
        
    def calculate_profit_pct(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        exit_price: float,
    ) -> float:
        """
        计算盈亏比例
        
        Args:
            symbol: 合约代码
            direction: 方向
            entry_price: 开仓价
            exit_price: 平仓价
            
        Returns:
            盈亏比例
        """
        profit = self.calculate_profit(symbol, direction, entry_price, exit_price)
        margin = self.calculate_margin(symbol, entry_price)
        
        if margin > 0:
            return profit / margin
        return 0.0
        
    def calculate_risk_level(
        self,
        positions: List[FuturesPosition],
        account_balance: float,
    ) -> Dict:
        """
        计算风险度
        
        Args:
            positions: 持仓列表
            account_balance: 账户余额
            
        Returns:
            风险度信息
        """
        total_margin = 0.0
        total_unrealized_pnl = 0.0
        
        for pos in positions:
            margin = self.calculate_margin(pos.symbol, pos.current_price)
            pnl = self.calculate_profit(
                pos.symbol,
                pos.direction,
                pos.entry_price,
                pos.current_price,
                pos.quantity,
            )
            total_margin += margin
            total_unrealized_pnl += pnl
            
        risk_level = total_margin / (account_balance + total_unrealized_pnl) * 100
        available = account_balance + total_unrealized_pnl - total_margin
        
        return {
            "total_margin": total_margin,
            "unrealized_pnl": total_unrealized_pnl,
            "risk_level": risk_level,
            "available": available,
            "account_balance": account_balance,
            "positions_count": len(positions),
        }
        
    def calculate_settlement(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        settlement_price: float,
        quantity: int = 1,
    ) -> Dict:
        """
        计算结算
        
        Args:
            symbol: 合约代码
            direction: 方向
            entry_price: 开仓价
            settlement_price: 结算价
            quantity: 持仓量
            
        Returns:
            结算信息
        """
        profit = self.calculate_profit(
            symbol, direction, entry_price, settlement_price, quantity
        )
        
        # 假设手续费为合约价值的万分之0.5
        value = self.calculate_contract_value(symbol, settlement_price)
        commission = value * quantity * 0.00005
        
        net_profit = profit - commission * 2  # 开仓+平仓
        
        return {
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry_price,
            "settlement_price": settlement_price,
            "quantity": quantity,
            "profit": profit,
            "commission": commission,
            "net_profit": net_profit,
        }
        
    def _extract_product(self, symbol: str) -> str:
        """从合约代码提取品种代码"""
        import re
        # 匹配字母部分
        match = re.match(r'^([A-Za-z]+)', symbol)
        if match:
            return match.group(1)
        # 中文品种
        for name in self.PRODUCTS.keys():
            if name in symbol:
                return name
        return symbol[:2]
