"""
智能数据适配器
统一的多源数据接口
借鉴聚宽的多源数据融合思想
"""

import asyncio
from typing import Dict, Any
from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime, timedelta

class DataAdapter(ABC):
    """数据适配器基类"""
    
    @abstractmethod
    async def fetch(self, symbol: str, start: datetime, end: datetime, **kwargs) -> pd.DataFrame:
        """获取数据"""
        pass
    
    @abstractmethod
    def get_data_quality(self) -> float:
        """获取数据质量评分"""
        pass

class IntelligentDataAdapter:
    """智能数据适配器"""
    
    def __init__(self):
        self.adapters: Dict[str, DataAdapter] = {}
        self.cache: Dict[str, pd.DataFrame] = {}
        
    def register_adapter(self, name: str, adapter: DataAdapter):
        """注册数据适配器"""
        self.adapters[name] = adapter
        
    async def fetch_intelligent_data(self, symbol: str, start: datetime, end: datetime, **kwargs) -> pd.DataFrame:
        """智能获取数据"""
        # 检查缓存
        cache_key = f"{symbol}_{start}_{end}"
        if cache_key in self.cache:
            print(f"📦 使用缓存数据: {cache_key}")
            return self.cache[cache_key]
        
        # 选择最优数据源（简化版：选择第一个）
        if self.adapters:
            best_adapter_name = list(self.adapters.keys())[0]
            adapter = self.adapters[best_adapter_name]
            
            try:
                data = await adapter.fetch(symbol, start, end, **kwargs)
                
                # 缓存数据
                self.cache[cache_key] = data
                print(f"✅ 获取数据成功: {symbol} from {best_adapter_name}")
                
                return data
                
            except Exception as e:
                print(f"❌ 获取数据失败: {e}")
                raise
        else:
            raise Exception("没有可用的数据适配器")
            
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            "cache_size": len(self.cache),
            "cache_keys": list(self.cache.keys()),
            "adapters": list(self.adapters.keys())
        }

# 示例数据适配器
class MockDataAdapter(DataAdapter):
    """模拟数据适配器"""
    
    async def fetch(self, symbol: str, start: datetime, end: datetime, **kwargs) -> pd.DataFrame:
        """模拟获取数据"""
        print(f"📊 模拟获取 {symbol} 数据，时间范围: {start} 到 {end}")
        
        # 创建模拟数据
        dates = pd.date_range(start=start, end=end, freq='D')
        data = pd.DataFrame({
            'date': dates,
            'open': [100 + i for i in range(len(dates))],
            'high': [105 + i for i in range(len(dates))],
            'low': [95 + i for i in range(len(dates))],
            'close': [102 + i for i in range(len(dates))],
            'volume': [1000000 + i * 10000 for i in range(len(dates))]
        })
        
        return data
    
    def get_data_quality(self) -> float:
        """数据质量评分"""
        return 0.95  # 模拟高质量数据
