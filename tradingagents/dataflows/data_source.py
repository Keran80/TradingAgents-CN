# -*- coding: utf-8 -*-
"""
数据源路由层
根据配置自动选择通达信(TDX) 或 AkShare 数据源

使用方式：
    from tradingagents.dataflows.data_source import get_data_source
    ds = get_data_source()          # 获取当前数据源
    df = ds.get_stock_data("000001", "2024-01-01", "2024-12-31")

配置方式（.env 或 set_config）：
    TRADINGAGENTS_DATA_SOURCE=tdx       # 强制使用通达信
    TRADINGAGENTS_DATA_SOURCE=akshare   # 强制使用 AkShare
    TRADINGAGENTS_DATA_SOURCE=auto      # 自动（优先TDX，失败回退AkShare）
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 当前活跃数据源实例
_current_source = None
_current_source_name = None


def get_data_source(source: Optional[str] = None):
    """
    获取数据源实例

    Args:
        source: 数据源名称 "tdx"/"akshare"/"auto"，None 时从配置读取

    Returns:
        数据源工具类实例（TdxStockUtils 或 AkShareUtils 兼容接口）
    """
    global _current_source, _current_source_name

    # 确定目标数据源
    target = _resolve_source(source)

    # 如果已有相同数据源，直接返回
    if _current_source is not None and _current_source_name == target:
        return _current_source

    # 创建新数据源
    _current_source = _create_source(target)
    _current_source_name = target
    return _current_source


def _resolve_source(source: Optional[str]) -> str:
    """解析数据源名称"""
    if source is not None:
        return source.lower()

    # 从配置读取
    try:
        from .config import get_config
        cfg = get_config()
        return cfg.get("data_source", "auto").lower()
    except Exception:
        return "auto"


def _create_source(name: str):
    """创建数据源实例"""
    global _current_source_name
    if name == "tdx":
        src = _try_tdx()
        if src is None:
            raise RuntimeError("指定了 TDX 但无法连接通达信服务器")
        _current_source_name = "TDX (通达信)"
        return src
    elif name == "akshare":
        src = _try_akshare()
        _current_source_name = "AkShare"
        return src
    else:
        # auto：优先 TDX，失败回退 AkShare
        tdx = _try_tdx()
        if tdx is not None:
            _current_source_name = "TDX (通达信)"
            return tdx
        logger.warning("[DataSource] TDX 不可用，回退到 AkShare")
        src = _try_akshare()
        _current_source_name = "AkShare"
        return src


def _try_tdx():
    """尝试初始化通达信数据源"""
    try:
        from .tdx_utils import TdxStockUtils, _pool
        # 验证连接
        api = _pool.get_api()
        if api is None:
            raise ConnectionError("无法连接通达信服务器")
        logger.info("[DataSource] 使用数据源: 通达信 (TDX)")
        return TdxStockUtils()
    except Exception as e:
        logger.debug(f"[DataSource] TDX 初始化失败: {e}")
        return None


def _try_akshare():
    """尝试初始化 AkShare 数据源"""
    try:
        from .akshare_stock_utils import AkShareUtils
        logger.info("[DataSource] 使用数据源: AkShare")
        return AkShareUtils()
    except Exception as e:
        logger.error(f"[DataSource] AkShare 也不可用: {e}")
        raise RuntimeError("所有数据源均不可用，请检查环境")


def set_data_source(source: str) -> None:
    """
    手动切换数据源

    Args:
        source: "tdx" | "akshare" | "auto"

    Example:
        from tradingagents.dataflows.data_source import set_data_source
        set_data_source("tdx")    # 切换到通达信
        set_data_source("akshare")  # 切换到 AkShare
    """
    global _current_source, _current_source_name
    _current_source = _create_source(source.lower())
    _current_source_name = source.lower()
    logger.info(f"[DataSource] 已切换到: {source}")


def get_current_source_name() -> str:
    """返回当前数据源名称"""
    return _current_source_name or "未初始化"


def reset_data_source() -> None:
    """重置数据源（下次调用时重新初始化）"""
    global _current_source, _current_source_name
    _current_source = None
    _current_source_name = None
