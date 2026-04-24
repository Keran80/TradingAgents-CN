# -*- coding: utf-8 -*-
"""
interface.py - 向后兼容的导入文件

原文件已拆分为 interface/ 包下的多个子模块。
此文件保留以确保原有导入路径仍然可用：
    from tradingagents.dataflows.interface import xxx

所有函数现已在 interface/ 包中按功能域组织：
- finnhub.py: Finnhub 新闻和内部交易
- simfin.py: Simfin 财务报表
- googlenews.py: Google 新闻
- reddit.py: Reddit 新闻
- yfinance.py: Yahoo Finance 数据
- stockstats.py: StockStats 技术指标
- openai_news.py: OpenAI 新闻搜索
"""

# 从 interface 包导入所有函数
from .interface import *
