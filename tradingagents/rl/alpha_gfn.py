# -*- coding: utf-8 -*-
"""
Alpha-GFN - 基于生成流网络的 Alpha 因子挖掘

参考 Alpha-GFN 思想，使用生成流网络进行因子发现
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import pandas as pd
from collections import defaultdict
import random

# 尝试导入 torch
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except (ImportError, OSError):
    TORCH_AVAILABLE = False
    torch = None
    nn = None
    F = None


@dataclass
class AlphaConfig:
    """Alpha 挖掘配置"""
    n_generations: int = 50  # 迭代轮数
    population_size: int = 100  # 种群大小
    n_parents: int = 20  # 父代数量
    mutation_rate: float = 0.1  # 变异率
    crossover_rate: float = 0.7  # 交叉率
    
    # 因子评估
    min_ic: float = 0.02  # 最小 IC 阈值
    max_drawdown_ratio: float = 0.5  # 最大回撤阈值
    
    # GFN 配置
    flow_steps: int = 5  # 流模型步骤
    hidden_dim: int = 64  # 隐藏层维度
    n_samples: int = 100  # 采样数量


# 基础操作符 (numpy 版本)
def _add(x, y): return x + y
def _sub(x, y): return x - y
def _mul(x, y): return x * y
def _div(x, y): return x / (y + 1e-8)
def _neg(x): return -x
def _abs(x): return np.abs(x)
def _log(x): return np.log(np.abs(x) + 1e-8)
def _sqrt(x): return np.sqrt(np.abs(x) + 1e-8)

def _rank(x):
    """排名函数"""
    return np.argsort(np.argsort(x, axis=-1), axis=-1) / (x.shape[-1] + 1e-8)

def _zscore(x):
    """Z-score 标准化"""
    mean = np.mean(x, axis=-1, keepdims=True)
    std = np.std(x, axis=-1, keepdims=True)
    return (x - mean) / (std + 1e-8)

def _delta(x):
    """差分"""
    return x[:, 1:] - x[:, :-1]

def _roll_max(x):
    return np.max(x, axis=-1)

def _roll_min(x):
    return np.min(x, axis=-1)

def _roll_std(x):
    return np.std(x, axis=-1)


OPERATORS = {
    'add': _add,
    'sub': _sub,
    'mul': _mul,
    'div': _div,
    'neg': _neg,
    'abs': _abs,
    'log': _log,
    'sqrt': _sqrt,
    'rank': _rank,
    'zscore': _zscore,
    'delta': _delta,
    'roll_max': _roll_max,
    'roll_min': _roll_min,
    'roll_std': _roll_std,
}


class FactorTree:
    """因子表达式树"""
    
    def __init__(self, root: Optional[Any] = None):
        self.root = root
        self._cache = None
    
    @staticmethod
    def random_tree(depth: int = 3) -> 'FactorTree':
        """随机生成因子树"""
        if depth == 0:
            # 叶子节点：随机特征或常量
            if np.random.rand() > 0.5:
                return FactorTree(('feature', np.random.choice(['close', 'volume', 'high', 'low'])))
            else:
                return FactorTree(('const', np.random.uniform(-1, 1)))
        
        # 内部节点
        op = np.random.choice(list(OPERATORS.keys()))
        
        if op in ['neg', 'abs', 'log', 'sqrt', 'rank', 'zscore', 'delta', 'roll_max', 'roll_min', 'roll_std']:
            # 一元操作
            child = FactorTree.random_tree(depth - 1)
            return FactorTree(('unary', op, child))
        else:
            # 二元操作
            left = FactorTree.random_tree(depth - 1)
            right = FactorTree.random_tree(depth - 1)
            return FactorTree(('binary', op, left, right))
    
    def evaluate(self, data: Dict[str, np.ndarray]) -> np.ndarray:
        """计算因子值"""
        return self._evaluate_node(self.root, data)
    
    def _evaluate_node(self, node, data: Dict[str, np.ndarray]) -> np.ndarray:
        if node is None:
            return np.zeros(1)
        
        if isinstance(node, tuple):
            if node[0] == 'feature':
                return data.get(node[1], np.zeros(1))
            elif node[0] == 'const':
                feature_shape = data[list(data.keys())[0]].shape if data else (1,)
                return np.full(feature_shape, node[1])
            
            elif node[0] == 'unary':
                op = node[1]
                child_val = self._evaluate_node(node[2], data)
                try:
                    return OPERATORS[op](child_val)
                except Exception:
                    return np.zeros_like(child_val)

            elif node[0] == 'binary':
                op = node[1]
                left_val = self._evaluate_node(node[2], data)
                right_val = self._evaluate_node(node[3], data)
                try:
                    return OPERATORS[op](left_val, right_val)
                except Exception:
                    return np.zeros_like(left_val)
        
        return np.zeros(1)
    
    def __repr__(self):
        return self._repr_node(self.root)
    
    def _repr_node(self, node):
        if node is None:
            return "empty"
        
        if isinstance(node, tuple):
            if node[0] == 'feature':
                return node[1]
            elif node[0] == 'const':
                return f"{node[1]:.2f}"
            elif node[0] == 'unary':
                return f"{node[1]}({self._repr_node(node[2])})"
            elif node[0] == 'binary':
                return f"({self._repr_node(node[2])} {node[1]} {self._repr_node(node[3])})"
        return "?"


class FlowNetwork:
    """生成流网络 (GFN) - NumPy 实现"""
    
    def __init__(self, input_dim: int, hidden_dim: int = 64, n_steps: int = 5):
        self.n_steps = n_steps
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        
        # 简化的权重矩阵
        self.W1 = np.random.randn(input_dim, hidden_dim) * 0.1
        self.b1 = np.zeros(hidden_dim)
        self.W_steps = [np.random.randn(hidden_dim, hidden_dim) * 0.1 for _ in range(n_steps)]
    
    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """前向传播"""
        h = x @ self.W1 + self.b1
        h = np.tanh(h)
        
        log_det = np.zeros(x.shape[0])
        
        for W in self.W_steps:
            h_before = h
            h = h @ W
            h = np.tanh(h)
            log_det += np.log(np.abs(1 + np.tanh(h_before @ W).mean()) + 1e-8)
        
        z = h
        return z, log_det
    
    def inverse(self, z: np.ndarray) -> np.ndarray:
        """逆变换"""
        h = z
        for W in reversed(self.W_steps):
            h = h @ W
            h = np.tanh(h)
        return h


class AlphaGFN:
    """
    基于生成流网络的 Alpha 因子挖掘
    
    使用 GFN 生成和优化 Alpha 因子表达式
    """
    
    def __init__(self, config: Optional[AlphaConfig] = None):
        self.config = config or AlphaConfig()
        
        self.population = []  # 因子种群
        self.best_alpha = None  # 最佳因子
        self.history = []  # 训练历史
        self.flow_net = None
    
    def evolve(self, data: Dict[str, np.ndarray], target: np.ndarray) -> List[FactorTree]:
        """
        进化搜索 Alpha 因子
        """
        print(f"开始 Alpha-GFN 因子挖掘...")
        print(f"  种群大小: {self.config.population_size}")
        print(f"  迭代轮数: {self.config.n_generations}")
        
        # 初始化种群
        self.population = [FactorTree.random_tree() for _ in range(self.config.population_size)]
        
        for generation in range(self.config.n_generations):
            # 评估
            scores = []
            for tree in self.population:
                try:
                    alpha = tree.evaluate(data)
                    if alpha.ndim > 0 and len(target) == len(alpha):
                        # 计算 IC
                        ic = self._calculate_ic(alpha, target)
                        # 计算回撤比
                        dd_ratio = self._calculate_drawdown_ratio(alpha)
                        
                        if dd_ratio > -self.config.max_drawdown_ratio and ic > self.config.min_ic:
                            score = abs(ic)
                        else:
                            score = 0
                    else:
                        score = 0
                except Exception:
                    score = 0
                
                scores.append(score)
            
            # 排序
            sorted_indices = np.argsort(scores)[::-1]
            self.population = [self.population[i] for i in sorted_indices]
            
            # 记录最佳
            best_score = scores[sorted_indices[0]]
            if best_score > 0:
                self.best_alpha = self.population[0]
                print(f"Gen {generation+1}: Best IC = {best_score:.4f}, Alpha = {self.best_alpha}")
            
            self.history.append(best_score)
            
            # 选择父代
            parents = self.population[:self.config.n_parents]
            
            # 生成新一代
            new_population = parents.copy()
            
            while len(new_population) < self.config.population_size:
                # 交叉
                if np.random.rand() < self.config.crossover_rate:
                    parent1 = np.random.choice(parents)
                    parent2 = np.random.choice(parents)
                    child = self._crossover(parent1, parent2)
                else:
                    child = np.random.choice(parents)
                
                # 变异
                if np.random.rand() < self.config.mutation_rate:
                    child = self._mutate(child)
                
                new_population.append(child)
            
            self.population = new_population
        
        # 返回最佳因子
        return self.get_top_alphas(n=10)
    
    def _calculate_ic(self, alpha: np.ndarray, target: np.ndarray) -> float:
        """计算 IC (Information Coefficient)"""
        if len(alpha.shape) > 1:
            alpha = alpha.mean(axis=0)
        
        if len(alpha) != len(target):
            return 0

        try:
            return np.corrcoef(alpha.flatten(), target.flatten())[0, 1]
        except Exception:
            return 0
    
    def _calculate_drawdown_ratio(self, alpha: np.ndarray) -> float:
        """计算回撤比"""
        if len(alpha.shape) > 1:
            alpha = alpha.mean(axis=0)
        
        cum_returns = np.cumsum(alpha)
        running_max = np.maximum.accumulate(cum_returns)
        drawdown = (cum_returns - running_max) / (np.abs(running_max) + 1e-8)
        
        return np.min(drawdown)
    
    def _crossover(self, parent1: FactorTree, parent2: FactorTree) -> FactorTree:
        """交叉操作"""
        return FactorTree.random_tree(depth=3)
    
    def _mutate(self, tree: FactorTree) -> FactorTree:
        """变异操作"""
        return FactorTree.random_tree(depth=3)
    
    def get_top_alphas(self, n: int = 10) -> List[FactorTree]:
        """获取 top N 因子"""
        return self.population[:n]
    
    def generate_alpha_flow(self, data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        使用 GFN 生成潜在 Alpha 向量
        """
        # 准备数据
        features = []
        for k, v in data.items():
            features.append(v)
        
        # 拼接特征
        combined = np.concatenate(features, axis=1)
        
        # 初始化 GFN
        if self.flow_net is None:
            self.flow_net = FlowNetwork(
                input_dim=combined.shape[1],
                hidden_dim=self.config.hidden_dim,
                n_steps=self.config.flow_steps,
            )
        
        # GFN 前向
        z, log_det = self.flow_net.forward(combined)
        
        # 采样生成新因子
        n_samples = self.config.n_samples
        noise = np.random.randn(n_samples, z.shape[1]) * 0.1
        
        # 逆变换生成新因子
        generated = []
        for i in range(n_samples):
            z_sample = z[i % len(z)] + noise[i]
            alpha = self.flow_net.inverse(z_sample.reshape(1, -1))
            generated.append(alpha.flatten())
        
        # 整合
        result = {'gfn_alpha': np.array(generated)}
        
        return result
    
    def apply_alpha(self, data: pd.DataFrame, alpha_expr: str) -> pd.Series:
        """
        应用 Alpha 因子表达式
        """
        # 简化实现
        if 'close' in data.columns and 'volume' in data.columns:
            close_rank = data['close'].rank(pct=True)
            vol_rank = data['volume'].rank(pct=True)
            return close_rank - vol_rank
        
        return pd.Series(np.zeros(len(data)))
    
    def save(self, path: str):
        """保存"""
        import pickle
        with open(path, 'wb') as f:
            pickle.dump({
                'best_alpha': self.best_alpha,
                'population': self.population,
                'history': self.history,
                'config': self.config,
            }, f)
    
    def load(self, path: str):
        """加载"""
        import pickle
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.best_alpha = data['best_alpha']
            self.population = data['population']
            self.history = data['history']
            self.config = data['config']


def create_alpha_gfn(
    n_generations: int = 50,
    population_size: int = 100,
    min_ic: float = 0.02,
) -> AlphaGFN:
    """创建 Alpha-GFN 实例"""
    config = AlphaConfig(
        n_generations=n_generations,
        population_size=population_size,
        min_ic=min_ic,
    )
    return AlphaGFN(config)


# 示例用法
if __name__ == "__main__":
    # 测试
    np.random.seed(42)
    
    # 生成测试数据
    n = 1000
    data = {
        'close': np.random.randn(n).cumsum() + 100,
        'volume': np.random.rand(n) * 1000000,
        'high': np.random.randn(n).cumsum() + 105,
        'low': np.random.randn(n).cumsum() + 95,
    }
    target = np.random.randn(n) * 0.01
    
    # 挖掘因子
    alpha_gfn = create_alpha_gfn(n_generations=10, population_size=20)
    top_alphas = alpha_gfn.evolve(data, target)
    
    print("\nTop 10 Alpha 因子:")
    for i, alpha in enumerate(top_alphas):
        print(f"  {i+1}. {alpha}")