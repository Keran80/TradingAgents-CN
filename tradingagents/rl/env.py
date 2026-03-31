# -*- coding: utf-8 -*-
"""
Trading RL Environment - 基于 Gymnasium 的交易环境封装
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class TradingStepResult:
    """交易步骤结果"""
    observation: np.ndarray
    reward: float
    terminated: bool
    truncated: bool
    info: Dict[str, Any]


class TradingEnv(gym.Env):
    """
    单资产交易强化学习环境
    
    动作空间：
    - 0: 持有 (hold)
    - 1: 买入 (buy)
    - 2: 卖出 (sell)
    
    状态空间 (observation)：
    - [0]: 归一化价格
    - [1]: 归一化成交量
    - [2]: 技术指标 (RSI)
    - [3]: 技术指标 (MACD)
    - [4]: 持仓状态 (0/1)
    - [5-9]: 历史价格特征 (5日)
    - [10]: 账户余额 (归一化)
    - [11]: 当前持仓盈亏
    """
    
    metadata = {"render_modes": ["human"]}
    
    def __init__(
        self,
        prices: np.ndarray,
        initial_cash: float = 100000.0,
        transaction_cost: float = 0.001,
        max_position: int = 1000,
        window_size: int = 10,
        reward_type: str = "sharpe",  # sharpe / pnl / returns
    ):
        super().__init__()
        
        self.prices = prices
        self.initial_cash = initial_cash
        self.transaction_cost = transaction_cost
        self.max_position = max_position
        self.window_size = window_size
        self.reward_type = reward_type
        
        self.n_steps = len(prices)
        
        # 动作空间: 3 actions (hold, buy, sell)
        self.action_space = spaces.Discrete(3)
        
        # 状态空间
        obs_dim = 12 + window_size  # 基础特征 + 历史价格
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
        )
        
        # 内部状态
        self.reset()
    
    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        """重置环境"""
        super().reset(seed=seed)
        
        self.current_step = self.window_size
        self.cash = self.initial_cash
        self.position = 0
        self.portfolio_value = self.initial_cash
        self.trades = []
        self.reward_history = []
        
        # 计算技术指标
        self._compute_indicators()
        
        return self._get_observation(), {}
    
    def step(self, action: int) -> TradingStepResult:
        """执行一步交易"""
        price = self.prices[self.current_step]
        prev_value = self.portfolio_value
        
        # 执行交易
        if action == 1:  # 买入
            max_buy = self.cash / price / (1 + self.transaction_cost)
            buy_amount = min(max_buy, self.max_position - self.position)
            if buy_amount > 0:
                cost = buy_amount * price * (1 + self.transaction_cost)
                self.cash -= cost
                self.position += buy_amount
                self.trades.append(("buy", self.current_step, buy_amount, price))
        
        elif action == 2:  # 卖出
            if self.position > 0:
                sell_amount = self.position
                revenue = sell_amount * price * (1 - self.transaction_cost)
                self.cash += revenue
                self.trades.append(("sell", self.current_step, sell_amount, price))
                self.position = 0
        
        # 更新组合价值
        self.portfolio_value = self.cash + self.position * price
        
        # 计算奖励
        reward = self._calculate_reward(prev_value)
        self.reward_history.append(reward)
        
        # 检查终止条件
        self.current_step += 1
        terminated = self.current_step >= self.n_steps - 1
        truncated = self.portfolio_value < self.initial_cash * 0.5  # 爆仓
        
        info = {
            "portfolio_value": self.portfolio_value,
            "cash": self.cash,
            "position": self.position,
            "price": price,
            "step": self.current_step,
        }
        
        return TradingStepResult(
            observation=self._get_observation(),
            reward=reward,
            terminated=terminated,
            truncated=truncated,
            info=info,
        )
    
    def _get_observation(self) -> np.ndarray:
        """获取当前状态"""
        price = self.prices[self.current_step]
        volume = self.volume[self.current_step] if hasattr(self, 'volume') else 1.0
        
        # 归一化价格
        norm_price = (price - self.prices[:self.current_step].min()) / (
            self.prices[:self.current_step].max() - self.prices[:self.current_step].min() + 1e-8
        )
        
        # 归一化成交量
        norm_volume = volume / (self.volume.max() + 1e-8) if hasattr(self, 'volume') else 0.5
        
        # 技术指标
        rsi = self.rsi[self.current_step] if hasattr(self, 'rsi') else 0.5
        macd = self.macd[self.current_step] if hasattr(self, 'macd') else 0.0
        
        # 持仓状态
        position_state = 1.0 if self.position > 0 else 0.0
        
        # 历史价格特征
        start = max(0, self.current_step - self.window_size)
        hist_prices = self.prices[start:self.current_step]
        if len(hist_prices) < self.window_size:
            hist_prices = np.pad(hist_prices, (self.window_size - len(hist_prices), 0))
        
        # 归一化历史价格
        price_min = self.prices[:self.current_step].min()
        price_max = self.prices[:self.current_step].max()
        norm_hist = (hist_prices - price_min) / (price_max - price_min + 1e-8)
        
        # 账户状态
        norm_cash = self.cash / self.initial_cash
        pnl = (self.portfolio_value - self.initial_cash) / self.initial_cash
        
        # 组合观测
        obs = np.array([
            norm_price,
            norm_volume,
            rsi,
            macd,
            position_state,
            *norm_hist,
            norm_cash,
            pnl,
        ], dtype=np.float32)
        
        return obs
    
    def _calculate_reward(self, prev_value: float) -> float:
        """计算奖励"""
        returns = (self.portfolio_value - prev_value) / prev_value
        
        if self.reward_type == "pnl":
            return returns
        elif self.reward_type == "returns":
            return self.portfolio_value / self.initial_cash - 1
        elif self.reward_type == "sharpe":
            if len(self.reward_history) < 10:
                return returns
            rets = np.array(self.reward_history[-50:])
            if rets.std() > 0:
                sharpe = rets.mean() / rets.std() * np.sqrt(252)
                return sharpe * 0.01  # 缩放
            return returns
        return returns
    
    def _compute_indicators(self):
        """计算技术指标"""
        prices = self.prices
        
        # RSI
        delta = np.diff(prices)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = self._ema(gain, 14)
        avg_loss = self._ema(loss, 14)
        rs = avg_gain / (avg_loss + 1e-8)
        self.rsi = 100 - (100 / (1 + rs))
        self.rsi = np.concatenate([[50], self.rsi])
        
        # MACD
        ema12 = self._ema(prices, 12)
        ema26 = self._ema(prices, 26)
        self.macd = ema12 - ema26
        signal = self._ema(self.macd, 9)
        self.macd = self.macd - signal
        
        # 成交量（模拟）
        if not hasattr(self, 'volume'):
            self.volume = np.random.rand(len(prices)) * 1000000 + 500000
    
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """指数移动平均"""
        ema = np.zeros_like(data)
        ema[0] = data[0]
        multiplier = 2 / (period + 1)
        for i in range(1, len(data)):
            ema[i] = data[i] * multiplier + ema[i-1] * (1 - multiplier)
        return ema
    
    def render(self):
        """渲染环境"""
        print(f"Step: {self.current_step}, Price: {self.prices[self.current_step]:.2f}, "
              f"Position: {self.position}, Portfolio: {self.portfolio_value:.2f}")


class PortfolioEnv(TradingEnv):
    """
    多资产组合强化学习环境
    
    支持多只股票的组合交易决策
    """
    
    def __init__(
        self,
        prices_dict: Dict[str, np.ndarray],
        initial_cash: float = 100000.0,
        transaction_cost: float = 0.001,
        max_position_pct: float = 0.3,
        window_size: int = 10,
        reward_type: str = "sharpe",
    ):
        self.prices_dict = prices_dict
        self.assets = list(prices_dict.keys())
        self.n_assets = len(self.assets)
        
        # 统一价格长度
        min_len = min(len(p) for p in prices_dict.values())
        for k in self.assets:
            self.prices_dict[k] = prices_dict[k][:min_len]
        
        # 合并价格数组
        self.combined_prices = np.array([self.prices_dict[k] for k in self.assets])
        
        super().__init__(
            prices=self.combined_prices.mean(axis=0),
            initial_cash=initial_cash,
            transaction_cost=transaction_cost,
            max_position=int(initial_cash * max_position_pct / prices_dict[self.assets[0]][0]),
            window_size=window_size,
            reward_type=reward_type,
        )
        
        # 扩展动作空间：每资产 3 动作
        self.action_space = spaces.Discrete(3 ** self.n_assets)
        
        # 扩展状态空间
        obs_dim = 12 + window_size + self.n_assets * 4
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
        )
        
        self.positions = {asset: 0 for asset in self.assets}
    
    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        self.positions = {asset: 0 for asset in self.assets}
        return super().reset(seed=seed, options=options)
    
    def _get_observation(self) -> np.ndarray:
        """获取多资产状态"""
        base_obs = super()._get_observation()
        
        # 添加各资产特征
        asset_features = []
        for asset in self.assets:
            price = self.prices_dict[asset][self.current_step]
            norm_price = (price - self.prices_dict[asset][:self.current_step].min()) / (
                self.prices_dict[asset][:self.current_step].max() - 
                self.prices_dict[asset][:self.current_step].min() + 1e-8
            )
            position_val = self.positions[asset] * price / self.initial_cash
            asset_features.extend([norm_price, position_val, self.rsi[self.current_step], self.macd[self.current_step]])
        
        return np.concatenate([base_obs, np.array(asset_features, dtype=np.float32)])


class MultiAssetEnv(PortfolioEnv):
    """
    多资产交易环境（简化版）
    
    动作编码：每个资产 3 种动作 (hold/buy/sell)
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _decode_action(self, action: int) -> list:
        """解码动作"""
        actions = []
        for _ in range(self.n_assets):
            actions.append(action % 3)
            action //= 3
        return actions
    
    def step(self, action: int) -> TradingStepResult:
        """执行多资产交易"""
        actions = self._decode_action(action)
        
        for asset, act in zip(self.assets, actions):
            price = self.prices_dict[asset][self.current_step]
            
            if act == 1:  # 买入
                max_buy = self.cash / price / (1 + self.transaction_cost) / self.n_assets
                self.cash -= max_buy * price * (1 + self.transaction_cost)
                self.positions[asset] += max_buy
            
            elif act == 2:  # 卖出
                if self.positions[asset] > 0:
                    self.cash += self.positions[asset] * price * (1 - self.transaction_cost)
                    self.positions[asset] = 0
        
        # 更新组合价值
        self.portfolio_value = self.cash + sum(
            self.positions[asset] * self.prices_dict[asset][self.current_step]
            for asset in self.assets
        )
        
        # 后续逻辑复用父类
        prev_value = self.initial_cash  # 简化
        reward = self._calculate_reward(prev_value)
        
        self.current_step += 1
        terminated = self.current_step >= len(self.prices) - 1
        truncated = self.portfolio_value < self.initial_cash * 0.5
        
        info = {
            "portfolio_value": self.portfolio_value,
            "positions": self.positions.copy(),
        }
        
        return TradingStepResult(
            observation=self._get_observation(),
            reward=reward,
            terminated=terminated,
            truncated=truncated,
            info=info,
        )
