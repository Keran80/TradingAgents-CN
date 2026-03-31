# -*- coding: utf-8 -*-
"""
分布式架构示例

演示多策略并行管理、分布式数据服务、RPC 通信
"""

import asyncio
import sys
sys.path.insert(0, '.')

from tradingagents.distributed import (
    StrategyManager, WorkerConfig, DistributedDataService,
    StrategyIsolator, RPCClient, RPCServer, K8sDeployment, DeploymentConfig
)


async def example_strategy_manager():
    """示例：多策略管理器"""
    print("=" * 50)
    print("1. 多策略并行管理器")
    print("=" * 50)
    
    # 创建管理器
    manager = StrategyManager(max_workers=4)
    
    # 注册 Workers
    manager.register_worker(WorkerConfig(
        worker_id="worker-1",
        max_strategies=5,
        priority=1
    ))
    manager.register_worker(WorkerConfig(
        worker_id="worker-2",
        max_strategies=3,
        priority=0
    ))
    
    # 注册策略
    sid1 = manager.register_strategy(
        name="均线策略",
        strategy_class="strategies.ma.MAStrategy",
        config={"symbol": "000001.SZ", "period": 20}
    )
    
    sid2 = manager.register_strategy(
        name="动量策略",
        strategy_class="strategies.momentum.MomentumStrategy",
        config={"symbol": "600519.SH", "window": 10}
    )
    
    # 启动策略
    await manager.start()
    await manager.start_strategy(sid1)
    await manager.start_strategy(sid2)
    
    # 查看状态
    print(f"策略列表: {manager.list_strategies()}")
    print(f"Worker 状态: {manager.get_worker_status()}")
    
    # 停止
    await manager.stop()
    print("[OK] 策略管理器示例完成\n")


async def example_data_service():
    """示例：分布式数据服务"""
    print("=" * 50)
    print("2. 分布式数据服务")
    print("=" * 50)
    
    # 创建服务
    service = DistributedDataService(
        cache_size=1000,
        cache_ttl=300
    )
    
    # 注册数据加载器
    def load_stock_prices(symbol):
        import random
        return {
            'symbol': symbol,
            'prices': [100 + random.random() * 10 for _ in range(100)],
            'volumes': [random.randint(1000, 10000) for _ in range(100)]
        }
    
    service.register_loader('stock_prices', load_stock_prices)
    
    # 获取数据（带缓存）
    data1 = await service.get_data('stock_prices', '000001.SZ')
    print(f"首次获取: {data1['symbol']}")
    
    data2 = await service.get_data('stock_prices', '000001.SZ')
    print(f"缓存命中: {data2['symbol']}")
    
    # 查看统计
    stats = service.get_stats()
    print(f"缓存命中率: {stats['memory_cache']['hit_rate']:.2%}")
    print("[OK] 分布式数据服务示例完成\n")


async def example_rpc():
    """示例：RPC 通信"""
    print("=" * 50)
    print("3. RPC 通信层")
    print("=" * 50)
    
    # 创建 RPC 服务器
    async with RPCServer(host="127.0.0.1", port=8765) as server:
        # 注册方法
        def add(a, b):
            return a + b
        
        def get_price(symbol):
            return {'symbol': symbol, 'price': 100.5}
        
        server.register_method('add', add)
        server.register_method('get_price', get_price)
        
        # 创建客户端
        async with RPCClient(['127.0.0.1:8765']) as client:
            # 调用方法
            result = await client.call('add', {'a': 10, 'b': 20})
            print(f"add(10, 20) = {result}")
            
            result = await client.call('get_price', {'symbol': '000001.SZ'})
            print(f"get_price('000001.SZ') = {result}")
        
        print("[OK] RPC 通信示例完成\n")


def example_kubernetes():
    """示例：Kubernetes 部署"""
    print("=" * 50)
    print("4. Kubernetes 部署配置")
    print("=" * 50)
    
    # 创建部署
    deployment = K8sDeployment(DeploymentConfig(
        name="trading-agents",
        namespace="quant",
        replicas=3,
        container=ContainerConfig(
            name="agent",
            image="tradingagents-cn:v1.0",
            port=8000,
            env={
                "LOG_LEVEL": "INFO",
                "DATA_SOURCE": "akshare"
            }
        ),
        service_type="LoadBalancer"
    ))
    
    # 生成 YAML
    yaml_output = deployment.generate_yaml()
    print("生成的 K8s YAML:")
    print(yaml_output[:500] + "...")
    
    # 保存到文件
    deployment.save_yaml("k8s-deployment.yaml")
    print("[OK] Kubernetes 部署配置示例完成\n")


def example_isolator():
    """示例：策略隔离"""
    print("=" * 50)
    print("5. 策略隔离运行")
    print("=" * 50)
    
    isolator = StrategyIsolator(IsolationConfig(
        max_memory_mb=1024,
        max_cpu_percent=30.0
    ))
    
    # 创建策略进程
    process_id = isolator.create_strategy_process(
        strategy_id="test-001",
        strategy_class="strategies.example.Strategy",
        config={"param": "value"}
    )
    print(f"创建进程: {process_id}")
    
    # 启动进程
    isolator.start_process(process_id)
    print(f"进程状态: {isolator.get_process_status(process_id)}")
    
    # 停止进程
    isolator.stop_process(process_id)
    
    isolator.cleanup()
    print("[OK] 策略隔离示例完成\n")


async def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("TradingAgents-CN 分布式架构示例")
    print("=" * 60 + "\n")
    
    # 示例 1: 策略管理器
    await example_strategy_manager()
    
    # 示例 2: 数据服务
    await example_data_service()
    
    # 示例 3: RPC 通信
    await example_rpc()
    
    # 示例 4: K8s 部署
    example_kubernetes()
    
    # 示例 5: 策略隔离
    example_isolator()
    
    print("=" * 60)
    print("所有示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())