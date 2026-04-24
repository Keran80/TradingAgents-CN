# -*- coding: utf-8 -*-
"""
Strategy Builder 模块单元测试

测试范围：
- BuilderConfig 配置类
- VisualStrategyBuilder 主类
- 策略创建/加载/保存
- 指标/条件/信号管理
- 编译和代码生成
- 边界条件和异常处理
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json
import tempfile

# 条件导入（处理依赖缺失）
try:
    from tradingagents.strategies.builder.builder import (
        BuilderConfig,
        VisualStrategyBuilder,
    )
    from tradingagents.strategies.builder.dsl import (
        StrategyBlueprint,
        StrategyDSL,
        IndicatorDefinition,
        ConditionDefinition,
        SignalDefinition,
    )
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装（tradingagents）", allow_module_level=True)


class TestBuilderConfig:
    """BuilderConfig 配置类测试"""

    def test_默认配置(self):
        """测试默认配置"""
        config = BuilderConfig()
        assert config.workspace == "./strategies_workspace"
        assert config.auto_save is True
        assert config.save_interval == 300

    def test_自定义配置(self):
        """测试自定义配置"""
        config = BuilderConfig(
            workspace="/tmp/test_workspace",
            auto_save=False,
            save_interval=600,
        )
        assert config.workspace == "/tmp/test_workspace"
        assert config.auto_save is False
        assert config.save_interval == 600


class TestVisualStrategyBuilder:
    """VisualStrategyBuilder 主类测试"""

    def setup_method(self):
        """设置测试环境"""
        self.test_workspace = tempfile.mkdtemp()

    def test_初始化_默认配置(self):
        """测试初始化使用默认配置"""
        builder = VisualStrategyBuilder()
        assert builder.config is not None
        assert builder.blueprint is None
        assert builder.compiled_strategy is None

    def test_初始化_自定义配置(self):
        """测试初始化使用自定义配置"""
        config = BuilderConfig(workspace=self.test_workspace)
        builder = VisualStrategyBuilder(config)
        assert builder.config.workspace == self.test_workspace

    def test_new_strategy(self):
        """测试创建新策略"""
        builder = VisualStrategyBuilder()
        builder.new_strategy("TestStrategy", symbols=["000001.SZ", "000002.SZ"])
        assert builder.blueprint is not None
        assert builder.blueprint.name == "TestStrategy"
        assert len(builder.blueprint.symbols) == 2

    def test_add_indicator(self):
        """测试添加指标"""
        builder = VisualStrategyBuilder()
        builder.new_strategy("TestStrategy")
        builder.add_indicator("MA5", "MA", {"period": 5})

        assert len(builder.blueprint.indicators) == 1
        assert builder.blueprint.indicators[0].name == "MA5"
        assert builder.blueprint.indicators[0].component_type == "MA"

    def test_add_indicator_重复更新(self):
        """测试添加重复指标时更新"""
        builder = VisualStrategyBuilder()
        builder.new_strategy("TestStrategy")
        builder.add_indicator("MA5", "MA", {"period": 5})
        builder.add_indicator("MA5", "MA", {"period": 10})  # 更新

        assert len(builder.blueprint.indicators) == 1
        assert builder.blueprint.indicators[0].params == {"period": 10}

    def test_remove_indicator(self):
        """测试移除指标"""
        builder = VisualStrategyBuilder()
        builder.new_strategy("TestStrategy")
        builder.add_indicator("MA5", "MA", {"period": 5})
        builder.remove_indicator("MA5")

        assert len(builder.blueprint.indicators) == 0

    def test_add_condition(self):
        """测试添加条件"""
        builder = VisualStrategyBuilder()
        builder.new_strategy("TestStrategy")
        builder.add_condition("金叉", "IndicatorCondition", {
            "indicator_name": "MA5",
            "operator": "cross_up",
        })

        assert len(builder.blueprint.conditions) == 1
        assert builder.blueprint.conditions[0].name == "金叉"

    def test_remove_condition(self):
        """测试移除条件"""
        builder = VisualStrategyBuilder()
        builder.new_strategy("TestStrategy")
        builder.add_condition("条件1", "PriceCondition", {})
        builder.remove_condition("条件1")

        assert len(builder.blueprint.conditions) == 0

    def test_set_buy_signal(self):
        """测试设置买入信号"""
        builder = VisualStrategyBuilder()
        builder.new_strategy("TestStrategy")
        builder.set_buy_signal(conditions=["金叉"], logic="AND")

        assert len(builder.blueprint.buy_signals) == 1
        assert builder.blueprint.buy_signals[0].signal_type == "buy"
        assert builder.blueprint.buy_signals[0].conditions == ["金叉"]

    def test_set_sell_signal(self):
        """测试设置卖出信号"""
        builder = VisualStrategyBuilder()
        builder.new_strategy("TestStrategy")
        builder.set_sell_signal(conditions=["死叉"], logic="OR")

        assert len(builder.blueprint.sell_signals) == 1
        assert builder.blueprint.sell_signals[0].signal_type == "sell"

    def test_configure(self):
        """测试配置参数"""
        builder = VisualStrategyBuilder()
        builder.new_strategy("TestStrategy")
        builder.configure(
            initial_capital=500000.0,
            commission_rate=0.001,
            position_size=0.5,
            stop_loss=0.1,
            take_profit=0.2,
        )

        assert builder.blueprint.initial_capital == 500000.0
        assert builder.blueprint.commission_rate == 0.001
        assert builder.blueprint.position_size == 0.5
        assert builder.blueprint.stop_loss == 0.1
        assert builder.blueprint.take_profit == 0.2

    def test_compile_无蓝图异常(self):
        """测试无蓝图时编译抛出异常"""
        builder = VisualStrategyBuilder()
        with pytest.raises(ValueError):
            builder.compile()

    def test_compile_验证错误异常(self):
        """测试编译时验证错误抛出异常"""
        builder = VisualStrategyBuilder()
        builder.new_strategy("TestStrategy")
        # 添加无效条件可能导致验证失败
        with pytest.raises(ValueError):
            builder.compile()

    def test_save_and_load(self, tmp_path):
        """测试保存和加载策略"""
        builder = VisualStrategyBuilder()
        builder.new_strategy("TestStrategy")
        builder.add_indicator("MA5", "MA", {"period": 5})

        save_path = str(tmp_path / "test_strategy.json")
        builder.save(save_path)

        # 加载到新builder
        builder2 = VisualStrategyBuilder()
        builder2.load(save_path)

        assert builder2.blueprint.name == "TestStrategy"
        assert len(builder2.blueprint.indicators) == 1

    def test_save_自动路径(self, tmp_path):
        """测试保存到自动路径"""
        config = BuilderConfig(workspace=str(tmp_path))
        builder = VisualStrategyBuilder(config)
        builder.new_strategy("AutoSaveTest")

        filepath = builder.save()
        assert os.path.exists(filepath)
        assert "AutoSaveTest" in filepath

    def test_get_blueprint_dict(self):
        """测试获取蓝图字典"""
        builder = VisualStrategyBuilder()
        builder.new_strategy("TestStrategy")
        builder.add_indicator("MA5", "MA", {"period": 5})

        bp_dict = builder.get_blueprint_dict()
        assert bp_dict["name"] == "TestStrategy"
        assert len(bp_dict["indicators"]) == 1

    def test_get_blueprint_dict_无蓝图(self):
        """测试无蓝图时获取返回空字典"""
        builder = VisualStrategyBuilder()
        bp_dict = builder.get_blueprint_dict()
        assert bp_dict == {}

    def test_list_components(self):
        """测试列出组件"""
        builder = VisualStrategyBuilder()
        components = builder.list_components()
        assert isinstance(components, dict)

    def test_get_strategy_summary(self):
        """测试获取策略摘要"""
        builder = VisualStrategyBuilder()
        builder.new_strategy("TestStrategy")
        builder.add_indicator("MA5", "MA", {"period": 5})
        builder.set_buy_signal(conditions=["金叉"])
        builder.set_sell_signal(conditions=["死叉"])

        summary = builder.get_strategy_summary()
        assert summary["name"] == "TestStrategy"
        assert len(summary["indicators"]) == 1
        assert summary["buy_signals"] == 1
        assert summary["sell_signals"] == 1

    def test_get_strategy_summary_无蓝图(self):
        """测试无蓝图时获取返回空字典"""
        builder = VisualStrategyBuilder()
        summary = builder.get_strategy_summary()
        assert summary == {}


class TestStrategyBlueprint:
    """StrategyBlueprint 数据类测试"""

    def test_创建蓝图_默认值(self):
        """测试创建蓝图使用默认值"""
        bp = StrategyBlueprint()
        assert bp.name == "UnnamedStrategy"
        assert bp.symbols == ["000001.SZ"]
        assert bp.initial_capital == 1000000.0
        assert bp.commission_rate == 0.0003

    def test_to_dict(self):
        """测试转换为字典"""
        bp = StrategyBlueprint(name="TestStrategy")
        bp_dict = bp.to_dict()
        assert bp_dict["name"] == "TestStrategy"
        assert isinstance(bp_dict, dict)

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "name": "TestStrategy",
            "symbols": ["000001.SZ", "000002.SZ"],
            "initial_capital": 500000.0,
            "indicators": [],
            "conditions": [],
            "buy_signals": [],
            "sell_signals": [],
        }
        bp = StrategyBlueprint.from_dict(data)
        assert bp.name == "TestStrategy"
        assert len(bp.symbols) == 2


class TestIndicatorDefinition:
    """IndicatorDefinition 测试"""

    def test_创建指标定义(self):
        """测试创建指标定义"""
        indicator = IndicatorDefinition(
            name="MA5",
            component_type="MA",
            params={"period": 5},
        )
        assert indicator.name == "MA5"
        assert indicator.component_type == "MA"
        assert indicator.params == {"period": 5}

    def test_创建指标定义_默认参数(self):
        """测试创建指标定义使用默认参数"""
        indicator = IndicatorDefinition(
            name="MA5",
            component_type="MA",
        )
        assert indicator.params == {}


class TestConditionDefinition:
    """ConditionDefinition 测试"""

    def test_创建条件定义(self):
        """测试创建条件定义"""
        condition = ConditionDefinition(
            name="金叉",
            condition_type="IndicatorCondition",
            params={"indicator_name": "MA5"},
        )
        assert condition.name == "金叉"
        assert condition.condition_type == "IndicatorCondition"

    def test_创建条件定义_带子条件(self):
        """测试创建条件定义带子条件"""
        child = ConditionDefinition(
            name="子条件",
            condition_type="PriceCondition",
            params={},
        )
        parent = ConditionDefinition(
            name="父条件",
            condition_type="AndCondition",
            params={},
            children=[child],
        )
        assert len(parent.children) == 1


class TestSignalDefinition:
    """SignalDefinition 测试"""

    def test_创建信号定义_买入(self):
        """测试创建买入信号"""
        signal = SignalDefinition(
            signal_type="buy",
            conditions=["金叉"],
            logic="AND",
        )
        assert signal.signal_type == "buy"
        assert signal.conditions == ["金叉"]
        assert signal.logic == "AND"

    def test_创建信号定义_默认值(self):
        """测试创建信号定义使用默认值"""
        signal = SignalDefinition(signal_type="sell")
        assert signal.conditions == []
        assert signal.logic == "AND"
