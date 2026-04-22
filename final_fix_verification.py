#!/usr/bin/env python3
"""
最终修复验证脚本
检查所有已知问题是否已修复
"""

import os
import re

def check_file(filepath):
    """检查单个文件的问题"""
    print(f"\n🔍 检查 {filepath}")
    
    if not os.path.exists(filepath):
        print("   ❌ 文件不存在")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    
    # 检查 use_container_width
    if 'use_container_width' in content:
        issues.append("❌ 仍有 use_container_width")
    
    # 检查 rgba 颜色
    if 'rgba(76, 175, 80, 0.1)' in content:
        issues.append("❌ 仍有 rgba(76, 175, 80, 0.1) 颜色")
    
    # 检查 freq='M'
    if "freq='M'" in content:
        issues.append("❌ 仍有 freq='M'")
    
    # 检查语法
    try:
        import py_compile
        py_compile.compile(filepath, doraise=True)
    except SyntaxError as e:
        issues.append(f"❌ 语法错误: {e}")
    except Exception as e:
        issues.append(f"⚠️  其他错误: {e}")
    
    if issues:
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print("   ✅ 所有问题已修复")
        return True

def main():
    print("🎯 TradingAgents-CN Streamlit 应用最终修复验证")
    print("=" * 50)
    
    files_to_check = [
        "app_buttons_tables_windows.py",
        "app_streamlit.py",
        "app_streamlit_complete.py",
        "app_streamlit_enhanced.py",
        "app_visualization_integrated.py",
        "intelligent_phase2/strategies/ml_trend_predictor.py",
        "intelligent_phase2/data_sources/multi_source_adapter.py"
    ]
    
    all_passed = True
    passed_count = 0
    total_count = len(files_to_check)
    
    for file in files_to_check:
        if check_file(file):
            passed_count += 1
        else:
            all_passed = False
    
    print(f"\n{'='*50}")
    print(f"📊 验证结果: {passed_count}/{total_count} 文件通过")
    
    if all_passed:
        print("🎉 所有文件修复成功！")
        print("\n🚀 启动命令:")
        print("  cd /tmp/TradingAgents-CN")
        print("  ./start_fixed_app.sh")
        print("\n🌐 访问地址:")
        print("  http://localhost:8501")
    else:
        print("⚠️  部分文件仍有问题，需要进一步修复")
        
        # 提供修复建议
        print("\n🔧 修复建议:")
        print("  1. 运行修复脚本: ./fix_all_streamlit_issues.sh")
        print("  2. 手动检查错误文件")
        print("  3. 重新验证: python final_fix_verification.py")

if __name__ == "__main__":
    main()