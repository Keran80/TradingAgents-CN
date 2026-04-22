"""TradingAgents-CN - 多代理AI量化交易框架（通达信优化版）

Phase 1-15 完整实现:
- Phase 1: 交易执行层 (broker/account/portfolio/order_manager)
- Phase 2: 事件引擎 + 策略模板 + 参数优化
- Phase 3: 风控体系 (manager/interceptor/规则库)
- Phase 4: 监控告警 (trigger/notifier)
- Phase 5: 回测引擎 + 绩效分析
- Phase 6: 数据层扩展 (实时/期货/期权)
- Phase 7: AI决策框架 (多代理辩论)
- Phase 8: 可视化策略构建器
- Phase 9: 因子研究平台
- Phase 10: RAG知识库
- Phase 11: 多代理辩论系统
- Phase 12: 全市场数据支持
- Phase 13: 交互式Dashboard
- Phase 14: 强化学习集成
- Phase 15: 分布式架构

数据源: AkShare + 通达信 pytdx
"""

__version__ = "1.0.0"
__author__ = "Keran80"

# 核心事件引擎
from .event_engine import (
    EventEngine,
    EventBus,
    EventType,
    Event,
    TickEvent,
    BarEvent,
    OrderEvent,
    TradeEvent,
    SignalEvent,
)

# 多代理辩论系统
try:
    from .agents import MultiAgentDebateSystem
except ImportError:
    MultiAgentDebateSystem = None

# 策略模板
try:
    from .strategies import (
        StrategyTemplate,
        MomentumStrategy,
        MeanReversionStrategy,
        BreakoutStrategy,
        GridStrategy,
    )
except ImportError:
    StrategyTemplate = None
    MomentumStrategy = None
    MeanReversionStrategy = None
    BreakoutStrategy = None
    GridStrategy = None

# 默认配置
try:
    from .default_config import DEFAULT_CONFIG
except ImportError:
    DEFAULT_CONFIG = {}

# 数据流
try:
    from .dataflows import DataFlow, DataSource
except ImportError:
    DataFlow = None
    DataSource = None

# 风控
try:
    from .risk import RiskManager
except ImportError:
    RiskManager = None

# 回测
try:
    from .backtest import BacktestEngine
except ImportError:
    BacktestEngine = None

# 分布式
try:
    from .distributed import (
        StrategyManager,
        DistributedDataService,
        StrategyIsolator,
        RPCClient,
        RPCServer,
    )
except ImportError:
    StrategyManager = None
    DistributedDataService = None
    StrategyIsolator = None
    RPCClient = None
    RPCServer = None


__all__ = [
    # 版本
    "__version__",
    # 事件引擎
    "EventEngine",
    "EventBus",
    "EventType",
    "Event",
    "TickEvent",
    "BarEvent",
    "OrderEvent",
    "TradeEvent",
    "SignalEvent",
    # 多代理系统
    "MultiAgentDebateSystem",
    # 策略
    "StrategyTemplate",
    "MomentumStrategy",
    "MeanReversionStrategy",
    "BreakoutStrategy",
    "GridStrategy",
    # 配置
    "DEFAULT_CONFIG",
    # 数据流
    "DataFlow",
    "DataSource",
    # 风控
    "RiskManager",
    # 回测
    "BacktestEngine",
    # 分布式
    "StrategyManager",
    "DistributedDataService",
    "StrategyIsolator",
    "RPCClient",
    "RPCServer",
]
from .error_handling import TradingException, DataException, APIException
