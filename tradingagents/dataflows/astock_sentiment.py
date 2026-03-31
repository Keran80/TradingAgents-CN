# -*- coding: utf-8 -*-
"""
A股新闻和情绪分析数据模块
用于 TradingAgents-CN 框架
基于 AkShare 提供的数据接口
版本: AkShare 1.18.48 兼容
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class AStockNews:
    """A股新闻数据获取类"""
    
    @staticmethod
    def get_stock_news(symbol: str = "A股") -> pd.DataFrame:
        """获取东方财富个股新闻"""
        try:
            df = ak.stock_news_em(symbol=symbol)
            return df
        except Exception as e:
            logger.error(f"获取个股新闻失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_notice() -> pd.DataFrame:
        """获取个股公告"""
        try:
            df = ak.stock_notice_em()
            return df
        except Exception as e:
            logger.error(f"获取个股公告失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_cctv_news() -> pd.DataFrame:
        """获取新闻联播文字稿"""
        try:
            df = ak.news_cctv()
            return df
        except Exception as e:
            logger.error(f"获取新闻联播失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_news_report() -> pd.DataFrame:
        """获取百度新闻报道时间"""
        try:
            df = ak.news_report_time_baidu()
            return df
        except Exception as e:
            logger.error(f"获取新闻报道时间失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_suspended_news() -> pd.DataFrame:
        """获取停复牌通知"""
        try:
            df = ak.news_trade_notify_suspend_baidu()
            return df
        except Exception as e:
            logger.error(f"获取停复牌通知失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_dividend_news() -> pd.DataFrame:
        """获取分红送转通知"""
        try:
            df = ak.news_trade_notify_dividend_baidu()
            return df
        except Exception as e:
            logger.error(f"获取分红送转通知失败: {e}")
            return pd.DataFrame()


class AStockSentiment:
    """A股情绪/舆情数据获取类 - 基于 AkShare 1.18.48 验证接口"""
    
    # ===== 东方财富热度数据 =====
    
    @staticmethod
    def get_东财热度排行(limit: int = 50) -> pd.DataFrame:
        """获取东方财富股票热度排行榜"""
        try:
            df = ak.stock_hot_rank_em()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取东财热度排行失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_东财热度最新(limit: int = 50) -> pd.DataFrame:
        """获取东方财富股票热度最新排行"""
        try:
            df = ak.stock_hot_rank_latest_em()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取东财热度最新排行失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_东财飙升榜(limit: int = 50) -> pd.DataFrame:
        """获取东方财富股票热度飙升榜"""
        try:
            df = ak.stock_hot_up_em()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取东财飙升榜失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_东财热度详情实时() -> pd.DataFrame:
        """获取东方财富热度详情实时数据"""
        try:
            df = ak.stock_hot_rank_detail_realtime_em()
            return df
        except Exception as e:
            logger.error(f"获取东财热度详情实时失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_东财热搜关键词() -> pd.DataFrame:
        """获取东方财富热搜关键词"""
        try:
            df = ak.stock_hot_keyword_em()
            return df
        except Exception as e:
            logger.error(f"获取东财热搜关键词失败: {e}")
            return pd.DataFrame()
    
    # ===== 港股热度 =====
    
    @staticmethod
    def get_港股热度排行(limit: int = 50) -> pd.DataFrame:
        """获取港股热度排行榜"""
        try:
            df = ak.stock_hk_hot_rank_em()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取港股热度排行失败: {e}")
            return pd.DataFrame()
    
    # ===== 雪球热度数据 (加载较慢) =====
    
    @staticmethod
    def get_雪球热度讨论(limit: int = 30) -> pd.DataFrame:
        """获取雪球股票热度-讨论"""
        try:
            df = ak.stock_hot_tweet_xq()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取雪球热度讨论失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_雪球热度关注(limit: int = 30) -> pd.DataFrame:
        """获取雪球股票热度-关注"""
        try:
            df = ak.stock_hot_follow_xq()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取雪球热度关注失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_雪球热度交易(limit: int = 30) -> pd.DataFrame:
        """获取雪球股票热度-交易"""
        try:
            df = ak.stock_hot_deal_xq()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取雪球热度交易失败: {e}")
            return pd.DataFrame()
    
    # ===== 资金流向 =====
    
    @staticmethod
    def get_资金流向排行(limit: int = 50) -> pd.DataFrame:
        """获取个股资金流向排行"""
        try:
            df = ak.stock_individual_fund_flow_rank()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取资金流向排行失败: {e}")
            return pd.DataFrame()
    
    # ===== 同花顺热榜数据 =====
    
    @staticmethod
    def get_同花顺概念板块(limit: int = 50) -> pd.DataFrame:
        """获取同花顺概念板块行情"""
        try:
            df = ak.stock_board_concept_index_ths()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取同花顺概念板块失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_同花顺行业板块(limit: int = 50) -> pd.DataFrame:
        """获取同花顺行业板块行情"""
        try:
            df = ak.stock_board_industry_index_ths()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取同花顺行业板块失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_同花顺概念名称() -> pd.DataFrame:
        """获取同花顺概念板块名称列表"""
        try:
            df = ak.stock_board_concept_name_ths()
            return df
        except Exception as e:
            logger.error(f"获取同花顺概念名称失败: {e}")
            return pd.DataFrame()
    
    # ===== 同花顺涨停板/跌停板数据 =====
    
    @staticmethod
    def get_同花顺涨停板(limit: int = 50) -> pd.DataFrame:
        """获取同花顺涨停板股票池（强势股池）
        注意：仅在交易时间段有数据，非交易时间返回空DataFrame
        """
        try:
            df = ak.stock_zt_pool_strong_em()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取同花顺涨停板失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_同花顺跌停板(limit: int = 50) -> pd.DataFrame:
        """获取同花顺跌停板股票池
        注意：仅在交易时间段有数据，非交易时间返回空DataFrame
        """
        try:
            df = ak.stock_zt_pool_dtgc_em()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取同花顺跌停板失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_同花顺炸板率(limit: int = 50) -> pd.DataFrame:
        """获取同花顺炸板股池（曾涨停但未封住的股票）
        注意：仅在交易时间段有数据，非交易时间返回空DataFrame
        """
        try:
            df = ak.stock_zt_pool_zbgc_em()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取同花顺炸板率失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_同花顺涨跌停池(limit: int = 50) -> pd.DataFrame:
        """获取同花顺涨跌停池
        注意：仅在交易时间段有数据，非交易时间返回空DataFrame
        """
        try:
            df = ak.stock_zt_pool_em()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取同花顺涨跌停池失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_同花顺昨日涨停(limit: int = 50) -> pd.DataFrame:
        """获取同花顺昨日涨停股票
        注意：仅在交易时间段有数据，非交易时间返回空DataFrame
        """
        try:
            df = ak.stock_zt_pool_previous_em()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取同花顺昨日涨停失败: {e}")
            return pd.DataFrame()
    
    # ===== 龙虎榜数据 =====
    
    @staticmethod
    def get_龙虎榜详情(limit: int = 50) -> pd.DataFrame:
        """获取龙虎榜详情数据"""
        try:
            df = ak.stock_lhb_detail_em()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取龙虎榜详情失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_龙虎榜机构统计(limit: int = 50) -> pd.DataFrame:
        """获取龙虎榜机构统计数据"""
        try:
            df = ak.stock_lhb_jgstatistic_em()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取龙虎榜机构统计失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_龙虎榜股票统计(limit: int = 50) -> pd.DataFrame:
        """获取龙虎榜股票统计数据"""
        try:
            df = ak.stock_lhb_stock_statistic_em()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取龙虎榜股票统计失败: {e}")
            return pd.DataFrame()
    
    # ===== 机构评级 =====

    @staticmethod
    def get_机构评级排行(limit: int = 50) -> pd.DataFrame:
        """获取机构评级排行"""
        try:
            df = ak.stock_analyst_rank_em()
            if limit and not df.empty:
                df = df.head(limit)
            return df
        except Exception as e:
            logger.error(f"获取机构评级排行失败: {e}")
            return pd.DataFrame()


class AStockAnalyst:
    """A股分析师/机构数据"""
    
    @staticmethod
    def get_机构评级(ticker: str = None) -> pd.DataFrame:
        """获取机构评级数据"""
        try:
            df = ak.stock_analyst_em()
            if ticker:
                df = df[df['代码'] == ticker]
            return df
        except Exception as e:
            logger.error(f"获取机构评级失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_研报(ticker: str = None) -> pd.DataFrame:
        """获取券商研报"""
        try:
            df = ak.stock_research_report_em()
            if ticker:
                df = df[df['股票代码'] == ticker]
            return df
        except Exception as e:
            logger.error(f"获取研报失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_资金流向(ticker: str) -> pd.DataFrame:
        """获取个股资金流向"""
        try:
            if ticker.startswith('6'):
                symbol = f"{ticker}.SH"
            else:
                symbol = f"{ticker}.SZ"
            df = ak.stock_individual_fund_flow(stock=symbol)
            return df
        except Exception as e:
            logger.error(f"获取资金流向失败: {e}")
            return pd.DataFrame()


# ============ 便捷函数 ============

def get_news_all() -> Dict[str, pd.DataFrame]:
    """获取所有类型的新闻数据"""
    return {
        '个股新闻': AStockNews.get_stock_news(),
        '个股公告': AStockNews.get_notice(),
        '新闻联播': AStockNews.get_cctv_news(),
    }


def get_sentiment_all(ticker: str = None) -> Dict[str, pd.DataFrame]:
    """获取所有类型的情绪数据
    
    注意：涨停板、跌停板、炸板率等数据仅在交易时间段有数据，
    非交易时间这些数据源返回空DataFrame
    """
    result = {
        # 热度排行
        '东财热度排行': AStockSentiment.get_东财热度排行(),
        '东财飙升榜': AStockSentiment.get_东财飙升榜(),
        '东财热搜关键词': AStockSentiment.get_东财热搜关键词(),
        '港股热度': AStockSentiment.get_港股热度排行(),
        
        # 同花顺热榜（板块行情）
        '同花顺概念板块': AStockSentiment.get_同花顺概念板块(),
        '同花顺行业板块': AStockSentiment.get_同花顺行业板块(),
        
        # 同花顺涨跌停（仅交易日有数据）
        '同花顺涨停板': AStockSentiment.get_同花顺涨停板(),
        '同花顺跌停板': AStockSentiment.get_同花顺跌停板(),
        '同花顺炸板率': AStockSentiment.get_同花顺炸板率(),
        '同花顺涨跌停池': AStockSentiment.get_同花顺涨跌停池(),
        '同花顺昨日涨停': AStockSentiment.get_同花顺昨日涨停(),
        
        # 龙虎榜
        '龙虎榜详情': AStockSentiment.get_龙虎榜详情(),
        '龙虎榜机构统计': AStockSentiment.get_龙虎榜机构统计(),
        '龙虎榜股票统计': AStockSentiment.get_龙虎榜股票统计(),
        
        # 资金与评级
        '资金流向排行': AStockSentiment.get_资金流向排行(),
        '机构评级排行': AStockSentiment.get_机构评级排行(),
    }
    
    if ticker:
        result['资金流向'] = AStockAnalyst.get_资金流向(ticker)
        result['机构评级'] = AStockAnalyst.get_机构评级(ticker)
    
    return result


def get_stock_sentiment_summary(ticker: str) -> Dict:
    """
    获取单只股票的情绪摘要
    
    Args:
        ticker: 股票代码，如 '000001'
    
    Returns:
        Dict: 情绪摘要数据
    """
    result = {
        'ticker': ticker,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    # 资金流向
    try:
        df = AStockAnalyst.get_资金流向(ticker)
        if not df.empty:
            result['fund_flow'] = df.to_dict('records')[0] if len(df) > 0 else {}
    except:
        pass
    
    # 机构评级
    try:
        df = AStockAnalyst.get_机构评级(ticker)
        if not df.empty:
            result['analyst'] = df.to_dict('records')[0] if len(df) > 0 else {}
    except:
        pass
    
    return result
