#!/usr/bin/env python3
"""
简单有效的AI事件调度器测试
"""
import os
import sys

def test_ai_event_scheduler():
    """测试AI事件调度器文件"""
    print("🧪 测试AI事件调度器文件")
    
    # 文件路径
    file_path = "intelligent_phase1/week1/events_optimization/ai_event_scheduler.py"
    
    # 测试1: 文件存在
    print(f"1. 检查文件存在: {file_path}")
    if os.path.exists(file_path):
        print("   ✅ 文件存在")
    else:
        print("   ❌ 文件不存在")
        return False
    
    # 测试2: 文件大小
    file_size = os.path.getsize(file_path)
    print(f"2. 文件大小: {file_size} 字节")
    if file_size > 0:
        print("   ✅ 文件非空")
    else:
        print("   ❌ 文件为空")
        return False
    
    # 测试3: 文件可读
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print("   ✅ 文件可读")
    except Exception as e:
        print(f"   ❌ 文件读取失败: {e}")
        # 尝试其他编码
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            print("   ✅ 文件可读（使用latin-1编码）")
        except Exception as e2:
            print(f"   ❌ 所有编码尝试失败: {e2}")
            return False
    
    # 测试4: 基本内容检查
    lines = content.split('\n')
    print(f"3. 文件行数: {len(lines)}")
    
    # 检查关键内容
    checks = [
        ("类定义", "class " in content),
        ("函数定义", "def " in content),
        ("导入语句", "import " in content or "from " in content),
        ("Python文件", ".py" in file_path),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"   {status} {check_name}: {check_result}")
        if not check_result:
            all_passed = False
    
    # 测试5: 语法检查
    print("4. 语法检查")
    try:
        compile(content, file_path, 'exec')
        print("   ✅ 语法正确")
    except SyntaxError as e:
        print(f"   ❌ 语法错误: {e}")
        all_passed = False
    
    # 测试6: AI相关关键字（可选）
    print("5. AI相关关键字检查")
    content_lower = content.lower()
    ai_keywords = ["ai", "intelligent", "event", "scheduler", "async", "await"]
    found_keywords = [kw for kw in ai_keywords if kw in content_lower]
    
    if found_keywords:
        print(f"   ✅ 发现关键字: {found_keywords}")
    else:
        print("   ⚠️  未发现AI相关关键字")
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 所有基本测试通过！")
        return True
    else:
        print("⚠️  部分测试失败")
        return False

def test_advanced_plugins():
    """测试高级插件文件"""
    print("\n🧪 测试高级插件文件")
    
    file_path = "intelligent_phase1/week1/plugins_enhancement/advanced_plugins.py"
    
    print(f"1. 检查文件存在: {file_path}")
    if os.path.exists(file_path):
        print("   ✅ 文件存在")
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        print(f"2. 文件大小: {file_size} 字节")
        
        # 尝试读取
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 语法检查
            compile(content, file_path, 'exec')
            print("   ✅ 语法正确")
            
            # 检查插件相关关键字
            plugin_keywords = ["plugin", "class", "def", "import"]
            found = [kw for kw in plugin_keywords if kw in content.lower()]
            print(f"   ✅ 发现插件关键字: {found[:3]}...")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 文件检查失败: {e}")
            return False
    else:
        print("   ❌ 文件不存在")
        return False

if __name__ == "__main__":
    print("="*50)
    print("TradingAgents-CN 核心文件测试")
    print("="*50)
    
    test1_passed = test_ai_event_scheduler()
    test2_passed = test_advanced_plugins()
    
    print("\n" + "="*50)
    print("测试结果汇总:")
    print(f"AI事件调度器: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"高级插件文件: {'✅ 通过' if test2_passed else '❌ 失败'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 所有文件测试通过！")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败，需要检查")
        sys.exit(1)
