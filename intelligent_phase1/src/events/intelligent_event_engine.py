"""
智能事件引擎
基于 asyncio 的高性能事件驱动系统
借鉴通达信的实时预警思想
"""

import asyncio
from typing import Dict, List, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import heapq

@dataclass
class Event:
    """事件类"""
    type: str
    data: Any
    timestamp: datetime = None
    priority: int = 0  # 0=最高优先级
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def __lt__(self, other):
        # 用于优先队列排序
        if self.priority == other.priority:
            return self.timestamp < other.timestamp
        return self.priority < other.priority

class IntelligentEventEngine:
    """智能事件引擎"""
    
    def __init__(self):
        self.event_queue = asyncio.PriorityQueue()
        self.handlers: Dict[str, List[Callable]] = {}
        self.running = False
        
    def register_handler(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        self.handlers.setdefault(event_type, []).append(handler)
        
    async def put_event(self, event: Event):
        """放入事件"""
        await self.event_queue.put(event)
        
    async def process_events(self):
        """处理事件循环"""
        self.running = True
        while self.running:
            try:
                event = await self.event_queue.get()
                await self.process_event(event)
                self.event_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ 事件处理错误: {e}")
                
    async def process_event(self, event: Event):
        """处理单个事件"""
        handlers = self.handlers.get(event.type, [])
        
        # 并行执行处理器
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(handler(event))
            tasks.append(task)
            
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def start(self):
        """启动事件引擎"""
        self.process_task = asyncio.create_task(self.process_events())
        
    async def stop(self):
        """停止事件引擎"""
        self.running = False
        if hasattr(self, 'process_task'):
            self.process_task.cancel()
            try:
                await self.process_task
            except asyncio.CancelledError:
                pass

# 示例事件处理器
async def market_data_handler(event: Event):
    """市场数据处理"""
    print(f"📈 处理市场数据事件: {event.data}")
    
async def trade_signal_handler(event: Event):
    """交易信号处理"""
    print(f"🎯 处理交易信号事件: {event.data}")
