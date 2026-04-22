#!/usr/bin/env python3
"""
调试版本的主应用
添加详细的日志输出定位问题
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# ============================================
# 页面配置
# ============================================
st.set_page_config(
    page_title="TradingAgents 调试版",
    page_icon="🐛",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🐛 TradingAgents 按钮表格窗口集成 - 调试版")
st.info("这是调试版本，添加了详细的日志输出")

# ============================================
# 初始化会话状态
# ============================================
st.subheader("🔧 会话状态初始化")

# 初始化必要的会话状态变量
if 'module' not in st.session_state:
    st.session_state.module = "🏠 首页"
    st.write("✅ 初始化 module = '🏠 首页'")

if 'click_count' not in st.session_state:
    st.session_state.click_count = {}
    st.write("✅ 初始化 click_count = {}")

if 'test_data' not in st.session_state:
    st.session_state.test_data = {"test": "data"}
    st.write("✅ 初始化 test_data")

# 显示当前会话状态
st.write("📊 当前会话状态:")
st.json(st.session_state)

# ============================================
# 侧边栏 - 模块选择
# ============================================
st.sidebar.title("📊 TradingAgents - 调试")

# 模块选择按钮
st.sidebar.subheader("选择可视化模块")
module_options = [
    "🏠 首页",
    "📊 Dashboard 按钮表格",
    "📋 回测报告表格",
    "🎨 图表控制按钮", 
    "🔥 热力图窗口",
    "⚡ 监控告警表格",
    "📉 因子分析窗口",
    "🎯 策略对比表格",
    "🤖 AI 分析按钮"
]

# 使用 radio 而不是 selectbox 以便立即看到效果
selected_module = st.sidebar.radio(
    "选择模块",
    module_options,
    index=module_options.index(st.session_state.module) if st.session_state.module in module_options else 0
)

st.write(f"🔍 选择的模块: {selected_module}")
st.write(f"🔍 当前 session_state.module: {st.session_state.module}")

# 更新会话状态
if selected_module != st.session_state.module:
    st.session_state.module = selected_module
    st.write(f"🔄 更新 session_state.module 为: {selected_module}")
    st.rerun()

# ============================================
# 首页模块 - 简化测试
# ============================================
if st.session_state.module == "🏠 首页":
    st.header("🏠 首页 - 简化测试")
    
    # 测试按钮1
    st.subheader("测试按钮1 - 简单回调")
    if st.button("测试按钮1", width='stretch'):
        st.success("✅ 测试按钮1 点击成功！")
        st.session_state.click_count['btn1'] = st.session_state.click_count.get('btn1', 0) + 1
        st.write(f"点击次数: {st.session_state.click_count['btn1']}")
    
    # 测试按钮2 - 带类型
    st.subheader("测试按钮2 - 带类型")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("主要按钮", type="primary", width='stretch'):
            st.success("✅ 主要按钮点击成功")
    with col2:
        if st.button("次要按钮", type="secondary", width='stretch'):
            st.warning("⚠️ 次要按钮点击成功")
    with col3:
        if st.button("危险按钮", type="primary", width='stretch'):
            st.error("❌ 危险按钮点击成功")
    
    # 表单测试
    st.subheader("表单测试")
    with st.form("test_form"):
        name = st.text_input("姓名")
        submitted = st.form_submit_button("提交", width='stretch')
        if submitted:
            st.success(f"✅ 表单提交成功！姓名: {name}")
    
    # 链接测试
    st.subheader("链接测试")
    st.markdown("[测试链接到 Streamlit](https://streamlit.io)")
    
    # 显示会话状态
    st.subheader("当前点击统计")
    st.write(st.session_state.click_count)

# ============================================
# Dashboard 模块 - 简化测试
# ============================================
elif st.session_state.module == "📊 Dashboard 按钮表格":
    st.header("📊 Dashboard 按钮表格 - 简化测试")
    
    # 标签页按钮测试
    st.subheader("标签页按钮测试")
    tab_cols = st.columns(4)
    with tab_cols[0]:
        if st.button("持仓监控", type="primary", width='stretch'):
            st.success("✅ 持仓监控按钮点击")
    with tab_cols[1]:
        if st.button("策略表现", width='stretch'):
            st.success("✅ 策略表现按钮点击")
    with tab_cols[2]:
        if st.button("告警历史", width='stretch'):
            st.success("✅ 告警历史按钮点击")
    with tab_cols[3]:
        if st.button("热力图", width='stretch'):
            st.success("✅ 热力图按钮点击")
    
    # 控制按钮测试
    st.subheader("控制按钮测试")
    control_cols = st.columns(3)
    with control_cols[0]:
        if st.button("刷新数据", width='stretch'):
            st.success("✅ 刷新数据按钮点击")
    with control_cols[1]:
        if st.button("导出数据", width='stretch'):
            st.success("✅ 导出数据按钮点击")
    with control_cols[2]:
        auto_refresh = st.checkbox("自动刷新", value=True)
        st.write(f"自动刷新状态: {auto_refresh}")
    
    # 表格测试
    st.subheader("表格测试")
    test_data = pd.DataFrame({
        '证券代码': ['000001', '600519', '300750'],
        '证券名称': ['平安银行', '贵州茅台', '宁德时代'],
        '价格': [16.80, 1850.20, 430.50]
    })
    st.dataframe(test_data, width='stretch')
    
    # 表格操作按钮
    if st.button("导出表格", width='stretch'):
        st.success("✅ 表格导出成功")

# ============================================
# 其他模块占位符
# ============================================
else:
    st.header(f"{st.session_state.module} - 简化测试")
    st.info(f"这是 {st.session_state.module} 模块的简化测试版本")
    
    # 通用测试按钮
    if st.button(f"测试 {st.session_state.module} 按钮", width='stretch'):
        st.success(f"✅ {st.session_state.module} 按钮点击成功")
    
    # 返回首页按钮
    if st.button("返回首页", width='stretch'):
        st.session_state.module = "🏠 首页"
        st.rerun()

# ============================================
# 调试信息
# ============================================
st.markdown("---")
st.subheader("🐛 调试信息")

# 显示所有会话状态
st.write("📋 完整会话状态:")
st.json(dict(st.session_state))

# 性能信息
st.write("⏱️ 页面生成时间:", datetime.now().strftime("%H:%M:%S"))

# 重启按钮
if st.button("🔄 重启应用", type="primary", width='stretch'):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 运行命令提示
st.markdown("---")
st.code("streamlit run debug_app_buttons.py --server.port 8503")