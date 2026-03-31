# -*- coding: utf-8 -*-
"""
A股数据全面适配模块
用于 TradingAgents-CN 框架
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


# A股常用指数代码映射
INDEX_CODES = {
    '上证指数': '000001',
    '深证成指': '399001',
    '创业板指': '399006',
    '科创50': '000688',
    '沪深300': '000300',
    '上证50': '000016',
    '中证500': '000905',
    '中证1000': '000852',
}

# A股市场板块
MARKET_SECTORS = {
    '银行': 'BK0401',
    '证券': 'BK0473',
    '保险': 'BK0415',
    '白酒': 'BK0504',
    '新能源车': 'BK0725',
    '光伏': 'BK0588',
    '医药': 'BK0465',
    '半导体': 'BK1033',
    '人工智能': 'BK1036',
}


class AStockData:
    """A股数据获取类"""
    
    @staticmethod
    def get_realtime_quote(ticker: str = None) -> pd.DataFrame:
        """
        获取A股实时行情
        
        Args:
            ticker: 股票代码，如 '000001'，None表示获取全部
        
        Returns:
            DataFrame: 实时行情数据
        """
        try:
            df = ak.stock_zh_a_spot_em()
            if ticker:
                df = df[df['代码'] == ticker]
            return df
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_daily(ticker: str, start_date: str = None, end_date: str = None, 
                  adjust: str = "qfq") -> pd.DataFrame:
        """
        获取A股日线数据
        
        Args:
            ticker: 股票代码，如 '000001'
            start_date: 开始日期 'YYYYMMDD'
            end_date: 结束日期 'YYYYMMDD'
            adjust: 复权类型 'qfq'前复权 'hfq'后复权 ''不复权
        
        Returns:
            DataFrame: 日线数据
        """
        try:
            if start_date:
                start_date = start_date.replace('-', '')
            if end_date:
                end_date = end_date.replace('-', '')
                
            df = ak.stock_zh_a_hist(
                symbol=ticker,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            return df
        except Exception as e:
            logger.error(f"获取日线数据失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_weekly(ticker: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取A股周线数据"""
        try:
            if start_date:
                start_date = start_date.replace('-', '')
            if end_date:
                end_date = end_date.replace('-', '')
                
            df = ak.stock_zh_a_hist(
                symbol=ticker,
                period="weekly",
                start_date=start_date,
                end_date=end_date
            )
            return df
        except Exception as e:
            logger.error(f"获取周线数据失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_minute(ticker: str, period: str = "5", adjust: str = "qfq") -> pd.DataFrame:
        """
        获取A股分钟线数据
        
        Args:
            ticker: 股票代码
            period: 周期 '1'/'5'/'15'/'30'/'60'
            adjust: 复权类型
        """
        try:
            df = ak.stock_zh_a_hist_min_em(
                symbol=ticker,
                period=period,
                adjust=adjust
            )
            return df
        except Exception as e:
            logger.error(f"获取分钟数据失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_realtime_bid(ticker: str) -> pd.DataFrame:
        """获取实时涨跌停价格"""
        try:
            df = ak.stock_zh_a_staple_price_em()
            if ticker:
                df = df[df['代码'] == ticker]
            return df
        except Exception as e:
            logger.error(f"获取涨跌停数据失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_index_spot() -> pd.DataFrame:
        """获取所有指数实时行情"""
        try:
            df = ak.stock_zh_index_spot_em()
            return df
        except Exception as e:
            logger.error(f"获取指数行情失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_index_daily(index_code: str, start_date: str = None, 
                        end_date: str = None) -> pd.DataFrame:
        """获取指数日线"""
        try:
            df = ak.stock_zh_index_daily(symbol=index_code)
            if start_date:
                df = df[df['date'] >= start_date]
            if end_date:
                df = df[df['date'] <= end_date]
            return df
        except Exception as e:
            logger.error(f"获取指数日线失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_stock_info(ticker: str) -> Dict:
        """获取股票基本信息"""
        try:
            df = ak.stock_individual_info_em(symbol=ticker)
            info = {}
            for _, row in df.iterrows():
                info[row['item']] = row['value']
            return info
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return {}
    
    @staticmethod
    def get_financial_report(ticker: str, report_type: str = "annual") -> pd.DataFrame:
        """
        获取财务报表
        
        Args:
            ticker: 股票代码
            report_type: 'annual'年报 'season'季报
        """
        try:
            df = ak.stock_financial_abstract_ths(symbol=ticker, indicator="按报告期")
            return df
        except Exception as e:
            logger.error(f"获取财务报表失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_financial_indicator(ticker: str) -> pd.DataFrame:
        """获取财务指标"""
        try:
            df = ak.stock_financial_analysis_indicator(symbol=ticker)
            return df
        except Exception as e:
            logger.error(f"获取财务指标失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_moneyflow_hsgt(period: str = "daily") -> pd.DataFrame:
        """获取北向资金流向"""
        try:
            df = ak.stock_hsgt_fund_flow_summary_em()
            return df
        except Exception as e:
            logger.error(f"获取北向资金失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_moneyflow_hsgt_stocks() -> pd.DataFrame:
        """获取北向资金持仓股票"""
        try:
            df = ak.stock_hsgt_hold_stock_em()
            return df
        except Exception as e:
            logger.error(f"获取北向持仓失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_margin_detail() -> pd.DataFrame:
        """获取融资融券明细"""
        try:
            df = ak.margin_detail(symbol="融资融券")
            return df
        except Exception as e:
            logger.error(f"获取融资融券失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_margin_top() -> pd.DataFrame:
        """获取融资融券热门股票"""
        try:
            df = ak.margin_top_em()
            return df
        except Exception as e:
            logger.error(f"获取融资融券热门失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_lhb_detail() -> pd.DataFrame:
        """获取龙虎榜明细"""
        try:
            df = ak.stock_lhb_detail_em()
            return df
        except Exception as e:
            logger.error(f"获取龙虎榜失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_lhb_stocks() -> pd.DataFrame:
        """获取龙虎榜上榜股票"""
        try:
            df = ak.stock_lhb_em()
            return df
        except Exception as e:
            logger.error(f"获取龙虎榜股票失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_top_inst(trade_date: str = None) -> pd.DataFrame:
        """获取龙虎榜机构明细"""
        try:
            df = ak.top_inst(trade_date=trade_date)
            return df
        except Exception as e:
            logger.error(f"获取机构明细失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_stock_news(symbol: str = "A股") -> pd.DataFrame:
        """获取A股新闻"""
        try:
            df = ak.stock_news_em(symbol=symbol)
            return df
        except Exception as e:
            logger.error(f"获取新闻失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_stock_notice(ticker: str = None) -> pd.DataFrame:
        """获取股票公告"""
        try:
            df = ak.stock_notice_em()
            if ticker:
                df = df[df['代码'] == ticker]
            return df
        except Exception as e:
            logger.error(f"获取公告失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_stock_block_trade() -> pd.DataFrame:
        """获取大宗交易数据"""
        try:
            df = ak.stock_block_trade_em()
            return df
        except Exception as e:
            logger.error(f"获取大宗交易失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_stock_holdertrade(ticker: str = None) -> pd.DataFrame:
        """获取股东增减持数据"""
        try:
            df = ak.stock_holdertrade_em()
            if ticker:
                df = df[df['代码'] == ticker]
            return df
        except Exception as e:
            logger.error(f"获取股东增减持失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_stock_kline(ticker: str, start_date: str = None, 
                        end_date: str = None) -> pd.DataFrame:
        """获取股票K线数据（未复权）"""
        try:
            if start_date:
                start_date = start_date.replace('-', '')
            if end_date:
                end_date = end_date.replace('-', '')
                
            df = ak.stock_zh_a_hist(
                symbol=ticker,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=""
            )
            return df
        except Exception as e:
            logger.error(f"获取K线失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_stock_tick(ticker: str, date: str = None) -> pd.DataFrame:
        """获取分笔成交数据"""
        try:
            df = ak.stock_zh_a_tick_trans(
                ts_code=ticker,
                trade_date=date
            )
            return df
        except Exception as e:
            logger.error(f"获取分笔数据失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_stock_zt_pool() -> pd.DataFrame:
        """获取涨停板池"""
        try:
            df = ak.stock_zt_pool_em()
            return df
        except Exception as e:
            logger.error(f"获取涨停池失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_stock_zt_pool_strong() -> pd.DataFrame:
        """获取强势涨停股"""
        try:
            df = ak.stock_zt_pool_strong_em()
            return df
        except Exception as e:
            logger.error(f"获取强势涨停失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_stock_zt_pool_subnew() -> pd.DataFrame:
        """获取次新股"""
        try:
            df = ak.stock_zt_pool_subnew_em()
            return df
        except Exception as e:
            logger.error(f"获取次新股失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_limit_list(date: str = None) -> pd.DataFrame:
        """获取涨跌停列表"""
        try:
            df = ak.stock_zt_pool_em(date=date)
            return df
        except Exception as e:
            logger.error(f"获取涨跌停列表失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_fund_flow() -> pd.DataFrame:
        """获取资金流向"""
        try:
            df = ak.stock_fund_flow_em()
            return df
        except Exception as e:
            logger.error(f"获取资金流向失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_sector_flow() -> pd.DataFrame:
        """获取板块资金流向"""
        try:
            df = ak.stock_sector_fund_flow_rank_em()
            return df
        except Exception as e:
            logger.error(f"获取板块资金流向失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_industry_stocks(industry: str) -> pd.DataFrame:
        """获取行业股票列表"""
        try:
            df = ak.stock_board_industry_name_em()
            return df
        except Exception as e:
            logger.error(f"获取行业股票失败: {e}")
            return pd.DataFrame()


# 便捷函数
def get_stock_realtime_quote(ticker: str = None) -> pd.DataFrame:
    """获取实时行情"""
    return AStockData.get_realtime_quote(ticker)


def get_stock_daily(ticker: str, start_date: str = None, 
                    end_date: str = None, adjust: str = "qfq") -> pd.DataFrame:
    """获取日线数据"""
    return AStockData.get_daily(ticker, start_date, end_date, adjust)


def get_stock_news(ticker: str = None, symbol: str = "A股") -> pd.DataFrame:
    """获取新闻"""
    return AStockData.get_stock_news(symbol)


def get_moneyflow_hsgt(period: str = "daily") -> pd.DataFrame:
    """获取北向资金"""
    return AStockData.get_moneyflow_hsgt(period)


def get_stock_top_list() -> pd.DataFrame:
    """获取龙虎榜"""
    return AStockData.get_lhb_stocks()


def get_stock_top_inst(trade_date: str = None) -> pd.DataFrame:
    """获取机构明细"""
    return AStockData.get_top_inst(trade_date)


def get_margin_detail(symbol: str = "融资融券") -> pd.DataFrame:
    """获取融资融券"""
    return AStockData.get_margin_detail()


def get_index_daily(index_code: str, start_date: str = None, 
                    end_date: str = None) -> pd.DataFrame:
    """获取指数日线"""
    return AStockData.get_index_daily(index_code, start_date, end_date)


def format_stock_data_for_agent(df: pd.DataFrame, ticker: str, days: int = 30) -> str:
    """格式化股票数据为Agent可读格式"""
    if df.empty:
        return f"暂无 {ticker} 数据"
    
    df = df.tail(days)
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
