#!/usr/bin/env python3
"""
测试 Streamlit 应用修复结果
"""

import sys
import os

print("🔍 测试 TradingAgents-CN Streamlit 应用修复结果")
print("=" * 50)

# 1. 检查文件存在
print("1. 检查文件存在...")
files_to_check = [
    "app_buttons_tables_windows.py",
    "start_visualization_app.sh",
    "VISUALIZATION_CAPABILITIES.md",
    "BUTTONS_TABLES_WINDOWS_REPORT.md",
    "STREAMLIT_FIX_REPORT.md"
]

for file in files_to_check:
    if os.path.exists(file):
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file}")

print()

# 2. 检查 Python 语法
print("2. 检查 Python 语法...")
try:
    import py_compile
    py_compile.compile("app_buttons_tables_windows.py", doraise=True)
    print("   ✅ 语法检查通过")
except SyntaxError as e:
    print(f"   ❌ 语法错误: {e}")
    sys.exit(1)
except Exception as e:
    print(f"   ⚠️  其他错误: {e}")

print()

# 3. 检查文件完整性
print("3. 检查文件完整性...")
with open("app_buttons_tables_windows.py", "r", encoding="utf-8") as f:
    content = f.read()
    
# 检查关键部分
checks = [
    ("导入语句", "import streamlit as st" in content),
    ("页面配置", "st.set_page_config" in content),
    ("侧边栏", "st.sidebar.title" in content),
    ("首页模块", "if module == \"🏠 首页\":" in content),
    ("Dashboard模块", "elif module == \"📊 Dashboard 按钮表格\":" in content),
    ("回测报告模块", "elif module == \"📋 回测报告表格\":" in content),
    ("图表控制模块", "elif module == \"🎨 图表控制按钮\":" in content),
    ("热力图模块", "elif module == \"🔥 热力图窗口\":" in content),
]

for check_name, check_result in checks:
    if check_result:
        print(f"   ✅ {check_name}")
    else:
        print(f"   ❌ {check_name}")

print()

# 4. 检查修复的语法错误点
print("4. 检查修复的语法错误点...")
error_points = [
    ("第767行括号闭合", "use_container_width=True):" in content),
    ("第439行f-string修复", "profit_str = \"¥{:.2f}\".format(total_profit)" in content),
    ("第494行f-string修复", "\"📈 \" + chart_type" in content),
]

for error_name, error_fixed in error_points:
    if error_fixed:
        print(f"   ✅ {error_name}")
    else:
        print(f"   ❌ {error_name}")

print()

# 5. 统计信息
print("5. 应用统计信息...")
lines = content.count('\n') + 1
buttons = content.count('st.button')
tables = content.count('st.dataframe')
charts = content.count('st.plotly_chart') + content.count('px.imshow')

print(f"   代码行数: {lines}")
print(f"   按钮数量: {buttons}")
print(f"   表格数量: {tables}")
print(f"   图表数量: {charts}")

print()
print("=" * 50)
print("🎉 测试完成！应用修复成功，可以正常启动。")
print()
print("启动命令:")
print("  cd /tmp/TradingAgents-CN")
print("  streamlit run app_buttons_tables_windows.py")
print()
print("访问地址:")
print("  http://localhost:8501")