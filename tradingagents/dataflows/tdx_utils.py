# -*- coding: utf-8 -*-
"""
通达信股票数据接口 (pytdx)
直接连接通达信行情服务器，获取 A 股实时/历史数据
无需安装通达信软件，无需 API Key，国内访问极速稳定

优点：
  - 比 AkShare 更快（直接 TCP 协议，无 HTTP 开销）
  - 数据覆盖更全（分钟线、日线、周线、月线、实时五档报价）
  - 支持除权除息信息
  - 完全离线可用（只需网络能到通达信服务器）
"""

import pandas as pd
import numpy as np
import logging
import time
import threading
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

# ─── 通达信服务器列表（自动选择最优） ─────────────────────────────────────────
TDX_SERVERS = [
    ("218.75.126.9", 7709),
    ("119.147.212.81", 7709),
    ("121.14.110.210", 7709),
    ("221.231.141.60", 7709),
    ("14.215.128.18", 7709),
    ("106.14.95.149", 7709),
    ("47.107.75.159", 7709),
    ("60.28.23.80", 7709),
]

# K 线类型映射
K_TYPE_MAP = {
    "1min":   7,
    "5min":   0,
    "15min":  1,
    "30min":  2,
    "60min":  3,
    "daily":  9,
    "weekly": 5,
    "monthly": 6,
}

# ─── 市场代码工具 ─────────────────────────────────────────────────────────────

def get_market(symbol: str) -> int:
    """
    根据股票代码判断市场
    Returns:
        0 = 深交所 (SZ)
        1 = 上交所 (SH)
    """
    code = symbol.strip()
    # 去除交易所后缀
    if "." in code:
        parts = code.split(".")
        code = parts[0]
        suffix = parts[1].upper() if len(parts) > 1 else ""
        if suffix == "SH":
            return 1
        if suffix == "SZ":
            return 0

    # 按代码前缀判断
    if code.startswith(("6", "5", "900")):
        return 1  # 上交所
    elif code.startswith(("0", "1", "2", "3")):
        return 0  # 深交所
    elif code.startswith(("000", "300", "002")):
        return 0
    else:
        return 0


def normalize_symbol(symbol: str) -> str:
    """将股票代码规范化为 6 位纯数字"""
    code = symbol.strip()
    if "." in code:
        code = code.split(".")[0]
    return code.zfill(6)


# ─── 连接池 ─────────────────────────────────────────────────────────────────


class TdxConnectionPool:
    """线程安全的通达信连接池（单连接，自动重连）"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._api = None
                cls._instance._server = None
                cls._instance._api_lock = threading.Lock()
        return cls._instance

    def _create_api(self):
        """创建并连接到最优服务器"""
        try:
            from pytdx.hq import TdxHq_API
        except ImportError:
            raise ImportError(
                "pytdx 未安装，请运行: pip install pytdx"
            )

        for ip, port in TDX_SERVERS:
            try:
                api = TdxHq_API(raise_exception=False, auto_retry=True)
                if api.connect(ip, port):
                    # 简单验证连通性
                    test = api.get_security_bars(9, 0, "000001", 0, 1)
                    if test:
                        logger.info(f"[TDX] 已连接服务器 {ip}:{port}")
                        self._server = (ip, port)
                        return api
                api.disconnect()
            except Exception as e:
                logger.debug(f"[TDX] 服务器 {ip}:{port} 不可用: {e}")
                continue

        raise ConnectionError("所有通达信服务器均不可用，请检查网络连接")

    def get_api(self):
        """获取可用 API 实例（自动重连）"""
        with self._api_lock:
            if self._api is None:
                self._api = self._create_api()
            return self._api

    def reset(self):
        """重置连接（遇到错误时调用）"""
        with self._api_lock:
            if self._api is not None:
                try:
                    self._api.disconnect()
                except Exception:
                    pass
                self._api = None
                self._server = None


_pool = TdxConnectionPool()


def _with_retry(func):
    """装饰器：失败时自动重置连接并重试"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        for attempt in range(3):
            try:
                api = _pool.get_api()
                return func(api, *args, **kwargs)
            except Exception as e:
                logger.warning(f"[TDX] 请求失败 (attempt {attempt+1}/3): {e}")
                _pool.reset()
                time.sleep(0.5 * (attempt + 1))
        logger.error(f"[TDX] {func.__name__} 多次重试均失败")
        return None
    return wrapper


# ─── 核心数据获取函数 ─────────────────────────────────────────────────────────


@_with_retry
def _get_security_bars_raw(api, market: int, symbol: str, k_type: int,
                            offset: int, count: int) -> Optional[list]:
    """获取 K 线原始数据"""
    return api.get_security_bars(k_type, market, symbol, offset, count)


@_with_retry
def _get_security_quotes_raw(api, params: list) -> Optional[list]:
    """获取实时报价"""
    return api.get_security_quotes(params)


@_with_retry
def _get_finance_info_raw(api, market: int, symbol: str) -> Optional[dict]:
    """获取财务信息"""
    return api.get_finance_info(market, symbol)


@_with_retry
def _get_security_list_raw(api, market: int, offset: int) -> Optional[list]:
    """获取股票列表"""
    return api.get_security_list(market, offset)


@_with_retry
def _get_security_count_raw(api, market: int) -> Optional[int]:
    """获取市场股票数量"""
    return api.get_security_count(market)


@_with_retry
def _get_xdxr_info_raw(api, market: int, symbol: str) -> Optional[list]:
    """获取除权除息数据"""
    return api.get_xdxr_info(market, symbol)


@_with_retry
def _to_df(api, data) -> pd.DataFrame:
    """转换为 DataFrame"""
    return api.to_df(data)


# ─── 高层接口函数 ─────────────────────────────────────────────────────────────


def get_stock_bars(
    symbol: str,
    start_date: str,
    end_date: str,
    k_type: str = "daily",
    adjust: bool = True,
) -> pd.DataFrame:
    """
    获取股票 K 线数据（支持日线/分钟线）

    Args:
        symbol: 股票代码（如 '000001' 或 '000001.SZ'）
        start_date: 开始日期 'YYYY-MM-DD'
        end_date: 结束日期 'YYYY-MM-DD'
        k_type: K 线类型 daily/1min/5min/15min/30min/60min/weekly/monthly
        adjust: 是否前复权（日线有效）

    Returns:
        DataFrame: Date/Open/High/Low/Close/Volume/Amount/Adj Close
    """
    code = normalize_symbol(symbol)
    market = get_market(symbol)
    cat = K_TYPE_MAP.get(k_type, 9)

    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date)

    all_bars = []
    offset = 0
    max_per_req = 800  # 通达信每次最多返回 800 条

    while True:
        raw = _get_security_bars_raw(market, code, cat, offset, max_per_req)
        if not raw:
            break

        try:
            api = _pool.get_api()
            df_chunk = api.to_df(raw)
        except Exception:
            break

        if df_chunk is None or df_chunk.empty:
            break

        all_bars.append(df_chunk)

        # 检查是否已超出 start_date 范围
        earliest = pd.Timestamp(df_chunk["datetime"].min())
        if earliest <= start_dt:
            break

        # 还没到 start_date，继续往前取
        if len(raw) < max_per_req:
            break  # 已取完所有历史数据

        offset += max_per_req
        time.sleep(0.05)  # 防止频率过快

    if not all_bars:
        logger.warning(f"[TDX] {symbol} 未获取到数据")
        return pd.DataFrame()

    df = pd.concat(all_bars, ignore_index=True)

    # 解析日期列
    df["Date"] = pd.to_datetime(df["datetime"].str[:10])

    # 过滤日期范围
    df = df[(df["Date"] >= start_dt) & (df["Date"] <= end_dt)]

    if df.empty:
        return pd.DataFrame()

    # 重命名列
    df = df.rename(columns={
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "vol": "Volume",
        "amount": "Amount",
    })

    # 如果是日线且需要复权，应用除权除息系数
    if k_type == "daily" and adjust:
        df = _apply_adjust(df, symbol, market, code)

    df["Adj Close"] = df["Close"]

    # 去重、排序
    df = df.drop_duplicates(subset=["Date"]).sort_values("Date")
    df = df.set_index("Date")

    # 选择标准列
    keep_cols = ["Open", "High", "Low", "Close", "Volume", "Amount", "Adj Close"]
    df = df[[c for c in keep_cols if c in df.columns]]

    return df


def _apply_adjust(df: pd.DataFrame, symbol: str, market: int, code: str) -> pd.DataFrame:
    """应用前复权系数（基于除权除息数据）"""
    try:
        xdxr_raw = _get_xdxr_info_raw(market, code)
        if not xdxr_raw:
            return df

        api = _pool.get_api()
        xdxr = api.to_df(xdxr_raw)

        if xdxr is None or xdxr.empty:
            return df

        # 仅处理分红（category=1）和送转股（category=9）
        xdxr = xdxr[xdxr["category"].isin([1, 9])].copy()

        if xdxr.empty:
            return df

        # 构建复权因子（前复权：从最新一期向前计算）
        # 前复权公式：复权价 = (原价 - 每股分红 + 配股价×配股比例) / (1 + 送转比 + 配股比例)
        for _, row in xdxr.iterrows():
            try:
                xdxr_date = pd.Timestamp(
                    f"{int(row['year'])}-{int(row['month']):02d}-{int(row['day']):02d}"
                )
                fenhong = float(row.get("fenhong", 0) or 0) / 10.0  # 每股分红（元）
                songzhuangu = float(row.get("songzhuangu", 0) or 0)  # 送转比例
                peigu = float(row.get("peigu", 0) or 0)  # 配股比例
                peigujia = float(row.get("peigujia", 0) or 0)  # 配股价

                factor_divisor = 1.0 + songzhuangu + peigu
                if factor_divisor == 0:
                    continue

                # 对除权日之前的数据应用复权系数
                mask = df["Date"] < xdxr_date
                if mask.sum() == 0:
                    continue

                for col in ["Open", "High", "Low", "Close"]:
                    if col in df.columns:
                        df.loc[mask, col] = (
                            df.loc[mask, col] - fenhong + peigujia * peigu
                        ) / factor_divisor

            except Exception as xe:
                logger.debug(f"[TDX] 复权计算跳过: {xe}")
                continue

    except Exception as e:
        logger.debug(f"[TDX] 复权数据获取失败，使用不复权数据: {e}")

    return df


def get_realtime_quotes(symbols: List[str]) -> pd.DataFrame:
    """
    获取多只股票的实时行情（五档报价）

    Args:
        symbols: 股票代码列表，如 ['000001', '600000']

    Returns:
        DataFrame: code/price/open/high/low/vol/amount/bid1~5/ask1~5
    """
    params = [(get_market(s), normalize_symbol(s)) for s in symbols]
    raw = _get_security_quotes_raw(params)
    if not raw:
        return pd.DataFrame()

    try:
        api = _pool.get_api()
        df = api.to_df(raw)
        return df
    except Exception as e:
        logger.error(f"[TDX] 实时报价解析失败: {e}")
        return pd.DataFrame()


def get_finance_info(symbol: str) -> Dict[str, Any]:
    """
    获取股票财务信息（来自通达信财务文件）

    Returns:
        dict: 包含总股本、流通股本、净资产、每股收益等财务指标
    """
    code = normalize_symbol(symbol)
    market = get_market(symbol)
    raw = _get_finance_info_raw(market, code)

    if not raw:
        return {}

    try:
        info = dict(raw)
        # 数值单位转换（通达信原始值单位为 "分"，即 /100）
        return {
            "symbol": symbol,
            "total_shares": info.get("zongguben", 0),
            "circulating_shares": info.get("liutongguben", 0),
            "total_assets": info.get("zongzichan", 0),
            "net_assets": info.get("jingzichan", 0),
            "main_revenue": info.get("zhuyingshouru", 0),
            "main_profit": info.get("zhuyinglirun", 0),
            "net_profit": info.get("jinglirun", 0),
            "operating_cashflow": info.get("jingyingxianjinliu", 0),
            "total_cashflow": info.get("zongxianjinliu", 0),
            "undistributed_profit": info.get("weifenpeilirun", 0),
            "net_asset_per_share": info.get("meigujingzichan", 0),
            "capital_reserve": info.get("zibengongjijin", 0),
            "shareholders_count": info.get("gudongrenshu", 0),
            "province": info.get("province", 0),
            "industry": info.get("industry", 0),
            "ipo_date": str(info.get("ipo_date", "")),
            "updated_date": str(info.get("updated_date", "")),
        }
    except Exception as e:
        logger.error(f"[TDX] 财务信息解析失败: {e}")
        return {}


def get_stock_list(market: int = -1) -> pd.DataFrame:
    """
    获取股票列表

    Args:
        market: -1=全部, 0=深交所, 1=上交所

    Returns:
        DataFrame: code/name/market
    """
    results = []
    markets = [0, 1] if market == -1 else [market]

    for m in markets:
        try:
            count = _get_security_count_raw(m)
            if not count:
                continue

            offset = 0
            while offset < count:
                raw = _get_security_list_raw(m, offset)
                if not raw:
                    break
                api = _pool.get_api()
                df_chunk = api.to_df(raw)
                if df_chunk is not None and not df_chunk.empty:
                    df_chunk["market"] = m
                    results.append(df_chunk)
                offset += len(raw)
                time.sleep(0.05)
        except Exception as e:
            logger.error(f"[TDX] 获取市场 {m} 股票列表失败: {e}")

    if not results:
        return pd.DataFrame()

    return pd.concat(results, ignore_index=True)


def get_xdxr_info(symbol: str) -> pd.DataFrame:
    """
    获取除权除息信息

    Returns:
        DataFrame: year/month/day/category/fenhong/songzhuangu/peigu
    """
    code = normalize_symbol(symbol)
    market = get_market(symbol)
    raw = _get_xdxr_info_raw(market, code)

    if not raw:
        return pd.DataFrame()

    try:
        api = _pool.get_api()
        df = api.to_df(raw)
        return df
    except Exception as e:
        logger.error(f"[TDX] 除权除息解析失败: {e}")
        return pd.DataFrame()


# ─── TradingAgents 适配接口（对标 AkShareUtils）───────────────────────────────


class TdxStockUtils:
    """
    通达信数据适配器 — 与 AkShareUtils 接口兼容
    可直接替换 tradingagents/dataflows/akshare_stock_utils.py 的 AkShareUtils 类
    """

    @staticmethod
    def get_stock_data(
        symbol: str,
        start_date: str,
        end_date: str,
        save_path: Optional[str] = None,
        use_cache: bool = True,
        k_type: str = "daily",
    ) -> pd.DataFrame:
        """
        获取股票 K 线数据

        Args:
            symbol: 股票代码（如 '000001' 或 '000001.SZ'）
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
            save_path: 保存路径（可选）
            use_cache: 暂未实现（预留兼容参数）
            k_type: K 线类型 daily/1min/5min/15min/30min/60min

        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume, Amount, Adj Close
        """
        df = get_stock_bars(symbol, start_date, end_date, k_type=k_type)

        if save_path and not df.empty:
            df.to_csv(save_path)
            logger.info(f"[TDX] 数据已保存到 {save_path}")

        return df

    @staticmethod
    def get_stock_info(symbol: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        获取股票基本信息

        Returns:
            dict: shortName/industry/totalShares/circulatingShares/totalMarketCap/listingDate
        """
        fin = get_finance_info(symbol)
        if not fin:
            return {}

        # 获取股票名称（通过实时报价）
        try:
            qt = get_realtime_quotes([symbol])
            name = qt["code"].iloc[0] if not qt.empty else symbol
            price = float(qt["price"].iloc[0]) if not qt.empty else 0.0
        except Exception:
            name = symbol
            price = 0.0

        total_shares = fin.get("total_shares", 0) or 0
        circ_shares = fin.get("circulating_shares", 0) or 0

        return {
            "shortName": name,
            "industry": str(fin.get("industry", "N/A")),
            "sector": str(fin.get("province", "N/A")),
            "totalShares": total_shares,
            "circulatingShares": circ_shares,
            "totalMarketCap": total_shares * price,
            "circulatingMarketCap": circ_shares * price,
            "listingDate": fin.get("ipo_date", ""),
            "netAssetPerShare": fin.get("net_asset_per_share", 0),
            "netProfit": fin.get("net_profit", 0),
            "mainRevenue": fin.get("main_revenue", 0),
        }

    @staticmethod
    def get_company_info(symbol: str, save_path: Optional[str] = None) -> pd.DataFrame:
        """获取公司信息"""
        info = TdxStockUtils.get_stock_info(symbol)
        if not info:
            return pd.DataFrame()

        company_info = {
            "Company Name": info.get("shortName", "N/A"),
            "Industry": info.get("industry", "N/A"),
            "Sector": info.get("sector", "N/A"),
            "Listing Date": info.get("listingDate", "N/A"),
            "Total Shares": info.get("totalShares", 0),
            "Net Asset Per Share": info.get("netAssetPerShare", 0),
        }
        df = pd.DataFrame([company_info])

        if save_path:
            df.to_csv(save_path, index=False)

        return df

    @staticmethod
    def get_stock_dividends(symbol: str, save_path: Optional[str] = None) -> pd.DataFrame:
        """获取除权除息（分红送转）数据"""
        df = get_xdxr_info(symbol)

        if not df.empty and save_path:
            df.to_csv(save_path, index=False)

        return df

    @staticmethod
    def get_income_stmt(symbol: str) -> pd.DataFrame:
        """获取利润表（通达信财务摘要）"""
        fin = get_finance_info(symbol)
        if not fin:
            return pd.DataFrame()

        data = {
            "指标": ["主营收入", "主营利润", "营业利润", "净利润", "经营现金流"],
            "数值": [
                fin.get("main_revenue", 0),
                fin.get("main_profit", 0),
                fin.get("main_profit", 0),
                fin.get("net_profit", 0),
                fin.get("operating_cashflow", 0),
            ]
        }
        return pd.DataFrame(data)

    @staticmethod
    def get_balance_sheet(symbol: str) -> pd.DataFrame:
        """获取资产负债表摘要"""
        fin = get_finance_info(symbol)
        if not fin:
            return pd.DataFrame()

        data = {
            "指标": ["总资产", "净资产", "资本公积金", "未分配利润", "总股本", "流通股本"],
            "数值": [
                fin.get("total_assets", 0),
                fin.get("net_assets", 0),
                fin.get("capital_reserve", 0),
                fin.get("undistributed_profit", 0),
                fin.get("total_shares", 0),
                fin.get("circulating_shares", 0),
            ]
        }
        return pd.DataFrame(data)

    @staticmethod
    def get_cash_flow(symbol: str) -> pd.DataFrame:
        """获取现金流量摘要"""
        fin = get_finance_info(symbol)
        if not fin:
            return pd.DataFrame()

        data = {
            "指标": ["经营现金流", "总现金流"],
            "数值": [
                fin.get("operating_cashflow", 0),
                fin.get("total_cashflow", 0),
            ]
        }
        return pd.DataFrame(data)

    @staticmethod
    def get_analyst_recommendations(symbol: str) -> Tuple[Optional[str], int]:
        """通达信无分析师评级数据，返回占位值"""
        return None, 0

    @staticmethod
    def get_realtime_quote(symbol: str) -> Dict[str, Any]:
        """
        获取实时行情（通达信专属，AkShareUtils 无此接口）

        Returns:
            dict: price/open/high/low/vol/amount/bid1~5/ask1~5
        """
        df = get_realtime_quotes([symbol])
        if df.empty:
            return {}

        row = df.iloc[0]
        return {
            "price": float(row.get("price", 0)),
            "open": float(row.get("open", 0)),
            "high": float(row.get("high", 0)),
            "low": float(row.get("low", 0)),
            "last_close": float(row.get("last_close", 0)),
            "volume": float(row.get("vol", 0)),
            "amount": float(row.get("amount", 0)),
            "bid1": float(row.get("bid1", 0)),
            "ask1": float(row.get("ask1", 0)),
            "bid_vol1": float(row.get("bid_vol1", 0)),
            "ask_vol1": float(row.get("ask_vol1", 0)),
            "bid2": float(row.get("bid2", 0)),
            "ask2": float(row.get("ask2", 0)),
            "bid3": float(row.get("bid3", 0)),
            "ask3": float(row.get("ask3", 0)),
            "bid4": float(row.get("bid4", 0)),
            "ask4": float(row.get("ask4", 0)),
            "bid5": float(row.get("bid5", 0)),
            "ask5": float(row.get("ask5", 0)),
            "b_vol": float(row.get("b_vol", 0)),
            "s_vol": float(row.get("s_vol", 0)),
        }


# ─── 便捷函数（模块级） ────────────────────────────────────────────────────────

def get_stock_data(symbol, start_date, end_date, save_path=None, k_type="daily"):
    """获取 K 线数据"""
    return TdxStockUtils.get_stock_data(symbol, start_date, end_date, save_path, k_type=k_type)


def get_stock_info(symbol):
    """获取股票基本信息"""
    return TdxStockUtils.get_stock_info(symbol)


def get_company_info(symbol, save_path=None):
    """获取公司信息"""
    return TdxStockUtils.get_company_info(symbol, save_path)


def get_stock_dividends(symbol, save_path=None):
    """获取分红数据"""
    return TdxStockUtils.get_stock_dividends(symbol, save_path)


def get_income_stmt(symbol):
    """获取利润表摘要"""
    return TdxStockUtils.get_income_stmt(symbol)


def get_balance_sheet(symbol):
    """获取资产负债表摘要"""
    return TdxStockUtils.get_balance_sheet(symbol)


def get_cash_flow(symbol):
    """获取现金流量摘要"""
    return TdxStockUtils.get_cash_flow(symbol)


def get_analyst_recommendations(symbol):
    """获取分析师建议（通达信不支持，返回占位值）"""
    return TdxStockUtils.get_analyst_recommendations(symbol)


# 单例实例（兼容 AkShareUtils 的 aks 调用方式）
tdx = TdxStockUtils()
