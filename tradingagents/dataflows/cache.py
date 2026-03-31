# -*- coding: utf-8 -*-
"""
数据缓存模块
提供内存缓存和磁盘缓存功能，支持过期时间和容量限制
"""

import os
import json
import hashlib
import time
import logging
from typing import Any, Callable, Optional, TypeVar, ParamSpec
from functools import wraps
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)

# 缓存配置
DEFAULT_CACHE_TTL = 3600  # 默认缓存时间 1 小时
DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(__file__), "data_cache")

# 内存缓存存储
_memory_cache: dict = {}


def _ensure_cache_dir(cache_dir: str = DEFAULT_CACHE_DIR) -> None:
    """确保缓存目录存在"""
    os.makedirs(cache_dir, exist_ok=True)


def _generate_cache_key(*args, **kwargs) -> str:
    """生成缓存键"""
    key_str = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_str.encode('utf-8')).hexdigest()


def _get_file_path(cache_key: str, cache_dir: str = DEFAULT_CACHE_DIR) -> str:
    """获取缓存文件路径"""
    return os.path.join(cache_dir, f"{cache_key}.json")


def get_cache(
    key: str,
    max_age: int = DEFAULT_CACHE_TTL,
    cache_dir: str = DEFAULT_CACHE_DIR,
) -> Optional[Any]:
    """
    获取缓存数据
    
    Args:
        key: 缓存键
        max_age: 最大缓存时间（秒）
        cache_dir: 缓存目录
    
    Returns:
        缓存的数据，如果不存在或过期返回 None
    """
    # 1. 先检查内存缓存
    if key in _memory_cache:
        cached_item = _memory_cache[key]
        if time.time() - cached_item['timestamp'] < max_age:
            logger.debug(f"内存缓存命中: {key}")
            return cached_item['data']
        else:
            del _memory_cache[key]
    
    # 2. 检查磁盘缓存
    _ensure_cache_dir(cache_dir)
    file_path = _get_file_path(key, cache_dir)
    
    if os.path.exists(file_path):
        try:
            # 检查文件修改时间
            file_mtime = os.path.getmtime(file_path)
            if time.time() - file_mtime < max_age:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 重新存入内存缓存
                _memory_cache[key] = {
                    'data': data,
                    'timestamp': time.time()
                }
                logger.debug(f"磁盘缓存命中: {key}")
                return data
            else:
                os.remove(file_path)  # 删除过期缓存
        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")
    
    return None


def set_cache(
    key: str,
    data: Any,
    cache_dir: str = DEFAULT_CACHE_DIR,
    use_memory: bool = True,
    use_disk: bool = True,
) -> None:
    """
    设置缓存数据
    
    Args:
        key: 缓存键
        data: 要缓存的数据
        cache_dir: 缓存目录
        use_memory: 是否使用内存缓存
        use_disk: 是否使用磁盘缓存
    """
    timestamp = time.time()
    
    # 内存缓存
    if use_memory:
        _memory_cache[key] = {
            'data': data,
            'timestamp': timestamp
        }
    
    # 磁盘缓存
    if use_disk:
        _ensure_cache_dir(cache_dir)
        file_path = _get_file_path(key, cache_dir)
        
        try:
            # 处理 pandas DataFrame
            if isinstance(data, pd.DataFrame):
                cache_data = {
                    'type': 'dataframe',
                    'data': data.to_dict('records'),
                    'columns': list(data.columns),
                    'index': list(data.index.astype(str)) if hasattr(data.index, 'astype') else list(data.index)
                }
            else:
                cache_data = {'type': 'json', 'data': data}
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.debug(f"缓存写入: {key}")
        except Exception as e:
            logger.warning(f"写入缓存失败: {e}")


def clear_cache(cache_dir: str = DEFAULT_CACHE_DIR, older_than: Optional[int] = None) -> int:
    """
    清理缓存
    
    Args:
        cache_dir: 缓存目录
        older_than: 只清理比此秒数更旧的缓存，None 则全部清理
    
    Returns:
        清理的缓存数量
    """
    count = 0
    
    # 清理内存缓存
    if older_than is None:
        _memory_cache.clear()
        count = 0
    else:
        current_time = time.time()
        keys_to_delete = [
            k for k, v in _memory_cache.items()
            if current_time - v['timestamp'] > older_than
        ]
        for k in keys_to_delete:
            del _memory_cache[k]
            count += 1
    
    # 清理磁盘缓存
    if os.path.exists(cache_dir):
        for filename in os.listdir(cache_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(cache_dir, filename)
                if older_than is None:
                    os.remove(file_path)
                    count += 1
                else:
                    file_mtime = os.path.getmtime(file_path)
                    if time.time() - file_mtime > older_than:
                        os.remove(file_path)
                        count += 1
    
    logger.info(f"清理缓存: {count} 项")
    return count


def cached(
    ttl: int = DEFAULT_CACHE_TTL,
    cache_dir: str = DEFAULT_CACHE_DIR,
    key_func: Optional[Callable] = None,
):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒）
        cache_dir: 缓存目录
        key_func: 自定义键生成函数
    
    Usage:
        @cached(ttl=3600)
        def get_stock_data(symbol, start_date, end_date):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(func.__name__, *args, **kwargs)
            
            # 尝试获取缓存
            cached_data = get_cache(cache_key, ttl, cache_dir)
            if cached_data is not None:
                # 还原 pandas DataFrame
                if isinstance(cached_data, dict) and cached_data.get('type') == 'dataframe':
                    df = pd.DataFrame(cached_data['data'])
                    if 'columns' in cached_data and 'index' in cached_data:
                        df.columns = cached_data['columns']
                        df.index = cached_data['index']
                    return df
                return cached_data
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            set_cache(cache_key, result, cache_dir)
            
            return result
        return wrapper
    return decorator


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟（秒）
        backoff: 退避系数
    
    Usage:
        @retry(max_attempts=3, delay=1.0)
        def fetch_data():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"{func.__name__} 第 {attempt + 1} 次尝试失败: {e}, "
                            f"{current_delay:.1f}秒后重试..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} 达到最大重试次数 {max_attempts}")
            
            raise last_exception
        return wrapper
    return decorator


# 便捷函数
def get_stock_cache(symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """获取股票数据缓存"""
    key = _generate_cache_key("stock_data", symbol, start_date, end_date)
    data = get_cache(key)
    if data and isinstance(data, dict) and data.get('type') == 'dataframe':
        df = pd.DataFrame(data['data'])
        df.columns = data['columns']
        return df
    return None


def set_stock_cache(symbol: str, start_date: str, end_date: str, df: pd.DataFrame) -> None:
    """设置股票数据缓存"""
    key = _generate_cache_key("stock_data", symbol, start_date, end_date)
    set_cache(key, df)


# ==================== 限流器模块 ====================

import threading
from collections import defaultdict
from typing import Dict, Tuple


class RateLimiter:
    """简单的滑动窗口限流器"""
    
    def __init__(self, calls: int = 10, period: float = 60.0):
        """
        初始化限流器
        
        Args:
            calls: 时间周期内允许的最大调用次数
            period: 时间周期（秒）
        """
        self.calls = calls
        self.period = period
        self._lock = threading.Lock()
        self._timestamps: Dict[str, list] = defaultdict(list)
    
    def acquire(self, key: str = "default") -> bool:
        """
        尝试获取调用许可
        
        Args:
            key: 限流键（可用于区分不同接口）
            
        Returns:
            True: 允许调用
            False: 达到限流阈值
        """
        with self._lock:
            now = time.time()
            # 清理过期的 timestamp
            self._timestamps[key] = [
                ts for ts in self._timestamps[key]
                if now - ts < self.period
            ]
            
            if len(self._timestamps[key]) < self.calls:
                self._timestamps[key].append(now)
                return True
            return False
    
    def wait_and_acquire(self, key: str = "default", timeout: float = 30.0) -> bool:
        """
        等待直到获取调用许可
        
        Args:
            key: 限流键
            timeout: 最大等待时间（秒）
            
        Returns:
            True: 成功获取许可
            False: 等待超时
        """
        start = time.time()
        while time.time() - start < timeout:
            if self.acquire(key):
                return True
            # 等待一段时间后重试
            sleep_time = min(0.1, timeout - (time.time() - start))
            if sleep_time > 0:
                time.sleep(sleep_time)
        return False
    
    def reset(self, key: str = None) -> None:
        """重置限流器"""
        with self._lock:
            if key:
                self._timestamps[key] = []
            else:
                self._timestamps.clear()


# 全局限流器实例
_global_rate_limiter = RateLimiter(calls=10, period=60.0)


def get_rate_limiter() -> RateLimiter:
    """获取全局限流器"""
    return _global_rate_limiter


def rate_limit(calls: int = 10, period: float = 60.0, key_func: str = "default"):
    """
    限流装饰器
    
    Args:
        calls: 时间周期内允许的最大调用次数
        period: 时间周期（秒）
        key_func: 限流键函数（可以是固定字符串或函数）
    
    Usage:
        @rate_limit(calls=10, period=60)
        def get_stock_data(symbol):
            ...
    """
    _limiter = RateLimiter(calls=calls, period=period)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成限流键
            if callable(key_func):
                rate_key = key_func(*args, **kwargs)
            else:
                rate_key = key_func
            
            # 尝试获取许可
            if not _limiter.wait_and_acquire(rate_key, timeout=30.0):
                logger.warning(f"{func.__name__} 限流等待超时: {rate_key}")
                raise RuntimeError(f"Rate limit exceeded for {func.__name__}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
