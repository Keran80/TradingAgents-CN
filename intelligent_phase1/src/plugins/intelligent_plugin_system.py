"""
智能插件系统
基于逆向工程思维设计的插件式架构
借鉴聚宽、米筐的模块化设计思想
"""

import asyncio
from typing import Dict, List, Any, Callable
import importlib
from pathlib import Path

class IntelligentPluginSystem:
    """智能插件系统"""
    
    def __init__(self):
        self.plugins: Dict[str, Any] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        self.dependencies: Dict[str, List[str]] = {}
        
    def register_plugin(self, name: str, plugin: Any, dependencies: List[str] = None):
        """注册插件"""
        self.plugins[name] = plugin
        if dependencies:
            self.dependencies[name] = dependencies
            
    def register_hook(self, hook_name: str, callback: Callable):
        """注册钩子"""
        self.hooks.setdefault(hook_name, []).append(callback)
        
    def trigger_hook(self, hook_name: str, *args, **kwargs):
        """触发钩子"""
        results = []
        for callback in self.hooks.get(hook_name, []):
            result = callback(*args, **kwargs)
            results.append(result)
        return results
    
    async def load_plugins_from_directory(self, directory: Path):
        """从目录加载插件"""
        for plugin_file in directory.glob("*.py"):
            module_name = plugin_file.stem
            try:
                spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 查找插件类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if hasattr(attr, '_is_plugin') and attr._is_plugin:
                        plugin_instance = attr()
                        self.register_plugin(module_name, plugin_instance)
                        print(f"✅ 加载插件: {module_name}")
                        
            except Exception as e:
                print(f"❌ 加载插件失败 {plugin_file}: {e}")
                
    def get_plugin(self, name: str) -> Any:
        """获取插件"""
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[str]:
        """列出所有插件"""
        return list(self.plugins.keys())

def plugin(cls):
    """插件装饰器"""
    cls._is_plugin = True
    return cls

# 示例插件
@plugin
class DataSourcePlugin:
    """数据源插件示例"""
    
    def __init__(self):
        self.name = "data_source"
        
    async def fetch_data(self, symbol: str):
        """获取数据"""
        print(f"📊 获取 {symbol} 数据")
        return {"symbol": symbol, "price": 100.0}

@plugin  
class StrategyPlugin:
    """策略插件示例"""
    
    def __init__(self):
        self.name = "strategy"
        
    async def execute_strategy(self, data):
        """执行策略"""
        print(f"🎯 执行策略，数据: {data}")
        return {"action": "BUY", "confidence": 0.85}
