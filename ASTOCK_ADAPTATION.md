# TradingAgents-CN A股全面适配指南

## 概述

本文档详细介绍 TradingAgents-CN 框架的中国A股数据适配方案。

---

## 数据源架构

### 新增模块

| 模块文件 | 功能 |
|---------|------|
| `astock_utils.py` | A股数据获取核心类 |
| `astock_technical.py` | A股技术指标计算 |
| `test_astock.py` | 测试和导出工具 |

---

## A股数据接口

### 1. 实时行情

```python
from tradingagents.dataflows import AStockData

# 获取单只股票实时行情
df = AStockData.get_realtime_quote('000001')  # 平安银行

# 获取所有A股实时行情
df = AStockData.get_realtime_quote()  # 返回全部

# 获取多只股票
stocks = ['000001', '600519', '300750']
for code in stocks:
    df = AStockData.get_realtime_quote(code)
    if not df.empty:
        print(df.iloc[0]['股票简称'], df.iloc[0]['最新价'])
```

### 2. 日线数据

```python
# 获取日线数据
df = AStockData.get_daily('600519', '20250101', '20250328')

# 参数说明:
# ticker: 股票代码
# start_date: 开始日期 'YYYYMMDD'
# end_date: 结束日期 'YYYYMMDD'  
# adjust: 复权类型 'qfq'(前复权) / 'hfq'(后复权) / '' (不复权)

# 获取周线数据
df = AStockData.get_weekly('600519', '20250101', '20250328')

# 获取分钟线数据
df = AStockData.get_minute('600519', period='5')  # 5分钟线
```

### 3. 技术指标

```python
from tradingagents.dataflows import AStockTechnical

# 获取日线数据
df = AStockData.get_daily('600519', '20250101', '20250328')

# 计算所有常用技术指标
df = AStockTechnical.calculate_all(df)

# 获取最新指标值
latest = AStockTechnical.get_latest_indicators(df)

print(latest)
# {
#     'close': 1685.50,
#     'ma5': 1660.20,
#     'ma10': 1645.80,
#     'ma20': 1620.35,
#     'rsi': 72.45,
#     'macd': 15.6789,
#     'macds': 12.3456,
#     'macdh': 3.3333,
#     'kdj_k': 85.32,
#     'kdj_d': 78.45,
#     'kdj_j': 99.06,
#     'boll_upper': 1750.00,
#     'boll_mid': 1680.00,
#     'boll_lower': 1610.00
# }
```

### 4. 资金流向

```python
# 北向资金流向（日度/月度）
df = AStockData.get_moneyflow_hsgt(period='daily')

# 北向资金持仓股票
df = AStockData.get_moneyflow_hsgt_stocks()

# 融资融券明细
df = AStockData.get_margin_detail()

# 融资融券热门股票
df = AStockData.get_margin_top()

# 大单资金流向
df = AStockData.get_fund_flow()

# 板块资金流向
df = AStockData.get_sector_flow()
```

### 5. 龙虎榜

```python
# 龙虎榜上榜股票
df = AStockData.get_lhb_stocks()

# 龙虎榜明细
df = AStockData.get_lhb_detail()

# 机构买卖明细
df = AStockData.get_top_inst()
```

### 6. 涨跌停数据

```python
# 涨停板池
df = AStockData.get_stock_zt_pool()

# 强势涨停股
df = AStockData.get_stock_zt_pool_strong()

# 次新股
df = AStockData.get_stock_zt_pool_subnew()

# 涨跌停列表
df = AStockData.get_limit_list()
```

### 7. 新闻公告

```python
# A股新闻
df = AStockData.get_stock_news()

# 股票公告
df = AStockData.get_stock_notice()

# 大宗交易
df = AStockData.get_stock_block_trade()

# 股东增减持
df = AStockData.get_stock_holdertrade()
```

### 8. 财务数据

```python
# 股票基本信息
info = AStockData.get_stock_info('600519')
# 返回: {'股票名称': '贵州茅台', '总市值': '...', '市盈率': '...', ...}

# 财务报表
df = AStockData.get_financial_report('600519')

# 财务指标
df = AStockData.get_financial_indicator('600519')
```

### 9. 指数数据

```python
# 指数日线
df = AStockData.get_index_daily('000300', '20250101', '20250328')  # 沪深300

# 常用指数代码
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
```

---

## 技术指标说明

### 支持的指标

| 指标 | 说明 | 计算方法 |
|-----|------|---------|
| MA5/10/20/30/60/120/250 | 移动平均线 | 简单移动平均 |
| EMA12/26 | 指数移动平均 | 指数加权 |
| MACD | 指数平滑异同移动平均线 | EMA12-EMA26 |
| RSI | 相对强弱指标 | 14周期 |
| KDJ | 随机指标 | 9,3,3周期 |
| BOLL | 布林带 | 20周期±2倍标准差 |
| ATR | 真实波幅 | 14周期 |
| CCI | 商品通道指数 | 14周期 |
| WR | 威廉指标 | 6,10周期 |
| OBV | 能量潮 | 成交量累计 |

---

## 便捷函数

直接导入使用:

```python
from tradingagents.dataflows import (
    get_stock_realtime_quote,  # 实时行情
    get_stock_daily,            # 日线数据
    get_stock_news,             # 新闻
    get_moneyflow_hsgt,         # 北向资金
    get_stock_top_list,         # 龙虎榜
    get_stock_top_inst,         # 机构明细
    get_margin_detail,          # 融资融券
    get_index_daily,            # 指数日线
    get_stock_technical_indicators,  # 技术指标
)
```

---

## 使用示例

### 示例1: 获取股票技术分析

```python
from tradingagents.dataflows import get_stock_technical_indicators

# 获取贵州茅台技术指标
result = get_stock_technical_indicators('600519', days=60)

print(result)
# {
#     'ticker': '600519',
#     'name': '贵州茅台',
#     'close': 1685.50,
#     'volume': 1234567,
#     'ma5': 1660.20,
#     'rsi': 72.45,
#     'macd': 15.6789,
#     ...
# }
```

### 示例2: 批量导出股票数据

```python
from tradingagents.dataflows import AStockData, AStockTechnical
import json

stocks = {
    '000001': '平安银行',
    '600519': '贵州茅台', 
    '300750': '宁德时代',
}

result = {}

for code, name in stocks.items():
    # 获取实时数据
    quote = AStockData.get_realtime_quote(code)
    if not quote.empty:
        q = quote.iloc[0]
        
        # 获取技术指标
        daily = AStockData.get_daily(code, '20250101', '20250328')
        if not daily.empty:
            daily = AStockTechnical.calculate_all(daily)
            tech = AStockTechnical.get_latest_indicators(daily)
        
        result[code] = {
            'name': name,
            'price': float(q.get('最新价', 0)),
            'change_pct': float(q.get('涨跌幅', 0)),
            'rsi': tech.get('rsi', 50),
            'macd': tech.get('macd', 0),
        }

# 保存到JSON
with open('stock_data.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
```

---

## 新闻和情绪分析模块

### 模块: astock_sentiment.py

基于 AkShare 1.18.48 验证接口，提供国内新闻和情绪数据。

### 10. 新闻数据

```python
from tradingagents.dataflows import AStockNews

# 获取A股新闻
df = AStockNews.get_stock_news('A股')

# 获取个股公告
df = AStockNews.get_notice()

# 获取新闻联播文字稿
df = AStockNews.get_cctv_news()

# 获取百度新闻报道时间
df = AStockNews.get_news_report()
```

### 11. 情绪分析数据

```python
from tradingagents.dataflows import AStockSentiment, AStockAnalyst

# 东方财富热度数据
df = AStockSentiment.get_东财热度排行(50)      # 热度排行榜
df = AStockSentiment.get_东财飙升榜(50)         # 飙升榜
df = AStockSentiment.get_东财热度最新(50)       # 最新热度排行

# 港股热度
df = AStockSentiment.get_港股热度排行(50)

# 资金流向
df = AStockSentiment.get_资金流向排行(50)

# 机构评级
df = AStockSentiment.get_机构评级排行(50)

# 雪球热度 (加载较慢，首次约30-60秒)
df = AStockSentiment.get_雪球热度讨论(30)       # 讨论热度
df = AStockSentiment.get_雪球热度关注(30)        # 关注热度
df = AStockSentiment.get_雪球热度交易(30)        # 交易热度
```

### 12. 个股资金流向和分析师评级

```python
from tradingagents.dataflows import AStockAnalyst

# 获取单只股票资金流向
df = AStockAnalyst.get_资金流向('600519')  # 茅台

# 获取机构评级
df = AStockAnalyst.get_机构评级('600519')

# 获取券商研报
df = AStockAnalyst.get_研报('600519')
```

### 13. 便捷函数

```python
from tradingagents.dataflows import (
    AStockNews,
    AStockSentiment,
    AStockAnalyst,
    get_news_all,
    get_sentiment_all,
    get_stock_sentiment_summary,
)

# 获取所有新闻类型
news = get_news_all()

# 获取所有情绪数据
sentiment = get_sentiment_all()  # 全局
sentiment = get_sentiment_all('600519')  # 包含个股数据

# 获取单只股票情绪摘要
summary = get_stock_sentiment_summary('600519')
# 返回: {'ticker': '600519', 'timestamp': '...', 'fund_flow': {...}, 'analyst': {...}}
```

### 数据源说明

| 数据类型 | 数据来源 | 备注 |
|---------|---------|------|
| 个股新闻 | 东方财富 | 实时新闻流 |
| 股票公告 | 东方财富 | 上市公司公告 |
| 热度排行 | 东方财富 | 实时热度 |
| 飙升榜 | 东方财富 | 热度上升最快 |
| 资金流向 | 东方财富 | 个股资金进出 |
| 机构评级 | 东方财富 | 券商分析师评级 |
| 雪球热度 | 雪球社区 | 讨论/关注/交易 |

### 首次使用注意

- **首次导入模块时**，AkShare 需要下载数据包（约45秒）
- **雪球接口**首次调用需要30-60秒
- 后续使用会使用缓存，速度更快

---

## 注意事项

1. **网络要求**: AkShare 需要连接国内服务器获取数据
2. **频率限制**: 避免短时间内大量请求
3. **数据延迟**: 实时行情有15分钟延迟
4. **复权类型**: 技术分析建议使用前复权(qfq)数据
5. **首次导入**: 首次导入模块需要下载数据包，请耐心等待

---

## 故障排除

### 问题: 获取数据失败

```python
# 尝试捕获异常
try:
    df = AStockData.get_daily('600519', '20250101', '20250328')
    if df.empty:
        print("未获取到数据，可能是股票代码错误或网络问题")
except Exception as e:
    print(f"错误: {e}")
```

### 问题: 技术指标计算错误

```python
# 确保数据足够长
df = AStockData.get_daily('600519', '20250101', '20250328')
print(f"数据条数: {len(df)}")  # 需要至少250条计算所有指标
```

---

## 更新日志

- 2026-03-29: 初始版本，支持实时行情、日线、技术指标、资金流向、龙虎榜等
