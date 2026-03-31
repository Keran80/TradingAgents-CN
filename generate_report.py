"""
生成股票分析报告 HTML
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from tradingagents.dataflows import akshare_utils as aks

# 获取数据
ticker = '000001'
days = 90
end_date = datetime.now().strftime("%Y%m%d")
start_date_obj = datetime.now() - timedelta(days=days)
start_date = start_date_obj.strftime("%Y%m%d")

df_daily = aks.get_stock_daily(ticker, start_date, end_date)
df_quote = aks.get_stock_realtime_quote(ticker)

quote = df_quote.iloc[0]
current_price = quote.get('最新价', 0)
change_pct = quote.get('涨跌幅', 0)
volume = quote.get('成交量', 0)
amount = quote.get('成交额', 0)
open_price = quote.get('开盘', 0)

# 准备 K线图数据
df_plot = df_daily.copy()
df_plot['日期'] = pd.to_datetime(df_plot['date'])
df_plot['MA5'] = df_plot['close'].rolling(window=5).mean()
df_plot['MA10'] = df_plot['close'].rolling(window=10).mean()
df_plot['MA20'] = df_plot['close'].rolling(window=20).mean()

# K线图
fig = go.Figure(data=[go.Candlestick(
    x=df_plot['日期'],
    open=df_plot['open'],
    high=df_plot['high'],
    low=df_plot['low'],
    close=df_plot['close'],
    name='K线'
)])
fig.add_trace(go.Scatter(x=df_plot['日期'], y=df_plot['MA5'], name='MA5', line=dict(color='orange', width=1)))
fig.add_trace(go.Scatter(x=df_plot['日期'], y=df_plot['MA10'], name='MA10', line=dict(color='purple', width=1)))
fig.add_trace(go.Scatter(x=df_plot['日期'], y=df_plot['MA20'], name='MA20', line=dict(color='blue', width=1)))
fig.update_layout(xaxis_rangeslider_visible=False, height=500, template='plotly_dark', title='平安银行(000001) K线走势')

# 成交量图
colors = ['red' if df_plot.iloc[i]['close'] >= df_plot.iloc[i]['open'] else 'green' for i in range(len(df_plot))]
fig_vol = go.Figure(data=[go.Bar(x=df_plot['日期'], y=df_plot['volume'], marker_color=colors, name='成交量')])
fig_vol.update_layout(height=250, template='plotly_dark', title='成交量')

# RSI
delta = df_plot['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df_plot['RSI'] = 100 - (100 / (1 + rs))

# MACD
exp1 = df_plot['close'].ewm(span=12, adjust=False).mean()
exp2 = df_plot['close'].ewm(span=26, adjust=False).mean()
df_plot['MACD'] = exp1 - exp2
df_plot['Signal'] = df_plot['MACD'].ewm(span=9, adjust=False).mean()
df_plot['Histogram'] = df_plot['MACD'] - df_plot['Signal']

latest_rsi = df_plot['RSI'].iloc[-1]
latest_macd = df_plot['MACD'].iloc[-1]
latest_signal = df_plot['Signal'].iloc[-1]

# 生成 HTML
change_class = 'positive' if change_pct > 0 else 'negative'
macd_class = 'positive' if latest_macd > latest_signal else 'negative'

html = f'''<!DOCTYPE html>
<html>
<head>
    <title>TradingAgents 股票分析报告</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #0e1117; color: #fafafa; }}
        .header {{ text-align: center; padding: 20px; background: #262730; border-radius: 10px; margin-bottom: 20px; }}
        .stock-info {{ display: flex; justify-content: space-around; padding: 20px; background: #262730; border-radius: 10px; margin-bottom: 20px; }}
        .metric {{ text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .metric-label {{ font-size: 14px; color: #aaa; }}
        .positive {{ color: #ff6b6b; }}
        .negative {{ color: #51cf66; }}
        .chart-container {{ background: #262730; border-radius: 10px; padding: 15px; margin-bottom: 20px; }}
        .indicators {{ display: flex; justify-content: space-around; padding: 15px; background: #262730; border-radius: 10px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📈 TradingAgents 股票分析报告</h1>
        <p>平安银行 (000001)</p>
    </div>
    
    <div class="stock-info">
        <div class="metric">
            <div class="metric-value">¥{current_price:.2f}</div>
            <div class="metric-label">当前价格</div>
        </div>
        <div class="metric">
            <div class="metric-value {change_class}">{change_pct:+.2f}%</div>
            <div class="metric-label">涨跌幅</div>
        </div>
        <div class="metric">
            <div class="metric-value">{volume/10000:.2f}万</div>
            <div class="metric-label">成交量</div>
        </div>
        <div class="metric">
            <div class="metric-value">¥{amount/100000000:.2f}亿</div>
            <div class="metric-label">成交额</div>
        </div>
    </div>
    
    <div class="indicators">
        <div class="metric">
            <div class="metric-value">{latest_rsi:.2f}</div>
            <div class="metric-label">RSI(14)</div>
        </div>
        <div class="metric">
            <div class="metric-value {macd_class}">{latest_macd:.4f}</div>
            <div class="metric-label">MACD</div>
        </div>
    </div>
    
    <div class="chart-container">
        <div id="kline"></div>
    </div>
    
    <div class="chart-container">
        <div id="volume"></div>
    </div>
    
    <script>
        var klineData = {fig.to_json()};
        Plotly.newPlot('kline', klineData.data, klineData.layout);
        
        var volData = {fig_vol.to_json()};
        Plotly.newPlot('volume', volData.data, volData.layout);
    </script>
</body>
</html>'''

with open('stock_report.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('报告已生成: stock_report.html')
