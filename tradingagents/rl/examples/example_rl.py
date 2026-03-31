# -*- coding: utf-8 -*-
"""
RL Module Example - 强化学习示例脚本
"""

import numpy as np
import sys
import os

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradingagents.rl import (
    TradingEnv,
    PortfolioEnv,
    RLTrainer,
    TrainingConfig,
    PortfolioRLAgent,
    AlphaGFN,
    create_alpha_gfn,
)


def example_single_asset_rl():
    """单资产 RL 训练示例"""
    print("\n" + "="*50)
    print("示例 1: 单资产 RL 训练")
    print("="*50)
    
    # 生成模拟价格数据
    np.random.seed(42)
    n_days = 500
    prices = 100 + np.cumsum(np.random.randn(n_days) * 2)
    
    # 创建环境
    env = TradingEnv(
        prices=prices,
        initial_cash=100000,
        transaction_cost=0.001,
        reward_type="sharpe",
    )
    
    # 训练配置
    config = TrainingConfig(
        algorithm="dqn",
        episodes=50,  # 快速测试用
        max_steps=200,
        batch_size=32,
        learning_rate=0.001,
        gamma=0.99,
        epsilon=1.0,
        epsilon_decay=0.995,
        epsilon_min=0.01,
        save_dir="models/rl",
        log_interval=10,
    )
    
    # 训练
    trainer = RLTrainer(env, config)
    results = trainer.train(episodes=50)
    
    # 评估
    eval_result = trainer.evaluate(episodes=5)
    print(f"\n评估结果: {eval_result}")
    
    return results


def example_portfolio_rl():
    """多资产组合 RL 示例"""
    print("\n" + "="*50)
    print("示例 2: 多资产组合 RL")
    print("="*50)
    
    # 生成多资产价格数据
    np.random.seed(123)
    n_days = 300
    
    price_data = {
        '股票A': 100 + np.cumsum(np.random.randn(n_days) * 2),
        '股票B': 50 + np.cumsum(np.random.randn(n_days) * 1.5),
        '股票C': 80 + np.cumsum(np.random.randn(n_days) * 1.8),
        '股票D': 30 + np.cumsum(np.random.randn(n_days) * 1.2),
    }
    
    # 创建组合 RL 代理
    from tradingagents.rl.portfolio_rl import PortfolioConfig, create_portfolio_rl
    
    agent = create_portfolio_rl(
        assets=['股票A', '股票B', '股票C', '股票D'],
        price_data=price_data,
        initial_cash=100000,
        algorithm="ppo",
        train_episodes=30,  # 快速测试
    )
    
    # 训练
    results = agent.train(verbose=True)
    
    # 评估
    eval_result = agent.evaluate()
    print(f"\n组合评估: {eval_result}")
    
    return results


def example_alpha_gfn():
    """Alpha-GFN 因子挖掘示例"""
    print("\n" + "="*50)
    print("示例 3: Alpha-GFN 因子挖掘")
    print("="*50)
    
    # 生成测试数据
    np.random.seed(456)
    n = 500
    
    data = {
        'close': np.random.randn(n).cumsum() + 100,
        'volume': np.random.rand(n) * 1000000 + 500000,
        'high': np.random.randn(n).cumsum() + 105,
        'low': np.random.randn(n).cumsum() + 95,
    }
    
    # 目标收益
    target = np.random.randn(n) * 0.01
    
    # 创建 Alpha-GFN
    alpha_gfn = create_alpha_gfn(
        n_generations=10,
        population_size=20,
        min_ic=0.01,
    )
    
    # 挖掘因子
    top_alphas = alpha_gfn.evolve(data, target)
    
    print("\nTop 5 Alpha 因子:")
    for i, alpha in enumerate(top_alphas[:5]):
        print(f"  {i+1}. {alpha}")
    
    # 使用 GFN 生成新因子
    generated = alpha_gfn.generate_alpha_flow(data)
    print(f"\nGFN 生成因子维度: {generated['gfn_alpha'].shape}")
    
    return top_alphas


def example_compare_algorithms():
    """对比不同 RL 算法"""
    print("\n" + "="*50)
    print("示例 4: 算法对比")
    print("="*50)
    
    # 生成数据
    np.random.seed(789)
    n_days = 400
    prices = 100 + np.cumsum(np.random.randn(n_days) * 2)
    
    algorithms = ['dqn', 'ppo', 'a2c']
    results = {}
    
    for algo in algorithms:
        print(f"\n训练 {algo.upper()}...")
        
        env = TradingEnv(
            prices=prices,
            initial_cash=100000,
            reward_type="sharpe",
        )
        
        config = TrainingConfig(
            algorithm=algo,
            episodes=20,
            max_steps=100,
            batch_size=32,
        )
        
        trainer = RLTrainer(env, config)
        train_results = trainer.train(episodes=20)
        eval_result = trainer.evaluate(episodes=5)
        
        results[algo] = eval_result
        print(f"  {algo}: {eval_result['mean_reward']:.2f}")
    
    print("\n算法对比结果:")
    for algo, result in results.items():
        print(f"  {algo}: mean={result['mean_reward']:.2f}, std={result['std_reward']:.2f}")
    
    return results


if __name__ == "__main__":
    # 检查依赖
    try:
        import gymnasium
        print("[OK] gymnasium 可用")
    except ImportError:
        print("[WARNING] 需要安装: pip install gymnasium")
    
    try:
        import torch
        print(f"[OK] torch 可用 (版本: {torch.__version__})")
    except ImportError:
        print("[WARNING] 需要安装: pip install torch")
    
    print("\n" + "="*50)
    print("TradingAgents-CN RL 模块示例")
    print("="*50)
    
    # 运行示例
    print("\n[1] 单资产 RL 训练")
    example_single_asset_rl()
    
    print("\n[2] 多资产组合 RL")
    example_portfolio_rl()
    
    print("\n[3] Alpha-GFN 因子挖掘")
    example_alpha_gfn()
    
    print("\n[4] 算法对比")
    example_compare_algorithms()
    
    print("\n" + "="*50)
    print("示例完成!")
    print("="*50)