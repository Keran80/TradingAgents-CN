# 数据流模块 — 支持通达信(TDX) + AkShare 双数据源
from .finnhub_utils import get_data_in_range
from .googlenews_utils import getNewsData
# AkShare 数据源（保留兼容）
from .akshare_stock_utils import AkShareUtils, aks
# 通达信(TDX)数据源
from .tdx_utils import TdxStockUtils, tdx, get_stock_data as tdx_get_stock_data
from .tdx_utils import get_realtime_quotes as tdx_get_realtime_quotes
from .tdx_utils import get_finance_info as tdx_get_finance_info
# 数据源路由（自动选择 TDX 或 AkShare）
from .data_source import get_data_source, set_data_source, get_current_source_name
from .reddit_utils import fetch_top_from_category
from .stockstats_utils import StockstatsUtils
# A股全面适配模块
from .astock_utils import AStockData, get_stock_realtime_quote, get_stock_daily
from .astock_utils import get_stock_news, get_moneyflow_hsgt, get_stock_top_list
from .astock_utils import get_stock_top_inst, get_margin_detail, get_index_daily
from .astock_technical import AStockTechnical, get_stock_technical_indicators
# A股新闻和情绪分析模块
from .astock_sentiment import AStockNews, AStockSentiment, AStockAnalyst
from .astock_sentiment import get_news_all, get_sentiment_all, get_stock_sentiment_summary
# 缓存模块
from .cache import cached, retry, clear_cache, get_cache, set_cache
from .cache import RateLimiter, get_rate_limiter, rate_limit

# 保留 yfinance 导入以备后用（可选）
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

from .interface import (
    # News and sentiment functions
    get_finnhub_news,
    get_finnhub_company_insider_sentiment,
    get_finnhub_company_insider_transactions,
    get_google_news,
    get_reddit_global_news,
    get_reddit_company_news,
    # Financial statements functions
    get_simfin_balance_sheet,
    get_simfin_cashflow,
    get_simfin_income_statements,
    # Technical analysis functions
    get_stock_stats_indicators_window,
    get_stockstats_indicator,
    # Market data functions
    get_YFin_data_window,
    get_YFin_data,
    get_YFin_data_online,  # 新增：使用 AkShare 的在线数据获取
)


__all__ = [
    # News and sentiment functions
    "get_finnhub_news",
    "get_finnhub_company_insider_sentiment",
    "get_finnhub_company_insider_transactions",
    "get_google_news",
    "get_reddit_global_news",
    "get_reddit_company_news",
    # Financial statements functions
    "get_simfin_balance_sheet",
    "get_simfin_cashflow",
    "get_simfin_income_statements",
    # Technical analysis functions
    "get_stock_stats_indicators_window",
    "get_stockstats_indicator",
    # Market data functions
    "get_YFin_data_window",
    "get_YFin_data",
    "get_YFin_data_online",
    # AkShare utilities
    "AkShareUtils",
    "aks",
    # 通达信(TDX)数据源
    "TdxStockUtils",
    "tdx",
    "tdx_get_stock_data",
    "tdx_get_realtime_quotes",
    "tdx_get_finance_info",
    # 数据源路由
    "get_data_source",
    "set_data_source",
    "get_current_source_name",
    # A股全面适配模块
    "AStockData",
    "AStockTechnical",
    "get_stock_realtime_quote",
    "get_stock_daily",
    "get_stock_news",
    "get_moneyflow_hsgt",
    "get_stock_top_list",
    "get_stock_top_inst",
    "get_margin_detail",
    "get_index_daily",
    "get_stock_technical_indicators",
    # A股新闻和情绪分析模块
    "AStockNews",
    "AStockSentiment",
    "AStockAnalyst",
    "get_news_all",
    "get_sentiment_all",
    "get_stock_sentiment_summary",
    # Cache utilities
    "cached",
    "retry",
    "clear_cache",
    "get_cache",
    "set_cache",
    # Rate limiter
    "RateLimiter",
    "get_rate_limiter",
    "rate_limit",
]
