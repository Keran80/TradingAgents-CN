"""
TradingAgents 可视化界面
基于 Streamlit 构建的 A股股票分析工具

使用方法:
    streamlit run app_streamlit.py
"""
import streamlit as st

# 初始化 session_state 用于跟踪股票变化
if 'current_stock' not in st.session_state:
    st.session_state.current_stock = "股票"
if 'stock_changed' not in st.session_state:
    st.session_state.stock_changed = False
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 导入数据获取模块
from tradingagents.dataflows import sina_utils as aks

# 页面配置
st.set_page_config(
    page_title="TradingAgents 可视化",
    page_icon="📈",
    layout="wide"
)

# 标题
st.title("📈 TradingAgents 股票分析工具")

# 侧边栏 - 股票选择
st.sidebar.header("股票选择")

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

# 选择模式：下拉选择 或 手动输入
input_mode = st.sidebar.radio("输入模式", ["选择股票", "输入代码"])


# 初始化 stock_name（全局）
stock_name = "股票"
if input_mode == "选择股票":
    selected_stock = st.sidebar.selectbox(
        "选择股票",
        list(STOCK_CODES.keys())
    )
    ticker = STOCK_CODES[selected_stock]
    stock_name = selected_stock
else:
    # 手动输入股票代码
    ticker_input = st.sidebar.text_input("输入股票代码", placeholder="如: 000001, 600519")
    if ticker_input:
        # 尝试获取股票名称
        ticker = ticker_input.strip()
        try:
            info = aks.get_stock_individual_info_em(ticker)
            if info is not None and len(info) > 0:
                # get_stock_individual_info_em 返回 item/value 格式，需要查找
                stock_name = '未知'
                for _, row in info.iterrows():
                    if row.get('item') == '股票简称':
                        stock_name = row.get('value', '未知')
                        break
                st.sidebar.success(f"已选择: {stock_name} ({ticker})")
            else:
                st.sidebar.warning("未找到该股票信息")
        except Exception as e:
            st.sidebar.info(f"输入代码: {ticker}")
    else:
        ticker = "000001"  # 默认
        st.sidebar.info("请输入股票代码")

# 时间范围选择
date_range = st.sidebar.slider(
    "时间范围（天）",
    min_value=30,
    max_value=365,
    value=90
)

# 获取数据
@st.cache_data(ttl=3600)
def get_stock_data(ticker_code, days):
    """获取股票数据"""
    end_date = datetime.now().strftime("%Y%m%d")
    start_date_obj = datetime.now() - timedelta(days=days)
    start_date = start_date_obj.strftime("%Y%m%d")
    
    try:
        df_daily = aks.get_stock_daily(ticker_code, start_date, end_date)
        df_quote = aks.get_stock_realtime_quote(ticker_code)
        
        # 转换为中文列名（保持与代码其他部分兼容）
        if df_daily is not None and not df_daily.empty:
            df_daily = df_daily.rename(columns={
                'date': '日期',
                'symbol': '股票代码',
                'open': '开盘',
                'close': '收盘',
                'high': '最高',
                'low': '最低',
                'volume': '成交量',
                'amount': '成交额',
                'amplitude': '振幅',
                'pct_change': '涨跌幅',
                'change': '涨跌额',
                'turnover': '换手率'
            })
        
        return df_daily, df_quote
    except Exception as e:
        st.error(f"获取数据失败: {e}")
        return None, None

with st.spinner("加载数据中..."):
    df_daily, df_quote = get_stock_data(ticker, date_range)

if df_daily is not None and not df_daily.empty:
    # 提取实时行情
    if df_quote is not None and not df_quote.empty:
        quote = df_quote.iloc[0]
        current_price = quote.get('最新价', 0)
        change_pct = quote.get('涨跌幅', 0)
        volume = quote.get('成交量', 0)
        amount = quote.get('成交额', 0)
        high = quote.get('最高', 0)
        low = quote.get('最低', 0)
        open_price = quote.get('开盘', 0)
        
        # 顶部信息卡片
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("当前价格", f"¥{current_price:.2f}", f"{change_pct:.2f}%")
        with col2:
            st.metric("涨跌额", f"¥{current_price - open_price:.2f}")
        with col3:
            st.metric("成交量", f"{volume/10000:.2f}万")
        with col4:
            st.metric("成交额", f"¥{amount/100000000:.2f}亿")
        
        st.markdown("---")
        
        # K线图
        st.subheader("📊 K线走势")
        
        # 准备数据
        df_plot = df_daily.copy()
        df_plot['日期'] = pd.to_datetime(df_plot['日期'])
        
        # 创建 K线图
        fig = go.Figure(data=[go.Candlestick(
            x=df_plot['日期'],
            open=df_plot['开盘'],
            high=df_plot['最高'],
            low=df_plot['最低'],
            close=df_plot['收盘'],
            name='K线'
        )])
        
        # 添加均线
        df_plot['MA5'] = df_plot['收盘'].rolling(window=5).mean()
        df_plot['MA10'] = df_plot['收盘'].rolling(window=10).mean()
        df_plot['MA20'] = df_plot['收盘'].rolling(window=20).mean()
        
        fig.add_trace(go.Scatter(x=df_plot['日期'], y=df_plot['MA5'], name='MA5', line=dict(color='orange', width=1)))
        fig.add_trace(go.Scatter(x=df_plot['日期'], y=df_plot['MA10'], name='MA10', line=dict(color='purple', width=1)))
        fig.add_trace(go.Scatter(x=df_plot['日期'], y=df_plot['MA20'], name='MA20', line=dict(color='blue', width=1)))
        
        fig.update_layout(
            xaxis_rangeslider_visible=False,
            height=500,
            template="plotly_dark"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 成交量图
        st.subheader("📉 成交量")
        
        # 涨跌幅颜色
        colors = ['red' if df_plot.iloc[i]['收盘'] >= df_plot.iloc[i]['开盘'] else 'green' 
                  for i in range(len(df_plot))]
        
        fig_vol = go.Figure(data=[go.Bar(
            x=df_plot['日期'],
            y=df_plot['成交量'],
            marker_color=colors,
            name='成交量'
        )])
        
        fig_vol.update_layout(
            height=250,
            template="plotly_dark",
            xaxis_title="日期",
            yaxis_title="成交量"
        )
        
        st.plotly_chart(fig_vol, use_container_width=True)
        
        # 技术指标
        st.markdown("---")
        st.subheader("📈 技术指标")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 计算技术指标
            df_tech = df_plot.copy()
            
            # RSI
            delta = df_tech['收盘'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df_tech['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = df_tech['收盘'].ewm(span=12, adjust=False).mean()
            exp2 = df_tech['收盘'].ewm(span=26, adjust=False).mean()
            df_tech['MACD'] = exp1 - exp2
            df_tech['Signal'] = df_tech['MACD'].ewm(span=9, adjust=False).mean()
            df_tech['Histogram'] = df_tech['MACD'] - df_tech['Signal']
            
            latest_rsi = df_tech['RSI'].iloc[-1]
            st.metric("RSI(14)", f"{latest_rsi:.2f}")
            
            if latest_rsi > 70:
                st.warning("⚠️ RSI 超买区域")
            elif latest_rsi < 30:
                st.success("🔔 RSI 超卖区域")
            else:
                st.info("➡️ RSI 正常区域")
        
        with col2:
            latest_macd = df_tech['MACD'].iloc[-1]
            latest_signal = df_tech['Signal'].iloc[-1]
            st.metric("MACD", f"{latest_macd:.4f}", f"{latest_macd - latest_signal:.4f}")
            
            if latest_macd > latest_signal:
                st.success("🔔 MACD 金叉（看涨）")
            else:
                st.warning("⚠️ MACD 死叉（看跌）")
        
        # RSI 图
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df_tech['日期'], y=df_tech['RSI'], name='RSI', line=dict(color='yellow', width=2)))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超买")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="超卖")
        fig_rsi.update_layout(
            height=200,
            template="plotly_dark",
            yaxis_range=[0, 100],
            xaxis_title="日期",
            yaxis_title="RSI"
        )
        
        st.plotly_chart(fig_rsi, use_container_width=True)
        
        # MACD 图
        fig_macd = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
                                 subplot_titles=('MACD', '价格'))
        
        # MACD
        fig_macd.add_trace(go.Bar(x=df_tech['日期'], y=df_tech['Histogram'], name='Histogram', 
                                   marker_color=['red' if x > 0 else 'green' for x in df_tech['Histogram']]),
                           row=1, col=1)
        fig_macd.add_trace(go.Scatter(x=df_tech['日期'], y=df_tech['MACD'], name='MACD', line=dict(color='blue')),
                           row=1, col=1)
        fig_macd.add_trace(go.Scatter(x=df_tech['日期'], y=df_tech['Signal'], name='Signal', line=dict(color='orange')),
                           row=1, col=1)
        
        # 价格
        fig_macd.add_trace(go.Scatter(x=df_tech['日期'], y=df_tech['收盘'], name='收盘价', line=dict(color='white')),
                           row=2, col=1)
        
        fig_macd.update_layout(height=350, template="plotly_dark", showlegend=True)
        
        st.plotly_chart(fig_macd, use_container_width=True)
        
        # AI 分析结论显示区域
        st.markdown("---")
        st.subheader("🤖 AI 分析结论")
        
        # 分析结论输入区域（允许用户粘贴AI分析结果）
        # 根据股票动态生成默认分析结论
        default_analysis = f"""1. 基本面：请分析 {stock_name} 的基本面情况
2. 技术面：请分析技术走势、支撑位和压力位
3. 资金面：请分析主力资金流向
4. 综合建议：请给出投资建议"""

        # 分析结论输入区域（允许用户粘贴 AI 分析结果）
        with st.expander("📝 粘贴/编辑 AI 分析结论", expanded=False):
            # 如果股票变化了，清空之前的分析结论
            if st.session_state.get('stock_changed', False):
                # 重置分析结论为新的默认值
                analysis_text = st.text_area(
                    "分析结论",
                    value=default_analysis,
                    height=150,
                    help=f"股票已切换为 {stock_name}，请重新分析",
                    key=f"analysis_{stock_name}"  # 使用唯一的 key 强制刷新
                )
                # 重置变化标志
                st.session_state.stock_changed = False
            else:
                analysis_text = st.text_area(
                    "分析结论",
                    value=default_analysis,
                    height=150,
                    help=f"可根据 AI 分析结果粘贴或修改结论，当前股票：{stock_name}",
                    key=f"analysis_{stock_name}"  # 使用唯一的 key
                )
        
        
        # 解析每行
        lines = analysis_text.strip().split('\n')
        
        # 使用卡片样式显示
        for line in lines:
            line = line.strip()
            if line:
                # 判断类型
                if "基本面" in line or "基本面分析" in line:
                    st.success(f"💰 {line}")
                elif "技术面" in line or "技术分析" in line:
                    st.info(f"📈 {line}")
                elif "资金面" in line or "资金分析" in line:
                    st.warning(f"💵 {line}")
                elif "综合建议" in line or "建议" in line:
                    if "买入" in line:
                        st.error(f"🎯 {line}")
                    elif "卖出" in line:
                        st.error(f"🎯 {line}")
                    elif "持有" in line or "观望" in line:
                        st.warning(f"🎯 {line}")
                    else:
                        st.info(f"🎯 {line}")
                else:
                    st.write(f"• {line}")
        
        # 结论摘要（自动生成）
        st.markdown("---")
        st.markdown("#### 📋 结论摘要")
        
        # 提取关键信息
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 判断趋势
            recent_closes = df_tech['收盘'].tail(5).values
            if len(recent_closes) >= 2:
                trend = "上涨" if recent_closes[-1] > recent_closes[0] else "下跌"
                st.metric("近期趋势", trend)
        
        with col2:
            # 支撑位/压力位（简化计算）
            support = df_tech['收盘'].min()
            resistance = df_tech['收盘'].max()
            st.metric("支撑/压力", f"¥{support:.2f} / ¥{resistance:.2f}")
        
        with col3:
            # 成交量变化
            if len(df_tech) >= 5:
                vol_now = df_tech['成交量'].iloc[-1]
                vol_avg = df_tech['成交量'].tail(5).mean()
                vol_change = (vol_now - vol_avg) / vol_avg * 100 if vol_avg > 0 else 0
                st.metric("成交量变化", f"{vol_change:+.1f}%")
        
        # 数据表格
        st.markdown("---")
        st.subheader("📋 历史数据")
        
        st.dataframe(
            df_plot[['日期', '开盘', '收盘', '最高', '最低', '成交量']].tail(20),
            use_container_width=True
        )
        
else:
    st.error("无法获取股票数据，请检查股票代码是否正确")
