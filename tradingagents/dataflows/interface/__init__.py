# -*- coding: utf-8 -*-
"""
interface 模块 - 自动拆分

原文件：interface.py (865 行)
拆分时间：2026-04-24
拆分说明：按功能域拆分为多个子模块

子模块：
- finnhub.py: Finnhub 新闻和内部交易相关函数 (3 个函数)
- simfin.py: Simfin 财务报表相关函数 (3 个函数)
- googlenews.py: Google 新闻函数 (1 个函数)
- reddit.py: Reddit 新闻函数 (2 个函数)
- yfinance.py: Yahoo Finance 数据函数 (3 个函数)
- stockstats.py: StockStats 技术指标函数 (2 个函数)
- openai_news.py: OpenAI 新闻搜索函数 (3 个函数)

总计：17 个函数
"""

# 从子模块导入所有函数
from .finnhub import *
from .simfin import *
from .googlenews import *
from .reddit import *
from .yfinance import *
from .stockstats import *
from .openai_news import *

__all__ = [
    # finnhub
    "get_finnhub_news",
    "get_finnhub_company_insider_sentiment",
    "get_finnhub_company_insider_transactions",
    # simfin
    "get_simfin_balance_sheet",
    "get_simfin_cashflow",
    "get_simfin_income_statements",
    # googlenews
    "get_google_news",
    # reddit
    "get_reddit_global_news",
    "get_reddit_company_news",
    # yfinance
    "get_YFin_data_window",
    "get_YFin_data_online",
    "get_YFin_data",
    # stockstats
    "get_stock_stats_indicators_window",
    "get_stockstats_indicator",
    # openai_news
    "get_stock_news_openai",
    "get_global_news_openai",
    "get_fundamentals_openai",
]
