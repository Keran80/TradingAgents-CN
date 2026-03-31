"""
A股股票分析 - 数据获取测试
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows import akshare_utils as ak
from datetime import datetime, timedelta

# 测试数据获取
ticker = "000001"  # 平安银行

print(f"测试获取 {ticker} 的数据...")
print("="*50)

# 1. 获取日线数据
end_date = datetime.now().strftime("%Y%m%d")
start_date_obj = datetime.now() - timedelta(days=30)
start_date = start_date_obj.strftime("%Y%m%d")

print(f"\n[1] 日线数据 ({start_date} - {end_date})...")
df_daily = ak.get_stock_daily(ticker, start_date, end_date)
print(f"获取到 {len(df_daily)} 条记录")
if not df_daily.empty:
    print(df_daily.tail(3))

# 2. 获取实时行情
print(f"\n[2] 实时行情...")
df_quote = ak.get_stock_realtime_quote(ticker)
if not df_quote.empty:
    quote = df_quote.iloc[0]
    print(f"名称: {quote.get('名称')}")
    print(f"当前价格: {quote.get('最新价')}")
    print(f"涨跌幅: {quote.get('涨跌幅')}%")
    print(f"成交量: {quote.get('成交量')}")
else:
    print("无法获取实时行情")

# 3. 获取北向资金
print(f"\n[3] 北向资金...")
df_money = ak.get_moneyflow_hsgt()
if not df_money.empty:
    print(df_money.head(3))

print("\n" + "="*50)
print("数据获取测试完成!")
