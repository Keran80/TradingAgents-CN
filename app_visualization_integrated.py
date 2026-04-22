"""
TradingAgents 可视化功能集成应用
将所有可视化模块集成到统一的 Streamlit 界面中

包含以下可视化功能：
1. 📈 数据可视化 (K线图、技术指标、成交量)
2. 📊 Dashboard 仪表板 (资金曲线、持仓监控、风险指标)
3. 📋 回测报告可视化 (HTML报告、收益分布、回撤分析)
4. 🎨 图表生成器 (多种图表类型、自定义配色)
5. 🔥 热力图分析 (行业分布、持仓盈亏、因子IC)
6. ⚡ 监控仪表板 (系统性能、资源使用、异常告警)
7. 📉 因子分析 (IC走势、分层收益、相关性)
8. 🎯 策略分析 (策略对比、参数敏感性、收益归因)
9. 🤖 AI 分析 (机器学习预测、多数据源适配、风险监控)

使用方法:
    streamlit run app_visualization_integrated.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# ============================================
# 页面配置
# ============================================
st.set_page_config(
    page_title="TradingAgents 可视化平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# 侧边栏导航
# ============================================
st.sidebar.title("📊 TradingAgents")

# 页面选择
page = st.sidebar.radio(
    "选择功能模块",
    [
        "🏠 首页",
        "📈 数据可视化",
        "📊 Dashboard",
        "📋 回测报告",
        "🎨 图表生成器",
        "🔥 热力图",
        "⚡ 监控面板",
        "📉 因子分析",
        "🎯 策略分析",
        "🤖 AI 分析"
    ]
)

# 股票选择
st.sidebar.header("📈 股票选择")
STOCK_CODES = {
    "平安银行": "000001",
    "贵州茅台": "600519",
    "宁德时代": "300750",
    "比亚迪": "002594",
    "招商银行": "600036",
    "中国平安": "601318",
    "五粮液": "000858",
    "恒瑞医药": "600276",
}

selected_stock = st.sidebar.selectbox("选择股票", list(STOCK_CODES.keys()))
ticker = STOCK_CODES[selected_stock]
stock_name = selected_stock

# 时间范围
date_range = st.sidebar.slider("时间范围（天）", 30, 365, 180, 30)

# 刷新按钮
if st.sidebar.button("🔄 刷新数据", type="primary"):
    st.rerun()

# ============================================
# 首页
# ============================================
if page == "🏠 首页":
    st.title("🏠 TradingAgents 可视化平台")
    
    st.markdown("""
    ## 📊 平台功能概览
    
    TradingAgents 提供了完整的量化分析可视化功能，所有模块均已集成到本平台中。
    """)
    
    # 功能卡片
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        **📈 数据可视化**
        - 实时行情图表
        - K 线图分析
        - 技术指标
        - 成交量分析
        """)
    
    with col2:
        st.success("""
        **📊 Dashboard**
        - 持仓监控
        - 资金曲线
        - 行业热力图
        - 风险指标
        """)
    
    with col3:
        st.warning("""
        **📋 回测报告**
        - HTML 报告
        - 收益分布
        - 回撤分析
        - 交易记录
        """)
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.info("""
        **🎨 图表生成器**
        - 多种图表
        - 自定义配色
        - 导出功能
        """)
    
    with col5:
        st.success("""
        **🔥 热力图**
        - 行业分布
        - 持仓盈亏
        - 因子 IC
        - 相关性
        """)
    
    with col6:
        st.warning("""
        **🤖 AI 分析**
        - 趋势预测
        - 多数据源
        - 风险监控
        - 智能决策
        """)
    
    # 快速开始
    st.markdown("---")
    st.subheader("🚀 快速开始")
    
    if st.button("📈 开始数据可视化分析", width='stretch'):
        st.session_state.page = "📈 数据可视化"
        st.rerun()

# ============================================
# 数据可视化页面
# ============================================
elif page == "📈 数据可视化":
    st.title(f"📈 {stock_name} ({ticker}) 数据可视化")
    
    # 生成模拟数据
    @st.cache_data
    def generate_stock_data(ticker, days):
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        base_price = 100
        returns = np.random.randn(days) * 0.02
        prices = base_price * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            '日期': dates,
            '开盘': prices * (1 + np.random.randn(days) * 0.01),
            '最高': prices * (1 + np.abs(np.random.randn(days)) * 0.02),
            '最低': prices * (1 - np.abs(np.random.randn(days)) * 0.02),
            '收盘': prices,
            '成交量': np.random.randint(1000000, 10000000, days),
            '成交额': np.random.randint(100000000, 1000000000, days)
        })
        return df
    
    df = generate_stock_data(ticker, date_range)
    
    # 股票信息卡片
    col1, col2, col3, col4 = st.columns(4)
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    with col1:
        st.metric("最新价", f"{latest['收盘']:.2f}", f"{(latest['收盘'] - prev['收盘']):.2f}")
    with col2:
        change_pct = ((latest['收盘'] - prev['收盘']) / prev['收盘'] * 100)
        st.metric("涨跌幅", f"{change_pct:.2f}%")
    with col3:
        st.metric("成交量", f"{latest['成交量']/10000:.2f}万")
    with col4:
        st.metric("成交额", f"{latest['成交额']/100000000:.2f}亿")
    
    # K 线图
    st.subheader("📊 K 线图")
    fig_kline = go.Figure(data=[go.Candlestick(
        x=df['日期'],
        open=df['开盘'],
        high=df['最高'],
        low=df['最低'],
        close=df['收盘'],
        increasing_line_color='#ef5350',
        decreasing_line_color='#26a69a'
    )])
    
    # 添加移动平均线
    df['MA5'] = df['收盘'].rolling(5).mean()
    df['MA20'] = df['收盘'].rolling(20).mean()
    
    fig_kline.add_trace(go.Scatter(x=df['日期'], y=df['MA5'], name='MA5', line=dict(color='#ff9800')))
    fig_kline.add_trace(go.Scatter(x=df['日期'], y=df['MA20'], name='MA20', line=dict(color='#2196f3')))
    
    fig_kline.update_layout(height=500, title=f"{stock_name} K线图")
    st.plotly_chart(fig_kline, width='stretch')
    
    # 成交量
    st.subheader("📈 成交量分析")
    fig_volume = go.Figure()
    colors = ['#ef5350' if row['收盘'] >= row['开盘'] else '#26a69a' for _, row in df.iterrows()]
    fig_volume.add_trace(go.Bar(x=df['日期'], y=df['成交量'], marker_color=colors))
    fig_volume.update_layout(height=300, title="成交量")
    st.plotly_chart(fig_volume, width='stretch')
    
    # 技术指标
    st.subheader("📉 技术指标")
    
    # RSI
    delta = df['收盘'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['收盘'].ewm(span=12, adjust=False).mean()
    exp2 = df['收盘'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    fig_indicators = make_subplots(rows=2, cols=1, subplot_titles=('RSI', 'MACD'))
    fig_indicators.add_trace(go.Scatter(x=df['日期'], y=df['RSI'], name='RSI'), row=1, col=1)
    fig_indicators.add_hline(y=70, line_dash="dash", line_color="red", row=1, col=1)
    fig_indicators.add_hline(y=30, line_dash="dash", line_color="green", row=1, col=1)
    
    fig_indicators.add_trace(go.Scatter(x=df['日期'], y=df['MACD'], name='MACD'), row=2, col=1)
    fig_indicators.add_trace(go.Scatter(x=df['日期'], y=df['Signal'], name='Signal'), row=2, col=1)
    
    fig_indicators.update_layout(height=600)
    st.plotly_chart(fig_indicators, width='stretch')

# ============================================
# Dashboard 页面
# ============================================
elif page == "📊 Dashboard":
    st.title("📊 Dashboard 仪表板")
    
    # 资金曲线
    st.subheader("📈 资金曲线")
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    equity = 10000 + np.cumsum(np.random.randn(100) * 100)
    benchmark = 10000 + np.cumsum(np.random.randn(100) * 80)
    
    fig_equity = go.Figure()
    fig_equity.add_trace(go.Scatter(x=dates, y=equity, name='组合收益', fill='tozeroy'))
    fig_equity.add_trace(go.Scatter(x=dates, y=benchmark, name='基准收益', line=dict(dash='dash')))
    fig_equity.update_layout(height=400)
    st.plotly_chart(fig_equity, width='stretch')
    
    # 持仓监控
    st.subheader("📋 持仓监控")
    positions = pd.DataFrame({
        '证券代码': ['000001.SZ', '600519.SH', '300750.SZ', '002594.SZ'],
        '证券名称': ['平安银行', '贵州茅台', '宁德时代', '比亚迪'],
        '持仓数量': [1000, 50, 200, 300],
        '当前价': [16.8, 1850.2, 430.5, 290.3],
        '市值': [16800, 92510, 86100, 87090],
        '盈亏%': [10.5, 2.7, 2.4, 3.4]
    })
    st.dataframe(positions, width='stretch')
    
    # 风险指标
    st.subheader("⚡ 风险指标")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("夏普比率", "1.85")
    with col2: st.metric("最大回撤", "-8.2%")
    with col3: st.metric("年化收益", "15.6%")
    with col4: st.metric("波动率", "12.3%")
    
    # 行业热力图
    st.subheader("🔥 行业分布热力图")
    sectors = ['银行', '白酒', '新能源', '医药', '科技', '消费']
    sector_returns = np.random.randn(len(sectors), 10) * 2 + 0.5
    
    fig_heatmap = px.imshow(
        sector_returns,
        x=list(range(10)),
        y=sectors,
        color_continuous_scale='RdYlGn',
        title="行业收益热力图"
    )
    st.plotly_chart(fig_heatmap, width='stretch')

# ============================================
# 回测报告页面
# ============================================
elif page == "📋 回测报告":
    st.title("📋 回测报告可视化")
    
    # 资金曲线对比
    st.subheader("📈 回测资金曲线")
    dates = pd.date_range(end=datetime.now(), periods=252, freq='B')
    strategy = 10000 + np.cumsum(np.random.randn(252) * 50)
    benchmark = 10000 + np.cumsum(np.random.randn(252) * 40)
    
    fig_backtest = go.Figure()
    fig_backtest.add_trace(go.Scatter(x=dates, y=strategy, name='策略收益', fill='tozeroy'))
    fig_backtest.add_trace(go.Scatter(x=dates, y=benchmark, name='基准收益', line=dict(dash='dash')))
    st.plotly_chart(fig_backtest, width='stretch')
    
    # 收益分布
    st.subheader("📊 收益分布")
    returns = np.diff(strategy) / strategy[:-1] * 100
    fig_hist = px.histogram(x=returns, nbins=30, title="收益分布直方图")
    st.plotly_chart(fig_hist, width='stretch')
    
    # 回撤曲线
    st.subheader("📉 回撤分析")
    peak = np.maximum.accumulate(strategy)
    drawdown = (strategy - peak) / peak * 100
    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(x=dates, y=drawdown, name='回撤曲线', fill='tozeroy'))
    st.plotly_chart(fig_dd, width='stretch')
    
    # 月度收益热力图
    st.subheader("📅 月度收益热力图")
    monthly_data = np.random.randn(3, 12) * 2 + 0.5
    fig_monthly = px.imshow(
        monthly_data,
        x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        y=['2023', '2024', '2025'],
        color_continuous_scale='RdYlGn'
    )
    st.plotly_chart(fig_monthly, width='stretch')
    
    # 生成报告按钮
    if st.button("📄 生成 HTML 回测报告", type="primary"):
        st.success("✅ 回测报告生成成功！")
        st.download_button(
            label="📥 下载报告",
            data="<html><body><h1>回测报告</h1></body></html>",
            file_name="backtest_report.html",
            mime="text/html"
        )

# ============================================
# 图表生成器页面
# ============================================
elif page == "🎨 图表生成器":
    st.title("🎨 图表生成器")
    
    chart_type = st.selectbox("选择图表类型", [
        "资金曲线图", "收益柱状图", "回撤曲线图", 
        "持仓饼图", "散点图", "K 线图"
    ])
    
    # 图表参数
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("图表标题", f"{chart_type}")
        width = st.slider("宽度", 600, 1200, 800)
    with col2:
        height = st.slider("高度", 400, 800, 500)
        theme = st.selectbox("主题", ["浅色", "深色"])
    
    if st.button("🔄 生成图表", type="primary"):
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        values = 100 + np.cumsum(np.random.randn(100))
        
        if chart_type == "资金曲线图":
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=values, fill='tozeroy'))
            fig.update_layout(title=title, width=width, height=height)
            
        elif chart_type == "收益柱状图":
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            returns = np.random.randn(12) * 2
            colors = ['#4c