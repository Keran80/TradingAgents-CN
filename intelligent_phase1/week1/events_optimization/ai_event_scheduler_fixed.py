#!/usr/bin/env python3
"""
AI 事件调度器 - 修复版本
第1周开发任务：事件引擎优化
"""

import asyncio
import heapq
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

# 使用本地导入替代
try:
    from .local_imports import IntelligentEventEngine, Event
    print("✅ 使用本地导入的 IntelligentEventEngine 和 Event")
except ImportError:
    # 如果本地导入失败，创建模拟类
    class IntelligentEventEngine:
        """智能事件引擎模拟类"""
        def __init__(self):
            self.events = []
        
        def register(self, event_type, handler):
            """注册事件处理器"""
            pass
        
        def emit(self, event):
            """触发事件"""
            pass
    
    class Event:
        """事件模拟类"""
        def __init__(self, event_type, data=None):
            self.type = event_type
            self.data = data or {}
    
    print("⚠️  使用模拟的 IntelligentEventEngine 和 Event")

class EventPriority(Enum):
    """事件优先级枚举"""
    CRITICAL = 0      # 关键事件：系统错误、风险预警
    HIGH = 1          # 高优先级：交易执行、实时数据
    MEDIUM = 2        # 中优先级：分析任务、报告生成
    LOW = 3           # 低优先级：日志记录、数据备份
    BACKGROUND = 4    # 后台任务：数据清理、缓存更新

@dataclass(order=True)
class ScheduledEvent:
    """调度事件"""
    priority: int
    timestamp: datetime
    event: Any = field(compare=False)
    callback: Callable = field(compare=False)
    
    def __post_init__(self):
        """初始化后处理"""
        if not callable(self.callback):
            raise ValueError("callback must be callable")

class AIEventScheduler:
    """AI 事件调度器"""
    
    def __init__(self, event_engine: Optional[IntelligentEventEngine] = None):
        """
        初始化 AI 事件调度器
        
        Args:
            event_engine: 智能事件引擎实例
        """
        self.event_engine = event_engine or IntelligentEventEngine()
        self.scheduled_events: List[ScheduledEvent] = []
        self.running = False
        self.loop = asyncio.get_event_loop()
        
        # 注册到事件引擎
        if self.event_engine:
            self.event_engine.register("schedule_event", self._handle_schedule_event)
            self.event_engine.register("cancel_event", self._handle_cancel_event)
    
    async def schedule(
        self,
        event: Event,
        delay_seconds: float = 0,
        priority: EventPriority = EventPriority.MEDIUM,
        callback: Optional[Callable] = None
    ) -> str:
        """
        调度事件
        
        Args:
            event: 事件对象
            delay_seconds: 延迟秒数
            priority: 事件优先级
            callback: 回调函数
            
        Returns:
            事件ID
        """
        if delay_seconds < 0:
            raise ValueError("delay_seconds must be non-negative")
        
        # 计算触发时间
        trigger_time = datetime.now() + timedelta(seconds=delay_seconds)
        
        # 创建调度事件
        scheduled_event = ScheduledEvent(
            priority=priority.value,
            timestamp=trigger_time,
            event=event,
            callback=callback or (lambda e: None)
        )
        
        # 添加到优先队列
        heapq.heappush(self.scheduled_events, scheduled_event)
        
        # 生成事件ID
        event_id = f"event_{len(self.scheduled_events)}_{trigger_time.timestamp()}"
        
        print(f"✅ 事件已调度: {event_id}, 触发时间: {trigger_time}, 优先级: {priority.name}")
        
        return event_id
    
    async def start(self):
        """启动调度器"""
        if self.running:
            return
        
        self.running = True
        print("🚀 AI 事件调度器已启动")
        
        # 启动事件处理循环
        asyncio.create_task(self._event_loop())
    
    async def stop(self):
        """停止调度器"""
        self.running = False
        print("🛑 AI 事件调度器已停止")
    
    async def _event_loop(self):
        """事件处理循环"""
        while self.running:
            now = datetime.now()
            
            # 检查是否有需要触发的事件
            while self.scheduled_events and self.scheduled_events[0].timestamp <= now:
                scheduled_event = heapq.heappop(self.scheduled_events)
                
                try:
                    # 执行回调
                    if scheduled_event.callback:
                        if asyncio.iscoroutinefunction(scheduled_event.callback):
                            await scheduled_event.callback(scheduled_event.event)
                        else:
                            scheduled_event.callback(scheduled_event.event)
                    
                    # 触发事件
                    if self.event_engine:
                        self.event_engine.emit(scheduled_event.event)
                    
                    print(f"🎯 事件已触发: {scheduled_event.event.type if hasattr(scheduled_event.event, 'type') else 'Unknown'}")
                
                except Exception as e:
                    print(f"❌ 事件处理失败: {e}")
            
            # 等待下一轮检查
            await asyncio.sleep(0.1)
    
    def _handle_schedule_event(self, event: Event):
        """处理调度事件请求"""
        asyncio.create_task(self.schedule(
            event=event.data.get('event'),
            delay_seconds=event.data.get('delay_seconds', 0),
            priority=EventPriority(event.data.get('priority', EventPriority.MEDIUM.value)),
            callback=event.data.get('callback')
        ))
    
    def _handle_cancel_event(self, event: Event):
        """处理取消事件请求"""
        event_id = event.data.get('event_id')
        if event_id:
            # 这里简化处理，实际应该根据event_id取消事件
            print(f"📝 收到取消事件请求: {event_id}")

# 示例使用
async def example_usage():
    """示例用法"""
    scheduler = AIEventScheduler()
    
    # 启动调度器
    await scheduler.start()
    
    # 调度几个事件
    event1 = Event("test_event", {"message": "Hello from event 1"})
    await scheduler.schedule(event1, delay_seconds=2, priority=EventPriority.HIGH)
    
    event2 = Event("test_event", {"message": "Hello from event 2"})
    await scheduler.schedule(event2, delay_seconds=5, priority=EventPriority.MEDIUM)
    
    # 运行一段时间
    await asyncio.sleep(10)
    
    # 停止调度器
    await scheduler.stop()

if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())
