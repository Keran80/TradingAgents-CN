# -*- coding: utf-8 -*-
"""
RL Environment 模块单元测试

测试范围：
- TradingEnv 环境
- PortfolioEnv 环境
- MultiAssetEnv 环境
- 状态空间/动作空间
- 奖励计算
- 边界条件和异常处理
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 条件导入（处理依赖缺失）
try:
    import numpy as np
    from tradingagents.rl.env import (
        TradingEnv,
        PortfolioEnv,
        MultiAssetEnv,
        TradingStepResult,
    )
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装（numpy/gymnasium）", allow_module_level=True)


class TestTradingStepResult:
    """TradingStepResult 数据结构测试"""

    def test_创建结果(self):
        """测试创建交易步骤结果"""
        obs = np.array([1, 2, 3])
        result = TradingStepResult(
            observation=obs,
            reward=5.0,
            terminated=False,
            truncated=False,
            info={"test": "value"}
        )
        np.testing.assert_array_equal(result.observation, obs)
        assert result.reward == 5.0
        assert result.terminated is False
        assert result.truncated is False
        assert result.info["test"] == "value"


class TestTradingEnv:
    """TradingEnv 交易环境测试"""

    def setup_method(self):
        """设置测试环境"""
        np.random.seed(42)
        self.prices = np.random.randn(100).cumsum() + 100  # 100个价格点

    def test_初始化_默认参数(self):
        """测试使用默认参数初始化"""
        env = TradingEnv(prices=self.prices)
        assert env.initial_cash == 100000.0
        assert env.transaction_cost == 0.001
        assert env.max_position == 1000
        assert env.window_size == 10
        assert env.reward_type == "sharpe"
        assert env.action_space.n == 3

    def test_初始化_自定义参数(self):
        """测试使用自定义参数初始化"""
        env = TradingEnv(
            prices=self.prices,
            initial_cash=50000.0,
            transaction_cost=0.002,
            max_position=500,
            window_size=20,
            reward_type="pnl",
        )
        assert env.initial_cash == 50000.0
        assert env.transaction_cost == 0.002
        assert env.max_position == 500
        assert env.window_size == 20
        assert env.reward_type == "pnl"

    def test_重置环境(self):
        """测试重置环境"""
        env = TradingEnv(prices=self.prices)
        obs, info = env.reset()
        assert obs is not None
        assert len(obs) == 12 + env.window_size  # 基础特征 + 历史价格
        assert isinstance(info, dict)

    def test_重置环境_带种子(self):
        """测试重置环境带种子"""
        env = TradingEnv(prices=self.prices)
        obs1, _ = env.reset(seed=42)
        obs2, _ = env.reset(seed=42)
        np.testing.assert_array_almost_equal(obs1, obs2)

    def test_step_持有动作(self):
        """测试执行持有动作"""
        env = TradingEnv(prices=self.prices)
        env.reset()
        result = env.step(0)  # hold
        assert result is not None
        assert isinstance(result.reward, float)
        assert result.info is not None

    def test_step_买入动作(self):
        """测试执行买入动作"""
        env = TradingEnv(prices=self.prices)
        env.reset()
        result = env.step(1)  # buy
        assert result is not None
        assert result.info["position"] >= 0

    def test_step_卖出动作(self):
        """测试执行卖出动作"""
        env = TradingEnv(prices=self.prices)
        env.reset()
        env.step(1)  # 先买入
        result = env.step(2)  # 卖出
        assert result is not None

    def test_step_终止条件(self):
        """测试终止条件"""
        short_prices = np.random.randn(20).cumsum() + 100
        env = TradingEnv(prices=short_prices, window_size=10)
        env.reset()

        # 逐步执行直到终止
        for _ in range(15):
            result = env.step(0)
            if result.terminated or result.truncated:
                break

        assert result.terminated or result.truncated

    def test_step_爆仓条件(self):
        """测试爆仓终止条件"""
        # 创建急剧下跌的价格序列
        crash_prices = np.array([100] * 50 + [90] * 50 + [50] * 50)
        env = TradingEnv(prices=crash_prices, initial_cash=100000.0)
        env.reset()

        # 持续买入导致爆仓
        for _ in range(50):
            result = env.step(1)  # 持续买入
            if result.truncated:
                break

        # 爆仓时 portfolio_value < initial_cash * 0.5
        if result.truncated:
            assert result.info["portfolio_value"] < 50000.0

    def test_观察空间形状(self):
        """测试观察空间形状"""
        env = TradingEnv(prices=self.prices, window_size=10)
        obs, _ = env.reset()
        expected_dim = 12 + env.window_size
        assert len(obs) == expected_dim

    def test_奖励类型_pnl(self):
        """测试PNL奖励类型"""
        env = TradingEnv(prices=self.prices, reward_type="pnl")
        env.reset()
        result = env.step(0)
        assert isinstance(result.reward, float)

    def test_奖励类型_returns(self):
        """测试Returns奖励类型"""
        env = TradingEnv(prices=self.prices, reward_type="returns")
        env.reset()
        result = env.step(0)
        assert isinstance(result.reward, float)

    def test_奖励类型_sharpe(self):
        """测试Sharpe奖励类型"""
        env = TradingEnv(prices=self.prices, reward_type="sharpe")
        env.reset()
        result = env.step(0)
        assert isinstance(result.reward, float)

    def test_render(self, capsys):
        """测试渲染环境"""
        env = TradingEnv(prices=self.prices)
        env.reset()
        env.step(0)
        env.render()
        captured = capsys.readouterr()
        assert "Step:" in captured.out
        assert "Price:" in captured.out


class TestPortfolioEnv:
    """PortfolioEnv 多资产组合环境测试"""

    def setup_method(self):
        """设置测试环境"""
        np.random.seed(42)
        self.prices_dict = {
            'stock_A': np.random.randn(100).cumsum() + 100,
            'stock_B': np.random.randn(100).cumsum() + 105,
            'stock_C': np.random.randn(100).cumsum() + 110,
        }

    def test_初始化(self):
        """测试初始化"""
        env = PortfolioEnv(prices_dict=self.prices_dict)
        assert env.n_assets == 3
        assert 'stock_A' in env.assets
        assert 'stock_B' in env.assets
        assert 'stock_C' in env.assets

    def test_动作空间扩展(self):
        """测试动作空间扩展"""
        env = PortfolioEnv(prices_dict=self.prices_dict)
        # 3资产，每资产3动作，总共 3^3 = 27 动作
        expected_actions = 3 ** 3
        assert env.action_space.n == expected_actions

    def test_观察空间扩展(self):
        """测试观察空间扩展"""
        env = PortfolioEnv(prices_dict=self.prices_dict)
        obs, _ = env.reset()
        expected_dim = 12 + env.window_size + env.n_assets * 4
        assert len(obs) == expected_dim

    def test_重置环境(self):
        """测试重置环境"""
        env = PortfolioEnv(prices_dict=self.prices_dict)
        obs, info = env.reset()
        assert obs is not None
        assert env.positions == {'stock_A': 0, 'stock_B': 0, 'stock_C': 0}

    def test_步骤执行(self):
        """测试执行步骤"""
        env = PortfolioEnv(prices_dict=self.prices_dict)
        env.reset()
        result = env.step(0)  # 所有资产持有
        assert result is not None
        assert result.info is not None


class TestMultiAssetEnv:
    """MultiAssetEnv 多资产交易环境测试"""

    def setup_method(self):
        """设置测试环境"""
        np.random.seed(42)
        self.prices_dict = {
            'asset_1': np.random.randn(100).cumsum() + 100,
            'asset_2': np.random.randn(100).cumsum() + 105,
        }

    def test_初始化(self):
        """测试初始化"""
        env = MultiAssetEnv(prices_dict=self.prices_dict)
        assert env.n_assets == 2

    def test_解码动作(self):
        """测试动作解码"""
        env = MultiAssetEnv(prices_dict=self.prices_dict)
        actions = env._decode_action(0)
        assert len(actions) == 2
        assert all(0 <= a < 3 for a in actions)

    def test_解码动作_多种组合(self):
        """测试多种动作组合"""
        env = MultiAssetEnv(prices_dict=self.prices_dict)
        for action in [0, 1, 5, 10, 20]:
            actions = env._decode_action(action)
            assert len(actions) == 2
            assert all(0 <= a < 3 for a in actions)

    def test_步骤执行(self):
        """测试执行步骤"""
        env = MultiAssetEnv(prices_dict=self.prices_dict)
        env.reset()
        result = env.step(0)
        assert result is not None
        assert "portfolio_value" in result.info
        assert "positions" in result.info

    def test_步骤执行_买入动作(self):
        """测试买入动作"""
        env = MultiAssetEnv(prices_dict=self.prices_dict)
        env.reset()
        result = env.step(1)  # 买入
        assert result is not None
        # 检查仓位变化
        for asset in env.assets:
            assert env.positions[asset] >= 0

    def test_步骤执行_卖出动作(self):
        """测试卖出动作"""
        env = MultiAssetEnv(prices_dict=self.prices_dict)
        env.reset()
        env.step(1)  # 先买入
        result = env.step(2)  # 再卖出
        assert result is not None
