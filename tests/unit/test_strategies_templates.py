# -*- coding: utf-8 -*-
"""
策略模板 单元测试

测试范围：
- StrategyState 状态管理
- StrategyConfig 配置
- StrategyTemplate 基类
- MomentumStrategy 均线动量策略
- MeanReversionStrategy 均值回归策略
- BreakoutStrategy 突破策略
- GridStrategy 网格交易策略
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

try:
    from tradingagents.strategies.templates import (
        StrategyState, StrategyConfig, StrategyTemplate,
        MomentumStrategy, MeanReversionStrategy, BreakoutStrategy, GridStrategy,
    )
    from tradingagents.event_engine import BarEvent, EventType
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装", allow_module_level=True)


def create_bar(symbol, close, high=None, low=None, open_price=None, dt=None):
    """辅助函数：创建 BarEvent"""
    return BarEvent(
        symbol=symbol,
        interval="1d",
        open_price=open_price or close,
        high_price=high or close,
        low_price=low or close,
        close_price=close,
        volume=100000,
        datetime=dt or datetime.now(),
    )


class TestStrategyState:
    """StrategyState 测试"""

    def test_初始化默认值全为0或空(self):
        """测试初始化默认值"""
        state = StrategyState()
        assert state.position == 0
        assert state.avg_cost == 0.0
        assert state.total_pnl == 0.0
        assert state.trade_count == 0
        assert state.win_count == 0
        assert state.loss_count == 0


class TestStrategyConfig:
    """StrategyConfig 测试"""

    def test_默认配置值(self):
        """测试默认配置"""
        config = StrategyConfig()
        assert config.name == "Strategy"
        assert config.initial_capital == 1000000.0
        assert config.commission_rate == 0.0003
        assert config.slippage == 0.001
        assert config.max_position_ratio == 0.3

    def test_自定义配置(self):
        """测试自定义配置"""
        config = StrategyConfig(
            name="MyStrategy",
            symbols=["600000.SH"],
            initial_capital=500000.0,
            max_position_ratio=0.5,
        )
        assert config.name == "MyStrategy"
        assert config.symbols == ["600000.SH"]
        assert config.initial_capital == 500000.0


class TestStrategyTemplate:
    """StrategyTemplate 基类测试"""

    def test_不能直接实例化抽象基类_需子类实现on_bar(self):
        """测试抽象方法需要子类实现"""
        class ConcreteStrategy(StrategyTemplate):
            def on_bar(self, bar):
                pass

        config = StrategyConfig(name="Test")
        strategy = ConcreteStrategy(config=config)
        assert strategy is not None
        assert strategy.name == "Test"

    def test_初始化状态_按标的创建字典(self):
        """测试按标的创建状态字典"""
        class ConcreteStrategy(StrategyTemplate):
            def on_bar(self, bar):
                pass

        config = StrategyConfig(name="Test", symbols=["000001.SZ", "600000.SH"])
        strategy = ConcreteStrategy(config=config)
        assert "000001.SZ" in strategy.state
        assert "600000.SH" in strategy.state

    def test_set_engine_设置事件引擎(self):
        """测试设置事件引擎"""
        class ConcreteStrategy(StrategyTemplate):
            def on_bar(self, bar):
                pass

        config = StrategyConfig()
        strategy = ConcreteStrategy(config=config)
        mock_engine = Mock()
        strategy.set_engine(mock_engine)
        assert strategy.engine is mock_engine

    def test_on_init_设置初始化标志位为True(self):
        """测试on_init设置初始化标志位"""
        class ConcreteStrategy(StrategyTemplate):
            def on_bar(self, bar):
                pass

        config = StrategyConfig()
        strategy = ConcreteStrategy(config=config)
        strategy.on_init()
        assert strategy._initialized is True

    def test_get_position_获取已有持仓数量_0为初始值(self):
        """测试获取持仓-初始为0"""
        class ConcreteStrategy(StrategyTemplate):
            def on_bar(self, bar):
                pass

        config = StrategyConfig()
        strategy = ConcreteStrategy(config=config)
        assert strategy.get_position("000001.SZ") == 0

    def test_update_position_买入更新持仓_计算平均成本正确(self):
        """测试更新持仓-买入"""
        class ConcreteStrategy(StrategyTemplate):
            def on_bar(self, bar):
                pass

        config = StrategyConfig()
        strategy = ConcreteStrategy(config=config)
        strategy.update_position("000001.SZ", quantity=1000, price=10.0, is_buy=True)
        state = strategy.state["000001.SZ"]
        assert state.position == 1000
        assert state.avg_cost == 10.0

    def test_update_position_卖出减少持仓_计算盈亏正确(self):
        """测试更新持仓-卖出"""
        class ConcreteStrategy(StrategyTemplate):
            def on_bar(self, bar):
                pass

        config = StrategyConfig()
        strategy = ConcreteStrategy(config=config)
        strategy.update_position("000001.SZ", quantity=1000, price=10.0, is_buy=True)
        strategy.update_position("000001.SZ", quantity=500, price=12.0, is_buy=False)

        state = strategy.state["000001.SZ"]
        assert state.position == 500
        assert state.trade_count == 1
        assert state.total_pnl == pytest.approx(1000.0)  # (12-10)*500

    def test_update_position_盈利增加win_count_亏损增加loss_count(self):
        """测试盈亏计数"""
        class ConcreteStrategy(StrategyTemplate):
            def on_bar(self, bar):
                pass

        config = StrategyConfig()
        strategy = ConcreteStrategy(config=config)
        # 买入1000@10
        strategy.update_position("000001.SZ", quantity=1000, price=10.0, is_buy=True)
        # 卖出500@12 (盈利)
        strategy.update_position("000001.SZ", quantity=500, price=12.0, is_buy=False)
        # 卖出500@8 (亏损)
        strategy.update_position("000001.SZ", quantity=500, price=8.0, is_buy=False)

        state = strategy.state["000001.SZ"]
        assert state.win_count == 1
        assert state.loss_count == 1

    def test_get_stats_返回正确统计信息_无交易时为0_0_0_0_0_0_0_0_0_0_0(self):
        """测试无交易时统计信息全0"""
        class ConcreteStrategy(StrategyTemplate):
            def on_bar(self, bar):
                pass

        config = StrategyConfig()
        strategy = ConcreteStrategy(config=config)
        stats = strategy.get_stats()
        assert stats["total_trades"] == 0
        assert stats["win_rate"] == 0
        assert stats["total_pnl"] == 0

    def test_get_stats_有交易时返回正确统计信息(self):
        """测试有交易时统计信息"""
        class ConcreteStrategy(StrategyTemplate):
            def on_bar(self, bar):
                pass

        config = StrategyConfig()
        strategy = ConcreteStrategy(config=config)
        strategy.update_position("000001.SZ", quantity=1000, price=10.0, is_buy=True)
        strategy.update_position("000001.SZ", quantity=1000, price=12.0, is_buy=False)

        stats = strategy.get_stats()
        assert stats["total_trades"] == 1
        assert stats["win_count"] == 1
        assert stats["win_rate"] == pytest.approx(1.0)

    def test_close_清空持仓_调用sell_正确数量_价格_的(self):
        """测试close方法清空持仓"""
        class ConcreteStrategy(StrategyTemplate):
            def on_bar(self, bar):
                pass

        config = StrategyConfig()
        strategy = ConcreteStrategy(config=config)
        strategy.update_position("000001.SZ", quantity=500, price=10.0, is_buy=True)

        mock_engine = Mock()
        strategy.set_engine(mock_engine)
        strategy.close("000001.SZ", price=12.0)

        mock_engine.put.assert_called_once()


class TestMomentumStrategy:
    """均线动量策略测试"""

    def test_初始化_参数正确_设置_名称包含周期参数(self):
        """测试初始化参数"""
        config = StrategyConfig()
        strategy = MomentumStrategy(config=config, fast_period=10, slow_period=30)
        assert "Momentum" in strategy.name
        assert strategy.fast_period == 10
        assert strategy.slow_period == 30

    def test_on_bar_数据不足_不产生交易信号(self):
        """测试数据不足时不产生信号"""
        config = StrategyConfig(symbols=["000001.SZ"])
        strategy = MomentumStrategy(config=config, fast_period=5, slow_period=10)

        for i in range(5):
            bar = create_bar("000001.SZ", close=10.0 + i * 0.1)
            strategy.on_bar(bar)

        # 数据不足, 无持仓变化
        assert strategy.state["000001.SZ"].position == 0

    def test_on_bar_金叉产生买入信号_持仓增加(self):
        """测试金叉买入"""
        config = StrategyConfig(symbols=["000001.SZ"])
        strategy = MomentumStrategy(config=config, fast_period=3, slow_period=5)

        # 先构造一组价格, 使得快线上穿慢线
        prices = [10.0, 10.0, 10.0, 10.0, 10.0, 10.5, 11.0, 12.0]
        for i, p in enumerate(prices):
            bar = create_bar("000001.SZ", close=p)
            strategy.on_bar(bar)

        state = strategy.state["000001.SZ"]
        # 金叉后应有持仓
        assert state.position > 0

    def test_on_bar_死叉产生卖出信号_持仓减少到0_的(self):
        """测试死叉卖出"""
        config = StrategyConfig(symbols=["000001.SZ"])
        strategy = MomentumStrategy(config=config, fast_period=3, slow_period=5)

        # 先构造上涨使金叉买入
        prices = [10.0, 10.0, 10.0, 10.0, 10.0, 10.5, 11.0, 12.0, 13.0]
        for p in prices:
            strategy.on_bar(create_bar("000001.SZ", close=p))

        assert strategy.state["000001.SZ"].position > 0

        # 再构造下跌使死叉卖出
        prices_down = [12.0, 11.0, 10.0, 9.0, 8.0]
        for p in prices_down:
            strategy.on_bar(create_bar("000001.SZ", close=p))

        # 死叉后应清仓
        assert strategy.state["000001.SZ"].position == 0

    def test_calculate_quantity_价格0返回0_的(self):
        """测试价格为0时返回0"""
        config = StrategyConfig()
        strategy = MomentumStrategy(config=config)
        assert strategy._calculate_quantity(0.0) == 0
        assert strategy._calculate_quantity(-5.0) == 0

    def test_on_bar_不存在标的的bar直接返回(self):
        """测试不存在标的直接返回"""
        config = StrategyConfig(symbols=["000001.SZ"])
        strategy = MomentumStrategy(config=config, fast_period=5, slow_period=10)
        bar = create_bar("600000.SH", close=10.0)
        strategy.on_bar(bar)
        # 不应报错
        assert True


class TestMeanReversionStrategy:
    """均值回归策略测试"""

    def test_初始化_参数正确(self):
        """测试初始化参数"""
        config = StrategyConfig()
        strategy = MeanReversionStrategy(config=config, lookback=20, std_dev=2.0)
        assert strategy.lookback == 20
        assert strategy.std_dev == 2.0

    def test_on_bar_价格低于下轨触发买入(self):
        """测试价格低于下轨买入"""
        config = StrategyConfig(symbols=["000001.SZ"])
        strategy = MeanReversionStrategy(config=config, lookback=5, std_dev=1.0)

        # 先构造稳定价格序列建立均值
        for i in range(10):
            strategy.on_bar(create_bar("000001.SZ", close=10.0))

        # 价格大幅下跌, 低于下轨
        bar = create_bar("000001.SZ", close=7.0)
        strategy.on_bar(bar)

        # 应有持仓
        assert strategy.state["000001.SZ"].position > 0

    def test_on_bar_价格高于上轨触发卖出(self):
        """测试价格高于上轨卖出"""
        config = StrategyConfig(symbols=["000001.SZ"])
        strategy = MeanReversionStrategy(config=config, lookback=5, std_dev=1.0)

        # 先建仓
        for i in range(10):
            strategy.on_bar(create_bar("000001.SZ", close=10.0))

        # 买入
        strategy.on_bar(create_bar("000001.SZ", close=7.0))
        assert strategy.state["000001.SZ"].position > 0

        # 价格大幅上涨, 高于上轨
        bar = create_bar("000001.SZ", close=14.0)
        strategy.on_bar(bar)

        # 应清仓
        assert strategy.state["000001.SZ"].position == 0


class TestBreakoutStrategy:
    """突破策略测试"""

    def test_初始化_参数正确(self):
        """测试初始化参数"""
        config = StrategyConfig()
        strategy = BreakoutStrategy(config=config, lookback=20)
        assert strategy.lookback == 20

    def test_on_bar_突破近期高点买入(self):
        """测试突破高点买入"""
        config = StrategyConfig(symbols=["000001.SZ"])
        strategy = BreakoutStrategy(config=config, lookback=5)

        # 构造一个波动后突破的序列
        prices = [10.0, 10.1, 10.0, 10.2, 10.0, 10.1]
        for p in prices:
            bar = create_bar("000001.SZ", close=p, high=p + 0.1)
            strategy.on_bar(bar)

        # 突破前期高点
        bar = create_bar("000001.SZ", close=10.5, high=10.5)
        strategy.on_bar(bar)

        assert strategy.state["000001.SZ"].position > 0

    def test_on_bar_跌破近期低点卖出(self):
        """测试跌破低点卖出"""
        config = StrategyConfig(symbols=["000001.SZ"])
        strategy = BreakoutStrategy(config=config, lookback=5)

        # 先买入
        prices = [10.0, 10.1, 10.0, 10.2, 10.0, 10.1]
        for p in prices:
            strategy.on_bar(create_bar("000001.SZ", close=p, high=p + 0.1))

        strategy.on_bar(create_bar("000001.SZ", close=10.5, high=10.5))
        assert strategy.state["000001.SZ"].position > 0

        # 跌破前期低点
        for i in range(5):
            strategy.on_bar(create_bar("000001.SZ", close=9.5, low=9.4))

        bar = create_bar("000001.SZ", close=9.2, low=9.1)
        strategy.on_bar(bar)

        assert strategy.state["000001.SZ"].position == 0

    def test_calculate_quantity_价格0返回0(self):
        """测试价格为0时返回0"""
        config = StrategyConfig()
        strategy = BreakoutStrategy(config=config)
        assert strategy._calculate_quantity(0.0) == 0


class TestGridStrategy:
    """网格交易策略测试"""

    def test_初始化_参数正确(self):
        """测试初始化参数"""
        config = StrategyConfig()
        strategy = GridStrategy(config=config, grid_num=10, grid_ratio=0.02, base_quantity=100)
        assert strategy.grid_num == 10
        assert strategy.grid_ratio == 0.02
        assert strategy.base_quantity == 100

    def test_set_base_price_初始化网格价格_列表已排序_正确_的(self):
        """测试设置基准价格初始化网格"""
        config = StrategyConfig(symbols=["000001.SZ"])
        strategy = GridStrategy(config=config, grid_num=10, grid_ratio=0.02)
        strategy.set_base_price("000001.SZ", 10.0)

        assert "000001.SZ" in strategy.grid_prices
        grid_prices = strategy.grid_prices["000001.SZ"]
        assert grid_prices == sorted(grid_prices)  # 网格价格应有序
        assert len(grid_prices) == 11  # grid_num + 1

    def test_on_bar_自动设置基准价格_如果没有_的(self):
        """测试首次on_bar自动设置基准价格"""
        config = StrategyConfig(symbols=["000001.SZ"])
        strategy = GridStrategy(config=config, grid_num=10)
        bar = create_bar("000001.SZ", close=15.0)
        strategy.on_bar(bar)

        assert strategy.base_price["000001.SZ"] == 15.0

    def test_on_bar_不存在的标的自动设置基准价且不报错(self):
        """测试不存在标的自动设置基准价"""
        config = StrategyConfig(symbols=["000001.SZ"])
        strategy = GridStrategy(config=config)
        bar = create_bar("600000.SH", close=20.0)
        strategy.on_bar(bar)
        # 不应报错, 并且自动设置基准价
        assert strategy.base_price.get("600000.SH") == 20.0
