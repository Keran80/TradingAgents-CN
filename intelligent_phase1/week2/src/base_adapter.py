#!/usr/bin/env python3
"""
数据适配器基类
"""

import abc
import asyncio
from typing import Dict, List, Any, Optional
import aiohttp

class DataSourceAdapter(abc.ABC):
    """数据源适配器基类"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_connected = False
        
    async def connect(self):
        """连接数据源"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        self.is_connected = True
        
    async def disconnect(self):
        """断开数据源连接"""
        if self.session:
            await self.session.close()
            self.session = None
        self.is_connected = False
        
    @abc.abstractmethod
    async def fetch_data(self, symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """获取数据（抽象方法）"""
        pass
    
    @abc.abstractmethod
    async def fetch_realtime_data(self, symbol: str) -> Dict[str, Any]:
        """获取实时数据（抽象方法）"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "name": self.name,
            "connected": self.is_connected,
            "timestamp": "2026-04-10T01:35:00"
        }

class DataAdapter:
    """统一数据适配器"""
    
    def __init__(self):
        self.adapters: Dict[str, DataSourceAdapter] = {}
        
    def register_adapter(self, adapter: DataSourceAdapter):
        """注册适配器"""
        self.adapters[adapter.name] = adapter
        
    async def get_data(self, source: str, symbol: str, **kwargs) -> List[Dict[str, Any]]:
        """获取数据"""
        if source not in self.adapters:
            raise ValueError(f"数据源未注册: {source}")
        
        adapter = self.adapters[source]
        if not adapter.is_connected:
            await adapter.connect()
            
        return await adapter.fetch_data(symbol, **kwargs)
    
    async def close_all(self):
        """关闭所有适配器"""
        for adapter in self.adapters.values():
            if adapter.is_connected:
                await adapter.disconnect()
