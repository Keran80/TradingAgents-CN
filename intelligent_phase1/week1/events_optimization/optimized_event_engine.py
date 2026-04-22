#!/usr/bin/env python3
"""
优化的事件引擎
必须完成的事件引擎优化
"""

import asyncio
import heapq
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import traceback
from collections import defaultdict, deque
import statistics

# ==================== 核心优化类 ====================

class EventPriority(Enum):
    """优化的事件优先级枚举"""
    CRITICAL = 0      # 关键事件：必须立即处理
    HIGH = 1          # 高优先级：实时交易、风险预警
    MEDIUM = 2        # 中优先级：数据分析、策略执行
    LOW = 3           # 低优先级：报告生成、日志记录
    BACKGROUND = 4    # 后台任务：数据清理、缓存更新
    
    @classmethod
    def from_value(cls, value):
        """从值创建优先级"""
        for priority in cls:
            if priority.value == value:
                return priority
        return cls.MEDIUM

@dataclass(order=True)
class OptimizedEvent:
    """优化的事件类"""
    priority: int
    timestamp: float
    sequence: int = field(compare=False)
    event_type: str = field(compare=False)
    data: Any = field(compare=False)
    source: str = field(compare=False, default="system")
    correlation_id: Optional[str] = field(compare=False, default=None)
    retry_count: int = field(compare=False, default=0)
    max_retries: int = field(compare=False, default=3)
    
    def __post_init__(self):
        if isinstance(self.priority, EventPriority):
            self.priority = self.priority.value

class OptimizedEventEngine:
    """优化的事件引擎"""
    
    def __init__(self, max_queue_size: int = 10000, worker_count: int = 4):
        self.event_queue = []  # 使用堆实现优先级队列
        self.sequence_counter = 0
        self.handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.middlewares: List[Callable] = []
        self.running = False
        self.workers: List[asyncio.Task] = []
        self.worker_count = worker_count
        self.max_queue_size = max_queue_size
        
        # 性能监控
        self.metrics = {
            "events_processed": 0,
            "events_failed": 0,
            "events_retried": 0,
            "avg_processing_time": 0.0,
            "queue_size_history": deque(maxlen=100),
            "processing_times": deque(maxlen=1000),
            "throughput_history": deque(maxlen=60),  # 每分钟吞吐量
            "last_minute_events": 0,
            "last_check_time": time.time()
        }
        
        # 事件溯源
        self.tracer = EventTracer()
        
        # 错误处理器
        self.error_handlers: List[Callable] = []
        
        # 限流器
        self.rate_limiter = RateLimiter()
        
        # 死信队列
        self.dead_letter_queue: List[OptimizedEvent] = []
        
    def register_handler(self, event_type: str, handler: Callable, priority: int = 0):
        """注册事件处理器（支持优先级）"""
        self.handlers[event_type].append((priority, handler))
        # 按优先级排序
        self.handlers[event_type].sort(key=lambda x: x[0])
        
    def register_middleware(self, middleware: Callable):
        """注册中间件"""
        self.middlewares.append(middleware)
        
    def register_error_handler(self, error_handler: Callable):
        """注册错误处理器"""
        self.error_handlers.append(error_handler)
        
    async def put_event(self, event_type: str, data: Any, 
                       priority: EventPriority = EventPriority.MEDIUM,
                       source: str = "system",
                       correlation_id: Optional[str] = None,
                       max_retries: int = 3) -> bool:
        """放入事件（优化版本）"""
        
        # 队列大小检查
        if len(self.event_queue) >= self.max_queue_size:
            print(f"⚠️ 事件队列已满 ({len(self.event_queue)}/{self.max_queue_size})，丢弃事件: {event_type}")
            return False
            
        # 限流检查
        if not self.rate_limiter.check_limit(event_type):
            print(f"⚠️ 事件限流: {event_type}")
            return False
            
        # 创建事件
        self.sequence_counter += 1
        event = OptimizedEvent(
            priority=priority.value,
            timestamp=time.time(),
            sequence=self.sequence_counter,
            event_type=event_type,
            data=data,
            source=source,
            correlation_id=correlation_id,
            max_retries=max_retries
        )
        
        # 执行中间件
        for middleware in self.middlewares:
            try:
                if asyncio.iscoroutinefunction(middleware):
                    event = await middleware(event)
                else:
                    event = middleware(event)
            except Exception as e:
                print(f"⚠️ 中间件执行失败: {e}")
                
        # 放入队列
        heapq.heappush(self.event_queue, event)
        
        # 更新队列大小历史
        self.metrics["queue_size_history"].append(len(self.event_queue))
        
        # 事件溯源
        self.tracer.trace_event(event, action="queued")
        
        return True
        
    async def start(self):
        """启动事件引擎"""
        if self.running:
            return
            
        self.running = True
        
        # 启动工作线程
        for i in range(self.worker_count):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i+1}"))
            self.workers.append(worker)
            
        print(f"🚀 优化事件引擎启动，工作线程数: {self.worker_count}")
        
        # 启动监控任务
        asyncio.create_task(self._monitoring_loop())
        
    async def stop(self, timeout: float = 5.0):
        """停止事件引擎"""
        if not self.running:
            return
            
        self.running = False
        
        # 等待工作线程完成
        if self.workers:
            await asyncio.wait(self.workers, timeout=timeout)
            
        print("🛑 优化事件引擎停止")
        
    async def _worker_loop(self, worker_name: str):
        """工作线程循环"""
        while self.running:
            try:
                # 从队列获取事件
                if not self.event_queue:
                    await asyncio.sleep(0.001)  # 短暂休眠避免CPU空转
                    continue
                    
                event = heapq.heappop(self.event_queue)
                
                # 处理事件
                start_time = time.time()
                success = await self._process_event(event, worker_name)
                processing_time = time.time() - start_time
                
                # 更新指标
                self.metrics["events_processed"] += 1
                self.metrics["processing_times"].append(processing_time)
                self.metrics["avg_processing_time"] = statistics.mean(self.metrics["processing_times"]) if self.metrics["processing_times"] else 0
                self.metrics["last_minute_events"] += 1
                
                if not success:
                    self.metrics["events_failed"] += 1
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ 工作线程 {worker_name} 异常: {e}")
                await asyncio.sleep(0.1)  # 异常后短暂休眠
                
    async def _process_event(self, event: OptimizedEvent, worker_name: str) -> bool:
        """处理单个事件"""
        handlers = self.handlers.get(event.event_type, [])
        
        if not handlers:
            print(f"⚠️ 无处理器 for 事件: {event.event_type}")
            return True  # 没有处理器不算失败
            
        # 事件溯源：开始处理
        trace_id = self.tracer.trace_event(event, action="processing_start", worker=worker_name)
        
        success = True
        error_info = None
        
        # 按优先级顺序执行处理器
        for priority, handler in handlers:
            try:
                start_time = time.time()
                
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(event.data, event)
                else:
                    result = handler(event.data, event)
                    
                processing_time = time.time() - start_time
                
                # 记录处理结果
                self.tracer.trace_processing(trace_id, handler.__name__, processing_time, result)
                
            except Exception as e:
                success = False
                error_info = {
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "handler": handler.__name__,
                    "event_type": event.event_type
                }
                
                print(f"❌ 事件处理失败: {event.event_type}, 处理器: {handler.__name__}, 错误: {e}")
                
                # 执行错误处理器
                for error_handler in self.error_handlers:
                    try:
                        if asyncio.iscoroutinefunction(error_handler):
                            await error_handler(event, e, handler.__name__)
                        else:
                            error_handler(event, e, handler.__name__)
                    except Exception as eh_error:
                        print(f"⚠️ 错误处理器失败: {eh_error}")
                        
                # 重试逻辑
                if event.retry_count < event.max_retries:
                    event.retry_count += 1
                    event.timestamp = time.time() + (2 ** event.retry_count)  # 指数退避
                    heapq.heappush(self.event_queue, event)
                    
                    self.metrics["events_retried"] += 1
                    print(f"🔄 事件重试: {event.event_type} 重试次数={event.retry_count}")
                    
                    # 事件溯源：重试
                    self.tracer.trace_event(event, action="retry", retry_count=event.retry_count)
                    
                else:
                    # 放入死信队列
                    self.dead_letter_queue.append(event)
                    print(f"💀 事件进入死信队列: {event.event_type} 达到最大重试次数")
                    
                break  # 一个处理器失败就停止执行后续处理器
                
        # 事件溯源：处理完成
        self.tracer.trace_event(event, action="processing_complete", success=success, error=error_info)
        
        return success
        
    async def _monitoring_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 计算吞吐量
                current_time = time.time()
                time_diff = current_time - self.metrics["last_check_time"]
                
                if time_diff >= 60:  # 每分钟计算一次吞吐量
                    throughput = self.metrics["last_minute_events"] / (time_diff / 60)  # 事件/分钟
                    self.metrics["throughput_history"].append(throughput)
                    self.metrics["last_minute_events"] = 0
                    self.metrics["last_check_time"] = current_time
                    
                # 检查死信队列
                if len(self.dead_letter_queue) > 100:
                    print(f"⚠️ 死信队列过大: {len(self.dead_letter_queue)}")
                    
                await asyncio.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                print(f"⚠️ 监控循环异常: {e}")
                await asyncio.sleep(5)
                
    def get_metrics(self) -> Dict[str, Any]:
        """获取引擎指标"""
        queue_size_history = list(self.metrics["queue_size_history"])
        processing_times = list(self.metrics["processing_times"])
        throughput_history = list(self.metrics["throughput_history"])
        
        return {
            "status": "running" if self.running else "stopped",
            "workers": self.worker_count,
            "queue_size": len(self.event_queue),
            "dead_letter_queue_size": len(self.dead_letter_queue),
            "events_processed": self.metrics["events_processed"],
            "events_failed": self.metrics["events_failed"],
            "events_retried": self.metrics["events_retried"],
            "avg_processing_time_ms": self.metrics["avg_processing_time"] * 1000,
            "current_throughput_events_per_min": throughput_history[-1] if throughput_history else 0,
            "avg_throughput_events_per_min": statistics.mean(throughput_history) if throughput_history else 0,
            "max_queue_size": max(queue_size_history) if queue_size_history else 0,
            "min_queue_size": min(queue_size_history) if queue_size_history else 0,
            "p95_processing_time_ms": statistics.quantiles(processing_times, n=20)[18] * 1000 if len(processing_times) >= 20 else 0,
            "handler_count": sum(len(handlers) for handlers in self.handlers.values()),
            "event_type_count": len(self.handlers),
            "tracer_events": self.tracer.get_event_count(),
            "uptime_seconds": time.time() - self.metrics.get("start_time", time.time())
        }
        
    def get_dead_letter_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取死信队列事件"""
        return [
            {
                "event_type": event.event_type,
                "data": event.data,
                "retry_count": event.retry_count,
                "max_retries": event.max_retries,
                "source": event.source,
                "correlation_id": event.correlation_id,
                "timestamp": datetime.fromtimestamp(event.timestamp).isoformat()
            }
            for event in self.dead_letter_queue[:limit]
        ]

class RateLimiter:
    """限流器"""
    
    def __init__(self):
        self.limits: Dict[str, Dict[str, Any]] = {}
        self.counters: Dict[str, Dict[str, int]] = defaultdict(lambda: {"count": 0, "window_start": time.time()})
        
    def set_limit(self, event_type: str, max_requests: int, window_seconds: int):
        """设置限流规则"""
        self.limits[event_type] = {
            "max_requests": max_requests,
            "window_seconds": window_seconds
        }
        
    def check_limit(self, event_type: str) -> bool:
        """检查是否超过限流"""
        if event_type not in self.limits:
            return True  # 无限流
            
        limit = self.limits[event_type]
        counter = self.counters[event_type]
        
        current_time = time.time()
        window_start = counter["window_start"]
        
        # 检查时间窗口是否过期
        if current_time - window_start >= limit["window_seconds"]:
            counter["count"] = 0
            counter["window_start"] = current_time
            
        # 检查是否超过限制
        if counter["count"] >= limit["max_requests"]:
            return False
            
        counter["count"] += 1
        return True

class EnhancedEventTracer:
    """增强的事件溯源器"""
    
    def __init__(self, max_traces: int = 10000):
        self.traces: Dict[str, Dict[str, Any]] = {}
        self.event_index: Dict[str, List[str]] = defaultdict(list)  # event_type -> trace_ids
        self.correlation_index: Dict[str, List[str]] = defaultdict(list)  # correlation_id -> trace_ids
        self.sequence = 0
        self.max_traces = max_traces
        
    def trace_event(self, event: OptimizedEvent, **kwargs) -> str:
        """追踪事件"""
        trace_id = f"trace_{self.sequence}_{int(time.time()*1000)}"
        self.sequence += 1
        
        trace = {
            "trace_id": trace_id,
            "event_type": event.event_type,
            "event_data": event.data,
            "priority": EventPriority.from_value(event.priority).name,
            "source": event.source,
            "correlation_id": event.correlation_id,
            "timestamp": datetime.now().isoformat(),
            "sequence": event.sequence,
            "retry_count": event.retry_count,
            "processing_steps": [],
            **kwargs
        }
        
        self.traces[trace_id] = trace
        
        # 更新索引
        self.event_index[event.event_type].append(trace_id)
        if event.correlation_id:
            self.correlation_index[event.correlation_id].append(trace_id)
            
        # 清理旧追踪
        if len(self.traces) > self.max_traces:
            self._cleanup_old_traces()
            
        return trace_id
        
    def trace_processing(self, trace_id: str, handler_name: str, processing_time: float, result: Any = None):
        """追踪处理步骤"""
        if trace_id in self.traces:
            step = {
                "handler": handler_name,
                "processing_time_ms": processing_time * 1000,
                "timestamp": datetime.now().isoformat(),
                "result": result
            }
            self.traces[trace_id]["processing_steps"].append(step)
            
    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """获取追踪信息"""
        return self.traces.get(trace_id)
        
    def get_traces_by_event_type(self, event_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """按事件类型获取追踪"""
        trace_ids = self.event_index.get(event_type, [])[-limit:]  # 获取最新的
        return [self.traces[tid] for tid in trace_ids if tid in self.traces]
        
    def get_traces_by_correlation(self, correlation_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """按关联ID获取追踪"""
        trace_ids = self.correlation_index.get(correlation_id, [])[-limit:]
        return [self.traces[tid] for tid in trace_ids if tid in self.traces]
        
    def get_event_count(self) -> int:
        """获取追踪事件数量"""
        return len(self.traces)
        
    def _cleanup_old_traces(self):
        """清理旧追踪"""
        # 简单的清理策略：删除最旧的追踪
        if len(self.traces) > self.max_traces:
            # 按时间排序，删除最旧的
            sorted_traces = sorted(self.traces.items(), key=lambda x: x[1].get('timestamp', ''))
            traces_to_remove = sorted_traces[:len(self.traces) - self.max_traces]
            
            for trace_id, _ in traces_to_remove:
                # 从索引中删除
                trace = self.traces[trace_id]
                event_type = trace.get('event_type')
                correlation_id = trace.get('correlation_id')
                
                if event_type in self.event_index and trace_id in self.event_index[event_type]:
                    self.event_index[event_type].remove(trace_id)
                    
                if correlation_id and correlation_id in self.correlation_index and trace_id in self.correlation_index[correlation_id]:
                    self.correlation_index[correlation_id].remove(trace_id)
                    
                # 从追踪字典中删除
                del self.traces[trace_id]
                
            print(f"🧹 清理了 {len(traces_to_remove)} 个旧追踪")

# 为兼容性保留旧类名
EventTracer = EnhancedEventTracer