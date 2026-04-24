回测引擎 API
==============

.. module:: tradingagents.backtest

回测引擎支持事件驱动和向量化两种模式，用于验证交易策略。

快速开始
--------

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
    print(result.to_dict())

核心类
------

BacktestEngine
~~~~~~~~~~~~~~

.. autoclass:: tradingagents.backtest.engine.BacktestEngine
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

BacktestConfig
~~~~~~~~~~~~~~

.. autoclass:: tradingagents.backtest.config.BacktestConfig
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

BacktestResult
~~~~~~~~~~~~~~

.. autoclass:: tradingagents.backtest.result.BacktestResult
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

BacktestMode
~~~~~~~~~~~~

.. autoclass:: tradingagents.backtest.config.BacktestMode
   :members:
   :undoc-members:
   :member-order: bysource

TradeRecord
~~~~~~~~~~~

.. autoclass:: tradingagents.backtest.result.TradeRecord
   :members:
   :undoc-members:
   :show-inheritance:

使用技巧
--------

1. **事件驱动模式**：适合复杂策略，逐K线执行，更精确
2. **向量化模式**：适合简单策略，批量计算，速度更快
3. 使用 ``engine.set_strategy()`` 设置自定义策略函数
4. 使用 ``engine.set_signals()`` 设置预计算信号
