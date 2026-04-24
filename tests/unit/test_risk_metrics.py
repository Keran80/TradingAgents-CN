# -*- coding: utf-8 -*-
"""
风险指标计算 单元测试

测试范围：
- VaR 计算 (历史法和参数法)
- 波动率计算
- 夏普比率
- 最大回撤
- 索提诺比率
- 持仓集中度
- Beta 计算
- 风险报告
"""
import pytest
import math

try:
    from tradingagents.risk.metrics import RiskMetrics
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装", allow_module_level=True)


class TestRiskVaR:
    """VaR 计算测试"""

    def test_历史法VaR_正常情况(self):
        """测试历史法 VaR 计算"""
        returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.005, -0.015]
        var = RiskMetrics.calculate_var(returns, confidence=0.95)
        assert var is not None
        assert var < 0  # VaR 为负

    def test_历史法VaR_置信度越高VaR越大(self):
        """测试置信度对 VaR 的影响"""
        returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.05, 0.005, -0.03]
        var_95 = RiskMetrics.calculate_var(returns, confidence=0.95)
        var_99 = RiskMetrics.calculate_var(returns, confidence=0.99)
        assert var_99 <= var_95  # 更高置信度 = 更大损失（更小的负数或更大绝对值）

    def test_空列表VaR返回0(self):
        """测试空列表返回 0"""
        assert RiskMetrics.calculate_var([]) == 0.0

    def test_单元素VaR返回0(self):
        """测试单元素返回 0"""
        assert RiskMetrics.calculate_var([0.01]) == 0.0

    def test_参数法VaR_需要scipy_跳过(self):
        """测试参数法 VaR 计算 - 需要 scipy"""
        try:
            import scipy.stats  # noqa: F401
            returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.005, -0.015]
            var = RiskMetrics.calculate_var(returns, confidence=0.95, method="parametric")
            assert var is not None
        except ImportError:
            pytest.skip("scipy 未安装")

    def test_未知方法VaR返回0(self):
        """测试未知方法返回 0"""
        returns = [0.01, -0.02, 0.03]
        assert RiskMetrics.calculate_var(returns, method="unknown") == 0.0


class TestRiskVolatility:
    """波动率计算测试"""

    def test_波动率_正常情况(self):
        """测试波动率计算"""
        returns = [0.01, -0.02, 0.03, -0.01, 0.02]
        vol = RiskMetrics.calculate_volatility(returns)
        assert vol > 0

    def test_波动率_年化大于非年化(self):
        """测试年化波动率大于非年化"""
        returns = [0.01, -0.02, 0.03, -0.01, 0.02]
        vol_annual = RiskMetrics.calculate_volatility(returns, annualize=True)
        vol_daily = RiskMetrics.calculate_volatility(returns, annualize=False)
        assert vol_annual > vol_daily

    def test_波动率_空列表返回0(self):
        """测试空列表返回 0"""
        assert RiskMetrics.calculate_volatility([]) == 0.0

    def test_波动率_单元素返回0(self):
        """测试单元素返回 0"""
        assert RiskMetrics.calculate_volatility([0.01]) == 0.0

    def test_波动率_零方差返回0(self):
        """测试相同收益率时波动率为 0"""
        returns = [0.01, 0.01, 0.01, 0.01]
        vol = RiskMetrics.calculate_volatility(returns, annualize=False)
        assert vol == 0.0


class TestRiskSharpe:
    """夏普比率测试"""

    def test_夏普比率_正收益为正(self):
        """测试正收益时夏普比率为正"""
        returns = [0.01, 0.02, 0.015, 0.01, 0.02]
        sharpe = RiskMetrics.calculate_sharpe_ratio(returns)
        assert sharpe > 0

    def test_夏普比率_负收益为负或较低(self):
        """测试负收益时夏普比率较低"""
        returns = [-0.01, -0.02, -0.015, -0.01, -0.02]
        sharpe = RiskMetrics.calculate_sharpe_ratio(returns)
        assert sharpe < 0

    def test_夏普比率_空列表返回0(self):
        """测试空列表返回 0"""
        assert RiskMetrics.calculate_sharpe_ratio([]) == 0.0

    def test_夏普比率_标准差为0时返回0(self):
        """测试标准差为 0 时返回 0"""
        returns = [0.01, 0.01, 0.01, 0.01]
        assert RiskMetrics.calculate_sharpe_ratio(returns) == 0.0

    def test_夏普比率_自定义无风险利率(self):
        """测试自定义无风险利率"""
        returns = [0.02, 0.01, 0.03, 0.015, 0.025]
        sharpe_low = RiskMetrics.calculate_sharpe_ratio(returns, risk_free_rate=0.01)
        sharpe_high = RiskMetrics.calculate_sharpe_ratio(returns, risk_free_rate=0.10)
        assert sharpe_low > sharpe_high


class TestRiskMaxDrawdown:
    """最大回撤测试"""

    def test_最大回撤_正常下跌情况(self):
        """测试正常下跌情况"""
        values = [100, 110, 105, 90, 85, 95]
        result = RiskMetrics.calculate_max_drawdown(values)
        assert result["max_drawdown"] > 0
        assert result["max_drawdown"] < 1.0

    def test_最大回撤_持续上涨回撤为0(self):
        """测试持续上涨时回撤为 0"""
        values = [100, 105, 110, 115, 120]
        result = RiskMetrics.calculate_max_drawdown(values)
        assert result["max_drawdown"] == 0.0

    def test_最大回撤_返回包含回撤序列(self):
        """测试返回包含回撤序列"""
        values = [100, 90, 80, 85, 90]
        result = RiskMetrics.calculate_max_drawdown(values)
        assert len(result["drawdown"]) == len(values)

    def test_最大回撤_空列表返回默认值(self):
        """测试空列表返回默认值"""
        result = RiskMetrics.calculate_max_drawdown([])
        assert result["max_drawdown"] == 0.0
        assert result["peak_index"] == 0

    def test_最大回撤_单元素返回默认值(self):
        """测试单元素返回默认值"""
        result = RiskMetrics.calculate_max_drawdown([100])
        assert result["max_drawdown"] == 0.0


class TestRiskSortino:
    """索提诺比率测试"""

    def test_索提诺比率_正常情况(self):
        """测试索提诺比率计算"""
        returns = [0.02, -0.01, 0.03, -0.005, 0.015]
        ratio = RiskMetrics.calculate_sortino_ratio(returns)
        assert ratio is not None

    def test_索提诺比率_空列表返回0(self):
        """测试空列表返回 0"""
        assert RiskMetrics.calculate_sortino_ratio([]) == 0.0

    def test_索提诺比率_无下行波动返回0(self):
        """测试无下行波动时返回 0"""
        returns = [0.01, 0.02, 0.015, 0.01]
        assert RiskMetrics.calculate_sortino_ratio(returns) == 0.0


class TestRiskConcentration:
    """持仓集中度测试"""

    def test_集中度_单只股票占比100(self):
        """测试单只股票时占比 100%"""
        positions = {"000001.SZ": 100000.0}
        result = RiskMetrics.calculate_position_concentration(positions)
        assert result["top1"] == pytest.approx(1.0)
        assert result["top5"] == pytest.approx(1.0)

    def test_集中度_均匀分布多只股票(self):
        """测试均匀分布时集中度"""
        positions = {
            "000001.SZ": 20000.0,
            "600000.SH": 20000.0,
            "300001.SZ": 20000.0,
        }
        result = RiskMetrics.calculate_position_concentration(positions)
        assert result["top1"] == pytest.approx(1.0 / 3, rel=1e-3)

    def test_集中度_HHI计算(self):
        """测试 HHI 计算"""
        positions = {"A": 50.0, "B": 50.0}
        result = RiskMetrics.calculate_position_concentration(positions)
        # HHI = (0.5)^2 + (0.5)^2 = 0.5
        assert result["hhi"] == pytest.approx(0.5)

    def test_集中度_空持仓返回0(self):
        """测试空持仓返回 0"""
        result = RiskMetrics.calculate_position_concentration({})
        assert result["concentration_ratio"] == 0.0
        assert result["top1"] == 0.0
        assert result["hhi"] == 0.0

    def test_集中度_总资产为0返回0(self):
        """测试总资产为 0 时返回 0"""
        positions = {"A": 0.0, "B": 0.0}
        result = RiskMetrics.calculate_position_concentration(positions)
        assert result["concentration_ratio"] == 0.0


class TestRiskBeta:
    """Beta 计算测试"""

    def test_Beta_与基准完全一致时为1(self):
        """测试与基准一致时 Beta 为 1"""
        returns = [0.01, 0.02, -0.01, 0.03]
        benchmark = [0.01, 0.02, -0.01, 0.03]
        beta = RiskMetrics.calculate_beta(returns, benchmark)
        assert beta == pytest.approx(1.0, rel=1e-3)

    def test_Beta_反向变动为负(self):
        """测试反向变动时 Beta 为负"""
        returns = [0.02, -0.02, 0.02, -0.02]
        benchmark = [-0.02, 0.02, -0.02, 0.02]
        beta = RiskMetrics.calculate_beta(returns, benchmark)
        assert beta < 0

    def test_Beta_长度不等返回1(self):
        """测试长度不等时返回 1"""
        returns = [0.01, 0.02, 0.03]
        benchmark = [0.01, 0.02]
        assert RiskMetrics.calculate_beta(returns, benchmark) == 1.0

    def test_Beta_长度不足2返回1(self):
        """测试长度不足 2 时返回 1"""
        returns = [0.01]
        benchmark = [0.01]
        assert RiskMetrics.calculate_beta(returns, benchmark) == 1.0


class TestRiskReport:
    """风险报告测试"""

    def test_风险报告包含所有指标(self):
        """测试风险报告包含所有关键指标"""
        returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.005, -0.015]
        portfolio = {
            "positions": [
                {"symbol": "000001.SZ", "market_value": 50000.0},
                {"symbol": "600000.SH", "market_value": 30000.0},
            ]
        }

        rm = RiskMetrics()
        report = rm.get_risk_report(portfolio, returns)

        assert "volatility" in report
        assert "sharpe_ratio" in report
        assert "sortino_ratio" in report
        assert "var_95" in report
        assert "var_99" in report
        assert "max_drawdown" in report
        assert "concentration" in report

    def test_风险报告含基准时包含beta(self):
        """测试含基准收益率时报告包含 Beta"""
        returns = [0.01, -0.02, 0.03, -0.01]
        benchmark = [0.005, -0.01, 0.02, -0.005]
        portfolio = {"positions": []}

        rm = RiskMetrics()
        report = rm.get_risk_report(portfolio, returns, benchmark)
        assert "beta" in report

    def test_风险报告_空仓位集中度为0(self):
        """测试空仓位时集中度为 0"""
        returns = [0.01, -0.01]
        portfolio = {"positions": []}

        rm = RiskMetrics()
        report = rm.get_risk_report(portfolio, returns)
        assert report["concentration"]["top1"] == 0.0
