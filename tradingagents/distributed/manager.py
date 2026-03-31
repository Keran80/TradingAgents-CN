# -*- coding: utf-8 -*-
"""
多策略并行管理器

支持多策略同时运行、负载均衡、策略调度
"""

import asyncio
import multiprocessing as mp
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class StrategyStatus(Enum):
    """策略状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class WorkerConfig:
    """Worker 配置"""
    worker_id: str
    max_strategies: int = 5
    cpu_affinity: Optional[List[int]] = None
    memory_limit_mb: int = 2048
    priority: int = 0
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class StrategyInstance:
    """策略实例"""
    strategy_id: str
    name: str
    strategy_class: str
    config: Dict[str, Any]
    status: StrategyStatus = StrategyStatus.PENDING
    worker_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


class StrategyManager:
    """
    多策略并行管理器
    
    负责：
    - 策略注册与调度
    - Worker 生命周期管理
    - 负载均衡
    - 策略状态监控
    """
    
    def __init__(
        self,
        max_workers: int = None,
        strategy_timeout: int = 300,
        health_check_interval: int = 30
    ):
        self.max_workers = max_workers or mp.cpu_count()
        self.strategy_timeout = strategy_timeout
        self.health_check_interval = health_check_interval
        
        # 策略注册表
        self.strategies: Dict[str, StrategyInstance] = {}
        
        # Worker 池
        self.workers: Dict[str, WorkerConfig] = {}
        self.worker_loads: Dict[str, int] = {}
        
        # 调度队列
        self.pending_queue: asyncio.Queue = None
        self.running_strategies: Dict[str, asyncio.Task] = {}
        
        # 回调
        self.on_strategy_start: Optional[Callable] = None
        self.on_strategy_stop: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # 内部状态
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        
    def register_worker(self, config: WorkerConfig) -> None:
        """注册 Worker"""
        self.workers[config.worker_id] = config
        self.worker_loads[config.worker_id] = 0
        logger.info(f"Worker 注册: {config.worker_id}, 最大策略数: {config.max_strategies}")
    
    def register_strategy(
        self,
        name: str,
        strategy_class: str,
        config: Dict[str, Any]
    ) -> str:
        """注册策略"""
        strategy_id = str(uuid.uuid4())[:8]
        instance = StrategyInstance(
            strategy_id=strategy_id,
            name=name,
            strategy_class=strategy_class,
            config=config
        )
        self.strategies[strategy_id] = instance
        logger.info(f"策略注册: {name} ({strategy_id})")
        return strategy_id
    
    def _select_worker(self) -> Optional[str]:
        """选择最佳 Worker（负载均衡）"""
        available = [
            (wid, self.worker_loads[wid])
            for wid in self.workers
            if self.worker_loads[wid] < self.workers[wid].max_strategies
        ]
        if not available:
            return None
        # 选择负载最低的
        return min(available, key=lambda x: x[1])[0]
    
    async def start_strategy(self, strategy_id: str) -> bool:
        """启动策略"""
        if strategy_id not in self.strategies:
            logger.error(f"策略不存在: {strategy_id}")
            return False
        
        instance = self.strategies[strategy_id]
        if instance.status == StrategyStatus.RUNNING:
            logger.warning(f"策略已在运行: {strategy_id}")
            return False
        
        # 选择 Worker
        worker_id = self._select_worker()
        if worker_id is None:
            logger.warning("没有可用的 Worker")
            return False
        
        # 分配到 Worker
        instance.worker_id = worker_id
        instance.status = StrategyStatus.RUNNING
        instance.started_at = datetime.now()
        self.worker_loads[worker_id] += 1
        
        # 异步启动
        task = asyncio.create_task(self._run_strategy(instance))
        self.running_strategies[strategy_id] = task
        
        logger.info(f"策略启动: {instance.name} on Worker {worker_id}")
        
        if self.on_strategy_start:
            await self._safe_callback(self.on_strategy_start, instance)
        
        return True
    
    async def _run_strategy(self, instance: StrategyInstance):
        """运行策略（异步）"""
        try:
            # 这里调用实际的策略执行逻辑
            # 实际实现需要根据具体策略类型来
            while instance.status == StrategyStatus.RUNNING:
                await asyncio.sleep(1)
                # 更新指标
                instance.metrics.setdefault('runtime', 0)
                instance.metrics['runtime'] += 1
                
        except Exception as e:
            logger.error(f"策略执行错误: {instance.strategy_id}, {e}")
            instance.status = StrategyStatus.ERROR
            if self.on_error:
                await self._safe_callback(self.on_error, instance, str(e))
    
    async def _safe_callback(self, callback, *args):
        """安全执行回调"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args)
            else:
                callback(*args)
        except Exception as e:
            logger.error(f"回调执行错误: {e}")
    
    async def stop_strategy(self, strategy_id: str) -> bool:
        """停止策略"""
        if strategy_id not in self.strategies:
            return False
        
        instance = self.strategies[strategy_id]
        if instance.status != StrategyStatus.RUNNING:
            return False
        
        instance.status = StrategyStatus.STOPPED
        
        # 停止异步任务
        if strategy_id in self.running_strategies:
            task = self.running_strategies[strategy_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.running_strategies[strategy_id]
        
        # 释放 Worker
        if instance.worker_id:
            self.worker_loads[instance.worker_id] -= 1
        
        logger.info(f"策略停止: {instance.name}")
        
        if self.on_strategy_stop:
            await self._safe_callback(self.on_strategy_stop, instance)
        
        return True
    
    def get_strategy_status(self, strategy_id: str) -> Optional[Dict]:
        """获取策略状态"""
        if strategy_id not in self.strategies:
            return None
        instance = self.strategies[strategy_id]
        return {
            'strategy_id': instance.strategy_id,
            'name': instance.name,
            'status': instance.status.value,
            'worker_id': instance.worker_id,
            'created_at': instance.created_at.isoformat(),
            'started_at': instance.started_at.isoformat() if instance.started_at else None,
            'metrics': instance.metrics
        }
    
    def list_strategies(self, status: Optional[StrategyStatus] = None) -> List[Dict]:
        """列出策略"""
        strategies = list(self.strategies.values())
        if status:
            strategies = [s for s in strategies if s.status == status]
        return [
            {
                'strategy_id': s.strategy_id,
                'name': s.name,
                'status': s.status.value,
                'worker_id': s.worker_id
            }
            for s in strategies
        ]
    
    def get_worker_status(self) -> List[Dict]:
        """获取 Worker 状态"""
        return [
            {
                'worker_id': wid,
                'load': self.worker_loads[wid],
                'max_strategies': self.workers[wid].max_strategies,
                'priority': self.workers[wid].priority
            }
            for wid in self.workers
        ]
    
    async def start(self):
        """启动管理器"""
        self._running = True
        self.pending_queue = asyncio.Queue()
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("策略管理器启动")
    
    async def stop(self):
        """停止管理器"""
        self._running = False
        
        # 停止所有策略
        for strategy_id in list(self.running_strategies.keys()):
            await self.stop_strategy(strategy_id)
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("策略管理器停止")
    
    async def _scheduler_loop(self):
        """调度循环"""
        while self._running:
            try:
                await asyncio.sleep(self.health_check_interval)
                # 健康检查、负载均衡等
                await self._health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"调度循环错误: {e}")
    
    async def _health_check(self):
        """健康检查"""
        for strategy_id, task in list(self.running_strategies.items()):
            if task.done():
                instance = self.strategies.get(strategy_id)
                if instance and instance.status == StrategyStatus.RUNNING:
                    instance.status = StrategyStatus.STOPPED
                    if instance.worker_id:
                        self.worker_loads[instance.worker_id] -= 1
                    del self.running_strategies[strategy_id]
                    logger.warning(f"策略异常退出: {strategy_id}")
