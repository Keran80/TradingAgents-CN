#!/usr/bin/env python3
"""
股票数据源适配器
支持A股、港股、美股数据获取
"""

import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

class StockDataSource:
    """股票数据源适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.name = "stock_data_source"
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_connected = False
        self.cache = {}  # 简单缓存
        
        # 数据源配置
        self.data_sources = {
            "a_share": {
                "name": "A股数据源",
                "base_url": "https://api.example.com/a-share",
                "supported_symbols": ["000001", "000002", "600000"],
                "rate_limit": 100  # 每分钟请求限制
            },
            "hk_stock": {
                "name": "港股数据源", 
                "base_url": "https://api.example.com/hk-stock",
                "supported_symbols": ["00700", "00941", "01299"],
                "rate_limit": 50
            },
            "us_stock": {
                "name": "美股数据源",
                "base_url": "https://api.example.com/us-stock",
                "supported_symbols": ["AAPL", "GOOGL", "TSLA"],
                "rate_limit": 200
            }
        }
    
    async def connect(self):
        """连接数据源"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        self.is_connected = True
        print(f"✅ {self.name} 已连接")
        
    async def disconnect(self):
        """断开数据源连接"""
        if self.session:
            await self.session.close()
            self.session = None
        self.is_connected = False
        print(f"🔌 {self.name} 已断开")
    
    def _detect_market(self, symbol: str) -> str:
        """检测股票所属市场"""
        if symbol.startswith(('00', '30', '60')):
            return "a_share"
        elif symbol.startswith(('0', '1', '2', '3', '4', '5')):
            return "hk_stock"
        elif symbol.isalpha() and len(symbol) <= 5:
            return "us_stock"
        else:
            raise ValueError(f"无法识别的股票代码: {symbol}")
    
    async def fetch_historical_data(self, symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """获取历史数据"""
        if not self.is_connected:
            await self.connect()
        
        market = self._detect_market(symbol)
        data_source = self.data_sources[market]
        
        # 检查缓存
        cache_key = f"{symbol}_{start_date}_{end_date}"
        if cache_key in self.cache:
            print(f"📦 从缓存获取数据: {symbol}")
            return self.cache[cache_key]
        
        print(f"📥 获取历史数据: {symbol} ({start_date} 至 {end_date})")
        
        # 模拟数据获取
        mock_data = self._generate_mock_data(symbol, start_date, end_date, market)
        
        # 缓存数据
        self.cache[cache_key] = mock_data
        
        return mock_data
    
    async def fetch_realtime_data(self, symbol: str) -> Dict[str, Any]:
        """获取实时数据"""
        if not self.is_connected:
            await self.connect()
        
        market = self._detect_market(symbol)
        
        print(f"⚡ 获取实时数据: {symbol}")
        
        # 模拟实时数据
        return {
            "symbol": symbol,
            "market": market,
            "price": 100.0 + (hash(symbol) % 100) / 10,  # 模拟价格
            "change": (hash(symbol) % 20) - 10,  # 模拟涨跌幅
            "volume": 1000000 + (hash(symbol) % 9000000),
            "timestamp": datetime.now().isoformat(),
            "data_source": self.data_sources[market]["name"]
        }
    
    def _generate_mock_data(self, symbol: str, start_date: str, end_date: str, market: str) -> List[Dict[str, Any]]:
        """生成模拟数据（开发阶段使用）"""
        data = []
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        days = (end - start).days
        if days <= 0:
            days = 30  # 默认30天
        
        base_price = 100.0 + (hash(symbol) % 100)
        
        for i in range(days):
            date = start + timedelta(days=i)
            price = base_price + (i * 0.1) + ((hash(symbol + str(i)) % 20) - 10) / 10
            volume = 1000000 + (hash(symbol + str(i)) % 9000000)
            
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "symbol": symbol,
                "market": market,
                "open": price - 0.5,
                "high": price + 1.0,
                "low": price - 1.0,
                "close": price,
                "volume": volume,
                "turnover": price * volume,
                "data_source": self.data_sources[market]["name"]
            })
        
        return data
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "name": self.name,
            "connected": self.is_connected,
            "data_sources": list(self.data_sources.keys()),
            "cache_size": len(self.cache),
            "timestamp": datetime.now().isoformat(),
            "status": "healthy"
        }
    
    async def get_supported_symbols(self, market: Optional[str] = None) -> List[str]:
        """获取支持的股票代码"""
        if market:
            if market in self.data_sources:
                return self.data_sources[market]["supported_symbols"]
            else:
                raise ValueError(f"不支持的市场: {market}")
        else:
            all_symbols = []
            for source in self.data_sources.values():
                all_symbols.extend(source["supported_symbols"])
            return all_symbols

async def demo_stock_adapter():
    """演示股票数据源适配器"""
    print("🧪 演示股票数据源适配器")
    
    # 创建适配器
    config = {
        "api_key": "demo_key",
        "cache_enabled": True,
        "timeout": 30
    }
    
    adapter = StockDataSource(config)
    
    try:
        # 连接
        await adapter.connect()
        
        # 健康检查
        health = await adapter.health_check()
        print(f"健康检查: {health['status']}")
        
        # 获取支持的股票代码
        a_share_symbols = await adapter.get_supported_symbols("a_share")
        print(f"A股支持代码: {a_share_symbols[:3]}...")
        
        # 获取历史数据
        historical_data = await adapter.fetch_historical_data(
            symbol="000001",
            start_date="2026-01-01",
            end_date="2026-01-10"
        )
        print(f"获取历史数据: {len(historical_data)}条记录")
        if historical_data:
            print(f"  第一条: {historical_data[0]['date']} - 收盘价: {historical_data[0]['close']}")
        
        # 获取实时数据
        realtime_data = await adapter.fetch_realtime_data("000001")
        print(f"实时数据: {realtime_data['symbol']} - 价格: {realtime_data['price']}")
        
        # 断开连接
        await adapter.disconnect()
        
        print("✅ 演示完成")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        await adapter.disconnect()

if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_stock_adapter())
