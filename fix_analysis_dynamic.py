#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复 AI 分析结论动态生成问题
"""

# 读取文件
with open('app_streamlit.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到并替换硬编码的分析结论
old_code = '''        # AI 分析结论显示区域
        st.markdown("---")
        st.subheader("🤖 AI 分析结论")
        
        # 分析结论输入区域（允许用户粘贴 AI 分析结果）
        with st.expander("📝 粘贴/编辑 AI 分析结论", expanded=False):
            analysis_text = st.text_area(
                "分析结论",
                value="""1. 基本面：银行业整体受益于金融政策支持，基本面正面
2. 技术面：呈上升趋势，支撑位 10.50 元，压力位 11.50 元
3. 资金面：主力资金持续流入
4. 综合建议：买入""",
                height=150
            )'''

new_code = '''        # AI 分析结论显示区域
        st.markdown("---")
        st.subheader("🤖 AI 分析结论")
        
        # 分析结论输入区域（允许用户粘贴 AI 分析结果）
        with st.expander("📝 粘贴/编辑 AI 分析结论", expanded=False):
            # 根据股票生成默认分析结论（动态）
            default_analysis = f"""1. 基本面：请分析 {stock_name} 的基本面情况
2. 技术面：请分析技术走势、支撑位和压力位
3. 资金面：请分析主力资金流向
4. 综合建议：请给出投资建议"""
            
            analysis_text = st.text_area(
                "分析结论",
                value=default_analysis,
                height=150,
                help="可根据 AI 分析结果粘贴或修改结论"
            )'''

# 替换
content = content.replace(old_code, new_code)

# 写回文件
with open('app_streamlit.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 修复完成：AI 分析结论现在会根据股票名称动态生成")
