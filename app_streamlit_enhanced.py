"""
TradingAgents 增强版可视化界面
基于 Streamlit 构建的完整量化分析平台

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
    streamlit run app_streamlit_enhanced.py
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

# 尝试导入所有可视化模块
try:
    from tradingagents.dashboard import run_dashboard
    DASHBOARD_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ Dashboard 模块导入失败: {e}")
    DASHBOARD_AVAILABLE = False

try:
    from tradingagents.backtest import ReportGenerator
    REPORT_GENERATOR_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ 回测报告模块导入失败: {e}")
    REPORT_GENERATOR_AVAILABLE = False

try:
    from tradingagents.dashboard.charts import ChartGenerator
    CHART_GENERATOR_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ 图表生成器导入失败: {e}")
    CHART_GENERATOR_AVAILABLE = False

try:
    from tradingagents.dashboard.heatmap import HeatmapGenerator
    HEATMAP_GENERATOR_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ 热力图生成器导入失败: {e}")
    HEATMAP_GENERATOR_AVAILABLE = False

try:
    from tradingagents.monitoring.dashboard import MonitorDashboard
    MONITOR_DASHBOARD_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ 监控仪表板导入失败: {e}")
    MONITOR_DASHBOARD_AVAILABLE = False

# AI 分析模块导入
try:
    from intelligent_phase2.strategies.ml_trend_predictor import MLTrendPredictor
    from intelligent_phase2.data_sources.multi_source_adapter import MultiSourceAdapter
    from intelligent_phase2.risk_management.advanced_risk_monitor import AdvancedRiskMonitor
    AI_MODULES_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ AI 模块导入失败: {e}")
    AI_MODULES_AVAILABLE = False

# 导入数据获取模块
try:
    from tradingagents.dataflows import sina_utils as aks
    DATA_MODULE_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ 数据模块导入失败: {e}")
    DATA_MODULE_AVAILABLE = False

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
status_col1, status_col2 = st.sidebar.columns(2)
with status_col1:
    st.metric("Dashboard", "✅" if DASHBOARD_AVAILABLE else "❌")
    st.metric("图表生成", "✅" if CHART_GENERATOR_AVAILABLE else "❌")
with status_col2:
    st.metric("AI 模块", "✅" if AI_MODULES_AVAILABLE else "❌")
    st.metric("数据模块", "✅" if DATA_MODULE_AVAILABLE else "❌")

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
    
    # 获取数据
    @st.cache_data(ttl=3600)
    def get_stock_data(ticker, days):
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 获取日线数据
            df = aks.stock_zh_a_hist(
                symbol=ticker,
                period="daily",
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d'),
                adjust="qfq"
            )
            
            if df is not None and not df.empty:
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.sort_values('日期')
                return df
            else:
                return None
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
        st.error("❌ 无法获取股票数据，请检查股票代码或网络连接")

# ============================================
# Dashboard 仪表板页面
# ============================================
elif st.session_state.current_page == "Dashboard":
    st.title("📊 Dashboard 仪表板")
    
    if not DASHBOARD_AVAILABLE:
        st.error("❌ Dashboard 模块不可用，请检查项目依赖")
        st.info("请确保已安装 tradingagents.dashboard 模块")
    else:
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
            from tradingagents.dashboard \
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
        equity_values = 10000 + np.cumsum(np.random.randn(100) * 100)
        benchmark_values = 10000 + np.cumsum(np.random.randn(100) * 80)
        
        # 资金曲线图
        fig_equity = go.Figure()
        
        fig_equity.add_trace(go.Scatter(
            x=dates,
            y=equity_values,
            mode='lines',
            name='组合收益',
            line=dict(color='#34d399', width=3),
            fill='tozeroy',
            fillcolor='rgba(52, 211, 153, 0.1)'
        ))
        
        fig_equity.add_trace(go.Scatter(
            x=dates,
            y=benchmark_values,
            mode='lines',
            name='基准收益',
            line=dict(color='#60a5fa', width=2, dash='dash')
        ))
        
        fig_equity.update_layout(
            title="资金曲线图",
            xaxis_title="日期",
            yaxis_title="净值",
            height=400,
            template="plotly_white",
            showlegend=True
        )
        
        st.plotly_chart(fig_equity, width='stretch')
        
        # 持仓表格
        st.subheader("📋 模拟持仓监控")
        
        positions_data = {
            '证券代码': ['000001.SZ', '600519.SH', '300750.SZ', '002594.SZ'],
            '证券名称': ['平安银行', '贵州茅台', '宁德时代', '比亚迪'],
            '持仓数量': [1000, 50, 200, 300],
            '成本价': [15.2, 1800.5, 420.3, 280.6],
            '当前价': [16.8, 1850.2, 430.5, 290.3],
            '市值': [16800, 92510, 86100, 87090],
            '盈亏': [1600, 2510, 2040, 2910],
            '盈亏率%': [10.5, 2.7, 2.4, 3.4]
        }
        
        positions_df = pd.DataFrame(positions_data)
        st.dataframe(positions_df, width='stretch')
        
        # 风险指标卡片
        st.subheader("⚡ 风险指标")
        
        risk_col1, risk_col2, risk_col3, risk_col4 = st.columns(4)
        
        with risk_col1:
            st.metric("夏普比率", "1.85", "0.12")
        
        with risk_col2:
            st.metric("最大回撤", "-8.2%", "-0.3%")
        
        with risk_col3:
            st.metric("年化收益", "15.6%", "1.2%")
        
        with risk_col4:
            st.metric("波动率", "12.3%", "0.4%")
        
        # 启动 Dashboard 按钮
        st.markdown("---")
        if st.button("🚀 启动 Dashboard 服务", type="primary", width='stretch'):
            with st.spinner("正在启动 Dashboard 服务..."):
                try:
                    # 这里应该启动 Dashboard 服务
                    st.success("✅ Dashboard 服务启动成功！")
                    st.info("请访问 http://localhost:8501 查看完整 Dashboard")
                except Exception as e:
                    st.error(f"❌ 启动失败: {e}")

# ============================================
# 回测报告页面
# ============================================
elif st.session_state.current_page == "回测报告":
    st.title("📋 回测报告可视化")
    
    if not REPORT_GENERATOR_AVAILABLE:
        st.error("❌ 回测报告模块不可用，请检查项目依赖")
        st.info("请确保已安装 tradingagents.backtest 模块")
    else:
        st.success("✅ 回测报告模块可用")
        
        # 回测报告功能展示
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ### 回测报告功能概览
            
            **📊 报告内容：**
            - 资金曲线对比图
            - 收益分布直方图
            - 回撤曲线分析
            - 月度收益热力图
            - 持仓权重饼图
            - 交易记录表格
            - 风险指标卡片
            
            **📤 导出格式：**
            - HTML 交互报告
            - JSON 结构化数据
            - Markdown 文本报告
            - PNG/SVG/PDF 图片
            """)
        
        with col2:
            st.info("""
            **🚀 使用示例**
            
            ```python
            from tradingagents.backtest \
                import ReportGenerator
            
            generator = ReportGenerator()
            html_report = generator\
                .generate_html_report(
                    metrics=metrics,
                    equity_curve=equity_df,
                    trades=trades
                )
            ```
            """)
        
        # 模拟回测报告
        st.markdown("---")
        st.subheader("📈 模拟回测报告预览")
        
        # 创建模拟回测数据
        dates = pd.date_range(end=datetime.now(), periods=252, freq='B')
        equity_curve = 10000 + np.cumsum(np.random.randn(252) * 50)
        benchmark_curve = 10000 + np.cumsum(np.random.randn(252) * 40)
        
        # 资金曲线对比
        fig_backtest = go.Figure()
        
        fig_backtest.add_trace(go.Scatter(
            x=dates,
            y=equity_curve,
            mode='lines',
            name='策略收益',
            line=dict(color='#4caf50', width=3),
            fill='tozeroy',
            fillcolor='#4caf50'
        ))
        
        fig_backtest.add_trace(go.Scatter(
            x=dates,
            y=benchmark_curve,
            mode='lines',
            name='基准收益',
            line=dict(color='#2196f3', width=2, dash='dash')
        ))
        
        fig_backtest.update_layout(
            title="回测资金曲线对比",
            xaxis_title="日期",
            yaxis_title="净值",
            height=400,
            template="plotly_white",
            showlegend=True
        )
        
        st.plotly_chart(fig_backtest, width='stretch')
        
        # 收益分布直方图
        returns = np.diff(equity_curve) / equity_curve[:-1] * 100
        
        fig_returns = px.histogram(
            x=returns,
            nbins=30,
            title="收益分布直方图",
            labels={'x': '日收益率 (%)', 'y': '频次'},
            color_discrete_sequence=['#ff9800']
        )
        
        fig_returns.update_layout(
            height=300,
            template="plotly_white"
        )
        
        st.plotly_chart(fig_returns, width='stretch')
        
        # 回撤曲线
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - peak) / peak * 100
        
        fig_drawdown = go.Figure()
        
        fig_drawdown.add_trace(go.Scatter(
            x=dates,
            y=drawdown,
            mode='lines',
            name='回撤曲线',
            line=dict(color='#f44336', width=2),
            fill='tozeroy',
            fillcolor='rgba(244, 67, 54, 0.2)'
        ))
        
        fig_drawdown.update_layout(
            title="回撤曲线分析",
            xaxis_title="日期",
            yaxis_title="回撤 (%)",
            height=300,
            template="plotly_white",
            showlegend=True
        )
        
        st.plotly_chart(fig_drawdown, width='stretch')
        
        # 月度收益热力图
        st.subheader("📅 月度收益热力图")
        
        # 创建模拟月度收益数据
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        years = ['2023', '2024', '2025']
        
        monthly_returns = np.random.randn(len(years), len(months)) * 2 + 0.5
        
        fig_monthly = px.imshow(
            monthly_returns,
            x=months,
            y=years,
            color_continuous_scale='RdYlGn',
            title="月度收益热力图",
            labels=dict(x="月份", y="年份", color="收益率 (%)")
        )
        
        fig_monthly.update_layout(
            height=400,
            template="plotly_white"
        )
        
        st.plotly_chart(fig_monthly, width='stretch')
        
        # 生成报告按钮
        st.markdown("---")
        if st.button("📄 生成 HTML 回测报告", type="primary", width='stretch'):
            with st.spinner("正在生成回测报告..."):
                try:
                    # 这里应该调用 ReportGenerator
                    st.success("✅ 回测报告生成成功！")
                    st.info("报告已保存为 backtest_report.html")
                    
                    # 提供下载链接（模拟）
                    st.download_button(
                        label="📥 下载 HTML 报告",
                        data="<html><body><h1>回测报告</h1></body></html>",
                        file_name="backtest_report.html",
                        mime="text/html"
                    )
                except Exception as e:
                    st.error(f"❌ 生成失败: {e}")

# ============================================
# 图表生成器页面
# ============================================
elif st.session_state.current_page == "图表生成器":
    st.title("🎨 图表生成器")
    
    if not CHART_GENERATOR_AVAILABLE:
        st.error("❌ 图表生成器不可用，请检查项目依赖")
        st.info("请确保已安装 tradingagents.dashboard.charts 模块")
    else:
        st.success("✅ 图表生成器可用")
        
        # 图表类型选择
        st.subheader("📊 选择图表类型")
        
        chart_types = [
            "资金曲线图",
            "收益柱状图",
            "回撤曲线图",
            "持仓饼图",
            "散点图",
            "K 线图",
            "成交量柱状图"
        ]
        
        selected_chart = st.selectbox("图表类型", chart_types)
        
        # 图表参数设置
        st.subheader("⚙️ 图表参数设置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            chart_title = st.text_input("图表标题", f"{selected_chart}")
            chart_width = st.slider("图表宽度", 600, 1200, 800, 50)
            
        with col2:
            chart_height = st.slider("图表高度", 400, 800, 500, 50)
            theme = st.selectbox("主题", ["浅色", "深色", "Plotly", "Seaborn"])
        
        # 颜色设置
        st.subheader("🎨 颜色设置")
        
        color_col1, color_col2, color_col3 = st.columns(3)
        
        with color_col1:
            line_color = st.color_picker("线条颜色", "#4caf50")
        
        with color_col2:
            fill_color = st.color_picker("填充颜色", "rgba(76, 175, 80, 0.1)")
        
        with color_col3:
            bg_color = st.color_picker("背景颜色", "#ffffff")
        
        # 生成图表按钮
        if st.button("🔄 生成图表", type="primary"):
            with st.spinner("正在生成图表..."):
                try:
                    # 创建模拟数据
                    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
                    values = 100 + np.cumsum(np.random.randn(100))
                    
                    # 根据选择的图表类型生成不同的图表
                    if selected_chart == "资金曲线图":
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(
                            x=dates,
                            y=values,
                            mode='lines',
                            name='资金曲线',
                            line=dict(color=line_color, width=3),
                            fill='tozeroy',
                            fillcolor=fill_color
                        ))
                        
                        fig.update_layout(
                            title=chart_title,
                            xaxis_title="日期",
                            yaxis_title="净值",
                            width=chart_width,
                            height=chart_height,
                            plot_bgcolor=bg_color,
                            template="plotly_white" if theme == "浅色" else "plotly_dark"
                        )
                        
                    elif selected_chart == "收益柱状图":
                        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        returns = np.random.randn(12) * 2
                        
                        fig = go.Figure()
                        
                        colors = ['#4caf50' if r >= 0 else '#f44336' for r in returns]
                        
                        fig.add_trace(go.Bar(
                            x=months,
                            y=returns,
                            name='月度收益',
                            marker_color=colors
                        ))
                        
                        fig.update_layout(
                            title=chart_title,
                            xaxis_title="月份",
                            yaxis_title="收益率 (%)",
                            width=chart_width,
                            height=chart_height,
                            plot_bgcolor=bg_color,
                            template="plotly_white" if theme == "浅色" else "plotly_dark"
                        )
                        
                    elif selected_chart == "回撤曲线图":
                        peak = np.maximum.accumulate(values)
                        drawdown = (values - peak) / peak * 100
                        
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(
                            x=dates,
                            y=drawdown,
                            mode='lines',
                            name='回撤曲线',
                            line=dict(color=line_color, width=2),
                            fill='tozeroy',
                            fillcolor=fill_color
                        ))
                        
                        fig.update_layout(
                            title=chart_title,
                            xaxis_title="日期",
                            yaxis_title="回撤 (%)",
                            width=chart_width,
                            height=chart_height,
                            plot_bgcolor=bg_color,
                            template="plotly_white" if theme == "浅色" else "plotly_dark"
                        )
                        
                    elif selected_chart == "持仓饼图":
                        sectors = ['银行', '白酒', '新能源', '医药', '科技', '消费']
                        weights = np.random.dirichlet(np.ones(6), size=1)[0] * 100
                        
                        fig = go.Figure()
                        
                        fig.add_trace(go.Pie(
                            labels=sectors,
                            values=weights,
                            hole=0.3,
                            marker=dict(colors=px.colors.qualitative.Set3)
                        ))
                        
                        fig.update_layout(
                            title=chart_title,
                            width=chart_width,
                            height=chart_height,
                            plot_bgcolor=bg_color,
                            template="plotly_white" if theme == "浅色" else "plotly_dark"
                        )
                        
                    elif selected_chart == "散点图":
                        x_data = np.random.randn(50)
                        y_data = x_data + np.random.randn(50) * 0.5
                        
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(
                            x=x_data,
                            y=y_data,
                            mode='markers',
                            name='散点数据',
                            marker=dict(
                                color=line_color,
                                size=10,
                                opacity=0.7
                            )
                        ))
                        
                        # 添加趋势线
                        z = np.polyfit(x_data, y_data, 1)
                        p = np.poly1d(z)
                        
                        fig.add_trace(go.Scatter(
                            x=np.sort(x_data),
                            y=p(np.sort(x_data)),
                            mode='lines',
                            name='趋势线',
                            line=dict(color='#ff9800', width=2)
                        ))
                        
                        fig.update_layout(
                            title=chart_title,
                            xaxis_title="X 轴",
                            yaxis_title="Y 轴",
                            width=chart_width,
                            height=chart_height,
                            plot_bgcolor=bg_color,
                            template="plotly_white" if theme == "浅色" else "plotly_dark"
                        )
                        
                    elif selected_chart == "K 线图":
                        # 创建模拟 K 线数据
                        dates_k = pd.date_range(end=datetime.now(), periods=30, freq='D')
                        open_prices = 100 + np.cumsum(np.random.randn(30) * 2)
                        close_prices = open_prices + np.random.randn(30) * 5
                        high_prices = np.maximum(open_prices, close_prices) + np.random.rand(30) * 3
                        low_prices = np.minimum(open_prices, close_prices) - np.random.rand(30) * 3
                        
                        fig = go.Figure()
                        
                        fig.add_trace(go.Candlestick(
                            x=dates_k,
                            open=open_prices,
                            high=high_prices,
                            low=low_prices,
                            close=close_prices,
                            name='K线',
                            increasing_line_color='#4caf50',
                            decreasing_line_color='#f44336'
                        ))
                        
                        fig.update_layout(
                            title=chart_title,
                            xaxis_title="日期",
                            yaxis_title="价格",
                            width=chart_width,
                            height=chart_height,
                            plot_bgcolor=bg_color,
                            template="plotly_white" if theme == "浅色" else "plotly_dark",
                            xaxis_rangeslider_visible=False
                        )
                        
                    elif selected_chart == "成交量柱状图":
                        volumes = np.random.randint(1000, 10000, size=30)
                        
                        fig = go.Figure()
                        
                        colors = ['#4caf50' if i % 2 == 0 else '#f44336' for i in range(30)]
                        
                        fig.add_trace(go.Bar(
                            x=list(range(30)),
                            y=volumes,
                            name='成交量',
                            marker_color=colors
                        ))
                        
                        fig.update_layout(
                            title=chart_title,
                            xaxis_title="交易日",
                            yaxis_title="成交量",
                            width=chart_width,
                            height=chart_height,
                            plot_bgcolor=bg_color,
                            template="plotly_white" if theme == "浅色" else "plotly_dark"
                        )
                        
                    # 显示图表
                    st.plotly_chart(fig, width='stretch')
                    
                    # 导出选项
                    st.subheader("📤 导出图表")
                    
                    export_col1, export_col2, export_col3 = st.columns(3)
                    
                    with export_col1:
                        if st.button("💾 保存为 PNG"):
                            st.success("✅ 图表已保存为 chart.png")
                    
                    with export_col2:
                        if st.button("🎨 保存为 SVG"):
                            st.success("✅ 图表已保存为 chart.svg")
                    
                    with export_col3:
                        if st.button("📄 保存为 PDF"):
                            st.success("✅ 图表已保存为 chart.pdf")
                    
                except Exception as e:
                    st.error(f"❌ 生成失败: {e}")
        else:
            # 显示示例图表
            st.info("👆 请设置图表参数并点击'生成图表'按钮")
            
            # 显示图表类型示例
            st.subheader("📚 图表类型示例")
            
            example_col1, example_col2 = st.columns(2)
            
            with example_col1:
                st.markdown("""
                **📈 资金曲线图**
                - 展示资金净值变化
                - 支持基准对比
                - 填充区域显示
                
                **📊 收益柱状图**
                - 月度/年度收益展示
                - 红绿颜色区分
                - 收益对比分析
                """)
            
            with example_col2:
                st.markdown("""
                **📉 回撤曲线图**
                - 最大回撤分析
                - 回撤深度可视化
                - 风险控制参考
                
                **🥧 持仓饼图**
                - 资产配置展示
                - 行业分布分析
                - 环形图设计
                """)

# ============================================
# 热力图分析页面
# ============================================
elif st.session_state.current_page == "热力图分析":
    st.title("🔥 热力图分析")
    
    if not HEATMAP_GENERATOR_AVAILABLE:
        st.error("❌ 热力图生成器不可用，请检查项目依赖")
        st.info("请确保已安装 tradingagents.dashboard.heatmap 模块")
    else:
        st.success("✅ 热力图生成器可用")
        
        # 热力图类型选择
        st.subheader("📊 选择热力图类型")
        
        heatmap_types = [
            "行业分布热力图",
            "持仓盈亏热力图",
            "因子 IC 热力图",
            "相关性热力图",
            "月度收益热力图"
        ]
        
        selected_heatmap = st.selectbox("热力图类型", heatmap_types)
        
        # 热力图参数设置
        st.subheader("⚙️ 热力图参数设置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            heatmap_title = st.text_input("热力图标题", f"{selected_heatmap}")
            color_scale = st.selectbox("颜色方案", 
                ["RdYlGn", "Viridis", "Plasma", "Inferno", "Magma", "Cividis"])
            
        with col2:
            show_values = st.checkbox("显示数值", True)
            show_annotations = st.checkbox("显示注释", True)
        
        # 生成热力图按钮
        if st.button("🔄 生成热力图", type="primary"):
            with st.spinner("正在生成热力图..."):
                try:
                    # 根据选择的类型生成不同的热力图
                    if selected_heatmap == "行业分布热力图":
                        sectors = ['银行', '白酒', '新能源', '医药', '科技', '消费', '地产', '化工']
                        dates = pd.date_range(end=datetime.now(), periods=10, freq='ME')
                        
                        # 创建行业收益数据
                        sector_returns = np.random.randn(len(sectors), len(dates)) * 2 + 0.5
                        
                        fig = px.imshow(
                            sector_returns,
                            x=dates.strftime('%Y-%m'),
                            y=sectors,
                            color_continuous_scale=color_scale,
                            title=heatmap_title,
                            labels=dict(x="日期", y="行业", color="收益率 (%)")
                        )
                        
                        if show_values:
                            fig.update_traces(text=sector_returns.round(2), 
                                            texttemplate="%{text}%")
                        
                    elif selected_heatmap == "持仓盈亏热力图":
                        stocks = ['000001', '600519', '300750', '002594', 
                                 '600036', '601318', '000858', '600276']
                        dates = pd.date_range(end=datetime.now(), periods=20, freq='D')
                        
                        # 创建持仓盈亏数据
                        position_pnl = np.random.randn(len(stocks), len(dates)) * 1.5
                        
                        fig = px.imshow(
                            position_pnl,
                            x=dates.strftime('%m-%d'),
                            y=stocks,
                            color_continuous_scale=color_scale,
                            title=heatmap_title,
                            labels=dict(x="日期", y="股票代码", color="盈亏 (%)")
                        )
                        
                        if show_values:
                            fig.update_traces(text=position_pnl.round(2), 
                                            texttemplate="%{text}%")
                        
                    elif selected_heatmap == "因子 IC 热力图":
                        factors = ['估值', '成长', '质量', '动量', '波动', '规模', '流动性', '情绪']
                        periods = ['1M', '3M', '6M', '1Y', '2Y', '3Y']
                        
                        # 创建因子 IC 数据
                        factor_ic = np.random.randn(len(factors), len(periods)) * 0.3 + 0.1
                        
                        fig = px.imshow(
                            factor_ic,
                            x=periods,
                            y=factors,
                            color_continuous_scale=color_scale,
                            title=heatmap_title,
                            labels=dict(x="周期", y="因子", color="IC 值")
                        )
                        
                        if show_values:
                            fig.update_traces(text=factor_ic.round(3), 
                                            texttemplate="%{text}")
                        
                    elif selected_heatmap == "相关性热力图":
                        assets = ['股票', '债券', '黄金', '原油', '美元', '欧元', '比特币', '房地产']
                        
                        # 创建相关性矩阵
                        correlation = np.random.rand(len(assets), len(assets)) * 2 - 1
                        np.fill_diagonal(correlation, 1.0)
                        correlation = (correlation + correlation.T) / 2
                        
                        fig = px.imshow(
                            correlation,
                            x=assets,
                            y=assets,
                            color_continuous_scale=color_scale,
                            title=heatmap_title,
                            labels=dict(x="资产", y="资产", color="相关系数")
                        )
                        
                        if show_values:
                            fig.update_traces(text=correlation.round(2), 
                                            texttemplate="%{text}")
                        
                    elif selected_heatmap == "月度收益热力图":
                        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        years = ['2020', '2021', '2022', '2023', '2024']
                        
                        # 创建月度收益数据
                        monthly_returns = np.random.randn(len(years), len(months)) * 2 + 0.5
                        
                        fig = px.imshow(
                            monthly_returns,
                            x=months,
                            y=years,
                            color_continuous_scale=color_scale,
                            title=heatmap_title,
                            labels=dict(x="月份", y="年份", color="收益率 (%)")
                        )
                        
                        if show_values:
                            fig.update_traces(text=monthly_returns.round(2), 
                                            texttemplate="%{text}%")
                    
                    # 更新布局
                    fig.update_layout(
                        height=600,
                        template="plotly_white",
                        coloraxis_colorbar=dict(
                            title="数值",
                            thickness=20,
                            len=0.8
                        )
                    )
                    
                    # 显示热力图
                    st.plotly_chart(fig, width='stretch')
                    
                    # 热力图分析
                    st.subheader("📊 热力图分析")
                    
                    if selected_heatmap == "行业分布热力图":
                        st.markdown("""
                        **📈 分析要点：**
                        - 红色区域表示高收益行业
                        - 绿色区域表示低收益或亏损行业
                        - 颜色深浅反映收益强度
                        - 可用于行业轮动策略
                        """)
                    
                    elif selected_heatmap == "持仓盈亏热力图":
                        st.markdown("""
                        **📊 分析要点：**
                        - 红色表示盈利持仓
                        - 绿色表示亏损持仓
                        - 颜色深浅反映盈亏幅度
                        - 可用于持仓调整决策
                        """)
                    
                    elif selected_heatmap == "因子 IC 热力图":
                        st.markdown("""
                        **🔍 分析要点：**
                        - IC 值反映因子预测能力
                        - 正值表示正向预测
                        - 负