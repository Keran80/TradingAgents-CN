# -*- coding: utf-8 -*-
"""
Distributed - 分布式架构模块

支持：
- 多策略并行管理
- 分布式数据服务
- 策略隔离运行
- RPC 通信
- Kubernetes 部署
"""

from .manager import StrategyManager, WorkerConfig
from .data_service import DistributedDataService, DataCache
from .isolator import StrategyIsolator, ProcessPool
from .rpc import RPCClient, RPCServer, MessageProtocol
from .kubernetes import K8sDeployment, DeploymentConfig

__all__ = [
    # 核心类
    'StrategyManager',
    'WorkerConfig',
    'DistributedDataService',
    'DataCache',
    'StrategyIsolator',
    'ProcessPool',
    'RPCClient',
    'RPCServer',
    'MessageProtocol',
    'K8sDeployment',
    'DeploymentConfig',
]
