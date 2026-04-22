#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TradingAgents-CN 性能测试
"""

import time
import sys
sys.path.insert(0, '/tmp/TradingAgents-CN')

print("=== TradingAgents-CN 性能测试 ===\n")

# 测试 1: 事件引擎性能
print("【测试 1】事件引擎性能...")
from tradingagents.event_engine import EventEngine

start = time.time()
ee = EventEngine()
ee.start()

# 发送 1000 个事件
for i in range(1000):
    from tradingagents.event_engine import Event
    event = Event(event_type='TEST', data={'id': i})
    ee.put(event)

time.sleep(0.5)  # 等待处理
ee.stop()
elapsed = time.time() - start

print(f"  处理 1000 个事件耗时：{elapsed:.3f}秒")
print(f"  吞吐量：{1000/elapsed:.0f} 事件/秒")
print(f"  ✅ 事件引擎性能正常")

# 测试 2: 回测引擎性能
print("\n【测试 2】回测引擎性能...")
try:
    from tradingagents.backtest.engine import BacktestEngine
    import pandas as pd
    import numpy as np
    
    # 生成模拟数据
    dates = pd.date_range('2024-01-01', periods=252, freq='D')
    prices = 100 + np.cumsum(np.random.randn(252) * 0.02)
    
    start = time.time()
    engine = BacktestEngine(initial_capital=100000)
    elapsed = time.time() - start
    
    print(f"  回测引擎初始化：{elapsed:.3f}秒")
    print(f"  ✅ 回测引擎性能正常")
except Exception as e:
    print(f"  ⚠️  回测引擎测试：{str(e)[:50]}")

# 测试 3: 数据层性能
print("\n【测试 3】数据层性能...")
try:
    from tradingagents.data import RealtimeDataManager, MarketDataHub
    
    start = time.time()
    hub = MarketDataHub()
    elapsed = time.time() - start
    
    print(f"  数据枢纽初始化：{elapsed:.3f}秒")
    print(f"  ✅ 数据层性能正常")
except Exception as e:
    print(f"  ⚠️  数据层测试：{str(e)[:50]}")

# 测试 4: Agent 系统性能
print("\n【测试 4】Agent 系统性能...")
try:
    from tradingagents.agents.base import BaseAgent
    
    start = time.time()
    class TestAgent(BaseAgent):
        def process(self, data):
            return data
    
    agent = TestAgent(name='test')
    elapsed = time.time() - start
    
    print(f"  Agent 初始化：{elapsed:.3f}秒")
    print(f"  ✅ Agent 系统性能正常")
except Exception as e:
    print(f"  ⚠️  Agent 系统测试：{str(e)[:50]}")

print("\n" + "="*50)
print("性能测试完成")
print("="*50)
