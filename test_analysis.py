import streamlit as st

st.title("测试 AI 分析结论功能")

analysis_text = st.text_area(
    "分析结论",
    value="""1. 基本面：银行业整体受益于金融政策支持，基本面正面
2. 技术面：呈上升趋势，支撑位 10.50 元，压力位 11.50 元
3. 资金面：主力资金持续流入
4. 综合建议：买入""",
    height=150
)

st.markdown("#### 📊 解析显示")

lines = analysis_text.strip().split('\n')

for line in lines:
    line = line.strip()
    if line:
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

