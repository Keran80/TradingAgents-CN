#!/usr/bin/env python3
"""
修复测试文件中的路径引用
"""

import os
import sys

def fix_test_paths():
    base_dir = "/tmp/TradingAgents-CN"
    
    # 修复测试文件中的相对路径
    test_files = [
        "tests/unit/intelligent_phase1/week1/events_optimization/test_ai_event_scheduler.py",
        "tests/unit/intelligent_phase1/week1/events_optimization/test_ai_event_scheduler_fixed.py",
        "tests/unit/intelligent_phase1/week1/plugins_enhancement/test_advanced_plugins.py",
    ]
    
    for test_file in test_files:
        file_path = os.path.join(base_dir, test_file)
        if os.path.exists(file_path):
            print(f"修复 {test_file}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 修复文件路径引用
            content = content.replace(
                "../../../../intelligent_phase1/week1/events_optimization/ai_event_scheduler.py",
                "../../../intelligent_phase1/week1/events_optimization/ai_event_scheduler.py"
            )
            
            content = content.replace(
                "../../../../intelligent_phase1/week1/plugins_enhancement/advanced_plugins.py",
                "../../../intelligent_phase1/week1/plugins_enhancement/advanced_plugins.py"
            )
            
            content = content.replace(
                "tests/intelligent_phase1/week1/events_optimization/ai_event_scheduler.py",
                "intelligent_phase1/week1/events_optimization/ai_event_scheduler.py"
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ {test_file} 修复完成")
        else:
            print(f"⚠️  {test_file} 不存在，跳过")

if __name__ == "__main__":
    fix_test_paths()
