# -*- coding: utf-8 -*-
"""
Portfolio RL Agent - 基于强化学习的组合优化

参考 FLAG-Trader 思想，使用 RL 进行资产组合优化
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import random

# 尝试导入 torch
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except (ImportError, OSError):
    TORCH_AVAILABLE = False
    torch = None
    nn = None

from .env import PortfolioEnv
from .trainer import RLTrainer, TrainingConfig, TORCH_AVAILABLE


@dataclass
class PortfolioConfig:
    """组合配置"""
    assets: List[str]  # 资产列表
    initial_cash: float = 100000.0
    max_position_pct: float = 0.3  # 单资产最大仓位
    transaction_cost: float = 0.001
    rebalance_freq: str = "weekly"  # weekly / daily / monthly
    risk_aversion: float = 1.0  # 风险厌恶系数
    
    # RL 配置
    rl_algorithm: str = "ppo"
    train_episodes: int = 200
    eval_episodes: int = 10


if TORCH_AVAILABLE:
    class PortfolioActor(nn.Module):
        """组合策略网络"""
        
        def __init__(self, state_dim: int, n_assets: int, hidden_dim: int = 128):
            super().__init__()
            
            self.n_assets = n_assets
            
            # 特征提取
            self.encoder = nn.Sequential(
                nn.Linear(state_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
            )
            
            # 资产权重输出
            self.weight_head = nn.Sequential(
                nn.Linear(hidden_dim, n_assets),
                nn.Softmax(dim=-1),  # 归一化为权重
            )
            
            # 风险调整输出
            self.risk_head = nn.Sequential(
                nn.Linear(hidden_dim, 1),
                nn.Sigmoid(),  # 风险敞口 [0, 1]
            )
        
        def forward(self, x):
            features = self.encoder(x)
            weights = self.weight_head(features)
            risk = self.risk_head(features)
            return weights, risk
    
    
    class PortfolioCritic(nn.Module):
        """组合价值网络"""
        
        def __init__(self, state_dim: int, hidden_dim: int = 128):
            super().__init__()
            
            self.network = nn.Sequential(
                nn.Linear(state_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, 1),
            )
        
        def forward(self, x):
            return self.network(x)
else:
    # PyTorch 不可用时的替代类
    class PortfolioActor:
        def __init__(self, *args, **kwargs):
            pass
        
        def __call__(self, x):
            n_assets = kwargs.get('n_assets', 4)
            return np.random.dirichlet(np.ones(n_assets)), 0.5
    
    class PortfolioCritic:
        def __init__(self, *args, **kwargs):
            pass


class PortfolioRLAgent:
    """
    基于强化学习的组合优化代理
    
    功能：
    - 多资产组合权重优化
    - 动态仓位管理
    - 风险控制
    - 策略适应
    """
    
    def __init__(self, config: PortfolioConfig, price_data: Dict[str, np.ndarray]):
        self.config = config
        self.price_data = price_data
        
        # 创建 RL 环境
        self.env = PortfolioEnv(
            prices_dict=price_data,
            initial_cash=config.initial_cash,
            transaction_cost=config.transaction_cost,
            max_position_pct=config.max_position_pct,
        )
        
        # 训练配置
        train_config = TrainingConfig(
            algorithm=config.rl_algorithm,
            episodes=config.train_episodes,
            learning_rate=0.0003,
            gamma=0.99,
            clip_eps=0.2,
            value_coef=0.5,
            entropy_coef=0.01,
        )
        
        # 训练器
        self.trainer = RLTrainer(self.env, train_config)
        
        # 组合状态
        self.weights = None
        self.is_trained = False
    
    def train(self, verbose: bool = True) -> Dict:
        """训练组合策略"""
        if verbose:
            print(f"开始训练 RL 组合优化器...")
            print(f"  资产: {self.config.assets}")
            print(f"  算法: {self.config.rl_algorithm}")
            print(f"  轮次: {self.config.train_episodes}")
        
        results = self.trainer.train(episodes=self.config.train_episodes)
        
        self.is_trained = True
        
        if verbose:
            final_reward = np.mean(results['rewards'][-10:])
            print(f"训练完成，最终平均收益: {final_reward:.2f}")
        
        return results
    
    def predict_weights(self, market_state: np.ndarray) -> np.ndarray:
        """
        预测组合权重
        
        Args:
            market_state: 市场状态特征
            
        Returns:
            weights: 各资产权重 (numpy array)
        """
        if not self.is_trained:
            # 未训练时返回等权重
            return np.ones(len(self.config.assets)) / len(self.config.assets)
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(market_state).unsqueeze(0)
            
            # 使用训练好的策略
            # 简化：使用动作解码
            action = self.trainer.agent.select_action(market_state, training=False)
            
            # 解码为权重
            weights = self._action_to_weights(action)
        
        return weights
    
    def _action_to_weights(self, action: int) -> np.ndarray:
        """将动作转换为权重"""
        n = len(self.config.assets)
        
        # 简单策略：基于动作选择不同的权重方案
        if action < 3:
            # 基础动作
            weights = np.ones(n) / n
            if action == 1:  # 超配风险资产
                weights = weights * 1.5
                weights[0] += 0.2
            elif action == 2:  # 低配风险资产
                weights = weights * 0.5
                weights[-1] += 0.3
        else:
            # 扩展动作空间
            np.random.seed(action)
            weights = np.random.dirichlet(np.ones(n))
        
        return weights / weights.sum()
    
    def rebalance(
        self, 
        current_weights: np.ndarray, 
        target_weights: np.ndarray,
        threshold: float = 0.05,
    ) -> Tuple[np.ndarray, List[str]]:
        """
        组合再平衡
        
        Args:
            current_weights: 当前权重
            target_weights: 目标权重
            threshold: 阈值，超过则调仓
            
        Returns:
            (调整后权重, 交易列表)
        """
        diff = target_weights - current_weights
        trades = []
        
        for i, d in enumerate(diff):
            if abs(d) > threshold:
                asset = self.config.assets[i]
                action = "buy" if d > 0 else "sell"
                trades.append(f"{action} {asset} {abs(d)*100:.1f}%")
        
        # 简单实现：直接应用目标权重
        return target_weights, trades
    
    def evaluate(self) -> Dict[str, float]:
        """评估组合表现"""
        if not self.is_trained:
            return {"status": "not_trained"}
        
        eval_result = self.trainer.evaluate(episodes=self.config.eval_episodes)
        
        return {
            "mean_return": eval_result['mean_reward'],
            "std_return": eval_result['std_reward'],
            "sharpe_ratio": eval_result['mean_reward'] / (eval_result['std_return'] + 1e-8),
            "max_return": eval_result['max_reward'],
            "min_return": eval_result['min_reward'],
        }
    
    def get_portfolio_stats(self, returns: pd.Series) -> Dict[str, float]:
        """计算组合统计指标"""
        
        # 年化收益率
        annual_return = returns.mean() * 252
        
        # 年化波动率
        annual_vol = returns.std() * np.sqrt(252)
        
        # 夏普比率
        sharpe = annual_return / (annual_vol + 1e-8)
        
        # 最大回撤
        cum_returns = (1 + returns).cumprod()
        running_max = cum_returns.cummax()
        drawdown = (cum_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 卡尔玛比率
        calmar = annual_return / (abs(max_drawdown) + 1e-8)
        
        # 胜率
        win_rate = (returns > 0).sum() / len(returns)
        
        return {
            "annual_return": annual_return,
            "annual_vol": annual_vol,
            "sharpe": sharpe,
            "max_drawdown": max_drawdown,
            "calmar": calmar,
            "win_rate": win_rate,
            "total_return": returns.sum(),
        }
    
    def save(self, path: str):
        """保存模型"""
        self.trainer.save(path)
    
    def load(self, path: str):
        """加载模型"""
        self.trainer.load(path)
        self.is_trained = True


def create_portfolio_rl(
    assets: List[str],
    price_data: Dict[str, np.ndarray],
    initial_cash: float = 100000.0,
    algorithm: str = "ppo",
    train_episodes: int = 200,
) -> PortfolioRLAgent:
    """创建组合 RL 代理的工厂函数"""
    
    config = PortfolioConfig(
        assets=assets,
        initial_cash=initial_cash,
        rl_algorithm=algorithm,
        train_episodes=train_episodes,
    )
    
    return PortfolioRLAgent(config, price_data)