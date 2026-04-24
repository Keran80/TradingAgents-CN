事件引擎 API
==============

.. module:: tradingagents.event_engine

事件驱动架构核心，支持事件分发和订阅。

快速开始
--------

.. code-block:: python

    from tradingagents.event_engine import EventEngine, TickEvent, EventBus
    
    # 创建引擎
    engine = EventEngine(async_mode=False)
    
    # 注册处理器
    def on_tick(event: TickEvent):
        print(f"Tick: {event.symbol} @ {event.last_price}")
    
    engine.register(TickEvent, on_tick)
    engine.start()
    
    # 发送事件
    engine.put(TickEvent(symbol="000001.SZ", last_price=12.50))
    engine.process()

事件类型
--------

EventType
~~~~~~~~~

.. autoclass:: tradingagents.event_engine.EventType
   :members:
   :undoc-members:
   :member-order: bysource

事件类
------

Event
~~~~~

.. autoclass:: tradingagents.event_engine.Event
   :members:
   :undoc-members:
   :special-members: __init__

TickEvent
~~~~~~~~~

.. autoclass:: tradingagents.event_engine.TickEvent
   :members:
   :undoc-members:
   :special-members: __init__

BarEvent
~~~~~~~~

.. autoclass:: tradingagents.event_engine.BarEvent
   :members:
   :undoc-members:
   :special-members: __init__

OrderEvent
~~~~~~~~~~

.. autoclass:: tradingagents.event_engine.OrderEvent
   :members:
   :undoc-members:
   :special-members: __init__

TradeEvent
~~~~~~~~~~

.. autoclass:: tradingagents.event_engine.TradeEvent
   :members:
   :undoc-members:
   :special-members: __init__

SignalEvent
~~~~~~~~~~~

.. autoclass:: tradingagents.event_engine.SignalEvent
   :members:
   :undoc-members:
   :special-members: __init__

PositionEvent
~~~~~~~~~~~~~

.. autoclass:: tradingagents.event_engine.PositionEvent
   :members:
   :undoc-members:
   :special-members: __init__

AccountEvent
~~~~~~~~~~~~

.. autoclass:: tradingagents.event_engine.AccountEvent
   :members:
   :undoc-members:
   :special-members: __init__

RiskEvent
~~~~~~~~~

.. autoclass:: tradingagents.event_engine.RiskEvent
   :members:
   :undoc-members:
   :special-members: __init__

TimerEvent
~~~~~~~~~~

.. autoclass:: tradingagents.event_engine.TimerEvent
   :members:
   :undoc-members:
   :special-members: __init__

引擎类
------

EventEngine
~~~~~~~~~~~

.. autoclass:: tradingagents.event_engine.EventEngine
   :members:
   :undoc-members:
   :special-members: __init__

EventBus
~~~~~~~~

.. autoclass:: tradingagents.event_engine.EventBus
   :members:
   :undoc-members:
   :special-members: __new__, __init__

EventHandler
~~~~~~~~~~~~

.. autoclass:: tradingagents.event_engine.EventHandler
   :members:
   :undoc-members:

事件数据类
----------

OrderEventData
~~~~~~~~~~~~~~

.. autoclass:: tradingagents.event_engine.OrderEventData
   :members:
   :undoc-members:

TradeEventData
~~~~~~~~~~~~~~

.. autoclass:: tradingagents.event_engine.TradeEventData
   :members:
   :undoc-members:

SignalEventData
~~~~~~~~~~~~~~~

.. autoclass:: tradingagents.event_engine.SignalEventData
   :members:
   :undoc-members:
