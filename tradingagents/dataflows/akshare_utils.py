# -*- coding: utf-8 -*-
"""
AkShare A股数据接口
用于替代 FinnHub 获取国内A股数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


def get_stock_daily(ticker: str, start_date: str = None, end_date: str = None, adjust: str = "qfq") -> pd.DataFrame:
    """
    获取A股日线数据
    
    Args:
        ticker: 股票代码，如 '000001'（平安银行）
        start_date: 开始日期，格式 'YYYYMMDD' 或 'YYYY-MM-DD'
        end_date: 结束日期，格式 'YYYYMMDD' 或 'YYYY-MM-DD'
        adjust: 复权类型，'qfq'前复权，'hfq'后复权，''不复权
    
    Returns:
        DataFrame 包含日期、开盘、收盘、最高、最低、成交量等
    """
    try:
        # 转换日期格式
        if start_date:
            start_date = start_date.replace('-', '')
        if end_date:
            end_date = end_date.replace('-', '')
        
        # 获取数据
        df = ak.stock_zh_a_hist(
            symbol=ticker,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        
        # 重命名列为英文
        df = df.rename(columns={
            '日期': 'date',
            '股票代码': 'symbol',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'pct_change',
            '涨跌额': 'change',
            '换手率': 'turnover'
        })
        
        return df
    
    except Exception as e:
        logger.error(f"获取日线数据失败: {e}")
        return pd.DataFrame()


def get_stock_realtime_quote(ticker: str = None) -> pd.DataFrame:
    """
    获取A股实时行情
    
    Args:
        ticker: 股票代码，如 '000001'，None表示获取所有A股
    
    Returns:
        DataFrame 包含实时行情数据
    """
    try:
        df = ak.stock_zh_a_spot_em()
        
        if ticker:
            # 筛选特定股票
            df = df[df['代码'] == ticker]
        
        return df
    
    except Exception as e:
        logger.error(f"获取实时行情失败: {e}")
        return pd.DataFrame()


def get_stock_news(ticker: str = None, symbol: str = "A股") -> pd.DataFrame:
    """
    获取A股新闻
    
    Args:
        ticker: 股票代码（可选）
        symbol: 板块/市场类型，默认 'A股'
    
    Returns:
        DataFrame 包含新闻标题、内容、发布时间等
    """
    try:
        # 使用 stock_news_em 获取新闻
        df = ak.stock_news_em(symbol=symbol)
        return df
    
    except Exception as e:
        logger.error(f"获取新闻失败: {e}")
        return pd.DataFrame()


def get_moneyflow_hsgt(period: str = "daily") -> pd.DataFrame:
    """
    获取北向资金流向
    
    Args:
        period: 数据周期，'daily'日度，'monthly'月度
    
    Returns:
        DataFrame 包含北向资金流入流出数据
    """
    try:
        df = ak.stock_hsgt_fund_flow_summary_em()
        return df
    
    except Exception as e:
        logger.error(f"获取北向资金数据失败: {e}")
        return pd.DataFrame()


def get_stock_top_list() -> pd.DataFrame:
    """
    获取今日龙虎榜数据
    
    Returns:
        DataFrame 包含龙虎榜数据
    """
    try:
        df = ak.stock_lhb_detail_em()
        return df
    
    except Exception as e:
        logger.error(f"获取龙虎榜失败: {e}")
        return pd.DataFrame()


def get_stock_top_inst(trade_date: str = None) -> pd.DataFrame:
    """
    获取龙虎榜机构明细
    
    Args:
        trade_date: 交易日期，格式 'YYYYMMDD'，默认最新
    
    Returns:
        DataFrame 包含机构买卖明细
    """
    try:
        df = ak.top_inst(trade_date=trade_date)
        return df
    
    except Exception as e:
        logger.error(f"获取龙虎榜机构明细失败: {e}")
        return pd.DataFrame()


def get_margin_detail(symbol: str = "融资融券") -> pd.DataFrame:
    """
    获取融资融券明细
    
    Args:
        symbol: 数据类型，默认 '融资融券'
    
    Returns:
        DataFrame 包含融资融券数据
    """
    try:
        df = ak.margin_detail(symbol=symbol)
        return df
    
    except Exception as e:
        logger.error(f"获取融资融券数据失败: {e}")
        return pd.DataFrame()


def get_stock_tick(ticker: str, date: str = None) -> pd.DataFrame:
    """
    获取股票分笔数据（逐笔成交）
    
    Args:
        ticker: 股票代码
        date: 日期，格式 'YYYYMMDD'
    
    Returns:
        DataFrame 包含逐笔成交数据
    """
    try:
        df = ak.stock_zh_a_tick_trans(
            ts_code=ticker,
            trade_date=date
        )
        return df
    
    except Exception as e:
        logger.error(f"获取分笔数据失败: {e}")
        return pd.DataFrame()


def get_index_daily(index_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    获取指数日线数据
    
    Args:
        index_code: 指数代码，如 '000001'（上证指数）
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        DataFrame 包含指数日线数据
    """
    try:
        df = ak.stock_zh_index_daily(symbol=index_code)
        
        if start_date:
            df = df[df['date'] >= start_date]
        if end_date:
            df = df[df['date'] <= end_date]
        
        return df
    
    except Exception as e:
        logger.error(f"获取指数数据失败: {e}")
        return pd.DataFrame()


def get_stock_financial_analysis(ticker: str) -> Dict:
    """
    获取股票财务分析数据
    
    Args:
        ticker: 股票代码
    
    Returns:
        Dict 包含财务指标数据
    """
    try:
        # 获取主要财务指标
        df = ak.stock_financial_analysis_indicator(symbol=ticker)
        
        return {
            'ticker': ticker,
            'financial_data': df.to_dict(),
            'status': 'success'
        }
    
    except Exception as e:
        logger.error(f"获取财务数据失败: {e}")
        return {
            'ticker': ticker,
            'error': str(e),
            'status': 'failed'
        }


# 便捷函数：将 DataFrame 转换为字符串格式
def format_stock_data_for_agent(df: pd.DataFrame, ticker: str, days: int = 30) -> str:
    """
    将股票数据格式化为 Agent 可读的字符串
    
    Args:
        df: 股票数据 DataFrame
        ticker: 股票代码
        days: 显示天数
    
    Returns:
        str 格式化的数据字符串
    """
    if df.empty:
        return f"暂无 {ticker} 数据"
    
    # 取最近 N 天数据
    df = df.tail(days)
    
    # 格式化输出
    result = f"## {ticker} 最近{days}个交易日数据:\n\n"
    
    for _, row in df.iterrows():
        date = row.get('date', row.get('日期', 'N/A'))
        close = row.get('close', row.get('收盘', 'N/A'))
        open_price = row.get('open', row.get('开盘', 'N/A'))
        high = row.get('high', row.get('最高', 'N/A'))
        low = row.get('low', row.get('最低', 'N/A'))
        volume = row.get('volume', row.get('成交量', 'N/A'))
        
        result += f"- {date}: 开盘 {open_price}, 收盘 {close}, 最高 {high}, 最低 {low}, 成交量 {volume}\n"
    
    return result
