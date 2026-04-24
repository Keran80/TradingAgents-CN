# -*- coding: utf-8 -*-
"""
仓位管理器 单元测试

测试范围：
- PositionState 属性和计算
- PositionManager 建仓/平仓/更新价格
- 仓位限制检查
- 止损止盈设置
- 账户摘要和交易历史
"""
import pytest
from datetime import datetime
from unittest.mock import patch

try:
    from tradingagents.risk.position_manager import PositionManager, PositionState
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装", allow_module_level=True)


class TestPositionState:
    """PositionState 数据类测试"""

    def test_初始化默认值(self):
        """测试默认初始化"""
        state = PositionState(symbol="000001.SZ")
        assert state.symbol == "000001.SZ"
        assert state.quantity == 0
        assert state.avg_cost == 0.0
        assert state.realized_pnl == 0.0
        assert state.unrealized_pnl == 0.0

    def test_市值计算(self):
        """测试市值属性"""
        state = PositionState(symbol="000001.SZ", quantity=1000, current_price=15.5)
        assert state.market_value == 15500.0

    def test_总成本计算(self):
        """测试总成本属性"""
        state = PositionState(symbol="000001.SZ", quantity=1000, avg_cost=12.0)
        assert state.total_cost == 12000.0

    def test_总盈亏计算_无已实现盈亏(self):
        """测试总盈亏-仅未实现"""
        state = PositionState(
            symbol="000001.SZ", quantity=1000, avg_cost=12.0,
            current_price=15.0, realized_pnl=0.0, unrealized_pnl=3000.0
        )
        assert state.total_pnl == 3000.0

    def test_总盈亏计算_含已实现盈亏(self):
        """测试总盈亏-含已实现"""
        state = PositionState(
            symbol="000001.SZ", quantity=1000, avg_cost=12.0,
            current_price=15.0, realized_pnl=500.0, unrealized_pnl=3000.0
        )
        assert state.total_pnl == 3500.0

    def test_盈亏比例_正常情况(self):
        """测试盈亏比例"""
        state = PositionState(
            symbol="000001.SZ", quantity=1000, avg_cost=10.0,
            current_price=12.0, unrealized_pnl=2000.0
        )
        assert state.pnl_ratio == pytest.approx(0.2, rel=1e-3)

    def test_盈亏比例_零成本(self):
        """测试盈亏比例-零成本时返回0"""
        state = PositionState(symbol="000001.SZ", quantity=0, avg_cost=0.0)
        assert state.pnl_ratio == 0.0


class TestPositionManager初始化:
    """PositionManager 初始化测试"""

    def test_默认初始化(self):
        """测试默认参数初始化"""
        pm = PositionManager()
        assert pm.initial_cash == 100000.0
        assert pm.cash == 100000.0
        assert pm.max_total_position_ratio == 0.9
        assert pm.max_single_position_ratio == 0.2
        assert pm.max_positions == 10
        assert pm.positions == {}

    def test_自定义初始化(self):
        """测试自定义参数初始化"""
        pm = PositionManager(
            initial_cash=500000.0,
            max_total_position_ratio=0.8,
            max_single_position_ratio=0.25,
            max_positions=5
        )
        assert pm.initial_cash == 500000.0
        assert pm.max_total_position_ratio == 0.8
        assert pm.max_single_position_ratio == 0.25
        assert pm.max_positions == 5


class TestPositionManager建仓:
    """建仓功能测试"""

    def test_建仓_成功(self):
        """测试正常建仓"""
        pm = PositionManager(initial_cash=100000.0)
        success, msg = pm.open_position("000001.SZ", quantity=1000, price=10.0)
        assert success is True
        assert "建仓成功" in msg
        assert pm.cash == 90000.0
        assert "000001.SZ" in pm.positions
        assert pm.positions["000001.SZ"].quantity == 1000
        assert pm.positions["000001.SZ"].avg_cost == 10.0

    def test_建仓_数量为0失败(self):
        """测试建仓数量为0时失败"""
        pm = PositionManager()
        success, msg = pm.open_position("000001.SZ", quantity=0, price=10.0)
        assert success is False
        assert "无效" in msg

    def test_建仓_价格为负失败(self):
        """测试建仓价格为负时失败"""
        pm = PositionManager()
        success, msg = pm.open_position("000001.SZ", quantity=1000, price=-5.0)
        assert success is False

    def test_建仓_资金不足失败(self):
        """测试资金不足时建仓失败"""
        pm = PositionManager(initial_cash=5000.0)
        success, msg = pm.open_position("000001.SZ", quantity=1000, price=10.0)
        assert success is False
        assert "资金不足" in msg

    def test_建仓_增加已有持仓(self):
        """测试已有持仓时增加数量"""
        pm = PositionManager(initial_cash=200000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.open_position("000001.SZ", quantity=500, price=12.0)

        pos = pm.positions["000001.SZ"]
        assert pos.quantity == 1500
        # 平均成本: (1000*10 + 500*12) / 1500 = 16000/1500 = 10.666...
        assert pos.avg_cost == pytest.approx(16000.0 / 1500, rel=1e-3)
        assert pm.cash == 200000.0 - 10000.0 - 6000.0

    def test_建仓_自定义时间戳(self):
        """测试建仓时指定时间戳"""
        pm = PositionManager(initial_cash=100000.0)
        ts = datetime(2024, 1, 15, 10, 30, 0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0, timestamp=ts)

        pos = pm.positions["000001.SZ"]
        assert pos.entry_time == ts


class TestPositionManager平仓:
    """平仓功能测试"""

    def test_平仓_成功(self):
        """测试正常平仓"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        success, msg = pm.close_position("000001.SZ", quantity=1000, price=12.0)
        assert success is True
        assert "平仓成功" in msg
        assert pm.cash == 90000.0 + 12000.0
        assert "000001.SZ" not in pm.positions  # 完全平仓后应删除

    def test_平仓_部分平仓(self):
        """测试部分平仓"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.close_position("000001.SZ", quantity=500, price=12.0)

        pos = pm.positions["000001.SZ"]
        assert pos.quantity == 500
        assert pos.realized_pnl == pytest.approx(1000.0)

    def test_平仓_无持仓失败(self):
        """测试无持仓时平仓失败"""
        pm = PositionManager()
        success, msg = pm.close_position("000001.SZ", quantity=1000, price=12.0)
        assert success is False
        assert "无持仓" in msg

    def test_平仓_数量超限失败(self):
        """测试平仓数量超过持仓失败"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=500, price=10.0)
        success, msg = pm.close_position("000001.SZ", quantity=1000, price=12.0)
        assert success is False
        assert "超限" in msg

    def test_平仓_亏损情况(self):
        """测试亏损平仓"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.close_position("000001.SZ", quantity=1000, price=8.0)

        pos_data = pm.get_trade_history()[-1]
        assert pos_data["realized_pnl"] == pytest.approx(-2000.0)


class TestPositionManager价格更新:
    """价格更新功能测试"""

    def test_更新单个价格(self):
        """测试更新单个持仓价格"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.update_price("000001.SZ", 12.0)

        pos = pm.positions["000001.SZ"]
        assert pos.current_price == 12.0
        assert pos.unrealized_pnl == pytest.approx(2000.0)

    def test_更新不存在的股票价格_无影响(self):
        """测试更新不存在的股票价格"""
        pm = PositionManager()
        pm.update_price("000001.SZ", 12.0)
        # 不应该报错
        assert True

    def test_批量更新价格(self):
        """测试批量更新价格"""
        pm = PositionManager(initial_cash=200000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.open_position("600000.SH", quantity=500, price=20.0)

        pm.update_all_prices({
            "000001.SZ": 12.0,
            "600000.SH": 22.0,
        })

        assert pm.positions["000001.SZ"].current_price == 12.0
        assert pm.positions["600000.SH"].current_price == 22.0


class TestPositionManager仓位检查:
    """仓位限制检查测试"""

    def test_可以建仓_正常情况(self):
        """测试正常建仓检查通过"""
        pm = PositionManager(initial_cash=100000.0)
        can, reason = pm.can_open_position("000001.SZ", quantity=1000, price=10.0)
        assert can is True
        assert reason == "OK"

    def test_资金不足_检查失败(self):
        """测试资金不足检查失败"""
        pm = PositionManager(initial_cash=5000.0)
        can, reason = pm.can_open_position("000001.SZ", quantity=1000, price=10.0)
        assert can is False
        assert "资金不足" in reason

    def test_总持仓超限_检查失败(self):
        """测试总持仓超限检查失败"""
        # 使用较小的 max_total_position_ratio 确保触发
        pm = PositionManager(
            initial_cash=100000.0, max_total_position_ratio=0.2
        )
        # 第一次建仓 2000 * 10 = 20000
        success, _ = pm.open_position("000001.SZ", quantity=2000, price=10.0)
        assert success is True
        # 此时 cash = 80000, position_value = 20000, total_assets = 100000
        # max_total = 100000 * 0.2 = 20000
        # 再建仓 1000 * 10 = 10000, new_total_value = 20000 + 10000 = 30000 > 20000
        can, reason = pm.can_open_position("600000.SH", quantity=1000, price=10.0)
        assert can is False
        assert "总持仓超限" in reason

    def test_单只持仓超限_检查失败(self):
        """测试单只持仓超限检查失败"""
        pm = PositionManager(
            initial_cash=100000.0, max_single_position_ratio=0.1
        )
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        can, reason = pm.can_open_position("000001.SZ", quantity=1000, price=10.0)
        assert can is False
        assert "单只持仓超限" in reason

    def test_持仓数量超限_检查失败(self):
        """测试持仓数量超限检查失败"""
        pm = PositionManager(initial_cash=500000.0, max_positions=2)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.open_position("600000.SH", quantity=1000, price=10.0)
        can, reason = pm.can_open_position("300001.SZ", quantity=1000, price=10.0)
        assert can is False
        assert "持仓数量超限" in reason


class TestPositionManager止损止盈:
    """止损止盈功能测试"""

    def test_设置止损价(self):
        """测试设置止损价"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.set_stop_loss("000001.SZ", 9.5)
        assert pm.positions["000001.SZ"].stop_loss_price == 9.5

    def test_设置止盈价(self):
        """测试设置止盈价"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.set_take_profit("000001.SZ", 12.0)
        assert pm.positions["000001.SZ"].take_profit_price == 12.0

    def test_止损触发_价格下跌到止损价以下(self):
        """测试止损触发"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.set_stop_loss("000001.SZ", 9.5)
        pm.update_price("000001.SZ", 9.0)

        result = pm.check_stop_loss("000001.SZ")
        assert result is not None

    def test_止损未触发_价格高于止损价(self):
        """测试止损未触发"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.set_stop_loss("000001.SZ", 9.5)
        pm.update_price("000001.SZ", 9.8)

        result = pm.check_stop_loss("000001.SZ")
        assert result is None

    def test_止盈触发_价格上涨到止盈价以上(self):
        """测试止盈触发"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.set_take_profit("000001.SZ", 12.0)
        pm.update_price("000001.SZ", 13.0)

        result = pm.check_take_profit("000001.SZ")
        assert result is not None

    def test_止盈未触发_价格低于止盈价(self):
        """测试止盈未触发"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.set_take_profit("000001.SZ", 12.0)
        pm.update_price("000001.SZ", 11.5)

        result = pm.check_take_profit("000001.SZ")
        assert result is None

    def test_无止损设置时_检查返回None(self):
        """测试无止损设置时检查返回None"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        result = pm.check_stop_loss("000001.SZ")
        assert result is None


class TestPositionManager查询:
    """查询功能测试"""

    def test_获取持仓_存在(self):
        """测试获取已有持仓"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pos = pm.get_position("000001.SZ")
        assert pos is not None
        assert pos.symbol == "000001.SZ"

    def test_获取持仓_不存在(self):
        """测试获取不存在的持仓"""
        pm = PositionManager()
        pos = pm.get_position("000001.SZ")
        assert pos is None

    def test_获取所有持仓_空仓(self):
        """测试空仓时获取空列表"""
        pm = PositionManager()
        assert pm.get_all_positions() == []

    def test_获取所有持仓_多只股票(self):
        """测试多只股票持仓"""
        pm = PositionManager(initial_cash=200000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.open_position("600000.SH", quantity=500, price=20.0)
        positions = pm.get_all_positions()
        assert len(positions) == 2

    def test_持仓股票数量_空仓(self):
        """测试空仓时数量为0"""
        pm = PositionManager()
        assert pm.get_positions_count() == 0

    def test_持仓股票数量_多只股票(self):
        """测试多只股票持仓数量"""
        pm = PositionManager(initial_cash=200000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.open_position("600000.SH", quantity=500, price=20.0)
        assert pm.get_positions_count() == 2

    def test_总资产计算_无持仓(self):
        """测试无持仓时总资产等于初始资金"""
        pm = PositionManager(initial_cash=100000.0)
        assert pm.get_total_assets() == 100000.0

    def test_总资产计算_有持仓有盈利(self):
        """测试有持仓且盈利时总资产"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.update_price("000001.SZ", 12.0)
        total = pm.get_total_assets()
        assert total == pytest.approx(90000.0 + 12000.0)  # 现金 + 市值


class TestPositionManager账户摘要:
    """账户摘要测试"""

    def test_获取摘要_空仓情况(self):
        """测试空仓时账户摘要"""
        pm = PositionManager(initial_cash=100000.0)
        summary = pm.get_summary()
        assert summary["cash"] == 100000.0
        assert summary["position_value"] == 0.0
        assert summary["total_assets"] == 100000.0
        assert summary["total_pnl"] == 0.0
        assert summary["position_count"] == 0

    def test_获取摘要_有持仓有盈利(self):
        """测试有持仓且有盈利时摘要"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.update_price("000001.SZ", 12.0)
        summary = pm.get_summary()
        assert summary["cash"] == 90000.0
        assert summary["position_value"] == pytest.approx(12000.0)
        assert summary["position_count"] == 1
        assert len(summary["positions"]) == 1

    def test_获取摘要_含已实现盈亏(self):
        """测试摘要中包含已实现盈亏"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.close_position("000001.SZ", quantity=500, price=12.0)
        summary = pm.get_summary()
        assert summary["position_count"] == 1  # 仍有500股


class TestPositionManager交易历史:
    """交易历史测试"""

    def test_交易历史_初始为空列表(self):
        """测试初始交易历史为空"""
        pm = PositionManager()
        assert pm.get_trade_history() == []

    def test_交易历史_建仓后有记录(self):
        """测试建仓后交易历史"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        history = pm.get_trade_history()
        assert len(history) == 1
        assert history[0]["action"] == "OPEN"
        assert history[0]["symbol"] == "000001.SZ"
        assert history[0]["quantity"] == 1000

    def test_交易历史_平仓后有记录含盈亏(self):
        """测试平仓后交易历史含盈亏"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        pm.close_position("000001.SZ", quantity=1000, price=12.0)
        history = pm.get_trade_history()
        assert len(history) == 2
        assert history[1]["action"] == "CLOSE"
        assert history[1]["realized_pnl"] == pytest.approx(2000.0)

    def test_交易历史_返回副本_非引用(self):
        """测试返回交易历史副本"""
        pm = PositionManager(initial_cash=100000.0)
        pm.open_position("000001.SZ", quantity=1000, price=10.0)
        history1 = pm.get_trade_history()
        history1.append({"fake": True})
        history2 = pm.get_trade_history()
        assert len(history2) == 1  # 原始历史不受影响
