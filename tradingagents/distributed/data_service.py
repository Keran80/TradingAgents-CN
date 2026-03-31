# -*- coding: utf-8 -*-
"""
分布式数据服务

支持：
- 多级缓存（内存 + Redis）
- 数据分片
- 读写分离
- 数据预热
"""

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import OrderedDict
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    accessed_at: float
    access_count: int = 0
    ttl: Optional[int] = None  # 秒
    
    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl


class DataCache:
    """
    内存缓存（LRU + TTL）
    
    支持：
    - LRU 淘汰
    - TTL 过期
    - 访问统计
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def _make_key(self, namespace: str, *args) -> str:
        """生成缓存 key"""
        key_str = f"{namespace}:{':'.join(str(a) for a in args)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self._cache:
            self._stats['misses'] += 1
            return None
        
        entry = self._cache[key]
        
        # 检查过期
        if entry.is_expired():
            del self._cache[key]
            self._stats['misses'] += 1
            return None
        
        # 更新访问信息（LRU）
        entry.accessed_at = time.time()
        entry.access_count += 1
        self._cache.move_to_end(key)
        
        self._stats['hits'] += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存"""
        # LRU 淘汰
        while len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
            self._stats['evictions'] += 1
        
        now = time.time()
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=now,
            accessed_at=now,
            ttl=ttl or self.default_ttl
        )
        self._cache[key] = entry
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._stats = {'hits': 0, 'misses': 0, 'evictions': 0}
    
    def get_stats(self) -> Dict:
        """获取缓存统计"""
        total = self._stats['hits'] + self._stats['misses']
        hit_rate = self._stats['hits'] / total if total > 0 else 0
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'hit_rate': hit_rate,
            'evictions': self._stats['evictions']
        }


@dataclass
class DataShard:
    """数据分片"""
    shard_id: str
    nodes: List[str]
    primary_node: str
    weight: int = 1


class DistributedDataService:
    """
    分布式数据服务
    
    支持：
    - 多级缓存（内存 + Redis 可选）
    - 数据分片
    - 读写分离
    - 数据预热
    """
    
    def __init__(
        self,
        cache_size: int = 5000,
        cache_ttl: int = 300,
        redis_url: Optional[str] = None,
        shards: Optional[List[DataShard]] = None
    ):
        # 内存缓存
        self.memory_cache = DataCache(max_size=cache_size, default_ttl=cache_ttl)
        
        # Redis 缓存（可选）
        self.redis_client = None
        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url)
                logger.info(f"Redis 连接成功: {redis_url}")
            except ImportError:
                logger.warning("redis 库未安装，跳过 Redis 缓存")
            except Exception as e:
                logger.warning(f"Redis 连接失败: {e}")
        
        # 数据分片
        self.shards = shards or []
        
        # 数据加载器
        self.loaders: Dict[str, Callable] = {}
        
        # 预热任务
        self._warmup_task: Optional[asyncio.Task] = None
    
    def register_loader(self, data_type: str, loader: Callable):
        """注册数据加载器"""
        self.loaders[data_type] = loader
        logger.info(f"数据加载器注册: {data_type}")
    
    async def get_data(
        self,
        data_type: str,
        *args,
        use_cache: bool = True,
        **kwargs
    ) -> Optional[Any]:
        """
        获取数据（带缓存）
        
        优先级：
        1. 内存缓存
        2. Redis 缓存
        3. 数据加载器
        """
        cache_key = self.memory_cache._make_key(data_type, *args)
        
        # 1. 内存缓存
        if use_cache:
            value = self.memory_cache.get(cache_key)
            if value is not None:
                logger.debug(f"内存缓存命中: {data_type}")
                return value
            
            # 2. Redis 缓存
            if self.redis_client:
                try:
                    value = self.redis_client.get(cache_key)
                    if value:
                        value = json.loads(value)
                        # 回填内存缓存
                        self.memory_cache.set(cache_key, value)
                        logger.debug(f"Redis 缓存命中: {data_type}")
                        return value
                except Exception as e:
                    logger.warning(f"Redis 读取失败: {e}")
        
        # 3. 数据加载器
        if data_type not in self.loaders:
            logger.warning(f"未注册的数据类型: {data_type}")
            return None
        
        try:
            loader = self.loaders[data_type]
            if asyncio.iscoroutinefunction(loader):
                value = await loader(*args, **kwargs)
            else:
                value = loader(*args, **kwargs)
            
            # 写入缓存
            if use_cache and value is not None:
                self.memory_cache.set(cache_key, value)
                if self.redis_client:
                    try:
                        self.redis_client.setex(
                            cache_key,
                            self.memory_cache.default_ttl,
                            json.dumps(value, default=str)
                        )
                    except Exception as e:
                        logger.warning(f"Redis 写入失败: {e}")
            
            logger.debug(f"数据加载: {data_type}")
            return value
            
        except Exception as e:
            logger.error(f"数据加载失败: {data_type}, {e}")
            return None
    
    def invalidate(self, data_type: str, *args):
        """失效缓存"""
        cache_key = self.memory_cache._make_key(data_type, *args)
        self.memory_cache.delete(cache_key)
        
        if self.redis_client:
            try:
                self.redis_client.delete(cache_key)
            except Exception as e:
                logger.warning(f"Redis 失效失败: {e}")
    
    def preload(self, data_type: str, *args, **kwargs):
        """预热缓存"""
        if data_type not in self.loaders:
            return
        
        # 异步预热
        asyncio.create_task(self.get_data(data_type, *args, use_cache=True, **kwargs))
    
    async def warmup(self, data_configs: List[Dict]):
        """批量预热"""
        tasks = []
        for config in data_configs:
            data_type = config.get('type')
            args = config.get('args', [])
            kwargs = config.get('kwargs', {})
            if data_type in self.loaders:
                tasks.append(self.get_data(data_type, *args, **kwargs))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"预热完成: {len(tasks)} 项")
    
    def get_stats(self) -> Dict:
        """获取服务统计"""
        stats = {
            'memory_cache': self.memory_cache.get_stats(),
            'redis_connected': self.redis_client is not None,
            'shards': len(self.shards),
            'loaders': list(self.loaders.keys())
        }
        return stats
    
    def get_shard(self, key: str) -> Optional[DataShard]:
        """获取数据分片"""
        if not self.shards:
            return None
        # 简单哈希取模
        shard_idx = int(hashlib.md5(key.encode()).hexdigest(), 16) % len(self.shards)
        return self.shards[shard_idx]
