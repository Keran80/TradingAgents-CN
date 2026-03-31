# -*- coding: utf-8 -*-
"""测试A股情绪分析模块"""
from tradingagents.dataflows import AStockSentiment, AStockNews
import time

print("=" * 50)
print("测试 A股新闻和情绪分析模块")
print("=" * 50)

# 1. 测试东财热度排行
print("\n1. 测试获取东财热度排行...")
start = time.time()
df = AStockSentiment.get_东财热度排行(5)
elapsed = time.time() - start
if not df.empty:
    print(f"成功! (耗时 {elapsed:.1f}秒)")
    print(df[['当前排名', '代码', '股票名称', '涨跌幅']].to_string())
else:
    print("返回为空")

# 2. 测试东财飙升榜
print("\n2. 测试获取东财飙升榜...")
start = time.time()
df = AStockSentiment.get_东财飙升榜(5)
elapsed = time.time() - start
if not df.empty:
    print(f"成功! (耗时 {elapsed:.1f}秒)")
    print(df[['排名较昨日变动', '当前排名', '代码', '股票名称']].to_string())
else:
    print("返回为空")

# 3. 测试资金流向排行
print("\n3. 测试获取资金流向排行...")
start = time.time()
df = AStockSentiment.get_资金流向排行(5)
elapsed = time.time() - start
if not df.empty:
    print(f"成功! (耗时 {elapsed:.1f}秒)")
    print(df.columns.tolist()[:8])
else:
    print("返回为空")

# 4. 测试个股新闻
print("\n4. 测试获取个股新闻...")
start = time.time()
df = AStockNews.get_stock_news('A股')
elapsed = time.time() - start
if not df.empty:
    print(f"成功! (耗时 {elapsed:.1f}秒)")
    print(f"共 {len(df)} 条新闻")
    print(df.head(2).to_string())
else:
    print("返回为空")

print("\n" + "=" * 50)
print("测试完成!")
print("=" * 50)
