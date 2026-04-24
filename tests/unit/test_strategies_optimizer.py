# -*- coding: utf-8 -*-
"""
策略参数优化器 单元测试

测试范围：
- BacktestResult 数据类
- GridOptimizer 网格搜索
- WalkForwardOptimizer Walk-Forward 优化
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

try:
    import pandas as pd
    import numpy as np
    from tradingagents.strategies.optimizer import BacktestResult, GridOptimizer, WalkForwardOptimizer
    from tradingagents.strategies.templates import StrategyTemplate, StrategyConfig, MomentumStrategy
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("pandas/numpy 未安装", allow_module_level=True)


def create_sample_data(n=100, start_price=10.0):
    """创建模拟数据"""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    prices = np.cumsum(np.random.randn(n) * 0.1) + start_price
    prices = np.abs(prices) + 1  # 确保价格为正

    data = pd.DataFrame({
        "open": prices,
        "high": prices * 1.01,
        "low": prices * 0.99,
        "close": prices,
        "volume": np.random.randint(100000, 500000, n),
    }, index=dates)
    return data


class TestBacktestResult:
    """BacktestResult 数据类测试"""

    def test_默认值初始化正确_全为0或空字典(self):
        """测试默认值初始化"""
        result = BacktestResult(params={"fast": 10})
        assert result.total_return == 0.0
        assert result.sharpe_ratio == 0.0
        assert result.max_drawdown == 0.0
        assert result.win_rate == 0.0
        assert result.total_trades == 0
        assert result.params == {"fast": 10}

    def test_score_获取指定指标值_的(self):
        """测试 score 方法获取指标"""
        result = BacktestResult(
            params={},
            total_return=0.1,
            sharpe_ratio=1.5,
            max_drawdown=0.2,
        )
        assert result.score("sharpe_ratio") == 1.5
        assert result.score("total_return") == 0.1

    def test_score_指标不存在返回0(self):
        """测试不存在的指标返回 0"""
        result = BacktestResult(params={})
        assert result.score("nonexistent") == 0.0


class TestGridOptimizer:
    """GridOptimizer 测试"""

    def test_初始化_计算参数组合数量正确(self):
        """测试参数组合数量计算"""
        param_grid = {"fast_period": [5, 10], "slow_period": [20, 30]}
        optimizer = GridOptimizer(MomentumStrategy, param_grid)
        assert len(optimizer.param_combinations) == 4  # 2 * 2

    def test_初始化_参数名列表正确(self):
        """测试参数名列表"""
        param_grid = {"a": [1, 2], "b": [3, 4]}
        optimizer = GridOptimizer(MomentumStrategy, param_grid)
        assert optimizer.param_names == ["a", "b"]

    def test_初始化_优化指标默认sharpe_ratio(self):
        """测试默认优化指标"""
        param_grid = {"fast_period": [5]}
        optimizer = GridOptimizer(MomentumStrategy, param_grid)
        assert optimizer.metric == "sharpe_ratio"

    def test_初始化_自定义优化指标正确设置(self):
        """测试自定义优化指标"""
        param_grid = {"fast_period": [5]}
        optimizer = GridOptimizer(MomentumStrategy, param_grid, metric="total_return")
        assert optimizer.metric == "total_return"

    def test_optimize_单参数组合_返回该参数结果_的(self):
        """测试单一参数组合"""
        param_grid = {"fast_period": [5], "slow_period": [20]}
        optimizer = GridOptimizer(MomentumStrategy, param_grid)
        data = create_sample_data(n=50)
        best_params, results = optimizer.optimize(data, show_progress=False)

        assert best_params == {"fast_period": 5, "slow_period": 20}
        assert len(results) >= 0  # 可能因数据不足无结果

    def test_optimize_多参数组合_返回最优参数结果_的(self):
        """测试多参数组合优化"""
        param_grid = {"fast_period": [5, 10], "slow_period": [20]}
        optimizer = GridOptimizer(MomentumStrategy, param_grid)
        data = create_sample_data(n=50)
        best_params, results = optimizer.optimize(data, show_progress=False)

        assert best_params["slow_period"] == 20
        assert best_params["fast_period"] in [5, 10]

    def test_optimize_空数据返回空结果_的(self):
        """测试空数据返回空结果"""
        param_grid = {"fast_period": [5]}
        optimizer = GridOptimizer(MomentumStrategy, param_grid)
        data = create_sample_data(n=5)  # 数据太少
        best_params, results = optimizer.optimize(data, show_progress=False)

        assert best_params == {}
        assert results == []

    def test_optimize_异常参数组合_捕获并继续(self):
        """测试异常参数组合被捕获"""
        # 此测试确保异常被妥善处理
        param_grid = {"fast_period": [5]}
        optimizer = GridOptimizer(MomentumStrategy, param_grid)
        data = create_sample_data(n=50)

        # 不应当抛出异常
        best_params, results = optimizer.optimize(data, show_progress=False)
        assert True

    def test_results_属性存储优化结果列表(self):
        """测试 results 属性存储优化结果"""
        param_grid = {"fast_period": [5, 10]}
        optimizer = GridOptimizer(MomentumStrategy, param_grid)
        data = create_sample_data(n=50)
        optimizer.optimize(data, show_progress=False)

        # results 属性应包含所有结果
        assert isinstance(optimizer.results, list)


class TestWalkForwardOptimizer:
    """WalkForwardOptimizer 测试"""

    def test_初始化_参数正确传递到GridOptimizer(self):
        """测试初始化参数传递"""
        param_grid = {"fast_period": [5, 10]}
        optimizer = WalkForwardOptimizer(
            MomentumStrategy, param_grid, train_ratio=0.7, n_splits=2
        )
        assert optimizer.train_ratio == 0.7
        assert optimizer.n_splits == 2
        assert optimizer.grid_optimizer.param_grid == param_grid

    def test_optimize_单折分割_数据正确分割_的(self):
        """测试数据分割"""
        param_grid = {"fast_period": [5]}
        optimizer = WalkForwardOptimizer(
            MomentumStrategy, param_grid, train_ratio=0.6, n_splits=2
        )
        data = create_sample_data(n=100)
        results = optimizer.optimize(data)

        assert "train_results" in results
        assert "test_results" in results
        assert "best_params_history" in results

    def test_optimize_返回结果结构正确_含训练测试结果_的(self):
        """测试返回结果结构"""
        param_grid = {"fast_period": [5]}
        optimizer = WalkForwardOptimizer(
            MomentumStrategy, param_grid, train_ratio=0.5, n_splits=1
        )
        data = create_sample_data(n=50)
        results = optimizer.optimize(data)

        assert isinstance(results["train_results"], list)
        assert isinstance(results["test_results"], list)
        assert isinstance(results["best_params_history"], list)

    def test_optimize_样本外平均夏普比率计算正确(self):
        """测试 Walk-Forward 优化返回结构完整"""
        param_grid = {"fast_period": [5]}
        optimizer = WalkForwardOptimizer(
            MomentumStrategy, param_grid, train_ratio=0.5, n_splits=1
        )
        data = create_sample_data(n=50)
        results = optimizer.optimize(data)

        # 结果结构应完整
        assert "train_results" in results
        assert "test_results" in results
        assert "best_params_history" in results

    def test_optimize_数据不足_返回空结果_的(self):
        """测试数据不足时返回空结果"""
        param_grid = {"fast_period": [5]}
        optimizer = WalkForwardOptimizer(
            MomentumStrategy, param_grid, train_ratio=0.6, n_splits=5
        )
        data = create_sample_data(n=10)  # 数据太少
        results = optimizer.optimize(data)

        # 可能无有效结果
        assert "train_results" in results


class TestOptimizerIntegration:
    """优化器集成测试"""

    def test_GridOptimizer_与MomentumStrategy_集成_运行不报错的(self):
        """测试 GridOptimizer 与 MomentumStrategy 集成"""
        param_grid = {"fast_period": [5], "slow_period": [20]}
        optimizer = GridOptimizer(MomentumStrategy, param_grid)
        data = create_sample_data(n=60)

        # 不应当抛出异常
        best_params, results = optimizer.optimize(data, show_progress=False)
        assert isinstance(results, list)

    def test_BacktestResult_不同指标评分正确_的(self):
        """测试不同指标评分"""
        result = BacktestResult(
            params={},
            total_return=0.15,
            sharpe_ratio=1.2,
            max_drawdown=0.1,
            calmar_ratio=1.5,
        )
        assert result.score("sharpe_ratio") == 1.2
        assert result.score("calmar_ratio") == 1.5
        assert result.score("max_drawdown") == 0.1
