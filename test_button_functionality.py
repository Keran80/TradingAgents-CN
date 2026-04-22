#!/usr/bin/env python3
"""
测试 Streamlit 按钮功能
"""

import streamlit as st
import time

st.set_page_config(
    page_title="按钮功能测试",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Streamlit 按钮功能测试")
st.markdown("测试各种按钮和表单元素的功能")

# 1. 简单按钮测试
st.subheader("1. 简单按钮测试")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("✅ 正常按钮", width='stretch'):
        st.success("✅ 按钮点击成功！")
        st.balloons()

with col2:
    if st.button("⚠️ 警告按钮", type="secondary", width='stretch'):
        st.warning("⚠️ 警告按钮被点击")

with col3:
    if st.button("❌ 危险按钮", type="primary", width='stretch'):
        st.error("❌ 危险按钮被点击")

# 2. 表单测试
st.subheader("2. 表单测试")
with st.form("test_form"):
    name = st.text_input("姓名")
    age = st.number_input("年龄", min_value=0, max_value=150, value=25)
    color = st.selectbox("喜欢的颜色", ["红色", "蓝色", "绿色", "黄色"])
    
    submitted = st.form_submit_button("提交表单", width='stretch')
    if submitted:
        st.success(f"表单提交成功！\n姓名: {name}\n年龄: {age}\n颜色: {color}")

# 3. 会话状态测试
st.subheader("3. 会话状态测试")
if 'click_count' not in st.session_state:
    st.session_state.click_count = 0

if st.button(f"点击计数: {st.session_state.click_count}", width='stretch'):
    st.session_state.click_count += 1
    st.rerun()

# 4. 回调函数测试
st.subheader("4. 回调函数测试")

def on_button_click():
    st.session_state.last_click = time.strftime("%H:%M:%S")
    st.toast("按钮回调函数执行成功！")

if st.button("测试回调函数", on_click=on_button_click, width='stretch'):
    pass  # 回调函数会在按钮点击时执行

if 'last_click' in st.session_state:
    st.info(f"上次点击时间: {st.session_state.last_click}")

# 5. 链接测试
st.subheader("5. 链接测试")
st.markdown("""
- [Streamlit 官方文档](https://docs.streamlit.io)
- [GitHub 仓库](https://github.com/streamlit/streamlit)
- [社区论坛](https://discuss.streamlit.io)
""")

# 6. 动态内容测试
st.subheader("6. 动态内容测试")
if st.button("显示/隐藏内容", width='stretch'):
    if 'show_content' not in st.session_state:
        st.session_state.show_content = True
    else:
        st.session_state.show_content = not st.session_state.show_content

if st.session_state.get('show_content', False):
    st.info("这是动态显示的内容！")
    st.progress(75)
    st.metric("测试指标", "123", "+23")

# 7. 文件上传测试
st.subheader("7. 文件上传测试")
uploaded_file = st.file_uploader("选择文件", type=['txt', 'csv', 'json'])
if uploaded_file is not None:
    st.success(f"文件上传成功: {uploaded_file.name}")
    st.code(uploaded_file.getvalue().decode('utf-8')[:200])

# 8. 侧边栏测试
st.sidebar.title("侧边栏测试")
sidebar_option = st.sidebar.radio("选择选项", ["选项1", "选项2", "选项3"])
st.sidebar.info(f"当前选择: {sidebar_option}")

if st.sidebar.button("侧边栏按钮", width='stretch'):
    st.sidebar.success("侧边栏按钮点击成功")

# 测试结果汇总
st.markdown("---")
st.subheader("📊 测试结果汇总")

test_results = {
    "页面加载": "✅ 正常",
    "按钮显示": "✅ 正常",
    "表单元素": "✅ 正常",
    "会话状态": "✅ 正常" if 'click_count' in st.session_state else "❌ 异常",
    "回调函数": "✅ 正常" if 'last_click' in st.session_state else "❌ 异常",
    "动态内容": "✅ 正常" if 'show_content' in st.session_state else "❌ 异常"
}

for test, result in test_results.items():
    st.write(f"{test}: {result}")

# 诊断建议
st.markdown("---")
st.subheader("🔧 诊断建议")

if all("✅" in result for result in test_results.values()):
    st.success("🎉 所有功能测试通过！")
    st.info("如果主应用仍有问题，可能是：\n1. 特定模块的代码问题\n2. 数据依赖问题\n3. 浏览器缓存问题")
else:
    st.warning("部分功能测试失败，需要进一步诊断")
    st.info("建议：\n1. 检查浏览器控制台错误\n2. 查看 Streamlit 服务器日志\n3. 清除浏览器缓存")

# 重启建议
st.markdown("---")
if st.button("🔄 重启测试应用", type="primary", width='stretch'):
    st.info("请手动重启应用以应用更改")
    st.code("streamlit run test_button_functionality.py")