# -*- coding: utf-8 -*-
"""
RL Trainer 模块单元测试

测试范围：
- TrainingConfig 配置类
- DQN 算法
- PPO 算法
- A2C 算法
- RLTrainer 训练器
- 边界条件和异常处理
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 条件导入（处理依赖缺失）
try:
    import numpy as np
    from tradingagents.rl.trainer import (
        TrainingConfig,
        RLTrainer,
        Transition,
        TORCH_AVAILABLE,
    )
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装（numpy/tradingagents）", allow_module_level=True)


class TestTrainingConfig:
    """TrainingConfig 配置类测试"""

    def test_默认配置(self):
        """测试默认配置值"""
        config = TrainingConfig()
        assert config.algorithm == "dqn"
        assert config.env_name == "TradingEnv"
        assert config.episodes == 500
        assert config.max_steps == 1000
        assert config.batch_size == 64
        assert config.learning_rate == 0.001
        assert config.gamma == 0.99
        assert config.epsilon == 1.0
        assert config.epsilon_decay == 0.995
        assert config.epsilon_min == 0.01
        assert config.tau == 0.005

    def test_自定义配置(self):
        """测试自定义配置"""
        config = TrainingConfig(
            algorithm="ppo",
            episodes=100,
            batch_size=32,
            learning_rate=0.0005,
        )
        assert config.algorithm == "ppo"
        assert config.episodes == 100
        assert config.batch_size == 32
        assert config.learning_rate == 0.0005

    def test_ppo配置(self):
        """测试PPO特有配置"""
        config = TrainingConfig()
        assert config.clip_eps == 0.2
        assert config.value_coef == 0.5
        assert config.entropy_coef == 0.01
        assert config.ppo_epochs == 10


class TestTransition:
    """Transition 数据结构测试"""

    def test_创建转换(self):
        """测试创建Transition"""
        state = np.array([1, 2, 3])
        action = 1
        reward = 10.0
        next_state = np.array([2, 3, 4])
        done = False

        t = Transition(state, action, reward, next_state, done)
        assert t.state is state
        assert t.action == 1
        assert t.reward == 10.0
        assert t.next_state is next_state
        assert t.done is False


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch 未安装")
class TestDQN:
    """DQN 算法测试"""

    def setup_method(self):
        """设置测试环境"""
        from tradingagents.rl.trainer import DQN
        config = TrainingConfig(
            algorithm="dqn",
            episodes=10,
            batch_size=4,
        )
        self.dqn = DQN(state_dim=10, action_dim=3, config=config)

    def test_初始化(self):
        """测试DQN初始化"""
        assert self.dqn.state_dim == 10
        assert self.dqn.action_dim == 3
        assert self.dqn.epsilon == 1.0

    def test_选择动作_训练模式(self):
        """测试训练模式下选择动作"""
        state = np.random.randn(10)
        action = self.dqn.select_action(state, training=True)
        assert 0 <= action < 3

    def test_选择动作_评估模式(self):
        """测试评估模式下选择动作"""
        state = np.random.randn(10)
        action = self.dqn.select_action(state, training=False)
        assert 0 <= action < 3

    def test_存储转换(self):
        """测试存储转换"""
        state = np.random.randn(10)
        action = 1
        reward = 5.0
        next_state = np.random.randn(10)
        done = False

        self.dqn.store_transition(state, action, reward, next_state, done)
        assert len(self.dqn.memory) == 1

    def test_更新_内存不足(self):
        """测试内存不足时更新返回None"""
        result = self.dqn.update()
        assert result is None

    def test_更新_有足够数据(self):
        """测试有足够数据时更新"""
        for i in range(10):
            state = np.random.randn(10)
            self.dqn.store_transition(state, i % 3, 1.0, np.random.randn(10), False)

        loss = self.dqn.update()
        assert loss is not None
        assert isinstance(loss, float)

    def test_保存和加载(self, tmp_path):
        """测试保存和加载模型"""
        save_path = str(tmp_path / "dqn_model.pt")
        self.dqn.save(save_path)

        from tradingagents.rl.trainer import DQN
        config = TrainingConfig()
        dqn2 = DQN(state_dim=10, action_dim=3, config=config)
        dqn2.load(save_path)
        assert dqn2.epsilon == self.dqn.epsilon


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch 未安装")
class TestPPO:
    """PPO 算法测试"""

    def setup_method(self):
        """设置测试环境"""
        from tradingagents.rl.trainer import PPO
        config = TrainingConfig(
            algorithm="ppo",
            episodes=10,
            batch_size=4,
        )
        self.ppo = PPO(state_dim=10, action_dim=3, config=config)

    def test_初始化(self):
        """测试PPO初始化"""
        assert self.ppo.state_dim == 10
        assert self.ppo.action_dim == 3
        assert len(self.ppo.buffer) == 0

    def test_选择动作(self):
        """测试选择动作"""
        state = np.random.randn(10)
        action, log_prob, value = self.ppo.select_action(state)
        assert 0 <= action < 3
        assert isinstance(log_prob, float)
        assert isinstance(value, float)

    def test_存储经验(self):
        """测试存储经验"""
        state = np.random.randn(10)
        self.ppo.store(state, 1, 5.0, 0.5, 1.0, False)
        assert len(self.ppo.buffer) == 1

    def test_更新_内存不足(self):
        """测试内存不足时更新返回None"""
        result = self.ppo.update()
        assert result is None

    def test_保存和加载(self, tmp_path):
        """测试保存和加载模型"""
        save_path = str(tmp_path / "ppo_model.pt")
        self.ppo.save(save_path)

        from tradingagents.rl.trainer import PPO
        config = TrainingConfig()
        ppo2 = PPO(state_dim=10, action_dim=3, config=config)
        ppo2.load(save_path)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch 未安装")
class TestA2C:
    """A2C 算法测试"""

    def setup_method(self):
        """设置测试环境"""
        from tradingagents.rl.trainer import A2C
        config = TrainingConfig(
            algorithm="a2c",
            episodes=10,
            batch_size=4,
        )
        self.a2c = A2C(state_dim=10, action_dim=3, config=config)

    def test_初始化(self):
        """测试A2C初始化"""
        assert self.a2c.state_dim == 10
        assert self.a2c.action_dim == 3

    def test_选择动作(self):
        """测试选择动作"""
        state = np.random.randn(10)
        action, log_prob, value = self.a2c.select_action(state)
        assert 0 <= action < 3
        assert isinstance(log_prob, float)
        assert isinstance(value, float)

    def test_存储和更新(self):
        """测试存储和更新"""
        for i in range(10):
            state = np.random.randn(10)
            self.a2c.store(state, i % 3, 1.0, 0.5, 1.0, False)

        loss = self.a2c.update()
        assert loss is not None

    def test_保存和加载(self, tmp_path):
        """测试保存和加载模型"""
        save_path = str(tmp_path / "a2c_model.pt")
        self.a2c.save(save_path)

        from tradingagents.rl.trainer import A2C
        config = TrainingConfig()
        a2c2 = A2C(state_dim=10, action_dim=3, config=config)
        a2c2.load(save_path)


class TestDummyAgent:
    """DummyAgent 测试（PyTorch不可用时）"""

    def test_选择动作(self):
        """测试选择动作"""
        from tradingagents.rl.trainer import DummyAgent
        agent = DummyAgent()
        action = agent.select_action(np.random.randn(10))
        assert 0 <= action < 3

    def test_保存加载无异常(self, tmp_path):
        """测试保存加载不抛出异常"""
        from tradingagents.rl.trainer import DummyAgent
        agent = DummyAgent()
        save_path = str(tmp_path / "dummy.pt")
        agent.save(save_path)  # 不应抛出异常
        agent.load(save_path)  # 不应抛出异常


class TestRLTrainer:
    """RLTrainer 训练器测试"""

    def _create_mock_env(self):
        """创建模拟环境"""
        env = Mock()
        env.reset.return_value = (np.random.randn(10), {})
        env.step.return_value = (np.random.randn(10), 1.0, False, False, {})
        env.observation_space = Mock()
        env.observation_space.shape = (10,)
        env.action_space = Mock()
        env.action_space.n = 3
        return env

    @pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch 未安装")
    def test_初始化_dqn(self):
        """测试使用DQN算法初始化"""
        env = self._create_mock_env()
        config = TrainingConfig(algorithm="dqn", episodes=5)
        trainer = RLTrainer(env, config)
        assert trainer.config.algorithm == "dqn"
        assert trainer.state_dim == 10
        assert trainer.action_dim == 3

    @pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch 未安装")
    def test_初始化_ppo(self):
        """测试使用PPO算法初始化"""
        env = self._create_mock_env()
        config = TrainingConfig(algorithm="ppo", episodes=5)
        trainer = RLTrainer(env, config)
        assert trainer.config.algorithm == "ppo"

    @pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch 未安装")
    def test_初始化_a2c(self):
        """测试使用A2C算法初始化"""
        env = self._create_mock_env()
        config = TrainingConfig(algorithm="a2c", episodes=5)
        trainer = RLTrainer(env, config)
        assert trainer.config.algorithm == "a2c"

    @pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch 未安装")
    def test_初始化_未知算法(self):
        """测试使用未知算法抛出异常"""
        env = self._create_mock_env()
        config = TrainingConfig(algorithm="unknown", episodes=5)
        with pytest.raises(ValueError):
            RLTrainer(env, config)

    @pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch 未安装")
    def test_训练_少量轮次(self):
        """测试训练少量轮次"""
        env = self._create_mock_env()
        config = TrainingConfig(algorithm="dqn", episodes=2, max_steps=5, batch_size=4)
        trainer = RLTrainer(env, config)

        results = trainer.train(episodes=2)
        assert 'rewards' in results
        assert 'losses' in results
        assert len(results['rewards']) == 2

    def test_评估(self):
        """测试评估"""
        env = self._create_mock_env()
        config = TrainingConfig(episodes=2)

        if not TORCH_AVAILABLE:
            pytest.skip("PyTorch 未安装")

        trainer = RLTrainer(env, config)
        result = trainer.evaluate(episodes=2)
        assert 'mean_reward' in result
        assert 'std_reward' in result
        assert 'max_reward' in result
        assert 'min_reward' in result

    def test_保存和加载(self, tmp_path):
        """测试保存和加载模型"""
        env = self._create_mock_env()
        config = TrainingConfig(episodes=2)

        if not TORCH_AVAILABLE:
            pytest.skip("PyTorch 未安装")

        trainer = RLTrainer(env, config)
        save_path = str(tmp_path / "trainer_model.pt")
        trainer.save(save_path)

        trainer2 = RLTrainer(env, config)
        trainer2.load(save_path)
