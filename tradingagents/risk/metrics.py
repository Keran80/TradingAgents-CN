# TradingAgents-CN 风险指标计算
# Risk Metrics Calculation

from typing import Dict, List, Optional
import math


class RiskMetrics:
    """风险指标计算器

    计算 VaR、波动率、夏普比率等风险指标

    使用示例:
        metrics = RiskMetrics()

        # 计算 VaR
        var_95 = metrics.calculate_var(returns, confidence=0.95)

        # 计算波动率
        vol = metrics.calculate_volatility(returns)

        # 获取完整风险报告
        report = metrics.get_risk_report(portfolio, returns)
    """

    @staticmethod
    def calculate_var(
        returns: List[float],
        confidence: float = 0.95,
        method: str = "historical"
    ) -> float:
        """
        计算 Value at Risk (VaR)

        Args:
            returns: 收益率列表
            confidence: 置信度（默认 95%）
            method: 计算方法 "historical" 或 "parametric"

        Returns:
            VaR 值（负数表示损失）
        """
        if not returns or len(returns) < 2:
            return 0.0

        if method == "historical":
            sorted_returns = sorted(returns)
            index = int((1 - confidence) * len(sorted_returns))
            return sorted_returns[max(0, index)]

        elif method == "parametric":
            mean = sum(returns) / len(returns)
            variance = sum((r - mean) ** 2 for r in returns) / len(returns)
            std = math.sqrt(variance)

            # 正态分布分位数
            from scipy.stats import norm
            z = norm.ppf(1 - confidence)
            return mean + z * std

        return 0.0

    @staticmethod
    def calculate_volatility(returns: List[float], annualize: bool = True) -> float:
        """
        计算波动率

        Args:
            returns: 收益率列表
            annualize: 是否年化

        Returns:
            波动率
        """
        if not returns or len(returns) < 2:
            return 0.0

        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)

        vol = math.sqrt(variance)
        if annualize:
            # 假设日频数据，年化系数 16（A股交易日约 250 的平方根约 16）
            vol = vol * 16

        return vol

    @staticmethod
    def calculate_sharpe_ratio(
        returns: List[float],
        risk_free_rate: float = 0.03,
        annualize: bool = True
    ) -> float:
        """
        计算夏普比率

        Args:
            returns: 收益率列表
            risk_free_rate: 无风险利率（年化）
            annualize: 是否年化

        Returns:
            夏普比率
        """
        if not returns or len(returns) < 2:
            return 0.0

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std = math.sqrt(variance)

        if std == 0:
            return 0.0

        if annualize:
            mean_return = mean_return * 250  # 年化收益
            std = std * 16  # 年化波动率
            risk_free_rate = risk_free_rate

        return (mean_return - risk_free_rate) / std

    @staticmethod
    def calculate_max_drawdown(values: List[float]) -> Dict:
        """
        计算最大回撤

        Args:
            values: 资产净值列表

        Returns:
            {"max_drawdown": float, "drawdown": List[float], "peak_index": int, "trough_index": int}
        """
        if not values or len(values) < 2:
            return {"max_drawdown": 0.0, "drawdown": [], "peak_index": 0, "trough_index": 0}

        peak = values[0]
        peak_index = 0
        max_drawdown = 0.0
        trough_index = 0
        drawdowns = []

        for i, value in enumerate(values):
            if value > peak:
                peak = value
                peak_index = i

            drawdown = (peak - value) / peak if peak > 0 else 0
            drawdowns.append(drawdown)

            if drawdown > max_drawdown:
                max_drawdown = drawdown
                trough_index = i

        return {
            "max_drawdown": max_drawdown,
            "drawdown": drawdowns,
            "peak_index": peak_index,
            "trough_index": trough_index,
        }

    @staticmethod
    def calculate_sortino_ratio(
        returns: List[float],
        target_return: float = 0.0,
        risk_free_rate: float = 0.03
    ) -> float:
        """
        计算索提诺比率

        Args:
            returns: 收益率列表
            target_return: 目标收益
            risk_free_rate: 无风险利率

        Returns:
            索提诺比率
        """
        if not returns:
            return 0.0

        mean_return = sum(returns) / len(returns)
        downside_returns = [min(0, r - target_return) for r in returns]
        downside_variance = sum(r ** 2 for r in downside_returns) / len(returns)

        if downside_variance == 0:
            return 0.0

        downside_std = math.sqrt(downside_variance)
        return (mean_return - risk_free_rate) / downside_std

    @staticmethod
    def calculate_position_concentration(positions: Dict[str, float]) -> Dict:
        """
        计算持仓集中度

        Args:
            positions: {symbol: market_value}

        Returns:
            集中度指标
        """
        if not positions:
            return {"concentration_ratio": 0.0, "top1": 0.0, "top5": 0.0, "hhi": 0.0}

        total = sum(positions.values())
        if total == 0:
            return {"concentration_ratio": 0.0, "top1": 0.0, "top5": 0.0, "hhi": 0.0}

        sorted_positions = sorted(positions.values(), reverse=True)

        # Top-N 集中度
        top1 = sorted_positions[0] / total if len(sorted_positions) > 0 else 0
        top5 = sum(sorted_positions[:min(5, len(sorted_positions))]) / total

        # HHI (Herfindahl-Hirschman Index)
        hhi = sum((v / total) ** 2 for v in positions.values())

        return {
            "concentration_ratio": top5,
            "top1": top1,
            "top5": top5,
            "hhi": hhi,
        }

    @staticmethod
    def calculate_beta(returns: List[float], benchmark_returns: List[float]) -> float:
        """
        计算 Beta

        Args:
            returns: 资产收益率
            benchmark_returns: 基准收益率

        Returns:
            Beta 值
        """
        if len(returns) != len(benchmark_returns) or len(returns) < 2:
            return 1.0

        mean_return = sum(returns) / len(returns)
        mean_benchmark = sum(benchmark_returns) / len(benchmark_returns)

        covariance = sum(
            (r - mean_return) * (b - mean_benchmark)
            for r, b in zip(returns, benchmark_returns)
        ) / len(returns)

        benchmark_variance = sum(
            (b - mean_benchmark) ** 2 for b in benchmark_returns
        ) / len(benchmark_returns)

        if benchmark_variance == 0:
            return 1.0

        return covariance / benchmark_variance

    def get_risk_report(
        self,
        portfolio_summary: Dict,
        returns: List[float],
        benchmark_returns: Optional[List[float]] = None
    ) -> Dict:
        """
        获取完整风险报告

        Args:
            portfolio_summary: 账户摘要
            returns: 收益率列表
            benchmark_returns: 基准收益率（可选）

        Returns:
            风险报告
        """
        report = {
            "volatility": self.calculate_volatility(returns),
            "sharpe_ratio": self.calculate_sharpe_ratio(returns),
            "sortino_ratio": self.calculate_sortino_ratio(returns),
            "var_95": self.calculate_var(returns, confidence=0.95),
            "var_99": self.calculate_var(returns, confidence=0.99),
            "max_drawdown": self.calculate_max_drawdown(
                [1 + r for r in returns]
            )["max_drawdown"],
        }

        if benchmark_returns:
            report["beta"] = self.calculate_beta(returns, benchmark_returns)

        # 持仓集中度
        positions = {
            p["symbol"]: p["market_value"]
            for p in portfolio_summary.get("positions", [])
        }
        report["concentration"] = self.calculate_position_concentration(positions)

        return report
