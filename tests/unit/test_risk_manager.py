# -*- coding: utf-8 -*-
"""
风控管理器 单元测试

测试范围：
- RiskManager 初始化与配置
- 规则添加与移除
- 订单风控检查
- 止损止盈设置与触发
- 自定义验证器
- 风控摘要
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

try:
    from tradingagents.risk.manager import RiskManager, create_default_risk_manager
    from tradingagents.risk.interceptor import RiskInterceptor
    from tradingagents.risk.rules.base import RiskRule, RuleResult, RuleType
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装", allow_module_level=True)


class MockPortfolio:
    """模拟 Portfolio 对象用于测试"""

    def __init__(self, cash=100000.0, position_value=0.0):
        self._cash = cash
        self._position_value = position_value

    def get_cash(self):
        return self._cash

    def get_total_value(self):
        return self._position_value

    def get_position(self, symbol):
        return None


class DummyRule(RiskRule):
    """简单测试规则，始终通过"""

    def __init__(self, should_pass=True):
        super().__init__(name="DummyRule")
        self.should_pass = should_pass

    def check(self, context):
        return RuleResult(
            passed=self.should_pass,
            rule_name=self.name,
            rule_type=RuleType.CUSTOM,
            message="Dummy rule passed" if self.should_pass else "Dummy rule failed",
        )


class TestRiskManager初始化:
    """RiskManager 初始化测试"""

    def test_默认初始化(self):
        """测试默认初始化参数"""
        rm = RiskManager()
        assert rm.initial_cash == 100000.0
        assert rm.is_enabled() is True

    def test_自定义初始资金初始化(self):
        """测试自定义初始资金"""
        rm = RiskManager(initial_cash=500000.0)
        assert rm.initial_cash == 500000.0

    def test_初始化包含子组件(self):
        """测试初始化时创建子组件"""
        rm = RiskManager()
        assert rm.interceptor is not None
        assert rm.position_manager is not None
        assert rm.stop_loss_tp is not None
        assert rm.metrics is not None


class TestRiskManager配置:
    """风控配置测试"""

    def test_配置仓位规则(self):
        """测试配置仓位限制规则"""
        rm = RiskManager()
        rm.configure({"max_position_size": 5000})
        rules = rm.interceptor.get_enabled_rules()
        assert len(rules) == 1
        assert rules[0].name == "MaxPositionSize"

    def test_配置总持仓比例(self):
        """测试配置总持仓比例"""
        rm = RiskManager()
        rm.configure({"max_total_position_ratio": 0.8})
        rules = rm.interceptor.get_enabled_rules()
        assert any(r.name == "MaxTotalPosition" for r in rules)

    def test_配置现金比例规则(self):
        """测试配置现金比例规则"""
        rm = RiskManager()
        rm.configure({"min_cash_ratio": 0.05})
        rules = rm.interceptor.get_enabled_rules()
        assert any(r.name == "MinCashBalance" for r in rules)

    def test_配置单只股票仓位比例(self):
        """测试配置单只股票仓位比例"""
        rm = RiskManager()
        rm.configure({"max_single_position_ratio": 0.15})
        rules = rm.interceptor.get_enabled_rules()
        assert any(r.name == "MaxSingleStockExposure" for r in rules)

    def test_配置流动性规则(self):
        """测试配置流动性规则"""
        rm = RiskManager()
        rm.configure({"min_daily_volume": 100000})
        rules = rm.interceptor.get_enabled_rules()
        assert any(r.name == "MinVolume" for r in rules)

    def test_配置时段限制规则(self):
        """测试配置时段限制规则"""
        rm = RiskManager()
        rm.configure({"allowed_trading_hours": [9, 10, 11]})
        rules = rm.interceptor.get_enabled_rules()
        assert any(r.name == "TimeBased" for r in rules)

    def test_配置清空旧规则(self):
        """测试配置时先清空旧规则"""
        rm = RiskManager()
        rm.configure({"max_position_size": 5000})
        rm.configure({"min_cash_ratio": 0.1})
        rules = rm.interceptor.get_enabled_rules()
        assert len(rules) == 1  # 只保留最新配置

    def test_配置多个规则同时添加(self):
        """测试同时配置多个规则"""
        rm = RiskManager()
        rm.configure({
            "max_position_size": 5000,
            "min_cash_ratio": 0.1,
            "max_single_position_ratio": 0.2,
        })
        rules = rm.interceptor.get_enabled_rules()
        assert len(rules) == 3


class TestRiskManager订单检查:
    """订单风控检查测试"""

    def test_禁用风控时_订单自动通过(self):
        """测试风控禁用时订单自动通过"""
        rm = RiskManager()
        rm.disable()
        result = rm.check_order(
            order={"symbol": "000001.SZ", "side": "BUY", "quantity": 1000, "price": 10.0},
            portfolio=MockPortfolio(),
        )
        assert result["approved"] is True

    def test_无规则时_订单通过(self):
        """测试无规则时订单通过"""
        rm = RiskManager()
        result = rm.check_order(
            order={"symbol": "000001.SZ", "side": "BUY", "quantity": 1000, "price": 10.0},
            portfolio=MockPortfolio(),
        )
        assert result["approved"] is True

    def test_规则通过时_订单通过(self):
        """测试规则通过时订单通过"""
        rm = RiskManager()
        rm.configure({"max_position_size": 10000})
        result = rm.check_order(
            order={"symbol": "000001.SZ", "side": "BUY", "quantity": 1000, "price": 10.0},
            portfolio=MockPortfolio(),
        )
        assert result["approved"] is True

    def test_规则失败时_订单被拦截(self):
        """测试规则失败时订单被拦截"""
        rm = RiskManager()
        rm.interceptor.add_rule(DummyRule(should_pass=False))
        result = rm.check_order(
            order={"symbol": "000001.SZ", "side": "BUY", "quantity": 1000, "price": 10.0},
            portfolio=MockPortfolio(),
        )
        assert result["approved"] is False
        assert "failed_rules" in result
        assert len(result["failed_rules"]) > 0


class TestRiskManager自定义验证器:
    """自定义验证器测试"""

    def test_添加自定义验证器_通过(self):
        """测试自定义验证器通过"""

        def custom_validator(order, portfolio, market_data):
            return {"approved": True, "message": "custom OK"}

        rm = RiskManager()
        rm.add_custom_validator(custom_validator)
        # 自定义验证器在 check_order 中被调用
        result = rm.check_order(
            order={"symbol": "000001.SZ", "side": "BUY", "quantity": 1000, "price": 10.0},
            portfolio=MockPortfolio(),
        )
        assert result["approved"] is True

    def test_自定义验证器_拒绝订单(self):
        """测试自定义验证器拒绝订单"""

        def reject_validator(order, portfolio, market_data):
            if order.get("quantity", 0) > 5000:
                return {"approved": False, "message": "Quantity too large"}
            return {"approved": True, "message": "OK"}

        rm = RiskManager()
        rm.add_custom_validator(reject_validator)
        result = rm.check_order(
            order={"symbol": "000001.SZ", "side": "BUY", "quantity": 10000, "price": 10.0},
            portfolio=MockPortfolio(),
        )
        assert result["approved"] is False

    def test_自定义验证器异常_订单被拒绝(self):
        """测试自定义验证器抛出异常时订单被拒绝"""

        def broken_validator(order, portfolio, market_data):
            raise RuntimeError("Validator error")

        rm = RiskManager()
        rm.add_custom_validator(broken_validator)
        result = rm.check_order(
            order={"symbol": "000001.SZ", "side": "BUY", "quantity": 1000, "price": 10.0},
            portfolio=MockPortfolio(),
        )
        assert result["approved"] is False
        assert "自定义验证失败" in result["message"]

    def test_添加多个自定义规则方法(self):
        """测试添加多个自定义规则"""
        rm = RiskManager()
        rm.add_custom_rule(DummyRule(should_pass=True))
        rm.add_custom_rule(DummyRule(should_pass=True))
        rules = rm.interceptor.get_enabled_rules()
        assert len(rules) == 2


class TestRiskManager止损止盈:
    """止损止盈管理测试"""

    def test_设置固定止损(self):
        """测试设置固定止损"""
        rm = RiskManager()
        rm.set_stop_loss("000001.SZ", entry_price=10.0, stop_ratio=0.05)
        stop_info = rm.stop_loss_tp.get_stop_info("000001.SZ")
        assert stop_info is not None
        assert stop_info["entry_price"] == 10.0

    def test_设置追踪止损(self):
        """测试设置追踪止损"""
        rm = RiskManager()
        rm.set_trailing_stop("000001.SZ", entry_price=10.0, trailing_delta=0.05)
        stop_info = rm.stop_loss_tp.get_stop_info("000001.SZ")
        assert stop_info is not None
        assert stop_info["type"].value == "trailing"

    def test_设置固定止盈(self):
        """测试设置固定止盈"""
        rm = RiskManager()
        rm.set_take_profit("000001.SZ", entry_price=10.0, take_ratio=0.15)
        tp_info = rm.stop_loss_tp.get_take_profit_info("000001.SZ")
        assert tp_info is not None

    def test_设置追踪止盈(self):
        """测试设置追踪止盈"""
        rm = RiskManager()
        rm.set_trailing_take_profit("000001.SZ", entry_price=10.0, trailing_delta=0.03)
        tp_info = rm.stop_loss_tp.get_take_profit_info("000001.SZ")
        assert tp_info is not None
        assert tp_info["type"].value == "trailing"

    def test_检查止损触发_触发(self):
        """测试检查止损触发-触发"""
        rm = RiskManager()
        rm.set_stop_loss("000001.SZ", entry_price=10.0, stop_ratio=0.05)
        result = rm.check_stop_loss_trigger("000001.SZ", current_price=9.0)
        assert result["stop_triggered"] is True

    def test_检查止损触发_未触发(self):
        """测试检查止损触发-未触发"""
        rm = RiskManager()
        rm.set_stop_loss("000001.SZ", entry_price=10.0, stop_ratio=0.05)
        result = rm.check_stop_loss_trigger("000001.SZ", current_price=9.8)
        assert result["stop_triggered"] is False


class TestRiskManager启用禁用:
    """风控启用禁用测试"""

    def test_默认启用状态(self):
        """测试默认启用状态"""
        rm = RiskManager()
        assert rm.is_enabled() is True

    def test_禁用风控(self):
        """测试禁用风控"""
        rm = RiskManager()
        rm.disable()
        assert rm.is_enabled() is False

    def test_重新启用水控(self):
        """测试重新启用水控"""
        rm = RiskManager()
        rm.disable()
        rm.enable()
        assert rm.is_enabled() is True


class TestRiskManager获取器:
    """获取器方法测试"""

    def test_获取仓位管理器(self):
        """测试获取仓位管理器"""
        rm = RiskManager()
        pm = rm.get_position_manager()
        assert pm is not None
        assert pm.cash == rm.initial_cash

    def test_获取止损止盈管理器(self):
        """测试获取止损止盈管理器"""
        rm = RiskManager()
        sl = rm.get_stop_loss_tp()
        assert sl is not None


class TestRiskManager摘要:
    """风控摘要测试"""

    def test_风控摘要包含基本信息(self):
        """测试风控摘要包含基本信息"""
        rm = RiskManager()
        summary = rm.get_risk_summary()
        assert "enabled" in summary
        assert "position_summary" in summary
        assert "risk_interceptor" in summary
        assert "active_stops" in summary
        assert summary["enabled"] is True


class TestCreateDefaultRiskManager:
    """创建默认风控管理器测试"""

    @pytest.mark.parametrize("risk_level", ["strict", "normal", "loose"])
    def test_创建不同风险等级的管理器(self, risk_level):
        """测试创建不同风险等级配置"""
        rm = create_default_risk_manager(initial_cash=100000.0, risk_level=risk_level)
        assert rm is not None
        assert isinstance(rm, RiskManager)

    def test_未知风险等级使用默认配置(self):
        """测试未知风险等级使用normal配置"""
        rm = create_default_risk_manager(risk_level="unknown")
        assert rm is not None
        rules = rm.interceptor.get_enabled_rules()
        assert len(rules) > 0

    def test_默认管理器_严格模式规则更多限制(self):
        """测试严格模式有更严格的限制"""
        strict_rm = create_default_risk_manager(risk_level="strict")
        loose_rm = create_default_risk_manager(risk_level="loose")

        # 严格模式最大持仓数量应该更小
        strict_rules = {r.name: r for r in strict_rm.interceptor.get_enabled_rules()}
        loose_rules = {r.name: r for r in loose_rm.interceptor.get_enabled_rules()}

        strict_max = strict_rules.get("MaxPositionSize")
        loose_max = loose_rules.get("MaxPositionSize")

        if strict_max and loose_max:
            assert strict_max.max_quantity < loose_max.max_quantity
