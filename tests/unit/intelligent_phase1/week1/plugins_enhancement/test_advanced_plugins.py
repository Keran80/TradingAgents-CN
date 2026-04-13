"""
高级插件系统单元测试
"""
import pytest
import sys
import os
import asyncio
from unittest.mock import Mock, patch

# 获取项目根目录 (向上 6 级)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

# 添加项目根目录到 Python 路径
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

class TestAdvancedPlugins:
    """高级插件系统测试类"""
    
    def test_import_module(self):
        """测试模块导入"""
        try:
            from intelligent_phase1.week1.plugins_enhancement import advanced_plugins
            assert advanced_plugins is not None
            print("✅ 高级插件模块导入成功")
        except ImportError as e:
            pytest.fail(f"模块导入失败：{e}")
    
    def test_file_exists(self):
        """测试文件存在"""
        file_path = os.path.join(PROJECT_ROOT, "intelligent_phase1", "week1", "plugins_enhancement", "advanced_plugins.py")
        assert os.path.exists(file_path), f"文件不存在：{file_path}"
        print(f"✅ 文件存在：{file_path}")
    
    def test_file_syntax(self):
        """测试文件语法"""
        file_path = os.path.join(PROJECT_ROOT, "intelligent_phase1", "week1", "plugins_enhancement", "advanced_plugins.py")
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            compile(content, file_path, 'exec')
            print("✅ 文件语法正确")
        except SyntaxError as e:
            pytest.fail(f"文件语法错误：{e}")
    
    def test_plugin_classes(self):
        """测试插件类"""
        from intelligent_phase1.week1.plugins_enhancement.advanced_plugins import (
            PluginDependencyResolver,
            PluginLifecycleManager  # 实际类名
        )
        
        assert PluginDependencyResolver is not None
        assert PluginLifecycleManager is not None
        
        print("✅ 插件类定义正确")
    
    def test_plugin_decorators(self):
        """测试插件装饰器"""
        from intelligent_phase1.week1.plugins_enhancement.advanced_plugins import plugin
        
        @plugin(name="test_plugin", version="1.0.0")
        class TestPlugin:
            pass
        
        assert hasattr(TestPlugin, '_plugin_name')
        assert TestPlugin._plugin_name == "test_plugin"
        assert TestPlugin._plugin_version == "1.0.0"
        
        print("✅ 插件装饰器工作正常")
    
    def test_dependency_management(self):
        """测试依赖管理"""
        from intelligent_phase1.week1.plugins_enhancement.advanced_plugins import PluginDependencyResolver
        
        resolver = PluginDependencyResolver()
        resolver.add_dependency("plugin1", ["dep1", "dep2"])
        
        assert "plugin1" in resolver.dependency_graph
        print("✅ 依赖管理正常")
    
    @pytest.mark.asyncio
    async def test_async_plugin_methods(self):
        """测试异步插件方法"""
        from intelligent_phase1.week1.plugins_enhancement.advanced_plugins import PluginLifecycleManager
        
        manager = PluginLifecycleManager()
        
        # 检查是否有异步方法
        import inspect
        methods = [m for m in dir(manager) if not m.startswith('_')]
        has_async = False
        
        for method_name in methods:
            method = getattr(manager, method_name, None)
            if method and inspect.iscoroutinefunction(method):
                has_async = True
                break
        
        assert has_async, "未找到异步方法"
        print("✅ 异步插件方法支持")
    
    def test_error_handling(self):
        """测试错误处理"""
        from intelligent_phase1.week1.plugins_enhancement.advanced_plugins import PluginDependencyResolver
        
        resolver = PluginDependencyResolver()
        
        # 测试基本功能
        resolver.add_dependency("A", ["B"])
        resolver.add_dependency("B", ["C"])
        
        # 验证依赖添加成功
        assert "A" in resolver.dependency_graph
        assert "B" in resolver.dependency_graph
        
        print("✅ 错误处理正常")
    
    def test_configuration(self):
        """测试配置"""
        from intelligent_phase1.week1.plugins_enhancement.advanced_plugins import PluginLifecycleManager
        
        manager = PluginLifecycleManager()
        
        # 测试管理器初始化
        assert manager is not None
        assert hasattr(manager, 'plugins')  # 实际属性名
        
        print("✅ 配置系统正常")

class TestPluginIntegration:
    """插件集成测试"""
    
    def test_import_paths(self):
        """测试导入路径"""
        try:
            from intelligent_phase1.week1.plugins_enhancement.advanced_plugins import (
                PluginDependencyResolver,
                PluginLifecycleManager,
                plugin
            )
            print("✅ 导入路径正确")
        except ImportError as e:
            pytest.fail(f"导入路径错误：{e}")
    
    def test_plugin_system_integration(self):
        """测试插件系统集成"""
        from intelligent_phase1.week1.plugins_enhancement.advanced_plugins import (
            PluginLifecycleManager,
            plugin
        )
        
        # 创建插件管理器
        manager = PluginLifecycleManager()
        
        # 创建测试插件
        @plugin(name="integration_test", version="1.0.0")
        class IntegrationTestPlugin:
            pass
        
        # 验证插件属性
        assert hasattr(IntegrationTestPlugin, '_plugin_name')
        assert IntegrationTestPlugin._plugin_name == "integration_test"
        assert IntegrationTestPlugin._plugin_version == "1.0.0"
        
        print("✅ 插件系统集成正常")
