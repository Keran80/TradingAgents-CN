# -*- coding: utf-8 -*-
"""
TradingAgents-CN Reinforcement Learning Module

强化学习模块，支持：
- RL 交易环境封装 (Gymnasium)
- DQN/PPO/A2C 算法实现
- 组合优化 RL 模型
- Alpha-GFN 因子挖掘
"""

from .env import (
    TradingEnv,
    PortfolioEnv,
    MultiAssetEnv,
)
from .trainer import RLTrainer, TrainingConfig
from .portfolio_rl import PortfolioRLAgent
from .alpha_gfn import AlphaGFN

__all__ = [
    # 交易环境
    "TradingEnv",
    "PortfolioEnv",
    "MultiAssetEnv",
    
    # 训练器
    "RLTrainer",
    "TrainingConfig",
    
    # 组合优化
    "PortfolioRLAgent",
    
    # 因子挖掘
    "AlphaGFN",
]
