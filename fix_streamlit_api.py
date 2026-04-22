#!/usr/bin/env python3
"""
修复 Streamlit API 弃用问题
1. use_container_width=True -> width='stretch'
2. use_container_width=False -> width='content'
"""

import re

def fix_streamlit_api(filepath):
    """修复 Streamlit API 弃用问题"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复 use_container_width=True
    content = re.sub(r'use_container_width=True', "width='stretch'", content)
    
    # 修复 use_container_width=False
    content = re.sub(r'use_container_width=False', "width='content'", content)
    
    # 修复其他常见问题
    content = content.replace("freq='M'", "freq='ME'")
    content = content.replace("freq='Q'", "freq='QE'")
    content = content.replace("freq='Y'", "freq='YE'")
    content = content.replace("freq='A'", "freq='YE'")
    
    # 修复颜色选择器
    content = content.replace("'rgba(76, 175, 80, 0.1)'", "'#4caf50'")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已修复 {filepath}")

if __name__ == "__main__":
    files_to_fix = [
        "app_buttons_tables_windows.py",
        "app_streamlit.py",
        "app_streamlit_complete.py",
        "app_streamlit_enhanced.py",
        "app_visualization_integrated.py"
    ]
    
    for file in files_to_fix:
        try:
            fix_streamlit_api(file)
        except FileNotFoundError:
            print(f"⚠️  文件不存在: {file}")
        except Exception as e:
            print(f"❌ 修复 {file} 失败: {e}")