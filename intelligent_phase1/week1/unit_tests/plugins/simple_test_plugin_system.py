#!/usr/bin/env python3
"""
简单的插件系统单元测试
"""

import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "../../../..")
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

print(f"🔍 项目根目录: {project_root}")
print(f"🔍 源代码路径: {src_path}")
print(f"🔍 Python路径: {sys.path}")

try:
    from plugins.intelligent_plugin_system import IntelligentPluginSystem, plugin
    print("✅ 成功导入插件系统模块")
    
    # ==================== 测试插件类 ====================
    
    @plugin
    class SimpleTestPlugin:
        """简单测试插件"""
        
        def __init__(self):
            self.name = "simple_test"
            self.call_count = 0
            
        def test_method(self):
            """测试方法"""
            self.call_count += 1
            return f"called_{self.call_count}"
    
    # ==================== 简单测试 ====================
    
    print("\n🧪 开始简单测试...")
    print("=" * 60)
    
    # 测试1: 创建插件系统
    plugin_system = IntelligentPluginSystem()
    print("✅ 测试1: 创建插件系统 - 通过")
    
    # 测试2: 创建插件实例
    test_plugin = SimpleTestPlugin()
    print("✅ 测试2: 创建插件实例 - 通过")
    
    # 测试3: 注册插件
    plugin_system.register_plugin("simple_test", test_plugin)
    print("✅ 测试3: 注册插件 - 通过")
    
    # 测试4: 列出插件
    plugins = plugin_system.list_plugins()
    if "simple_test" in plugins:
        print("✅ 测试4: 列出插件 - 通过")
    else:
        print("❌ 测试4: 列出插件 - 失败")
        
    # 测试5: 获取插件
    retrieved_plugin = plugin_system.get_plugin("simple_test")
    if retrieved_plugin is not None:
        print("✅ 测试5: 获取插件 - 通过")
    else:
        print("❌ 测试5: 获取插件 - 失败")
        
    # 测试6: 调用插件方法
    if retrieved_plugin:
        result = retrieved_plugin.test_method()
        if result == "called_1":
            print("✅ 测试6: 调用插件方法 - 通过")
        else:
            print(f"❌ 测试6: 调用插件方法 - 失败 (结果: {result})")
    
    # 测试7: 注册钩子
    hook_called = [False]
    def hook_callback(data):
        hook_called[0] = True
        return f"hook_{data}"
        
    plugin_system.register_hook("test_hook", hook_callback)
    print("✅ 测试7: 注册钩子 - 通过")
    
    # 测试8: 触发钩子
    hook_results = plugin_system.trigger_hook("test_hook", "test_data")
    if hook_called[0] and hook_results == ["hook_test_data"]:
        print("✅ 测试8: 触发钩子 - 通过")
    else:
        print(f"❌ 测试8: 触发钩子 - 失败 (调用: {hook_called[0]}, 结果: {hook_results})")
    
    # 测试9: 触发不存在的钩子
    nonexistent_results = plugin_system.trigger_hook("nonexistent_hook")
    if nonexistent_results == []:
        print("✅ 测试9: 触发不存在的钩子 - 通过")
    else:
        print(f"❌ 测试9: 触发不存在的钩子 - 失败 (结果: {nonexistent_results})")
    
    # 测试10: 获取不存在的插件
    nonexistent_plugin = plugin_system.get_plugin("nonexistent")
    if nonexistent_plugin is None:
        print("✅ 测试10: 获取不存在的插件 - 通过")
    else:
        print("❌ 测试10: 获取不存在的插件 - 失败")
    
    print("=" * 60)
    print("🎉 所有简单测试完成！")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("尝试直接查看文件...")
    
    # 尝试直接查看插件系统文件
    plugin_file = os.path.join(src_path, "plugins", "intelligent_plugin_system.py")
    if os.path.exists(plugin_file):
        print(f"✅ 找到插件系统文件: {plugin_file}")
        with open(plugin_file, 'r') as f:
            content = f.read(500)
            print(f"文件前500字符:\n{content}")
    else:
        print(f"❌ 未找到插件系统文件: {plugin_file}")
        
except Exception as e:
    print(f"❌ 测试运行失败: {e}")
    import traceback
    traceback.print_exc()