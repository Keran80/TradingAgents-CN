#!/usr/bin/env python3
"""
正确的插件系统单元测试
"""

import sys
import os

# 直接添加正确的路径
plugin_file = "/tmp/TradingAgents-CN/intelligent_phase1/src/plugins/intelligent_plugin_system.py"
plugin_dir = os.path.dirname(plugin_file)

print(f"🔍 插件文件: {plugin_file}")
print(f"🔍 插件目录: {plugin_dir}")

if os.path.exists(plugin_file):
    print("✅ 找到插件系统文件")
    
    # 将插件目录添加到Python路径
    sys.path.insert(0, plugin_dir)
    
    try:
        # 动态导入
        import importlib.util
        spec = importlib.util.spec_from_file_location("intelligent_plugin_system", plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        IntelligentPluginSystem = module.IntelligentPluginSystem
        plugin = module.plugin
        
        print("✅ 成功导入插件系统模块")
        
        # ==================== 测试插件类 ====================
        
        @plugin
        class TestPlugin:
            """测试插件"""
            
            def __init__(self):
                self.name = "test_plugin"
                self.call_count = 0
                
            def test_method(self):
                """测试方法"""
                self.call_count += 1
                return f"called_{self.call_count}"
        
        # ==================== 运行测试 ====================
        
        print("\n🧪 开始运行测试...")
        print("=" * 60)
        
        tests_passed = 0
        tests_failed = 0
        
        # 测试1: 创建插件系统
        try:
            plugin_system = IntelligentPluginSystem()
            print("✅ 测试1: 创建插件系统 - 通过")
            tests_passed += 1
        except Exception as e:
            print(f"❌ 测试1: 创建插件系统 - 失败: {e}")
            tests_failed += 1
        
        # 测试2: 创建插件实例
        try:
            test_plugin = TestPlugin()
            print("✅ 测试2: 创建插件实例 - 通过")
            tests_passed += 1
        except Exception as e:
            print(f"❌ 测试2: 创建插件实例 - 失败: {e}")
            tests_failed += 1
        
        # 测试3: 注册插件
        try:
            plugin_system.register_plugin("test_plugin", test_plugin)
            print("✅ 测试3: 注册插件 - 通过")
            tests_passed += 1
        except Exception as e:
            print(f"❌ 测试3: 注册插件 - 失败: {e}")
            tests_failed += 1
        
        # 测试4: 列出插件
        try:
            plugins = plugin_system.list_plugins()
            if "test_plugin" in plugins:
                print("✅ 测试4: 列出插件 - 通过")
                tests_passed += 1
            else:
                print(f"❌ 测试4: 列出插件 - 失败 (插件列表: {plugins})")
                tests_failed += 1
        except Exception as e:
            print(f"❌ 测试4: 列出插件 - 失败: {e}")
            tests_failed += 1
        
        # 测试5: 获取插件
        try:
            retrieved_plugin = plugin_system.get_plugin("test_plugin")
            if retrieved_plugin is not None:
                print("✅ 测试5: 获取插件 - 通过")
                tests_passed += 1
            else:
                print("❌ 测试5: 获取插件 - 失败")
                tests_failed += 1
        except Exception as e:
            print(f"❌ 测试5: 获取插件 - 失败: {e}")
            tests_failed += 1
        
        # 测试6: 调用插件方法
        try:
            if retrieved_plugin:
                result = retrieved_plugin.test_method()
                if result == "called_1":
                    print("✅ 测试6: 调用插件方法 - 通过")
                    tests_passed += 1
                else:
                    print(f"❌ 测试6: 调用插件方法 - 失败 (结果: {result})")
                    tests_failed += 1
            else:
                print("❌ 测试6: 调用插件方法 - 跳过 (插件未获取)")
                tests_failed += 1
        except Exception as e:
            print(f"❌ 测试6: 调用插件方法 - 失败: {e}")
            tests_failed += 1
        
        # 测试7: 注册钩子
        try:
            hook_called = [False]
            def hook_callback(data):
                hook_called[0] = True
                return f"hook_{data}"
                
            plugin_system.register_hook("test_hook", hook_callback)
            print("✅ 测试7: 注册钩子 - 通过")
            tests_passed += 1
        except Exception as e:
            print(f"❌ 测试7: 注册钩子 - 失败: {e}")
            tests_failed += 1
        
        # 测试8: 触发钩子
        try:
            hook_results = plugin_system.trigger_hook("test_hook", "test_data")
            if hook_called[0] and hook_results == ["hook_test_data"]:
                print("✅ 测试8: 触发钩子 - 通过")
                tests_passed += 1
            else:
                print(f"❌ 测试8: 触发钩子 - 失败 (调用: {hook_called[0]}, 结果: {hook_results})")
                tests_failed += 1
        except Exception as e:
            print(f"❌ 测试8: 触发钩子 - 失败: {e}")
            tests_failed += 1
        
        # 测试9: 触发不存在的钩子
        try:
            nonexistent_results = plugin_system.trigger_hook("nonexistent_hook")
            if nonexistent_results == []:
                print("✅ 测试9: 触发不存在的钩子 - 通过")
                tests_passed += 1
            else:
                print(f"❌ 测试9: 触发不存在的钩子 - 失败 (结果: {nonexistent_results})")
                tests_failed += 1
        except Exception as e:
            print(f"❌ 测试9: 触发不存在的钩子 - 失败: {e}")
            tests_failed += 1
        
        # 测试10: 获取不存在的插件
        try:
            nonexistent_plugin = plugin_system.get_plugin("nonexistent")
            if nonexistent_plugin is None:
                print("✅ 测试10: 获取不存在的插件 - 通过")
                tests_passed += 1
            else:
                print("❌ 测试10: 获取不存在的插件 - 失败")
                tests_failed += 1
        except Exception as e:
            print(f"❌ 测试10: 获取不存在的插件 - 失败: {e}")
            tests_failed += 1
        
        print("=" * 60)
        print(f"📊 测试结果:")
        print(f"   总测试数: {tests_passed + tests_failed}")
        print(f"   通过测试: {tests_passed}")
        print(f"   失败测试: {tests_failed}")
        print(f"   通过率: {tests_passed/(tests_passed+tests_failed)*100:.1f}%")
        
        if tests_failed == 0:
            print("🎉 所有测试通过！")
        else:
            print("⚠️ 有测试失败，需要检查")
        
    except Exception as e:
        print(f"❌ 导入或测试失败: {e}")
        import traceback
        traceback.print_exc()
        
else:
    print("❌ 未找到插件系统文件")
    
    # 列出目录内容
    print("\n📁 目录内容:")
    base_dir = "/tmp/TradingAgents-CN/intelligent_phase1"
    for root, dirs, files in os.walk(base_dir):
        level = root.replace(base_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files[:5]:  # 只显示前5个文件
            if file.endswith('.py'):
                print(f'{subindent}{file}')