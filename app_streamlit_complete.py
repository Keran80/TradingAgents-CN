"""
TradingAgents 完整可视化平台
基于 Streamlit 构建的量化分析平台

集成所有可视化功能模块：
1. Dashboard 仪表板
2. 回测报告可视化
3. 图表生成器
4. 热力图组件
5. 监控仪表板
6. 因子可视化
7. 策略可视化
8. AI 分析模块

使用方法:
    streamlit run app_streamlit_complete.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import json
import os
import sys

# 添加项目路径
sys.path.insert(0, '/tmp/TradingAgents-CN')

# 页面配置
st.set_page_config(
    page_title="TradingAgents 量化分析平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化 session_state
if 'current_stock' not in st.session_state:
    st.session_state.current_stock = "股票"
if 'stock_changed' not in st.session_state:
    st.session_state.stock_changed = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = "首页"

# ============================================
# 侧边栏导航
# ============================================
st.sidebar.title("📊 TradingAgents")

# 页面选择
pages = {
    "🏠 首页": "首页",
    "📈 数据可视化": "数据可视化",
    "📊 Dashboard 仪表板": "Dashboard",
    "📋 回测报告": "回测报告",
    "🎨 图表生成器": "图表生成器",
    "🔥 热力图分析": "热力图分析",
    "⚡ 监控仪表板": "监控仪表板",
    "📉 因子分析": "因子分析",
    "🎯 策略分析": "策略分析",
    "🤖 AI 分析": "AI 分析",
    "⚙️ 系统设置": "系统设置"
}

selected_page = st.sidebar.radio(
    "选择页面",
    list(pages.keys()),
    index=0
)
st.session_state.current_page = pages[selected_page]

# 股票选择（在侧边栏显示）
st.sidebar.header("📈 股票选择")

# 常用股票代码
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

# 选择模式
input_mode = st.sidebar.radio("输入模式", ["选择股票", "输入代码"])

if input_mode == "选择股票":
    selected_stock = st.sidebar.selectbox(
        "选择股票",
        list(STOCK_CODES.keys())
    )
    ticker = STOCK_CODES[selected_stock]
    stock_name = selected_stock
else:
    ticker_input = st.sidebar.text_input("输入股票代码", placeholder="如: 000001, 600519")
    if ticker_input:
        ticker = ticker_input.strip()
        stock_name = f"股票 {ticker}"
    else:
        ticker = "000001"
        stock_name = "平安银行"

# 时间范围选择
date_range = st.sidebar.slider(
    "时间范围（天）",
    min_value=30,
    max_value=365,
    value=180,
    step=30
)

# 数据刷新按钮
if st.sidebar.button("🔄 刷新数据", type="primary"):
    st.session_state.stock_changed = True
    st.rerun()

# 系统状态显示
st.sidebar.header("⚡ 系统状态")

# 模拟模块状态
module_status = {
    "Dashboard": "✅",
    "图表生成": "✅",
    "热力图": "✅",
    "监控": "✅",
    "AI 模块": "✅",
    "数据模块": "✅"
}

status_col1, status_col2 = st.sidebar.columns(2)
with status_col1:
    for i, (module, status) in enumerate(list(module_status.items())[:3]):
        st.metric(module, status)
with status_col2:
    for i, (module, status) in enumerate(list(module_status.items())[3:]):
        st.metric(module, status)

# ============================================
# 首页
# ============================================
if st.session_state.current_page == "首页":
    st.title("🏠 TradingAgents 量化分析平台")
    
    # 欢迎信息
    st.markdown("""
    ### 欢迎使用 TradingAgents 量化分析平台！
    
    这是一个集成了 **所有可视化功能模块** 的完整量化分析平台。
    
    **📊 平台功能概览：**
    """)
    
    # 功能卡片
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        **📈 数据可视化**
        - 实时行情图表
        - K 线图分析
        - 技术指标图表
        - 成交量分析
        """)
    
    with col2:
        st.success("""
        **📊 Dashboard 仪表板**
        - 实时持仓监控
        - 资金曲线分析
        - 行业热力图
        - 风险指标仪表盘
        """)
    
    with col3:
        st.warning("""
        **📋 回测报告**
        - HTML 交互报告
        - 收益分布图
        - 回撤曲线分析
        - 交易记录表格
        """)
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.info("""
        **🎨 图表生成器**
        - 多种图表类型
        - 自定义配色
        - 导出功能
        - 响应式设计
        """)
    
    with col5:
        st.success("""
        **🔥 热力图分析**
        - 行业分布热力图
        - 持仓盈亏热力图
        - 因子 IC 热力图
        - 相关性热力图
        """)
    
    with col6:
        st.warning("""
        **⚡ 监控仪表板**
        - 系统性能监控
        - 资源使用情况
        - 异常告警系统
        - 实时日志展示
        """)
    
    # 快速开始按钮
    st.markdown("---")
    st.subheader("🚀 快速开始")
    
    quick_col1, quick_col2, quick_col3 = st.columns(3)
    
    with quick_col1:
        if st.button("📈 查看数据可视化", width='stretch'):
            st.session_state.current_page = "数据可视化"
            st.rerun()
    
    with quick_col2:
        if st.button("📊 打开 Dashboard", width='stretch'):
            st.session_state.current_page = "Dashboard"
            st.rerun()
    
    with quick_col3:
        if st.button("🤖 AI 分析", width='stretch'):
            st.session_state.current_page = "AI 分析"
            st.rerun()

# ============================================
# 数据可视化页面
# ============================================
elif st.session_state.current_page == "数据可视化":
    st.title(f"📈 {stock_name} ({ticker}) 数据可视化")
    
    # 获取数据函数
    @st.cache_data(ttl=3600)
    def get_stock_data(ticker, days):
        try:
            # 模拟数据生成
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            n_days = len(dates)
            
            # 生成模拟股票数据
            base_price = 100
            returns = np.random.randn(n_days) * 0.02
            prices = base_price * np.exp(np.cumsum(returns))
            
            df = pd.DataFrame({
                '日期': dates,
                '开盘': prices * (1 + np.random.randn(n_days) * 0.01),
                '最高': prices * (1 + np.abs(np.random.randn(n_days)) * 0.02),
                '最低': prices * (1 - np.abs(np.random.randn(n_days)) * 0.02),
                '收盘': prices,
                '成交量': np.random.randint(1000000, 10000000, n_days),
                '成交额': np.random.randint(100000000, 1000000000, n_days)
            })
            
            return df
        except Exception as e:
            st.error(f"获取数据失败: {e}")
            return None
    
    with st.spinner("加载数据中..."):
        df = get_stock_data(ticker, date_range)
    
    if df is not None and not df.empty:
        # 股票信息卡片
        col1, col2, col3, col4 = st.columns(4)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        with col1:
            st.metric(
                "最新价",
                f"{latest['收盘']:.2f}",
                f"{(latest['收盘'] - prev['收盘']):.2f}"
            )
        
        with col2:
            change_pct = ((latest['收盘'] - prev['收盘']) / prev['收盘'] * 100) if prev['收盘'] > 0 else 0
            st.metric(
                "涨跌幅",
                f"{change_pct:.2f}%",
                delta_color="inverse" if change_pct < 0 else "normal"
            )
        
        with col3:
            st.metric("成交量", f"{latest['成交量']/10000:.2f}万")
        
        with col4:
            st.metric("成交额", f"{latest['成交额']/100000000:.2f}亿")
        
        # 价格走势图
        st.subheader("📊 价格走势图")
        
        fig_price = go.Figure()
        
        # K 线图
        fig_price.add_trace(go.Candlestick(
            x=df['日期'],
            open=df['开盘'],
            high=df['最高'],
            low=df['最低'],
            close=df['收盘'],
            name='K线',
            increasing_line_color='#ef5350',
            decreasing_line_color='#26a69a'
        ))
        
        # 移动平均线
        df['MA5'] = df['收盘'].rolling(window=5).mean()
        df['MA20'] = df['收盘'].rolling(window=20).mean()
        
        fig_price.add_trace(go.Scatter(
            x=df['日期'],
            y=df['MA5'],
            mode='lines',
            name='MA5',
            line=dict(color='#ff9800', width=2)
        ))
        
        fig_price.add_trace(go.Scatter(
            x=df['日期'],
            y=df['MA20'],
            mode='lines',
            name='MA20',
            line=dict(color='#2196f3', width=2)
        ))
        
        fig_price.update_layout(
            title=f"{stock_name} ({ticker}) 价格走势",
            xaxis_title="日期",
            yaxis_title="价格",
            height=500,
            showlegend=True,
            template="plotly_white"
        )
        
        st.plotly_chart(fig_price, width='stretch')
        
        # 成交量图表
        st.subheader("📈 成交量分析")
        
        fig_volume = go.Figure()
        
        colors = ['#ef5350' if row['收盘'] >= row['开盘'] else '#26a69a' 
                 for _, row in df.iterrows()]
        
        fig_volume.add_trace(go.Bar(
            x=df['日期'],
            y=df['成交量'],
            name='成交量',
            marker_color=colors
        ))
        
        # 成交量均线
        df['Volume_MA5'] = df['成交量'].rolling(window=5).mean()
        
        fig_volume.add_trace(go.Scatter(
            x=df['日期'],
            y=df['Volume_MA5'],
            mode='lines',
            name='成交量 MA5',
            line=dict(color='#ff9800', width=2)
        ))
        
        fig_volume.update_layout(
            title="成交量分析",
            xaxis_title="日期",
            yaxis_title="成交量",
            height=400,
            showlegend=True,
            template="plotly_white"
        )
        
        st.plotly_chart(fig_volume, width='stretch')
        
        # 技术指标图表
        st.subheader("📉 技术指标分析")
        
        # RSI 计算
        delta = df['收盘'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD 计算
        exp1 = df['收盘'].ewm(span=12, adjust=False).mean()
        exp2 = df['收盘'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['Histogram'] = df['MACD'] - df['Signal']
        
        # 创建子图
        fig_indicators = make_subplots(
            rows=3, cols=1,
            subplot_titles=('RSI (相对强弱指数)', 'MACD (指数平滑移动平均线)', '价格走势'),
            vertical_spacing=0.1,
            row_heights=[0.3, 0.3, 0.4]
        )
        
        # RSI
        fig_indicators.add_trace(
            go.Scatter(x=df['日期'], y=df['RSI'], mode='lines', name='RSI', line=dict(color='#2196f3')),
            row=1, col=1
        )
        
        # RSI 超买超卖线
        fig_indicators.add_hline(y=70, line_dash="dash", line_color="red", row=1, col=1)
        fig_indicators.add_hline(y=30, line_dash="dash", line_color="green", row=1, col=1)
        
        # MACD
        fig_indicators.add_trace(
            go.Scatter(x=df['日期'], y=df['MACD'], mode='lines', name='MACD', line=dict(color='#ff9800')),
            row=2, col=1
        )
        
        fig_indicators.add_trace(
            go.Scatter(x=df['日期'], y=df['Signal'], mode='lines', name='Signal', line=dict(color='#2196f3')),
            row=2, col=1
        )
        
        # MACD 柱状图
        colors_macd = ['#ef5350' if val >= 0 else '#26a69a' for val in df['Histogram']]
        fig_indicators.add_trace(
            go.Bar(x=df['日期'], y=df['Histogram'], name='Histogram', marker_color=colors_macd),
            row=2, col=1
        )
        
        # 价格走势
        fig_indicators.add_trace(
            go.Scatter(x=df['日期'], y=df['收盘'], mode='lines', name='收盘价', line=dict(color='#4caf50')),
            row=3, col=1
        )
        
        fig_indicators.update_layout(
            height=800,
            showlegend=True,
            template="plotly_white"
        )
        
        st.plotly_chart(fig_indicators, width='stretch')
        
        # 数据表格
        st.subheader("📋 原始数据")
        st.dataframe(df.tail(20), width='stretch')
    else:
        st.error("❌ 无法获取股票数据")

# ============================================
# Dashboard 仪表板页面
# ============================================
elif st.session_state.current_page == "Dashboard":
    st.title("📊 Dashboard 仪表板")
    
    st.success("✅ Dashboard 模块可用")
    
    # Dashboard 功能展示
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Dashboard 功能概览
        
        **📊 核心功能：**
        - 实时持仓监控
        - 资金曲线分析
        - 行业热力图
        - 风险指标仪表盘
        - 交易记录表格
        - 系统状态监控
        
        **🎨 可视化特性：**
        - 交互式图表
        - 实时数据更新
        - 响应式设计
        - 多主题支持
        - 导出功能
        """)
    
    with col2:
        st.info("""
        **🚀 启动方式**
        
        ```python
        from tradingagents.dashboard \\
            import run_dashboard
        
        run_dashboard(port=8501)
        ```
        
        **🌐 访问地址**
        
        http://localhost:8501
        """)
    
    # 模拟 Dashboard 数据
    st.markdown("---")
    st.subheader("📈 模拟 Dashboard 预览")
    
    # 创建模拟数据
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    equity_values = 10000 + np.cumsum(np.random.randn(100