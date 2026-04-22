#!/usr/bin/env python3
"""
插件系统单元测试
"""

import asyncio
import sys
import unittest
from unittest.mock import Mock, patch
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root / 'src'))

from plugins.intelligent_plugin_system import IntelligentPluginSystem, plugin

# ==================== 测试插件类 ====================

@plugin
class TestDataSourcePlugin:
    """测试数据源插件"""
    
    def __init__(self):
        self.name = "test_data_source"
        self.call_count = 0
        
    async def fetch_data(self, symbol: str):
        """获取数据"""
        self.call_count += 1
        return {
            "symbol": symbol,
            "price": 100.0,
            "volume": 1000000,
            "timestamp": "2026-04-09"
        }

@plugin
class TestStrategyPlugin:
    """测试策略插件"""
    
    def __init__(self):
        self.name = "test_strategy"
        self.dependencies = ["test_data_source"]
        
    async def execute_strategy(self, data):
        """执行策略"""
        price = data.get("price", 0)
        if price > 95:
            return {"action": "SELL"}
        else:
            return {"action": "BUY"}

# ==================== 测试类 ====================

class TestPluginSystem(unittest.TestCase):
    """插件系统测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.plugin_system = IntelligentPluginSystem()
        self.data_plugin = TestDataSourcePlugin()
        self.strategy_plugin = TestStrategyPlugin()
        
    def tearDown(self):
        """测试后清理"""
        pass
        
    def test_plugin_decorator(self):
        """测试插件装饰器"""
        self.assertTrue(hasattr(TestDataSourcePlugin, '_is_plugin'))
        self.assertTrue(TestDataSourcePlugin._is_plugin)
        
    def test_register_plugin(self):
        """测试插件注册"""
        # 注册插件
        self.plugin_system.register_plugin("test_data", self.data_plugin)
        
        # 验证插件已注册
        plugins = self.plugin_system.list_plugins()
        self.assertIn("test_data", plugins)
        
    def test_get_plugin(self):
        """测试获取插件"""
        # 注册插件
        self.plugin_system.register_plugin("test_data", self.data_plugin)
        
        # 获取插件
        plugin_instance = self.plugin_system.get_plugin("test_data")
        self.assertIsNotNone(plugin_instance)
        self.assertEqual(plugin_instance.name, "test_data_source")
        
    def test_get_nonexistent_plugin(self):
        """测试获取不存在的插件"""
        plugin_instance = self.plugin_system.get_plugin("nonexistent")
        self.assertIsNone(plugin_instance)
        
    def test_list_plugins(self):
        """测试列出插件"""
        # 注册多个插件
        self.plugin_system.register_plugin("test_data", self.data_plugin)
        self.plugin_system.register_plugin("test_strategy", self.strategy_plugin)
        
        # 列出插件
        plugins = self.plugin_system.list_plugins()
        self.assertEqual(len(plugins), 2)
        self.assertIn("test_data", plugins)
        self.assertIn("test_strategy", plugins)
        
    def test_register_hook(self):
        """测试注册钩子"""
        # 创建模拟回调
        mock_callback = Mock()
        
        # 注册钩子
        self.plugin_system.register_hook("before_fetch", mock_callback)
        
        # 触发钩子
        results = self.plugin_system.trigger_hook("before_fetch", "AAPL")
        
        # 验证回调被调用
        mock_callback.assert_called_once_with("AAPL")
        self.assertEqual(len(results), 1)
        
    def test_trigger_nonexistent_hook(self):
        """测试触发不存在的钩子"""
        results = self.plugin_system.trigger_hook("nonexistent_hook")
        self.assertEqual(results, [])
        
    def test_multiple_hooks(self):
        """测试多个钩子"""
        # 创建多个模拟回调
        mock_callback1 = Mock(return_value="result1")
        mock_callback2 = Mock(return_value="result2")
        
        # 注册多个钩子
        self.plugin_system.register_hook("test_hook", mock_callback1)
        self.plugin_system.register_hook("test_hook", mock_callback2)
        
        # 触发钩子
        results = self.plugin_system.trigger_hook("test_hook", "test_data")
        
        # 验证所有回调被调用
        mock_callback1.assert_called_once_with("test_data")
        mock_callback2.assert_called_once_with("test_data")
        self.assertEqual(results, ["result1", "result2"])

class TestAsyncPluginSystem(unittest.IsolatedAsyncioTestCase):
    """异步插件系统测试类"""
    
    async def asyncSetUp(self):
        """异步测试前设置"""
        self.plugin_system = IntelligentPluginSystem()
        self.data_plugin = TestDataSourcePlugin()
        self.strategy_plugin = TestStrategyPlugin()
        
    async def test_async_plugin_method(self):
        """测试异步插件方法"""
        # 注册插件
        self.plugin_system.register_plugin("test_data", self.data_plugin)
        
        # 获取插件并调用异步方法
        plugin_instance = self.plugin_system.get_plugin("test_data")
        result = await plugin_instance.fetch_data("AAPL")
        
        # 验证结果
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["price"], 100.0)
        self.assertEqual(self.data_plugin.call_count, 1)
        
    async def test_plugin_workflow(self):
        """测试插件工作流程"""
        # 注册插件
        self.plugin_system.register_plugin("test_data", self.data_plugin)
        self.plugin_system.register_plugin("test_strategy", self.strategy_plugin)
        
        # 数据插件获取数据
        data_plugin = self.plugin_system.get_plugin("test_data")
        market_data = await data_plugin.fetch_data("GOOGL")
        
        # 策略插件分析数据
        strategy_plugin = self.plugin_system.get_plugin("test_strategy")
        decision = await strategy_plugin.execute_strategy(market_data)
        
        # 验证工作流程
        self.assertEqual(market_data["symbol"], "GOOGL")
        self.assertIn("action", decision)
        self.assertIn(decision["action"], ["BUY", "SELL"])
        
    async def test_hook_with_async_callback(self):
        """测试异步回调钩子"""
        # 创建异步模拟回调
        async def async_callback(data):
            await asyncio.sleep(0.01)
            return f"processed_{data}"
            
        # 注册钩子
        self.plugin_system.register_hook("async_hook", async_callback)
        
        # 触发钩子
        results = self.plugin_system.trigger_hook("async_hook", "test_data")
        
        # 异步钩子返回的是协程，需要等待
        if results and asyncio.iscoroutine(results[0]):
            result = await results[0]
            self.assertEqual(result, "processed_test_data")

# ==================== 测试运行 ====================

if __name__ == '__main__':
    # 运行单元测试
    print("🧪 运行插件系统单元测试...")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    
    # 添加同步测试
    sync_suite = loader.loadTestsFromTestCase(TestPluginSystem)
    
    # 添加异步测试
    async_suite = loader.loadTestsFromTestCase(TestAsyncPluginSystem)
    
    # 合并测试套件
    suite = unittest.TestSuite([sync_suite, async_suite])
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果
    print("=" * 60)
    print(f"📊 测试结果:")
    print(f"   运行测试: {result.testsRun}")
    print(f"   通过测试: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   失败测试: {len(result.failures)}")
    print(f"   错误测试: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ 失败测试:")
        for test, traceback in result.failures:
            print(f"   - {test}")
            
    if result.errors:
        print(f"\n⚠️ 错误测试:")
        for test, traceback in result.errors:
            print(f"   - {test}")
    
    # 退出码
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)