# -*- coding: utf-8 -*-
"""
AkShare 实时行情适配器

使用 AkShare 获取A股/期货实时行情数据
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Callable, List
import time

logger = logging.getLogger(__name__)


class AkShareRealtimeAdapter:
    """
    AkShare 实时行情适配器
    
    支持：
    - A股实时行情
    - 期货实时行情
    - 涨跌停数据
    """
    
    def __init__(self, poll_interval: float = 3.0):
        """
        初始化适配器
        
        Args:
            poll_interval: 轮询间隔（秒）
        """
        self.poll_interval = poll_interval
        self._callback: Optional[Callable] = None
        self._running = False
        self._symbols: Dict[str, str] = {}  # symbol -> market
        self._task: Optional[asyncio.Task] = None
        
        # AkShare 模块（延迟导入）
        self._ak = None
        
    def _ensure_akshare(self):
        """确保 AkShare 已导入"""
        if self._ak is None:
            import akshare as ak
            self._ak = ak
            logger.info("AkShare loaded successfully")
            
    def set_callback(self, callback: Callable):
        """设置数据回调"""
        self._callback = callback
        
    def subscribe(self, symbol: str, market: str = "stock"):
        """
        订阅行情
        
        Args:
            symbol: 股票代码（如 "000001.SZ"）
            market: 市场类型 ("stock", "futures", "index")
        """
        self._symbols[symbol] = market
        logger.debug(f"Subscribed: {symbol} ({market})")
        
    def unsubscribe(self, symbol: str):
        """取消订阅"""
        if symbol in self._symbols:
            del self._symbols[symbol]
            
    async def connect(self):
        """连接数据源"""
        self._ensure_akshare()
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("AkShare adapter connected")
        
    async def disconnect(self):
        """断开连接"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AkShare adapter disconnected")
        
    async def _poll_loop(self):
        """轮询循环"""
        while self._running:
            try:
                await self._fetch_data()
            except Exception as e:
                logger.error(f"Fetch error: {e}")
            await asyncio.sleep(self.poll_interval)
            
    async def _fetch_data(self):
        """获取数据"""
        if not self._symbols:
            return
            
        from .manager import TickData, MarketType
            
        # 批量获取 A股实时行情
        try:
            stock_df = self._ak.stock_zh_a_spot_em()
            
            for symbol in list(self._symbols.keys()):
                # 转换代码格式
                code = symbol.split(".")[0]
                
                # 查找匹配行
                row = stock_df[stock_df['代码'] == code]
                
                if not row.empty:
                    r = row.iloc[0]
                    tick = TickData(
                        symbol=symbol,
                        timestamp=datetime.now(),
                        last_price=float(r.get('最新价', 0)),
                        open=float(r.get('今开', 0)),
                        high=float(r.get('最高', 0)),
                        low=float(r.get('最低', 0)),
                        volume=float(r.get('成交量', 0)),
                        turnover=float(r.get('成交额', 0)),
                    )
                    
                    if self._callback:
                        self._callback(tick)
                        
        except Exception as e:
            logger.error(f"Failed to fetch stock data: {e}")
            
    def get_realtime_quote(self, symbol: str) -> Optional[Dict]:
        """
        获取单只股票实时行情
        
        Args:
            symbol: 股票代码（如 "000001.SZ"）
            
        Returns:
            行情数据字典
        """
        try:
            code = symbol.split(".")[0]
            df = self._ak.stock_zh_a_spot_em()
            row = df[df['代码'] == code]
            
            if not row.empty:
                r = row.iloc[0]
                return {
                    "symbol": symbol,
                    "name": r.get('名称', ''),
                    "price": float(r.get('最新价', 0)),
                    "open": float(r.get('今开', 0)),
                    "high": float(r.get('最高', 0)),
                    "low": float(r.get('最低', 0)),
                    "volume": float(r.get('成交量', 0)),
                    "turnover": float(r.get('成交额', 0)),
                    "change": float(r.get('涨跌额', 0)),
                    "change_pct": float(r.get('涨跌幅', 0)),
                    "bid": float(r.get('买一', 0)),
                    "ask": float(r.get('卖一', 0)),
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
        return None
        
    def get_realtime_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        批量获取实时行情
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            行情数据字典 {symbol: data}
        """
        results = {}
        for symbol in symbols:
            data = self.get_realtime_quote(symbol)
            if data:
                results[symbol] = data
        return results
        
    def get_limit_list(self, date: Optional[str] = None) -> List[Dict]:
        """
        获取涨停股票列表
        
        Args:
            date: 日期 (YYYYMMDD)，默认今天
            
        Returns:
            涨停股票列表
        """
        try:
            if date is None:
                date = datetime.now().strftime("%Y%m%d")
                
            df = self._ak.stock_zt_pool_em(date=date)
            
            results = []
            for _, row in df.iterrows():
                results.append({
                    "symbol": f"{row['代码']}.SZ" if row.get('市场') == '深交所' else f"{row['代码']}.SH",
                    "name": row.get('名称', ''),
                    "close": float(row.get('今收', 0)),
                    "change_pct": float(row.get('涨停统计', 0)),
                    "reason": row.get('涨停题材', ''),
                    "turnover": float(row.get('成交额', 0)),
                    "volume_ratio": float(row.get('量比', 0)),
                })
            return results
            
        except Exception as e:
            logger.error(f"Failed to get limit list: {e}")
            return []
