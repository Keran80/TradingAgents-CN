API 参考文档
==============

.. toctree::
   :maxdepth: 2
   :caption: 模块索引:

   backtest
   config
   event_engine
   agents

概述
----

TradingAgents-CN 提供完整的量化交易系统API，包括：

- **回测引擎**：验证交易策略，支持事件驱动和向量化双模式
- **配置系统**：集中管理配置，支持配置文件和环境变量
- **事件引擎**：事件驱动架构，支持多种事件类型和处理器
- **Agent系统**：多Agent协作分析，支持市场分析、辩论、交易决策

模块说明
--------

tradingagents.backtest
~~~~~~~~~~~~~~~~~~~~~~

回测引擎与绩效分析模块，位于 ``tradingagents/backtest/`` 目录下。

主要类：
- ``BacktestEngine`` - 回测引擎主类
- ``BacktestConfig`` - 回测配置
- ``BacktestResult`` - 回测结果
- ``BacktestMode`` - 回测模式枚举

.. code-block:: python

    from tradingagents.backtest import BacktestEngine, BacktestConfig, BacktestMode
    
    config = BacktestConfig(
        start_date="2024-01-01",
        end_date="2024-06-30",
        initial_cash=1000000,
        mode=BacktestMode.VECTORIZED
    )
    engine = BacktestEngine(config)
    engine.load_data("000001.SZ")
    result = engine.run()

tradingagents.config
~~~~~~~~~~~~~~~~~~~~

集中配置管理模块，位于 ``tradingagents/config.py`` 文件中。

主要类：
- ``Settings`` - 集中配置管理
- ``APISettings`` - API配置
- ``DatabaseSettings`` - 数据库配置
- ``StrategySettings`` - 策略配置
- ``LogSettings`` - 日志配置

tradingagents.event_engine
~~~~~~~~~~~~~~~~~~~~~~~~~~

事件驱动引擎，位于 ``tradingagents/event_engine.py`` 文件中。

主要类：
- ``EventEngine`` - 事件引擎
- ``EventBus`` - 全局事件总线
- ``Event`` / ``TickEvent`` / ``BarEvent`` / ``OrderEvent`` / ``TradeEvent`` 等事件类

tradingagents.agents
~~~~~~~~~~~~~~~~~~~~

多Agent协作系统，位于 ``tradingagents/agents/`` 目录下。

主要类：
- ``BaseAgent`` - Agent基类
- ``AgentConfig`` - Agent配置
- ``AnalysisResult`` / ``DebateResult`` / ``TradingDecision`` / ``RiskAssessment`` - 结果类

快速安装
--------

.. code-block:: bash

    pip install -e .
    pip install -r requirements.txt

生成文档
--------

.. code-block:: bash

    cd docs
    sphinx-build -b html . _build/html
