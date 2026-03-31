# -*- coding: utf-8 -*-
"""
策略隔离运行模块

支持：
- 进程隔离
- 资源限制
- 进程池管理
- 策略生命周期管理
"""

import asyncio
import multiprocessing as mp
from multiprocessing import Process, Queue as MPQueue
import sys
import os
import time
import uuid
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from datetime import datetime

# resource 模块仅在 Unix 系统可用
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

logger = logging.getLogger(__name__)


class IsolationLevel(Enum):
    """隔离级别"""
    PROCESS = "process"      # 进程隔离
    CONTAINER = "container"  # 容器隔离


@dataclass
class IsolationConfig:
    """隔离配置"""
    level: IsolationLevel = IsolationLevel.PROCESS
    max_memory_mb: int = 2048
    max_cpu_percent: float = 50.0
    max_open_files: int = 100
    env_vars: Dict[str, str] = field(default_factory=dict)
    working_dir: Optional[str] = None


@dataclass
class StrategyProcess:
    """策略进程"""
    process_id: str
    strategy_id: str
    process: Optional[Process] = None
    input_queue: Optional[MPQueue] = None
    output_queue: Optional[MPQueue] = None
    status: str = "created"
    started_at: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


class StrategyIsolator:
    """
    策略隔离运行器
    
    确保每个策略在独立进程中运行，资源隔离
    """
    
    def __init__(self, config: Optional[IsolationConfig] = None):
        self.config = config or IsolationConfig()
        
        # 策略进程管理
        self.processes: Dict[str, StrategyProcess] = {}
        
        # 回调
        self.on_start: Optional[Callable] = None
        self.on_stop: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # 主进程用于接收消息
        self._main_loop_task: Optional[asyncio.Task] = None
    
    def _setup_resources(self):
        """设置资源限制（仅 Unix）"""
        if sys.platform == 'win32' or not HAS_RESOURCE:
            return
        
        try:
            # 内存限制
            max_memory = self.config.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (max_memory, max_memory))
            
            # CPU 限制
            resource.setrlimit(resource.RLIMIT_CPU, (
                int(self.config.max_cpu_percent * 10),
                int(self.config.max_cpu_percent * 10)
            ))
            
            # 文件数限制
            resource.setrlimit(resource.RLIMIT_NOFILE, (
                self.config.max_open_files,
                self.config.max_open_files
            ))
            
        except Exception as e:
            logger.warning(f"资源限制设置失败: {e}")
    
    def _worker_process(
        self,
        strategy_class: str,
        config: Dict,
        input_queue: MPQueue,
        output_queue: MPQueue
    ):
        """工作进程入口"""
        # 设置资源限制
        self._setup_resources()
        
        # 设置环境变量
        for key, value in self.config.env_vars.items():
            os.environ[key] = value
        
        # 设置工作目录
        if self.config.working_dir:
            os.chdir(self.config.working_dir)
        
        # 初始化策略
        try:
            # 动态导入策略类
            module_name, class_name = strategy_class.rsplit('.', 1)
            module = __import__(module_name, fromlist=[class_name])
            strategy = getattr(module, class_name)(**config)
            
            output_queue.put({
                'type': 'init',
                'status': 'success'
            })
            
            # 主循环
            while True:
                try:
                    msg = input_queue.get(timeout=1)
                    
                    if msg.get('type') == 'stop':
                        break
                    
                    elif msg.get('type') == 'execute':
                        # 执行策略逻辑
                        result = strategy.execute(msg.get('data', {}))
                        output_queue.put({
                            'type': 'result',
                            'data': result
                        })
                        
                except Exception as e:
                    output_queue.put({
                        'type': 'error',
                        'error': str(e)
                    })
                    
        except Exception as e:
            output_queue.put({
                'type': 'error',
                'error': f"策略初始化失败: {e}"
            })
    
    def create_strategy_process(
        self,
        strategy_id: str,
        strategy_class: str,
        config: Dict[str, Any]
    ) -> str:
        """
        创建策略进程
        
        返回进程 ID
        """
        process_id = str(uuid.uuid4())[:8]
        
        # 创建进程队列
        input_queue = MPQueue()
        output_queue = MPQueue()
        
        # 创建进程
        process = Process(
            target=self._worker_process,
            args=(strategy_class, config, input_queue, output_queue),
            daemon=True
        )
        
        # 注册进程
        strategy_process = StrategyProcess(
            process_id=process_id,
            strategy_id=strategy_id,
            process=process,
            input_queue=input_queue,
            output_queue=output_queue
        )
        
        self.processes[process_id] = strategy_process
        
        logger.info(f"创建策略进程: {process_id} for {strategy_id}")
        return process_id
    
    def start_process(self, process_id: str) -> bool:
        """启动策略进程"""
        if process_id not in self.processes:
            logger.error(f"进程不存在: {process_id}")
            return False
        
        sp = self.processes[process_id]
        
        if sp.process and not sp.process.is_alive():
            sp.process.start()
            sp.status = "running"
            sp.started_at = datetime.now()
            
            # 等待初始化完成
            try:
                msg = sp.output_queue.get(timeout=5)
                if msg.get('type') == 'error':
                    logger.error(f"进程初始化失败: {msg.get('error')}")
                    sp.status = "error"
                    return False
            except:
                pass
            
            logger.info(f"策略进程启动: {process_id}")
            return True
        
        return False
    
    def stop_process(self, process_id: str) -> bool:
        """停止策略进程"""
        if process_id not in self.processes:
            return False
        
        sp = self.processes[process_id]
        
        # 发送停止信号
        if sp.input_queue:
            sp.input_queue.put({'type': 'stop'})
        
        # 等待进程结束
        if sp.process and sp.process.is_alive():
            sp.process.join(timeout=5)
            if sp.process.is_alive():
                sp.process.terminate()
                sp.process.join(timeout=2)
        
        sp.status = "stopped"
        logger.info(f"策略进程停止: {process_id}")
        
        return True
    
    def send_message(self, process_id: str, data: Any) -> Optional[Any]:
        """发送消息到策略进程"""
        if process_id not in self.processes:
            return None
        
        sp = self.processes[process_id]
        
        if sp.status != "running" or not sp.input_queue:
            return None
        
        sp.input_queue.put({
            'type': 'execute',
            'data': data
        })
        
        # 等待结果
        try:
            msg = sp.output_queue.get(timeout=30)
            return msg
        except:
            return None
    
    def get_process_status(self, process_id: str) -> Optional[Dict]:
        """获取进程状态"""
        if process_id not in self.processes:
            return None
        
        sp = self.processes[process_id]
        
        return {
            'process_id': sp.process_id,
            'strategy_id': sp.strategy_id,
            'status': sp.status,
            'alive': sp.process.is_alive() if sp.process else False,
            'started_at': sp.started_at.isoformat() if sp.started_at else None,
            'metrics': sp.metrics
        }
    
    def list_processes(self) -> List[Dict]:
        """列出所有进程"""
        return [
            self.get_process_status(pid)
            for pid in self.processes
        ]
    
    def cleanup(self):
        """清理所有进程"""
        for process_id in list(self.processes.keys()):
            self.stop_process(process_id)
        
        self.processes.clear()
        logger.info("策略隔离器清理完成")


class ProcessPool:
    """
    进程池管理器
    
    预先创建进程池，复用进程资源
    """
    
    def __init__(self, size: int = 4):
        self.size = size
        self.isolator = StrategyIsolator()
        self._pools: Dict[str, str] = {}  # strategy_id -> process_id
    
    async def submit(
        self,
        strategy_id: str,
        strategy_class: str,
        config: Dict
    ) -> Optional[str]:
        """提交策略到进程池"""
        if strategy_id in self._pools:
            return self._pools[strategy_id]
        
        # 检查是否有空闲进程
        for process_id, sp in self.isolator.processes.items():
            if sp.status == "idle":
                sp.strategy_id = strategy_id
                sp.status = "running"
                self._pools[strategy_id] = process_id
                return process_id
        
        # 如果池未满，创建新进程
        if len(self.isolator.processes) < self.size:
            process_id = self.isolator.create_strategy_process(
                strategy_id, strategy_class, config
            )
            self.isolator.start_process(process_id)
            self._pools[strategy_id] = process_id
            return process_id
        
        # 池已满，等待
        return None
    
    async def execute(
        self,
        strategy_id: str,
        data: Dict
    ) -> Optional[Any]:
        """执行策略"""
        process_id = self._pools.get(strategy_id)
        if not process_id:
            return None
        
        return self.isolator.send_message(process_id, data)
    
    def release(self, strategy_id: str):
        """释放策略（返回池中）"""
        if strategy_id in self._pools:
            process_id = self._pools[strategy_id]
            if process_id in self.isolator.processes:
                self.isolator.processes[process_id].status = "idle"
            del self._pools[strategy_id]
    
    def shutdown(self):
        """关闭进程池"""
        self.isolator.cleanup()
        self._pools.clear()
