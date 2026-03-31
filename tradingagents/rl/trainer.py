# -*- coding: utf-8 -*-
"""
RL Trainer - 支持 DQN/PPO/A2C 算法训练
"""

import numpy as np
import random
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from collections import deque, namedtuple

# 尝试导入 torch，如果不可用则使用 numpy 实现
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except (ImportError, OSError) as e:
    TORCH_AVAILABLE = False
    torch = None
    nn = None
    optim = None


Transition = namedtuple('Transition', ['state', 'action', 'reward', 'next_state', 'done'])


@dataclass
class TrainingConfig:
    """训练配置"""
    algorithm: str = "dqn"  # dqn / ppo / a2c
    env_name: str = "TradingEnv"
    
    # 训练参数
    episodes: int = 500
    max_steps: int = 1000
    batch_size: int = 64
    learning_rate: float = 0.001
    
    # RL 超参数
    gamma: float = 0.99  # 折扣因子
    epsilon: float = 1.0  # 探索率
    epsilon_decay: float = 0.995
    epsilon_min: float = 0.01
    tau: float = 0.005  # 目标网络软更新率
    
    # PPO/A2C 特有
    clip_eps: float = 0.2
    value_coef: float = 0.5
    entropy_coef: float = 0.01
    ppo_epochs: int = 10
    
    # 设备
    device: str = "auto"
    
    # 日志
    log_interval: int = 10
    save_interval: int = 50
    
    # 保存路径
    save_dir: str = "models/rl"


if TORCH_AVAILABLE:
    class QNetwork(nn.Module):
        """DQN Q 网络"""
        
        def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
            super().__init__()
            self.network = nn.Sequential(
                nn.Linear(state_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, action_dim),
            )
        
        def forward(self, x):
            return self.network(x)
    
    
    class PolicyNetwork(nn.Module):
        """策略网络 (Policy Gradient)"""
        
        def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
            super().__init__()
            self.actor = nn.Sequential(
                nn.Linear(state_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, action_dim),
                nn.Softmax(dim=-1),
            )
            self.critic = nn.Sequential(
                nn.Linear(state_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, 1),
            )
        
        def forward(self, x):
            return self.actor(x), self.critic(x)
    
    
    class DQN:
        """Deep Q-Network"""
        
        def __init__(self, state_dim: int, action_dim: int, config: TrainingConfig):
            self.state_dim = state_dim
            self.action_dim = action_dim
            self.config = config
            
            # 设备
            self.device = torch.device("cuda" if torch.cuda.is_available() and config.device == "auto" else config.device)
            
            # 网络
            self.policy_net = QNetwork(state_dim, action_dim).to(self.device)
            self.target_net = QNetwork(state_dim, action_dim).to(self.device)
            self.target_net.load_state_dict(self.policy_net.state_dict())
            
            self.optimizer = optim.Adam(self.policy_net.parameters(), lr=config.learning_rate)
            
            # 经验回放
            self.memory = deque(maxlen=100000)
            
            # 探索率
            self.epsilon = config.epsilon
        
        def select_action(self, state: np.ndarray, training: bool = True) -> int:
            """选择动作"""
            if training and random.random() < self.epsilon:
                return random.randint(0, self.action_dim - 1)
            
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                q_values = self.policy_net(state_tensor)
                return q_values.argmax(dim=1).item()
        
        def store_transition(self, state, action, reward, next_state, done):
            """存储转换"""
            self.memory.append(Transition(state, action, reward, next_state, done))
        
        def update(self) -> Optional[float]:
            """更新网络"""
            if len(self.memory) < self.config.batch_size:
                return None
            
            batch = random.sample(self.memory, self.config.batch_size)
            
            states = torch.FloatTensor(np.array([t.state for t in batch])).to(self.device)
            actions = torch.LongTensor([t.action for t in batch]).to(self.device)
            rewards = torch.FloatTensor([t.reward for t in batch]).to(self.device)
            next_states = torch.FloatTensor(np.array([t.next_state for t in batch])).to(self.device)
            dones = torch.FloatTensor([t.done for t in batch]).to(self.device)
            
            # Q 值
            q_values = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)
            
            # 目标 Q 值
            with torch.no_grad():
                next_q_values = self.target_net(next_states).max(dim=1)[0]
                target_q = rewards + self.config.gamma * (1 - dones) * next_q_values
            
            # 损失
            loss = nn.MSELoss()(q_values, target_q)
            
            # 更新
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
            self.optimizer.step()
            
            # 软更新目标网络
            for target_param, param in zip(self.target_net.parameters(), self.policy_net.parameters()):
                target_param.data.copy_(self.config.tau * param.data + (1 - self.config.tau) * target_param.data)
            
            # 衰减探索率
            self.epsilon = max(self.config.epsilon_min, self.epsilon * self.config.epsilon_decay)
            
            return loss.item()
        
        def save(self, path: str):
            """保存模型"""
            torch.save({
                'policy_net': self.policy_net.state_dict(),
                'target_net': self.target_net.state_dict(),
                'optimizer': self.optimizer.state_dict(),
                'epsilon': self.epsilon,
            }, path)
        
        def load(self, path: str):
            """加载模型"""
            checkpoint = torch.load(path, map_location=self.device)
            self.policy_net.load_state_dict(checkpoint['policy_net'])
            self.target_net.load_state_dict(checkpoint['target_net'])
            self.optimizer.load_state_dict(checkpoint['optimizer'])
            self.epsilon = checkpoint['epsilon']
    
    
    class PPO:
        """Proximal Policy Optimization"""
        
        def __init__(self, state_dim: int, action_dim: int, config: TrainingConfig):
            self.state_dim = state_dim
            self.action_dim = action_dim
            self.config = config
            
            self.device = torch.device("cuda" if torch.cuda.is_available() and config.device == "auto" else config.device)
            
            self.policy = PolicyNetwork(state_dim, action_dim).to(self.device)
            self.old_policy = PolicyNetwork(state_dim, action_dim).to(self.device)
            self.old_policy.load_state_dict(self.policy.state_dict())
            
            self.optimizer = optim.Adam(self.policy.parameters(), lr=config.learning_rate)
            
            self.buffer = []
        
        def select_action(self, state: np.ndarray, training: bool = True) -> tuple:
            """选择动作并返回概率"""
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                probs, value = self.old_policy(state_tensor)
                dist = torch.distributions.Categorical(probs)
                action = dist.sample()
                log_prob = dist.log_prob(action)
            
            return action.item(), log_prob.item(), value.item()
        
        def store(self, state, action, reward, log_prob, value, done):
            """存储经验"""
            self.buffer.append((state, action, reward, log_prob, value, done))
        
        def update(self) -> Optional[float]:
            """更新策略"""
            if len(self.buffer) < self.config.batch_size:
                return None
            
            # 转换为张量
            states, actions, rewards, log_probs, values, dones = zip(*self.buffer)
            
            states = torch.FloatTensor(np.array(states)).to(self.device)
            actions = torch.LongTensor(actions).to(self.device)
            rewards = torch.FloatTensor(rewards).to(self.device)
            old_log_probs = torch.FloatTensor(log_probs).to(self.device)
            old_values = torch.FloatTensor(values).to(self.device)
            dones = torch.FloatTensor(dones).to(self.device)
            
            # 计算回报
            returns = []
            discounted = 0
            for reward, done in zip(reversed(rewards), reversed(dones)):
                discounted = reward + self.config.gamma * discounted * (1 - done)
                returns.insert(0, discounted)
            returns = torch.FloatTensor(returns).to(self.device)
            
            # 优势估计
            advantages = returns - old_values.detach()
            
            # PPO 更新
            for _ in range(self.config.ppo_epochs):
                probs, values = self.policy(states)
                dist = torch.distributions.Categorical(probs)
                
                new_log_probs = dist.log_prob(actions)
                ratio = torch.exp(new_log_probs - old_log_probs)
                
                # PPO 裁剪
                surr1 = ratio * advantages
                surr2 = torch.clamp(ratio, 1 - self.config.clip_eps, 1 + self.config.clip_eps) * advantages
                policy_loss = -torch.min(surr1, surr2).mean()
                
                # 值函数损失
                value_loss = nn.MSELoss()(values.squeeze(), returns)
                
                # 熵奖励
                entropy = dist.entropy().mean()
                
                # 总损失
                loss = policy_loss + self.config.value_coef * value_loss - self.config.entropy_coef * entropy
                
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.policy.parameters(), 0.5)
                self.optimizer.step()
            
            # 更新旧策略
            self.old_policy.load_state_dict(self.policy.state_dict())
            
            # 清空 buffer
            self.buffer = []
            
            return loss.item()
        
        def save(self, path: str):
            torch.save(self.policy.state_dict(), path)
        
        def load(self, path: str):
            self.policy.load_state_dict(torch.load(path, map_location=self.device))
            self.old_policy.load_state_dict(self.policy.state_dict())
    
    
    class A2C:
        """Advantage Actor-Critic"""
        
        def __init__(self, state_dim: int, action_dim: int, config: TrainingConfig):
            self.state_dim = state_dim
            self.action_dim = action_dim
            self.config = config
            
            self.device = torch.device("cuda" if torch.cuda.is_available() and config.device == "auto" else config.device)
            
            self.policy = PolicyNetwork(state_dim, action_dim).to(self.device)
            self.optimizer = optim.Adam(self.policy.parameters(), lr=config.learning_rate)
            
            self.buffer = []
        
        def select_action(self, state: np.ndarray, training: bool = True) -> tuple:
            """选择动作"""
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            probs, value = self.policy(state_tensor)
            
            dist = torch.distributions.Categorical(probs)
            action = dist.sample()
            log_prob = dist.log_prob(action)
            
            return action.item(), log_prob.item(), value.item()
        
        def store(self, state, action, reward, log_prob, value, done):
            self.buffer.append((state, action, reward, log_prob, value, done))
        
        def update(self) -> Optional[float]:
            """更新"""
            if len(self.buffer) < self.config.batch_size:
                return None
            
            states, actions, rewards, log_probs, values, dones = zip(*self.buffer)
            
            states = torch.FloatTensor(np.array(states)).to(self.device)
            actions = torch.LongTensor(actions).to(self.device)
            rewards = torch.FloatTensor(rewards).to(self.device)
            log_probs = torch.FloatTensor(log_probs).to(self.device)
            values = torch.FloatTensor(values).to(self.device)
            dones = torch.FloatTensor(dones).to(self.device)
            
            # 计算回报和优势
            returns = []
            advantages = []
            discounted = 0
            advantage = 0
            
            for i in reversed(range(len(rewards))):
                reward = rewards[i]
                done = dones[i]
                value = values[i]
                
                if i == len(rewards) - 1:
                    next_value = 0
                else:
                    next_value = values[i + 1]
                
                # TD 目标
                td_target = reward + self.config.gamma * next_value * (1 - done)
                td_error = td_target - value
                
                advantage = td_error + self.config.gamma * 0.99 * advantage * (1 - done)
                advantages.insert(0, advantage)
                returns.insert(0, td_target)
            
            advantages = torch.FloatTensor(advantages).to(self.device)
            returns = torch.FloatTensor(returns).to(self.device)
            
            # 更新
            probs, values = self.policy(states)
            dist = torch.distributions.Categorical(probs)
            
            policy_loss = -(log_probs * advantages.detach()).mean()
            value_loss = nn.MSELoss()(values.squeeze(), returns)
            entropy = dist.entropy().mean()
            
            loss = policy_loss + self.config.value_coef * value_loss - self.config.entropy_coef * entropy
            
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            self.buffer = []
            
            return loss.item()
        
        def save(self, path: str):
            torch.save(self.policy.state_dict(), path)
        
        def load(self, path: str):
            self.policy.load_state_dict(torch.load(path, map_location=self.device))
else:
    # PyTorch 不可用时的替代实现
    class DummyAgent:
        """PyTorch 不可用时的虚拟代理"""
        def __init__(self, *args, **kwargs):
            pass
        def select_action(self, state, training=True):
            return random.randint(0, 2)
        def store_transition(self, *args):
            pass
        def store(self, *args):
            pass
        def update(self):
            return None
        def save(self, path):
            print(f"[INFO] 模型保存: {path} (PyTorch 不可用)")
        def load(self, path):
            print(f"[INFO] 模型加载: {path}")
    
    DQN = DummyAgent
    PPO = DummyAgent
    A2C = DummyAgent


class RLTrainer:
    """强化学习训练器"""
    
    def __init__(self, env, config: Optional[TrainingConfig] = None):
        self.env = env
        self.config = config or TrainingConfig()
        
        # 获取状态和动作维度
        if hasattr(env, 'reset'):
            obs, _ = env.reset()
            self.state_dim = len(obs)
        else:
            self.state_dim = env.observation_space.shape[0]
        
        self.action_dim = env.action_space.n
        
        # 检查 PyTorch 可用性
        if not TORCH_AVAILABLE:
            print("[WARNING] PyTorch 不可用，RL 训练功能受限")
            self.agent = DummyAgent(self.state_dim, self.action_dim, self.config)
            self._train_numpy = self._train_numpy_fallback
            return
        
        # 选择算法
        if self.config.algorithm == "dqn":
            self.agent = DQN(self.state_dim, self.action_dim, self.config)
        elif self.config.algorithm == "ppo":
            self.agent = PPO(self.state_dim, self.action_dim, self.config)
        elif self.config.algorithm == "a2c":
            self.agent = A2C(self.state_dim, self.action_dim, self.config)
        else:
            raise ValueError(f"Unknown algorithm: {self.config.algorithm}")
        
        self.episode_rewards = []
        self.best_reward = float('-inf')
        
    def train(self, episodes: Optional[int] = None) -> Dict[str, List[float]]:
        """训练"""
        if not TORCH_AVAILABLE:
            print("[WARNING] PyTorch 不可用，跳过实际训练")
            return {'rewards': [], 'losses': []}
        
        episodes = episodes or self.config.episodes
        
        results = {
            'rewards': [],
            'losses': [],
            'epsilons': [],
        }
        
        for episode in range(episodes):
            state, _ = self.env.reset()
            total_reward = 0
            losses = []
            
            for step in range(self.config.max_steps):
                # 选择动作
                if self.config.algorithm == "dqn":
                    action = self.agent.select_action(state, training=True)
                    next_state, reward, terminated, truncated, info = self.env.step(action)
                    done = terminated or truncated
                    
                    self.agent.store_transition(state, action, reward, next_state, float(done))
                    loss = self.agent.update()
                
                else:  # PPO / A2C
                    action, log_prob, value = self.agent.select_action(state, training=True)
                    next_state, reward, terminated, truncated, info = self.env.step(action)
                    done = terminated or truncated
                    
                    self.agent.store(state, action, reward, log_prob, value, float(done))
                    loss = self.agent.update()
                
                total_reward += reward
                state = next_state
                
                if done:
                    break
                
                if loss is not None:
                    losses.append(loss)
            
            self.episode_rewards.append(total_reward)
            results['rewards'].append(total_reward)
            results['losses'].append(np.mean(losses) if losses else 0)
            results['epsilons'].append(self.agent.epsilon if hasattr(self.agent, 'epsilon') else 0)
            
            # 记录最佳
            if total_reward > self.best_reward:
                self.best_reward = total_reward
            
            # 日志
            if episode % self.config.log_interval == 0:
                avg_reward = np.mean(self.episode_rewards[-self.config.log_interval:])
                print(f"Episode {episode}/{episodes}: Avg Reward: {avg_reward:.2f}, Best: {self.best_reward:.2f}")
            
            # 保存
            if episode > 0 and episode % self.config.save_interval == 0:
                self.save(f"{self.config.save_dir}/{self.config.algorithm}_ep{episode}.pt")
        
        return results
    
    def _train_numpy_fallback(self, episodes: int) -> Dict:
        """NumPy 回退训练"""
        print("[INFO] 使用随机策略进行训练")
        
        rewards = []
        for episode in range(episodes):
            state, _ = self.env.reset()
            total_reward = 0
            
            for step in range(self.config.max_steps):
                action = random.randint(0, self.action_dim - 1)
                next_state, reward, terminated, truncated, _ = self.env.step(action)
                total_reward += reward
                state = next_state
                
                if terminated or truncated:
                    break
            
            rewards.append(total_reward)
        
        return {'rewards': rewards, 'losses': []}
    
    def evaluate(self, episodes: int = 10) -> Dict[str, float]:
        """评估"""
        eval_rewards = []
        
        for _ in range(episodes):
            state, _ = self.env.reset()
            total_reward = 0
            
            while True:
                action = self.agent.select_action(state, training=False)
                next_state, reward, terminated, truncated, _ = self.env.step(action)
                total_reward += reward
                state = next_state
                
                if terminated or truncated:
                    break
            
            eval_rewards.append(total_reward)
        
        return {
            'mean_reward': np.mean(eval_rewards),
            'std_reward': np.std(eval_rewards),
            'max_reward': np.max(eval_rewards),
            'min_reward': np.min(eval_rewards),
        }
    
    def save(self, path: str):
        """保存模型"""
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.agent.save(path)
        print(f"Model saved to {path}")
    
    def load(self, path: str):
        """加载模型"""
        self.agent.load(path)
        print(f"Model loaded from {path}")