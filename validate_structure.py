#!/usr/bin/env python3
"""
验证项目结构
"""

import os
import sys

def validate_project_structure():
    base_dir = "/tmp/TradingAgents-CN"
    issues = []
    
    # 检查关键目录
    required_dirs = [
        "intelligent_phase1",
        "intelligent_phase1/week1",
        "intelligent_phase1/week1/events_optimization",
        "intelligent_phase1/week1/plugins_enhancement",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/performance",
    ]
    
    for dir_path in required_dirs:
        full_path = os.path.join(base_dir, dir_path)
        if os.path.exists(full_path):
            print(f"✅ {dir_path}: 存在")
        else:
            print(f"❌ {dir_path}: 不存在")
            issues.append(f"目录不存在: {dir_path}")
    
    # 检查关键文件
    required_files = [
        "pyproject.toml",
        "README.md",
        "requirements.txt",
        "pytest.ini",
        "intelligent_phase1/week1/events_optimization/ai_event_scheduler.py",
        "intelligent_phase1/week1/plugins_enhancement/advanced_plugins.py",
    ]
    
    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path}: 存在")
        else:
            print(f"❌ {file_path}: 不存在")
            issues.append(f"文件不存在: {file_path}")
    
    # 检查Python包结构
    print("\n检查Python包结构...")
    for root, dirs, files in os.walk(os.path.join(base_dir, "intelligent_phase1")):
        if "__pycache__" in root:
            continue
        
        # 检查是否需要__init__.py
        python_files = [f for f in files if f.endswith('.py')]
        if python_files and "__init__.py" not in files:
            rel_path = os.path.relpath(root, base_dir)
            print(f"⚠️  {rel_path}: 缺少__init__.py")
            issues.append(f"缺少__init__.py: {rel_path}")
    
    # 总结
    print(f"\n📊 验证结果:")
    print(f"总检查项: {len(required_dirs) + len(required_files)}")
    print(f"问题数量: {len(issues)}")
    
    if issues:
        print("\n🔧 需要修复的问题:")
        for issue in issues:
            print(f"  • {issue}")
        return False
    else:
        print("✅ 项目结构验证通过！")
        return True

if __name__ == "__main__":
    success = validate_project_structure()
    sys.exit(0 if success else 1)
