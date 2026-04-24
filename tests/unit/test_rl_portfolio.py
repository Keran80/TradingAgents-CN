# -*- coding: utf-8 -*-
"""
Portfolio RL 模块单元测试

测试范围：
- PortfolioConfig 配置类
- PortfolioActor 网络
- PortfolioCritic 网络
- PortfolioRLAgent 主类
- 组合权重预测
- 再平衡逻辑
- 统计指标计算
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 条件导入（处理依赖缺失）
try:
    import numpy as np
    import pandas as pd
    from tradingagents.rl.portfolio_rl import (
        PortfolioConfig,
        PortfolioRLAgent,
        create_portfolio_rl,
        TORCH_AVAILABLE,
    )
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装（numpy/pandas/tradingagents）", allow_module_level=True)


class TestPortfolioConfig:
    """PortfolioConfig 配置类测试"""

    def test_默认配置(self):
        """测试默认配置值"""
        config = PortfolioConfig(assets=['A', 'B'])
        assert config.assets == ['A', 'B']
        assert config.initial_cash == 100000.0
        assert config.max_position_pct == 0.3
        assert config.transaction_cost == 0.001
        assert config.rebalance_freq == "weekly"
        assert config.risk_aversion == 1.0
        assert config.rl_algorithm == "ppo"
        assert config.train_episodes == 200
        assert config.eval_episodes == 10

    def test_自定义配置(self):
        """测试自定义配置"""
        config = PortfolioConfig(
            assets=['X', 'Y', 'Z'],
            initial_cash=50000.0,
            max_position_pct=0.5,
            rl_algorithm="dqn",
            train_episodes=100,
        )
        assert config.assets == ['X', 'Y', 'Z']
        assert config.initial_cash == 50000.0
        assert config.max_position_pct == 0.5
        assert config.rl_algorithm == "dqn"
        assert config.train_episodes == 100


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch 未安装")
class TestPortfolioActor:
    """PortfolioActor 网络测试"""

    def test_初始化(self):
        """测试初始化"""
        from tradingagents.rl.portfolio_rl import PortfolioActor
        actor = PortfolioActor(state_dim=10, n_assets=4, hidden_dim=64)
        assert actor.n_assets == 4

    def test_前向传播(self):
        """测试前向传播"""
        from tradingagents.rl.portfolio_rl import PortfolioActor
        import torch

        actor = PortfolioActor(state_dim=10, n_assets=4, hidden_dim=64)
        x = torch.randn(2, 10)  # batch_size=2
        weights, risk = actor(x)

        assert weights.shape == (2, 4)
        assert risk.shape == (2, 1)

    def test_权重归一化(self):
        """测试权重归一化"""
        from tradingagents.rl.portfolio_rl import PortfolioActor
        import torch

        actor = PortfolioActor(state_dim=10, n_assets=4, hidden_dim=64)
        x = torch.randn(1, 10)
        weights, risk = actor(x)

        # Softmax 输出应该归一化
        assert torch.allclose(weights.sum(dim=-1), torch.tensor([1.0]))

    def test_风险输出范围(self):
        """测试风险输出在[0,1]范围内"""
        from tradingagents.rl.portfolio_rl import PortfolioActor
        import torch

        actor = PortfolioActor(state_dim=10, n_assets=4, hidden_dim=64)
        x = torch.randn(5, 10)
        weights, risk = actor(x)

        assert (risk >= 0).all()
        assert (risk <= 1).all()


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch 未安装")
class TestPortfolioCritic:
    """PortfolioCritic 网络测试"""

    def test_初始化(self):
        """测试初始化"""
        from tradingagents.rl.portfolio_rl import PortfolioCritic
        critic = PortfolioCritic(state_dim=10, hidden_dim=64)
        assert critic is not None

    def test_前向传播(self):
        """测试前向传播"""
        from tradingagents.rl.portfolio_rl import PortfolioCritic
        import torch

        critic = PortfolioCritic(state_dim=10, hidden_dim=64)
        x = torch.randn(2, 10)
        value = critic(x)

        assert value.shape == (2, 1)


class TestPortfolioRLAgent:
    """PortfolioRLAgent 主类测试"""

    def setup_method(self):
        """设置测试环境"""
        np.random.seed(42)
        self.price_data = {
            'stock_A': np.random.randn(100).cumsum() + 100,
            'stock_B': np.random.randn(100).cumsum() + 105,
        }

    @pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch 未安装")
    def test_初始化(self):
        """测试初始化"""
        config = PortfolioConfig(
            assets=['stock_A', 'stock_B'],
            train_episodes=5,
        )
        agent = PortfolioRLAgent(config, self.price_data)
        assert agent.config == config
        assert agent.is_trained is False
        assert agent.weights is None

    @pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch 未安装")
    def test_未训练时预测等权重(self):
        """测试未训练时返回等权重"""
        config = PortfolioConfig(
            assets=['stock_A', 'stock_B'],
            train_episodes=5,
        )
        agent = PortfolioRLAgent(config, self.price_data)
        market_state = np.random.randn(10)
        weights = agent.predict_weights(market_state)

        expected_weights = np.ones(2) / 2
        np.testing.assert_array_almost_equal(weights, expected_weights)

    def test_action_to_weights_基础动作0(self):
        """测试动作0转换为等权重"""
        config = PortfolioConfig(
            assets=['A', 'B', 'C'],
            train_episodes=5,
        )
        agent = PortfolioRLAgent(config, self.price_data)
        weights = agent._action_to_weights(0)

        assert len(weights) == 3
        assert np.allclose(weights.sum(), 1.0)

    def test_action_to_weights_超配风险(self):
        """测试动作1超配风险资产"""
        config = PortfolioConfig(
            assets=['A', 'B', 'C'],
            train_episodes=5,
        )
        agent = PortfolioRLAgent(config, self.price_data)
        weights = agent._action_to_weights(1)

        assert len(weights) == 3
        assert np.allclose(weights.sum(), 1.0)

    def test_action_to_weights_低配风险(self):
        """测试动作2低配风险资产"""
        config = PortfolioConfig(
            assets=['A', 'B', 'C'],
            train_episodes=5,
        )
        agent = PortfolioRLAgent(config, self.price_data)
        weights = agent._action_to_weights(2)

        assert len(weights) == 3
        assert np.allclose(weights.sum(), 1.0)

    def test_rebalance_无需调整(self):
        """测试无需调仓情况"""
        config = PortfolioConfig(
            assets=['A', 'B'],
            train_episodes=5,
        )
        agent = PortfolioRLAgent(config, self.price_data)
        current = np.array([0.5, 0.5])
        target = np.array([0.5, 0.5])

        new_weights, trades = agent.rebalance(current, target, threshold=0.05)
        np.testing.assert_array_equal(new_weights, target)
        assert len(trades) == 0

    def test_rebalance_需要调整(self):
        """测试需要调仓情况"""
        config = PortfolioConfig(
            assets=['A', 'B'],
            train_episodes=5,
        )
        agent = PortfolioRLAgent(config, self.price_data)
        current = np.array([0.5, 0.5])
        target = np.array([0.7, 0.3])

        new_weights, trades = agent.rebalance(current, target, threshold=0.05)
        np.testing.assert_array_equal(new_weights, target)
        assert len(trades) > 0

    def test_rebalance_多个资产(self):
        """测试多资产调仓"""
        config = PortfolioConfig(
            assets=['A', 'B', 'C'],
            train_episodes=5,
        )
        agent = PortfolioRLAgent(config, self.price_data)
        current = np.array([0.33, 0.33, 0.34])
        target = np.array([0.5, 0.3, 0.2])

        new_weights, trades = agent.rebalance(current, target, threshold=0.05)
        assert len(trades) >= 2  # 至少两个资产需要调整

    def test_get_portfolio_stats(self):
        """测试计算组合统计指标"""
        config = PortfolioConfig(
            assets=['A', 'B'],
            train_episodes=5,
        )
        agent = PortfolioRLAgent(config, self.price_data)

        # 模拟收益率序列
        returns = pd.Series(np.random.randn(100) * 0.01)
        stats = agent.get_portfolio_stats(returns)

        assert "annual_return" in stats
        assert "annual_vol" in stats
        assert "sharpe" in stats
        assert "max_drawdown" in stats
        assert "calmar" in stats
        assert "win_rate" in stats
        assert "total_return" in stats

    def test_get_portfolio_stats_正值收益(self):
        """测试正值收益统计"""
        config = PortfolioConfig(
            assets=['A', 'B'],
            train_episodes=5,
        )
        agent = PortfolioRLAgent(config, self.price_data)

        returns = pd.Series(np.random.randn(100) * 0.01 + 0.001)  # 轻微正值
        stats = agent.get_portfolio_stats(returns)

        assert stats["win_rate"] > 0
        assert stats["win_rate"] <= 1.0

    def test_evaluate_未训练(self):
        """测试未训练时评估"""
        config = PortfolioConfig(
            assets=['A', 'B'],
            train_episodes=5,
        )
        agent = PortfolioRLAgent(config, self.price_data)
        result = agent.evaluate()

        assert result["status"] == "not_trained"

    def test_save_and_load(self, tmp_path):
        """测试保存和加载"""
        if not TORCH_AVAILABLE:
            pytest.skip("PyTorch 未安装")

        config = PortfolioConfig(
            assets=['stock_A', 'stock_B'],
            train_episodes=5,
        )
        agent = PortfolioRLAgent(config, self.price_data)

        save_path = str(tmp_path / "portfolio_rl.pt")
        agent.save(save_path)

        agent2 = PortfolioRLAgent(config, self.price_data)
        agent2.load(save_path)
        assert agent2.is_trained is True


class TestCreatePortfolioRL:
    """create_portfolio_rl 工厂函数测试"""

    def setup_method(self):
        """设置测试环境"""
        np.random.seed(42)
        self.price_data = {
            'asset_A': np.random.randn(100).cumsum() + 100,
            'asset_B': np.random.randn(100).cumsum() + 105,
        }

    @pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch 未安装")
    def test_创建实例(self):
        """测试创建组合RL代理"""
        agent = create_portfolio_rl(
            assets=['asset_A', 'asset_B'],
            price_data=self.price_data,
            initial_cash=50000.0,
            algorithm="ppo",
            train_episodes=10,
        )
        assert isinstance(agent, PortfolioRLAgent)
        assert agent.config.assets == ['asset_A', 'asset_B']
        assert agent.config.initial_cash == 50000.0
        assert agent.config.rl_algorithm == "ppo"
        assert agent.config.train_episodes == 10
