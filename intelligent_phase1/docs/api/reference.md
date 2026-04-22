# Phase 1 智能增强 API 参考文档

## 📋 概述

本文档提供 Phase 1 智能增强系统的 API 参考，包括四个核心组件的详细接口说明。

## 🧩 智能插件系统 API

### IntelligentPluginSystem 类

#### 构造函数
```python
def __init__(self)
```
创建智能插件系统实例。

#### 方法

##### register_plugin
```python
def register_plugin(self, name: str, plugin: Any, dependencies: List[str] = None) -> None
```
注册一个插件。

**参数:**
- `name` (str): 插件名称
- `plugin` (Any): 插件实例
- `dependencies` (List[str], optional): 依赖的插件名称列表

**示例:**
```python
plugin_system = IntelligentPluginSystem()
data_plugin = DataSourcePlugin()
plugin_system.register_plugin("data_source", data_plugin, dependencies=[])
```

##### register_hook
```python
def register_hook(self, hook_name: str, callback: Callable) -> None
```
注册一个钩子。

**参数:**
- `hook_name` (str): 钩子名称
- `callback` (Callable): 回调函数

**示例:**
```python
def after_data_fetch(data):
    print(f"数据获取完成: {data}")

plugin_system.register_hook("after_data_fetch", after_data_fetch)
```

##### trigger_hook
```python
def trigger_hook(self, hook_name: str, *args, **kwargs) -> List[Any]
```
触发一个钩子。

**参数:**
- `hook_name` (str): 钩子名称
- `*args`: 位置参数
- `**kwargs`: 关键字参数

**返回:**
- `List[Any]`: 所有回调函数的返回值列表

**示例:**
```python
results = plugin_system.trigger_hook("before_strategy_execute", strategy_data)
```

##### load_plugins_from_directory
```python
async def load_plugins_from_directory(self, directory: Path) -> None
```
从目录加载插件。

**参数:**
- `directory` (Path): 插件目录路径

**示例:**
```python
import asyncio
from pathlib import Path

plugin_dir = Path("./plugins")
asyncio.run(plugin_system.load_plugins_from_directory(plugin_dir))
```

##### get_plugin
```python
def get_plugin(self, name: str) -> Any
```
获取指定名称的插件。

**参数:**
- `name` (str): 插件名称

**返回:**
- `Any`: 插件实例，如果不存在则返回 None

**示例:**
```python
data_plugin = plugin_system.get_plugin("data_source")
if data_plugin:
    data = await data_plugin.fetch_data("AAPL")
```

##### list_plugins
```python
def list_plugins(self) -> List[str]
```
列出所有已注册的插件。

**返回:**
- `List[str]`: 插件名称列表

**示例:**
```python
plugins = plugin_system.list_plugins()
print(f"已注册插件: {plugins}")
```

### 插件装饰器

#### plugin
```python
def plugin(cls) -> type
```
插件类装饰器。

**参数:**
- `cls` (type): 要装饰的类

**返回:**
- `type`: 装饰后的类

**示例:**
```python
@plugin
class DataSourcePlugin:
    def __init__(self):
        self.name = "data_source"
    
    async def fetch_data(self, symbol: str):
        return {"symbol": symbol, "price": 100.0}
```

## ⚡ 智能事件引擎 API

### Event 类

#### 构造函数
```python
def __init__(self, type: str, data: Any, timestamp: datetime = None, priority: int = 0)
```
创建事件实例。

**参数:**
- `type` (str): 事件类型
- `data` (Any): 事件数据
- `timestamp` (datetime, optional): 时间戳，默认为当前时间
- `priority` (int, optional): 优先级，0为最高，默认为0

**示例:**
```python
from datetime import datetime

event = Event(
    type="market_data",
    data={"symbol": "AAPL", "price": 150.25},
    timestamp=datetime.now(),
    priority=1
)
```

### IntelligentEventEngine 类

#### 构造函数
```python
def __init__(self)
```
创建智能事件引擎实例。

#### 方法

##### register_handler
```python
def register_handler(self, event_type: str, handler: Callable) -> None
```
注册事件处理器。

**参数:**
- `event_type` (str): 事件类型
- `handler` (Callable): 事件处理函数

**示例:**
```python
async def market_data_handler(event: Event):
    print(f"处理市场数据: {event.data}")

event_engine.register_handler("market_data", market_data_handler)
```

##### put_event
```python
async def put_event(self, event: Event) -> None
```
将事件放入队列。

**参数:**
- `event` (Event): 事件实例

**示例:**
```python
event = Event(type="trade_signal", data={"action": "BUY"})
await event_engine.put_event(event)
```

##### process_events
```python
async def process_events(self) -> None
```
处理事件循环（异步运行）。

**示例:**
```python
# 在异步任务中运行
asyncio.create_task(event_engine.process_events())
```

##### process_event
```python
async def process_event(self, event: Event) -> None
```
处理单个事件。

**参数:**
- `event` (Event): 事件实例

##### start
```python
async def start(self) -> None
```
启动事件引擎。

**示例:**
```python
await event_engine.start()
```

##### stop
```python
async def stop(self) -> None
```
停止事件引擎。

**示例:**
```python
await event_engine.stop()
```

## 📊 智能数据适配器 API

### DataAdapter 抽象基类

#### 抽象方法

##### fetch
```python
@abstractmethod
async def fetch(self, symbol: str, start: datetime, end: datetime, **kwargs) -> pd.DataFrame
```
获取数据。

**参数:**
- `symbol` (str): 股票代码
- `start` (datetime): 开始时间
- `end` (datetime): 结束时间
- `**kwargs`: 其他参数

**返回:**
- `pd.DataFrame`: 数据DataFrame

##### get_data_quality
```python
@abstractmethod
def get_data_quality(self) -> float
```
获取数据质量评分。

**返回:**
- `float`: 数据质量评分 (0.0-1.0)

### IntelligentDataAdapter 类

#### 构造函数
```python
def __init__(self)
```
创建智能数据适配器实例。

#### 方法

##### register_adapter
```python
def register_adapter(self, name: str, adapter: DataAdapter) -> None
```
注册数据适配器。

**参数:**
- `name` (str): 适配器名称
- `adapter` (DataAdapter): 适配器实例

**示例:**
```python
data_adapter = IntelligentDataAdapter()
mock_adapter = MockDataAdapter()
data_adapter.register_adapter("mock", mock_adapter)
```

##### fetch_intelligent_data
```python
async def fetch_intelligent_data(self, symbol: str, start: datetime, end: datetime, **kwargs) -> pd.DataFrame
```
智能获取数据。

**参数:**
- `symbol` (str): 股票代码
- `start` (datetime): 开始时间
- `end` (datetime): 结束时间
- `**kwargs`: 其他参数

**返回:**
- `pd.DataFrame`: 数据DataFrame

**示例:**
```python
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=30)

data = await data_adapter.fetch_intelligent_data("AAPL", start_date, end_date)
print(f"获取数据形状: {data.shape}")
```

##### clear_cache
```python
def clear_cache(self) -> None
```
清空缓存。

**示例:**
```python
data_adapter.clear_cache()
```

##### get_cache_info
```python
def get_cache_info(self) -> Dict[str, Any]
```
获取缓存信息。

**返回:**
- `Dict[str, Any]`: 缓存信息字典

**示例:**
```python
cache_info = data_adapter.get_cache_info()
print(f"缓存大小: {cache_info['cache_size']}")
print(f"缓存键: {cache_info['cache_keys']}")
```

### MockDataAdapter 类

#### 构造函数
```python
def __init__(self)
```
创建模拟数据适配器实例。

#### 方法

##### fetch
```python
async def fetch(self, symbol: str, start: datetime, end: datetime, **kwargs) -> pd.DataFrame
```
模拟获取数据。

**参数:**
- `symbol` (str): 股票代码
- `start` (datetime): 开始时间
- `end` (datetime): 结束时间
- `**kwargs`: 其他参数

**返回:**
- `pd.DataFrame`: 模拟数据DataFrame

##### get_data_quality
```python
def get_data_quality(self) -> float
```
获取数据质量评分。

**返回:**
- `float`: 数据质量评分 (0.95)

## 🤖 AI 集成框架 API

### AIIntegrationFramework 类

#### 构造函数
```python
def __init__(self, api_key: Optional[str] = None)
```
创建 AI 集成框架实例。

**参数:**
- `api_key` (Optional[str]): Qwen API 密钥，默认为 None（模拟模式）

#### 方法

##### connect
```python
async def connect(self) -> None
```
连接 AI 服务。

**示例:**
```python
ai_framework = AIIntegrationFramework(api_key="your_api_key")
await ai_framework.connect()
```

##### analyze_market
```python
async def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]
```
分析市场。

**参数:**
- `market_data` (Dict[str, Any]): 市场数据

**返回:**
- `Dict[str, Any]`: 分析结果

**示例:**
```python
market_data = {
    "symbol": "AAPL",
    "price": 150.25,
    "volume": 1000000,
    "trend": "up"
}

analysis = await ai_framework.analyze_market(market_data)
print(f"市场分析: {analysis['analysis']}")
print(f"置信度: {analysis['confidence']}")
```

##### generate_strategy
```python
async def generate_strategy(self, requirements: Dict[str, Any]) -> Dict[str, Any]
```
生成策略。

**参数:**
- `requirements` (Dict[str, Any]): 策略需求

**返回:**
- `Dict[str, Any]`: 策略结果

**示例:**
```python
requirements = {
    "risk_tolerance": "medium",
    "investment_horizon": "short_term",
    "capital": 100000
}

strategy = await ai_framework.generate_strategy(requirements)
print(f"策略名称: {strategy['strategy_name']}")
print(f"预期收益: {strategy['expected_return']}")
```

##### risk_assessment
```python
async def risk_assessment(self, portfolio: Dict[str, Any]) -> Dict[str, Any]
```
风险评估。

**参数:**
- `portfolio` (Dict[str, Any]): 投资组合数据

**返回:**
- `Dict[str, Any]`: 风险评估结果

**示例:**
```python
portfolio = {
    "holdings": {"AAPL": 0.4, "GOOGL": 0.3, "MSFT": 0.3},
    "total_value": 150000,
    "leverage": 1.0
}

risk = await ai_framework.risk_assessment(portfolio)
print(f"总体风险: {risk['overall_risk']}")
print(f"建议: {risk['recommendations']}")
```

## 🔧 工具函数 API

### 异步工具函数

#### run_demo
```python
async def run_demo() -> None
```
运行 Phase 1 演示。

**示例:**
```python
import asyncio
from demo_phase1 import main

asyncio.run(main())
```

#### create_phase1_project
```python
def create_phase1_project(directory: str) -> None
```
创建 Phase 1 项目结构。

**参数:**
- `directory` (str): 项目目录路径

**示例:**
```python
create_phase1_project("/tmp/my_phase1_project")
```

## 📝 使用示例

### 完整工作流程示例

```python
import asyncio
from datetime import datetime, timedelta

# 1. 初始化所有组件
plugin_system = IntelligentPluginSystem()
event_engine = IntelligentEventEngine()
data_adapter = IntelligentDataAdapter()
ai_framework = AIIntegrationFramework()

# 2. 注册插件
data_plugin = DataSourcePlugin()
strategy_plugin = StrategyPlugin()
plugin_system.register_plugin("data_source", data_plugin)
plugin_system.register_plugin("strategy", strategy_plugin)

# 3. 注册数据适配器
mock_adapter = MockDataAdapter()
data_adapter.register_adapter("mock", mock_adapter)

# 4. 连接 AI
await ai_framework.connect()

# 5. 注册事件处理器
async def market_data_handler(event: Event):
    print(f"📈 处理市场数据: {event.data}")
    
event_engine.register_handler("market_data", market_data_handler)

# 6. 启动事件引擎
await event_engine.start()

# 7. 获取数据
end_date = datetime.now()
start_date = end_date - timedelta(days=7)
data = await data_adapter.fetch_intelligent_data("AAPL", start_date, end_date)

# 8. AI 分析
market_data = {
    "symbol": "AAPL",
    "current_price": data['close'].iloc[-1] if len(data) > 0 else 150.0,
    "trend": "up" if len(data) > 1 and data['close'].iloc[-1] > data['close'].iloc[-2] else "down"
}
analysis = await ai_framework.analyze_market(market_data)

# 9. 生成策略
requirements = {
    "market_analysis": analysis,
    "risk_tolerance": "medium"
}
strategy = await ai_framework.generate_strategy(requirements)

# 10. 发送交易事件
trade_event = Event(
    type="trade_execution",
    data={
        "strategy": strategy['strategy_name'],
        "action": "BUY",
        "symbol": "AAPL",
        "price": market_data['current_price']
    },
    priority=1
)
await event_engine.put_event(trade_event)

# 11. 等待事件处理
await asyncio.sleep(0.5)

# 12. 停止事件引擎
await event_engine.stop()

print("🎉 完整工作流程执行完成！")
```

## 🔍 错误处理

### 常见错误及处理

| 错误类型 | 原因 | 处理方法 |
|----------|------|----------|
| **PluginNotFoundError** | 插件未找到 | 检查插件名称，确保已注册 |
| **EventHandlerError** | 事件处理器错误 | 检查处理器函数，添加异常处理 |
| **DataFetchError** | 数据获取失败 | 检查数据源，尝试备用适配器 |
| **APIConnectionError** | API 连接失败 | 检查网络，切换到模拟模式 |
| **CacheError** | 缓存错误 | 清空缓存，重新获取数据 |

### 错误处理示例

```python
try:
    data = await data_adapter.fetch_intelligent_data("AAPL", start_date, end_date)
except DataFetchError as e:
    print(f"❌ 数据获取失败: {e}")
    # 尝试备用数据源或使用缓存数据
    data = get_cached_data("AAPL")
except Exception as e:
    print(f"❌ 未知错误: {e}")
    # 记录日志，继续执行或优雅退出
```

## 📊 性能优化建议

### 插件系统优化
1. **延迟加载**: 只在需要时加载插件
2. **缓存插件实例**: 避免重复创建
3. **异步插件初始化**: 并行初始化插件

### 事件引擎优化
1. **批量处理**: 批量处理同类事件
2. **优先级调整**: 根据负载动态调整优先级
3. **事件过滤**: 过滤不重要的事件

### 数据适配器优化
1. **数据缓存**: 缓存常用数据
2. **预取数据**: 预取可能需要的的数据
3. **压缩存储**: 压缩存储历史数据

### AI 框架优化
1. **请求合并**: 合并多个 AI 请求
2. **结果缓存**: 缓存 AI 分析结果
3. **降级策略**: 在 API 失败时优雅降级

---

**文档版本**: 1.0  
**更新日期**: 2026-04-09  
**API 状态**: 稳定  
**兼容性**: Python 3.11+  
**依赖**: asyncio, pandas, aiohttp