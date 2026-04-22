#!/usr/bin/env python3
"""
期货数据源适配器
支持商品期货、金融期货数据获取
"""

import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

class FuturesDataSource:
    """期货数据源适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.name = "futures_data_source"
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_connected = False
        self.cache = {}  # 简单缓存
        
        # 数据源配置
        self.data_sources = {
            "commodity_futures": {
                "name": "商品期货数据源",
                "base_url": "https://api.example.com/commodity-futures",
                "supported_symbols": ["AU", "AG", "CU", "AL", "ZN", "PB"],
                "rate_limit": 80  # 每分钟请求限制
            },
            "financial_futures": {
                "name": "金融期货数据源", 
                "base_url": "https://api.example.com/financial-futures",
                "supported_symbols": ["IF", "IC", "IH", "TF", "T"],
                "rate_limit": 60
            },
            "energy_futures": {
                "name": "能源期货数据源",
                "base_url": "https://api.example.com/energy-futures",
                "supported_symbols": ["SC", "FU", "BU", "RU"],
                "rate_limit": 50
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
        """检测期货所属市场"""
        symbol_upper = symbol.upper()
        
        # 商品期货
        if symbol_upper in ["AU", "AG", "CU", "AL", "ZN", "PB"]:
            return "commodity_futures"
        # 金融期货
        elif symbol_upper in ["IF", "IC", "IH", "TF", "T"]:
            return "financial_futures"
        # 能源期货
        elif symbol_upper in ["SC", "FU", "BU", "RU"]:
            return "energy_futures"
        else:
            raise ValueError(f"无法识别的期货代码: {symbol}")
    
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
            "price": 5000.0 + (hash(symbol) % 2000),  # 模拟价格
            "change": (hash(symbol) % 100) - 50,  # 模拟涨跌幅
            "volume": 50000 + (hash(symbol) % 95000),
            "open_interest": 10000 + (hash(symbol) % 90000),  # 持仓量
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
        
        base_price = 5000.0 + (hash(symbol) % 2000)
        
        for i in range(days):
            date = start + timedelta(days=i)
            price = base_price + (i * 10) + ((hash(symbol + str(i)) % 200) - 100)
            volume = 50000 + (hash(symbol + str(i)) % 95000)
            open_interest = 10000 + (hash(symbol + str(i)) % 90000)
            
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "symbol": symbol,
                "market": market,
                "open": price - 20,
                "high": price + 50,
                "low": price - 50,
                "close": price,
                "volume": volume,
                "open_interest": open_interest,
                "settlement": price - 5,  # 结算价
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
        """获取支持的期货代码"""
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
    
    async def fetch_market_depth(self, symbol: str, depth: int = 5) -> Dict[str, Any]:
        """获取市场深度数据"""
        if not self.is_connected:
            await self.connect()
        
        market = self._detect_market(symbol)
        
        print(f"📊 获取市场深度: {symbol} (深度: {depth})")
        
        # 模拟市场深度数据
        base_price = 5000.0 + (hash(symbol) % 2000)
        
        bids = []  # 买盘
        asks = []  # 卖盘
        
        for i in range(1, depth + 1):
            bid_price = base_price - i * 5
            ask_price = base_price + i * 5
            
            bids.append({
                "price": bid_price,
                "volume": 100 * i,
                "orders": i * 2
            })
            
            asks.append({
                "price": ask_price,
                "volume": 80 * i,
                "orders": i
            })
        
        return {
            "symbol": symbol,
            "market": market,
            "timestamp": datetime.now().isoformat(),
            "bids": bids,
            "asks": asks,
            "best_bid": bids[0]["price"] if bids else None,
            "best_ask": asks[0]["price"] if asks else None,
            "spread": (asks[0]["price"] - bids[0]["price"]) if bids and asks else None
        }

async def demo_futures_adapter():
    """演示期货数据源适配器"""
    print("🧪 演示期货数据源适配器")
    
    # 创建适配器
    config = {
        "api_key": "demo_key",
        "cache_enabled": True,
        "timeout": 30,
        "max_depth": 10
    }
    
    adapter = FuturesDataSource(config)
    
    try:
        # 连接
        await adapter.connect()
        
        # 健康检查
        health = await adapter.health_check()
        print(f"健康检查: {health['status']}")
        
        # 获取支持的期货代码
        commodity_symbols = await adapter.get_supported_symbols("commodity_futures")
        print(f"商品期货支持代码: {commodity_symbols}")
        
        # 获取历史数据
        historical_data = await adapter.fetch_historical_data(
            symbol="AU",
            start_date="2026-01-01",
            end_date="2026-01-10"
        )
        print(f"获取历史数据: {len(historical_data)}条记录")
        if historical_data:
            print(f"  第一条: {historical_data[0]['date']} - 收盘价: {historical_data[0]['close']}")
        
        # 获取实时数据
        realtime_data = await adapter.fetch_realtime_data("AU")
        print(f"实时数据: {realtime_data['symbol']} - 价格: {realtime_data['price']}")
        
        # 获取市场深度
        market_depth = await adapter.fetch_market_depth("AU", depth=3)
        print(f"市场深度: 买盘{len(market_depth['bids'])}档, 卖盘{len(market_depth['asks'])}档")
        
        # 断开连接
        await adapter.disconnect()
        
        print("✅ 演示完成")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        await adapter.disconnect()

if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_futures_adapter())
