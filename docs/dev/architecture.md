# 架构设计

## 系统概览

TradingAgents-CN是一个基于AI的量化交易系统，采用多Agent协作架构。

### 核心组件

```
┌─────────────────────────────────────────────┐
│           Web Interface (Streamlit)          │
├─────────────────────────────────────────────┤
│              Agent System                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Research │  │  Trader  │  │   Risk   │  │
│  │ Manager  │→│  Agent   │←│ Manager  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────┤
│              Backtest Engine                 │
│  ┌──────────────┐  ┌──────────────┐        │
│  │ Event-driven │  │  Vectorized  │        │
│  │    Mode      │  │     Mode     │        │
│  └──────────────┘  └──────────────┘        │
├─────────────────────────────────────────────┤
│              Data Layer                      │
│  ┌────────┐ ┌────────┐ ┌────────┐          │
│  │AkShare │ │FinnHub │ │ YFin   │          │
│  └────────┘ └────────┘ └────────┘          │
└─────────────────────────────────────────────┘
```

## 模块职责

### 1. Agent系统 (`tradingagents/agents/`)

多Agent协作分析系统：

- **Research Manager**: 协调研究和辩论
- **Trader Agent**: 生成交易决策
- **Risk Manager**: 风险管理和审核

**数据流**：

```
Market Data → Research → Debate → Trader → Risk Check → Final Decision
```

### 2. 回测引擎 (`tradingagents/backtest/`)

支持两种回测模式：

- **事件驱动模式**: 逐K线执行，适合复杂策略
- **向量化模式**: 批量计算，适合简单策略

**模块结构**：

```
backtest/
├── config.py        # 配置类
├── result.py        # 结果类
├── engine.py        # 主引擎
└── strategies.py    # 策略函数
```

### 3. 数据接口 (`tradingagents/dataflows/`)

统一数据访问层：

- **A股数据**: AkShare（免费）
- **美股数据**: Finnhub, Yahoo Finance
- **新闻/情绪**: Google News, Reddit

### 4. 策略系统 (`tradingagents/strategies/`)

策略构建和管理：

- **Builder**: 策略构建器
- **Optimizer**: 策略优化器
- **Templates**: 策略模板

## 设计模式

### 1. 依赖注入

使用`dependency_injection.py`实现松耦合

### 2. 事件驱动

`event_engine.py`实现事件发布/订阅

### 3. 策略模式

支持多种回测和交易策略

## 数据流

### 回测流程

```
1. 配置加载 (Settings.load())
2. 数据获取 (dataflows.interface)
3. 信号生成 (strategies)
4. 交易模拟 (backtest.engine)
5. 结果生成 (backtest.result)
```

### 实时交易流程

```
1. 实时数据 (data.realtime)
2. Agent分析 (agents)
3. 风险审核 (risk_mgmt)
4. 订单执行 (execution)
```

## 扩展点

### 添加新数据源

1. 在`dataflows/`创建新模块
2. 实现标准接口
3. 在`interface/__init__.py`导出

### 添加新策略

1. 在`strategies/`创建策略函数
2. 返回标准信号格式
3. 在回测中使用

## 技术栈

- **Python 3.10+**
- **数据处理**: pandas, numpy
- **AI框架**: LangChain, LangGraph
- **Web**: Streamlit
- **回测**: 自研引擎
- **数据**: AkShare, Finnhub
