# -*- coding: utf-8 -*-
"""
止损止盈模块 单元测试

测试范围：
- 固定止损设置与触发
- 追踪止损设置与触发
- ATR止损设置与触发
- 固定止盈设置与触发
- 追踪止盈设置与触发
- 停用与移除
"""
import pytest

try:
    from tradingagents.risk.stop_loss import StopLossTakeProfit, StopType
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装", allow_module_level=True)


class TestFixedStopLoss:
    """固定止损测试"""

    def test_设置固定止损_默认比例(self):
        """测试设置固定止损-默认比例"""
        st = StopLossTakeProfit()
        st.set_fixed_stop_loss("000001.SZ", entry_price=10.0)
        info = st.get_stop_info("000001.SZ")
        assert info is not None
        assert info["entry_price"] == 10.0
        assert info["stop_price"] == pytest.approx(9.5)  # 10 * (1 - 0.05)

    def test_设置固定止损_自定义价格(self):
        """测试设置固定止损-自定义价格"""
        st = StopLossTakeProfit()
        st.set_fixed_stop_loss("000001.SZ", entry_price=10.0, stop_price=8.5)
        info = st.get_stop_info("000001.SZ")
        assert info["stop_price"] == 8.5

    def test_设置固定止损_自定义比例(self):
        """测试设置固定止损-自定义比例"""
        st = StopLossTakeProfit()
        st.set_fixed_stop_loss("000001.SZ", entry_price=10.0, stop_ratio=0.10)
        info = st.get_stop_info("000001.SZ")
        assert info["stop_price"] == pytest.approx(9.0)

    def test_固定止损_触发条件_价格跌破止损价(self):
        """测试固定止损触发"""
        st = StopLossTakeProfit()
        st.set_fixed_stop_loss("000001.SZ", entry_price=10.0, stop_ratio=0.05)
        result = st.check_trigger("000001.SZ", current_price=9.4)
        assert result["stop_triggered"] is True
        assert result["action"] == "stop"

    def test_固定止损_未触发_价格高于止损价(self):
        """测试固定止损未触发"""
        st = StopLossTakeProfit()
        st.set_fixed_stop_loss("000001.SZ", entry_price=10.0, stop_ratio=0.05)
        result = st.check_trigger("000001.SZ", current_price=9.6)
        assert result["stop_triggered"] is False

    def test_固定止损_正好在止损价触发(self):
        """测试正好在止损价时触发"""
        st = StopLossTakeProfit()
        st.set_fixed_stop_loss("000001.SZ", entry_price=10.0, stop_price=9.5)
        result = st.check_trigger("000001.SZ", current_price=9.5)
        assert result["stop_triggered"] is True


class TestTrailingStopLoss:
    """追踪止损测试"""

    def test_设置追踪止损_初始化最高价等于入场价(self):
        """测试设置追踪止损初始化"""
        st = StopLossTakeProfit()
        st.set_trailing_stop_loss("000001.SZ", entry_price=10.0, trailing_delta=0.05)
        info = st.get_stop_info("000001.SZ")
        assert info["highest_price"] == 10.0
        assert info["current_stop"] == 10.0

    def test_追踪止损_价格上涨提高止损位(self):
        """测试追踪止损价格上涨时提高止损位"""
        st = StopLossTakeProfit()
        st.set_trailing_stop_loss("000001.SZ", entry_price=10.0, trailing_delta=0.10)

        # 价格上涨到 15
        st.check_trigger("000001.SZ", current_price=15.0)
        info = st.get_stop_info("000001.SZ")
        assert info["current_stop"] == pytest.approx(15.0 * 0.90)  # 15 * (1 - 0.10) = 13.5

    def test_追踪止损_价格跌破止损位触发(self):
        """测试追踪止损触发"""
        st = StopLossTakeProfit()
        st.set_trailing_stop_loss("000001.SZ", entry_price=10.0, trailing_delta=0.10)

        # 价格上涨到 15，止损位提高到 13.5
        st.check_trigger("000001.SZ", current_price=15.0)

        # 价格跌破 13.5，触发止损
        result = st.check_trigger("000001.SZ", current_price=13.0)
        assert result["stop_triggered"] is True

    def test_追踪止损_价格未跌破不触发(self):
        """测试追踪止损未触发"""
        st = StopLossTakeProfit()
        st.set_trailing_stop_loss("000001.SZ", entry_price=10.0, trailing_delta=0.10)

        st.check_trigger("000001.SZ", current_price=12.0)
        result = st.check_trigger("000001.SZ", current_price=11.0)
        assert result["stop_triggered"] is False


class TestATRStopLoss:
    """ATR止损测试"""

    def test_设置ATR止损_计算止损价(self):
        """测试设置ATR止损"""
        st = StopLossTakeProfit()
        st.set_atr_stop_loss("000001.SZ", entry_price=10.0, atr=0.5, atr_multiplier=2.0)
        info = st.get_stop_info("000001.SZ")
        assert info["stop_price"] == pytest.approx(9.0)  # 10 - 0.5 * 2.0

    def test_ATR止损_触发条件_价格跌破止损价(self):
        """测试ATR止损触发"""
        st = StopLossTakeProfit()
        st.set_atr_stop_loss("000001.SZ", entry_price=10.0, atr=0.5, atr_multiplier=2.0)
        result = st.check_trigger("000001.SZ", current_price=8.5)
        assert result["stop_triggered"] is True

    def test_ATR止损_未触发_价格高于止损价(self):
        """测试ATR止损未触发"""
        st = StopLossTakeProfit()
        st.set_atr_stop_loss("000001.SZ", entry_price=10.0, atr=0.5, atr_multiplier=2.0)
        result = st.check_trigger("000001.SZ", current_price=9.5)
        assert result["stop_triggered"] is False


class TestFixedTakeProfit:
    """固定止盈测试"""

    def test_设置固定止盈_默认比例(self):
        """测试设置固定止盈-默认比例"""
        st = StopLossTakeProfit()
        st.set_fixed_take_profit("000001.SZ", entry_price=10.0)
        info = st.get_take_profit_info("000001.SZ")
        assert info["take_price"] == pytest.approx(11.5)  # 10 * (1 + 0.15)

    def test_设置固定止盈_自定义价格(self):
        """测试设置固定止盈-自定义价格"""
        st = StopLossTakeProfit()
        st.set_fixed_take_profit("000001.SZ", entry_price=10.0, take_price=13.0)
        info = st.get_take_profit_info("000001.SZ")
        assert info["take_price"] == 13.0

    def test_固定止盈_触发条件_价格超过止盈价(self):
        """测试固定止盈触发"""
        st = StopLossTakeProfit()
        st.set_fixed_take_profit("000001.SZ", entry_price=10.0, take_ratio=0.10)
        result = st.check_trigger("000001.SZ", current_price=11.5)
        assert result["profit_triggered"] is True
        assert result["action"] == "profit"

    def test_固定止盈_未触发_价格低于止盈价(self):
        """测试固定止盈未触发"""
        st = StopLossTakeProfit()
        st.set_fixed_take_profit("000001.SZ", entry_price=10.0, take_ratio=0.10)
        result = st.check_trigger("000001.SZ", current_price=10.5)
        assert result["profit_triggered"] is False


class TestTrailingTakeProfit:
    """追踪止盈测试"""

    def test_设置追踪止盈_初始化最高价等于入场价(self):
        """测试设置追踪止盈初始化"""
        st = StopLossTakeProfit()
        st.set_trailing_take_profit("000001.SZ", entry_price=10.0, trailing_delta=0.03)
        info = st.get_take_profit_info("000001.SZ")
        assert info["highest_price"] == 10.0

    def test_追踪止盈_价格上涨提高止盈位并触发回落止损(self):
        """测试追踪止盈价格上涨后回落触发"""
        st = StopLossTakeProfit()
        st.set_trailing_take_profit("000001.SZ", entry_price=10.0, trailing_delta=0.05)

        # 价格上涨到 20
        st.check_trigger("000001.SZ", current_price=20.0)

        # 止盈位提高到 20 * 0.95 = 19
        info = st.get_take_profit_info("000001.SZ")
        assert info["current_take"] == pytest.approx(19.0)

        # 价格回落到 18，触发止盈
        result = st.check_trigger("000001.SZ", current_price=18.0)
        assert result["profit_triggered"] is True


class TestStopManagement:
    """止损止盈管理测试"""

    def test_禁用止损_检查不触发(self):
        """测试禁用止损后不触发"""
        st = StopLossTakeProfit()
        st.set_fixed_stop_loss("000001.SZ", entry_price=10.0, stop_price=9.5)
        st.disable_stop("000001.SZ")
        result = st.check_trigger("000001.SZ", current_price=9.0)
        assert result["stop_triggered"] is False

    def test_禁用止盈_检查不触发(self):
        """测试禁用止盈后不触发"""
        st = StopLossTakeProfit()
        st.set_fixed_take_profit("000001.SZ", entry_price=10.0, take_price=11.5)
        st.disable_take_profit("000001.SZ")
        result = st.check_trigger("000001.SZ", current_price=12.0)
        assert result["profit_triggered"] is False

    def test_移除止损止盈_信息返回None(self):
        """测试移除止损止盈后信息返回 None"""
        st = StopLossTakeProfit()
        st.set_fixed_stop_loss("000001.SZ", entry_price=10.0, stop_price=9.5)
        st.set_fixed_take_profit("000001.SZ", entry_price=10.0, take_price=11.5)

        st.remove("000001.SZ")

        assert st.get_stop_info("000001.SZ") is None
        assert st.get_take_profit_info("000001.SZ") is None

    def test_移除不存在的标的_无错误(self):
        """测试移除不存在的标的不报错"""
        st = StopLossTakeProfit()
        st.remove("NONEXIST.SZ")  # 不应报错
        assert True

    def test_获取所有活跃止损止盈(self):
        """测试获取所有活跃的止损止盈"""
        st = StopLossTakeProfit()
        st.set_fixed_stop_loss("000001.SZ", entry_price=10.0, stop_price=9.5)
        st.set_fixed_take_profit("600000.SH", entry_price=20.0, take_price=23.0)

        all_active = st.get_all_active()
        symbols = {item["symbol"] for item in all_active}
        assert "000001.SZ" in symbols
        assert "600000.SH" in symbols

    def test_获取活跃列表_为空时返回空列表(self):
        """测试无任何止损止盈时返回空列表"""
        st = StopLossTakeProfit()
        assert st.get_all_active() == []

    def test_同标的止损止盈同时设置_两者都触发检查(self):
        """测试同标的同时设置止损和止盈"""
        st = StopLossTakeProfit()
        st.set_fixed_stop_loss("000001.SZ", entry_price=10.0, stop_price=9.5)
        st.set_fixed_take_profit("000001.SZ", entry_price=10.0, take_price=11.5)

        # 价格触发止损
        result = st.check_trigger("000001.SZ", current_price=9.0)
        assert result["stop_triggered"] is True
        assert result["profit_triggered"] is False

        # 重置后再测试触发止盈
        st2 = StopLossTakeProfit()
        st2.set_fixed_stop_loss("000001.SZ", entry_price=10.0, stop_price=9.5)
        st2.set_fixed_take_profit("000001.SZ", entry_price=10.0, take_price=11.5)

        result2 = st2.check_trigger("000001.SZ", current_price=12.0)
        assert result2["profit_triggered"] is True
        assert result2["stop_triggered"] is False

    def test_不存在的标的_检查返回空结果(self):
        """测试不存在的标的检查返回空结果"""
        st = StopLossTakeProfit()
        result = st.check_trigger("NONEXIST.SZ", current_price=10.0)
        assert result["stop_triggered"] is False
        assert result["profit_triggered"] is False
        assert result["action"] is None
