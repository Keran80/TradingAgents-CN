# -*- coding: utf-8 -*-
"""
TradingAgents-CN 错误处理模块
基于 Claude Code 错误处理最佳实践
"""
from typing import Any, Optional


class TradingException(Exception):
    """交易异常基类"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DataException(TradingException):
    """数据异常 - 数据获取、解析失败"""
    pass


class APIException(TradingException):
    """API 异常 - API 调用失败"""
    def __init__(self, message: str, status_code: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code


class ConfigException(TradingException):
    """配置异常 - 配置文件无效"""
    pass


class StrategyException(TradingException):
    """策略异常 - 策略执行失败"""
    pass


class BacktestException(TradingException):
    """回测异常 - 回测执行失败"""
    pass


# ========== 错误处理装饰器 ==========

from functools import wraps
import logging

logger = logging.getLogger(__name__)


def handle_data_errors(operation: str = "数据操作"):
    """
    数据操作错误处理装饰器
    
    Usage:
        @handle_data_errors("获取股票数据")
        def fetch_stock_data(symbol):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except DataException as e:
                logger.error(f"{operation} 失败 - 数据异常：{e.message}")
                raise
            except Exception as e:
                logger.exception(f"{operation} 失败：{e}")
                raise DataException(f"{operation} 失败：{str(e)}") from e
        return wrapper
    return decorator


def handle_api_errors(operation: str = "API 调用"):
    """
    API 调用错误处理装饰器
    
    Usage:
        @handle_api_errors("获取行情数据")
        async def fetch_market_data():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except APIException as e:
                logger.error(f"{operation} 失败 - API 异常：{e.message}")
                raise
            except Exception as e:
                logger.exception(f"{operation} 失败：{e}")
                raise APIException(f"{operation} 失败：{str(e)}") from e
        return async_wrapper
    return decorator


# ========== 上下文管理器 ==========

from contextlib import contextmanager


@contextmanager
def trading_error_context(operation: str):
    """
    交易错误处理上下文管理器
    
    Usage:
        with trading_error_context("加载配置"):
            config = load_config()
    """
    try:
        yield
    except TradingException:
        raise
    except FileNotFoundError as e:
        raise ConfigException(f"{operation} 失败：文件不存在") from e
    except Exception as e:
        logger.exception(f"{operation} 失败：{e}")
        raise TradingException(f"{operation} 失败：{str(e)}") from e
