# -*- coding: utf-8 -*-
"""
Alpha-GFN 模块单元测试

测试范围：
- AlphaConfig 配置类
- 操作符函数
- FactorTree 因子树
- FlowNetwork 流网络
- AlphaGFN 主类
- 边界条件和异常处理
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 条件导入（处理依赖缺失）
try:
    import numpy as np
    from tradingagents.rl.alpha_gfn import (
        AlphaConfig,
        FactorTree,
        FlowNetwork,
        AlphaGFN,
        create_alpha_gfn,
        OPERATORS,
        _add, _sub, _mul, _div, _neg, _abs, _log, _sqrt,
        _rank, _zscore, _delta, _roll_max, _roll_min, _roll_std,
    )
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装（numpy/tradingagents）", allow_module_level=True)


class TestAlphaConfig:
    """AlphaConfig 配置类测试"""

    def test_默认配置(self):
        """测试默认配置值"""
        config = AlphaConfig()
        assert config.n_generations == 50
        assert config.population_size == 100
        assert config.n_parents == 20
        assert config.mutation_rate == 0.1
        assert config.crossover_rate == 0.7
        assert config.min_ic == 0.02
        assert config.max_drawdown_ratio == 0.5
        assert config.flow_steps == 5
        assert config.hidden_dim == 64
        assert config.n_samples == 100

    def test_自定义配置(self):
        """测试自定义配置"""
        config = AlphaConfig(
            n_generations=100,
            population_size=200,
            min_ic=0.05,
        )
        assert config.n_generations == 100
        assert config.population_size == 200
        assert config.min_ic == 0.05


class TestOperators:
    """操作符函数测试"""

    def test_add(self):
        """测试加法操作符"""
        x = np.array([1, 2, 3])
        y = np.array([4, 5, 6])
        result = _add(x, y)
        np.testing.assert_array_equal(result, np.array([5, 7, 9]))

    def test_sub(self):
        """测试减法操作符"""
        x = np.array([4, 5, 6])
        y = np.array([1, 2, 3])
        result = _sub(x, y)
        np.testing.assert_array_equal(result, np.array([3, 3, 3]))

    def test_mul(self):
        """测试乘法操作符"""
        x = np.array([1, 2, 3])
        y = np.array([4, 5, 6])
        result = _mul(x, y)
        np.testing.assert_array_equal(result, np.array([4, 10, 18]))

    def test_div(self):
        """测试除法操作符（包含除零保护）"""
        x = np.array([1, 2, 3])
        y = np.array([2, 2, 0])
        result = _div(x, y)
        assert result[0] == 0.5
        assert result[2] != np.inf  # 除零保护

    def test_neg(self):
        """测试负号操作符"""
        x = np.array([1, -2, 3])
        result = _neg(x)
        np.testing.assert_array_equal(result, np.array([-1, 2, -3]))

    def test_abs(self):
        """测试绝对值操作符"""
        x = np.array([-1, 2, -3])
        result = _abs(x)
        np.testing.assert_array_equal(result, np.array([1, 2, 3]))

    def test_log(self):
        """测试对数操作符（包含负数保护）"""
        x = np.array([1, -2, 0])
        result = _log(x)
        assert not np.any(np.isnan(result))

    def test_sqrt(self):
        """测试平方根操作符（包含负数保护）"""
        x = np.array([4, -9, 0])
        result = _sqrt(x)
        assert not np.any(np.isnan(result))
        assert result[0] == 2.0

    def test_operators_dict(self):
        """测试操作符字典包含所有操作"""
        expected_ops = ['add', 'sub', 'mul', 'div', 'neg', 'abs', 'log', 'sqrt',
                        'rank', 'zscore', 'delta', 'roll_max', 'roll_min', 'roll_std']
        for op in expected_ops:
            assert op in OPERATORS


class TestFactorTree:
    """FactorTree 因子树测试"""

    def test_初始化空树(self):
        """测试初始化空树"""
        tree = FactorTree()
        assert tree.root is None

    def test_随机树生成(self):
        """测试随机树生成"""
        tree = FactorTree.random_tree(depth=2)
        assert tree.root is not None
        assert isinstance(tree, FactorTree)

    def test_随机树叶子节点(self):
        """测试深度为0时生成叶子节点"""
        tree = FactorTree.random_tree(depth=0)
        assert tree.root is not None
        assert tree.root[0] in ['feature', 'const']

    def test_评估特征节点(self):
        """测试评估特征节点"""
        tree = FactorTree(('feature', 'close'))
        data = {'close': np.array([1, 2, 3])}
        result = tree.evaluate(data)
        np.testing.assert_array_equal(result, np.array([1, 2, 3]))

    def test_评估常量节点(self):
        """测试评估常量节点"""
        tree = FactorTree(('const', 5.0))
        data = {'close': np.array([1, 2, 3])}
        result = tree.evaluate(data)
        np.testing.assert_array_equal(result, np.array([5.0, 5.0, 5.0]))

    def test_评估一元操作符(self):
        """测试评估一元操作符"""
        tree = FactorTree(('unary', 'abs', ('const', -5.0)))
        data = {'close': np.array([1, 2, 3])}
        result = tree.evaluate(data)
        assert result[0] == 5.0

    def test_评估二元操作符(self):
        """测试评估二元操作符"""
        left = FactorTree(('const', 10.0))
        right = FactorTree(('const', 5.0))
        tree = FactorTree(('binary', 'add', left, right))
        data = {'close': np.array([1, 2, 3])}
        result = tree.evaluate(data)
        assert result[0] == 15.0

    def test_评估空节点(self):
        """测试评估空节点"""
        tree = FactorTree()
        data = {'close': np.array([1, 2, 3])}
        result = tree.evaluate(data)
        np.testing.assert_array_equal(result, np.zeros(1))

    def test_评估异常处理(self):
        """测试评估异常处理"""
        tree = FactorTree(('binary', 'div', ('const', 1.0), ('const', 0.0)))
        data = {'close': np.array([1, 2, 3])}
        result = tree.evaluate(data)  # 不应抛出异常
        assert result is not None

    def test_repr空树(self):
        """测试空树的字符串表示"""
        tree = FactorTree()
        assert "empty" in repr(tree)

    def test_repr特征节点(self):
        """测试特征节点的字符串表示"""
        tree = FactorTree(('feature', 'close'))
        assert "close" in repr(tree)

    def test_repr一元操作符(self):
        """测试一元操作符的字符串表示"""
        tree = FactorTree(('unary', 'abs', ('const', 5.0)))
        assert "abs" in repr(tree)

    def test_repr二元操作符(self):
        """测试二元操作符的字符串表示"""
        left = FactorTree(('const', 10.0))
        right = FactorTree(('const', 5.0))
        tree = FactorTree(('binary', 'add', left, right))
        repr_str = repr(tree)
        assert "add" in repr_str


class TestFlowNetwork:
    """FlowNetwork 流网络测试"""

    def test_初始化(self):
        """测试初始化"""
        net = FlowNetwork(input_dim=10, hidden_dim=32, n_steps=3)
        assert net.input_dim == 10
        assert net.hidden_dim == 32
        assert net.n_steps == 3

    def test_前向传播形状(self):
        """测试前向传播输出形状"""
        net = FlowNetwork(input_dim=10, hidden_dim=32, n_steps=3)
        x = np.random.randn(5, 10)
        z, log_det = net.forward(x)
        assert z.shape == (5, 32)
        assert log_det.shape == (5,)

    def test_前向传播无NaN(self):
        """测试前向传播无NaN值"""
        net = FlowNetwork(input_dim=10, hidden_dim=32, n_steps=3)
        x = np.random.randn(5, 10)
        z, log_det = net.forward(x)
        assert not np.any(np.isnan(z))
        assert not np.any(np.isnan(log_det))

    def test_逆变换形状(self):
        """测试逆变换输出形状"""
        net = FlowNetwork(input_dim=10, hidden_dim=32, n_steps=3)
        z = np.random.randn(5, 32)
        x = net.inverse(z)
        assert x.shape == (5, 32)


class TestAlphaGFN:
    """AlphaGFN 主类测试"""

    def test_初始化默认配置(self):
        """测试初始化使用默认配置"""
        gfn = AlphaGFN()
        assert gfn.config is not None
        assert gfn.population == []
        assert gfn.best_alpha is None
        assert gfn.history == []

    def test_初始化自定义配置(self):
        """测试初始化使用自定义配置"""
        config = AlphaConfig(n_generations=10, population_size=20)
        gfn = AlphaGFN(config)
        assert gfn.config.n_generations == 10
        assert gfn.config.population_size == 20

    def test_calculate_ic(self):
        """测试IC计算"""
        gfn = AlphaGFN()
        alpha = np.array([1, 2, 3, 4, 5])
        target = np.array([1.1, 2.1, 3.1, 4.1, 5.1])
        ic = gfn._calculate_ic(alpha, target)
        assert ic > 0.9  # 高度正相关

    def test_calculate_ic长度不匹配(self):
        """测试IC计算长度不匹配时返回0"""
        gfn = AlphaGFN()
        alpha = np.array([1, 2, 3])
        target = np.array([1, 2, 3, 4, 5])
        ic = gfn._calculate_ic(alpha, target)
        assert ic == 0

    def test_calculate_drawdown(self):
        """测试回撤计算"""
        gfn = AlphaGFN()
        alpha = np.array([0.1, -0.05, 0.05, -0.1, 0.05])
        dd = gfn._calculate_drawdown_ratio(alpha)
        assert dd <= 0  # 回撤应为负值或零

    def test_get_top_alphas(self):
        """测试获取top N因子"""
        config = AlphaConfig(population_size=20)
        gfn = AlphaGFN(config)
        gfn.population = [FactorTree.random_tree() for _ in range(20)]
        top = gfn.get_top_alphas(n=5)
        assert len(top) == 5

    def test_apply_alpha_with_data(self):
        """测试应用Alpha因子"""
        import pandas as pd
        gfn = AlphaGFN()
        data = pd.DataFrame({
            'close': [100, 101, 102, 103, 104],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        result = gfn.apply_alpha(data, "close - volume")
        assert result is not None
        assert len(result) == 5

    def test_save_and_load(self, tmp_path):
        """测试保存和加载"""
        gfn = AlphaGFN()
        gfn.best_alpha = FactorTree(('feature', 'close'))
        gfn.history = [0.1, 0.2, 0.3]

        save_path = str(tmp_path / "alpha_gfn.pkl")
        gfn.save(save_path)

        gfn2 = AlphaGFN()
        gfn2.load(save_path)
        assert gfn2.best_alpha is not None
        assert len(gfn2.history) == 3


class TestCreateAlphaGFN:
    """create_alpha_gfn 工厂函数测试"""

    def test_创建实例(self):
        """测试创建Alpha-GFN实例"""
        gfn = create_alpha_gfn(
            n_generations=10,
            population_size=50,
            min_ic=0.03,
        )
        assert isinstance(gfn, AlphaGFN)
        assert gfn.config.n_generations == 10
        assert gfn.config.population_size == 50
        assert gfn.config.min_ic == 0.03
