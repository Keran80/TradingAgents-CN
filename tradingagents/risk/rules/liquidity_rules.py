# TradingAgents-CN 流动性风控规则
# Liquidity-based Risk Rules

from typing import Any, Dict
from .base import RiskRule, RuleType, RuleResult


class MinVolumeRule(RiskRule):
    """最小成交量规则

    检查股票日成交量是否满足要求

    Args:
        min_volume: 最小日成交量（股数）
    """

    def __init__(self, min_volume: int = 100000, name: str = None):
        super().__init__(name or "MinVolume")
        self.min_volume = min_volume

    def check(self, context: Dict[str, Any]) -> RuleResult:
        order = context.get("order", {})
        market_data = context.get("market_data", {})
        symbol = order.get("symbol", "")

        volume = market_data.get("volume", 0)
        passed = volume >= self.min_volume

        return RuleResult(
            passed=passed,
            rule_name=self.name,
            rule_type=RuleType.LIQUIDITY,
            message=f"{symbol} volume {volume} {'>=' if passed else '<'} {self.min_volume}",
            details={
                "symbol": symbol,
                "volume": volume,
                "min_volume": self.min_volume,
            }
        )


class MinTurnoverRule(RiskRule):
    """最小成交额规则

    检查股票日成交额是否满足要求

    Args:
        min_turnover: 最小日成交额（元）
    """

    def __init__(self, min_turnover: float = 1000000.0, name: str = None):
        super().__init__(name or "MinTurnover")
        self.min_turnover = min_turnover

    def check(self, context: Dict[str, Any]) -> RuleResult:
        order = context.get("order", {})
        market_data = context.get("market_data", {})
        symbol = order.get("symbol", "")

        volume = market_data.get("volume", 0)
        close = market_data.get("close", 0) or market_data.get("last_price", 0)
        turnover = volume * close
        passed = turnover >= self.min_turnover

        return RuleResult(
            passed=passed,
            rule_name=self.name,
            rule_type=RuleType.LIQUIDITY,
            message=f"{symbol} turnover {turnover:.2f} {'>=' if passed else '<'} {self.min_turnover:.2f}",
            details={
                "symbol": symbol,
                "turnover": turnover,
                "min_turnover": self.min_turnover,
            }
        )


class MaxOrderSizeRatioRule(RiskRule):
    """订单量占成交量比例规则

    防止大单对市场造成过大冲击

    Args:
        max_ratio: 订单量占日成交量的最大比例
    """

    def __init__(self, max_ratio: float = 0.01, name: str = None):
        super().__init__(name or "MaxOrderSizeRatio")
        self.max_ratio = max_ratio

    def check(self, context: Dict[str, Any]) -> RuleResult:
        order = context.get("order", {})
        market_data = context.get("market_data", {})
        symbol = order.get("symbol", "")

        order_qty = order.get("quantity", 0)
        volume = market_data.get("volume", 0)

        if volume <= 0:
            return RuleResult(
                passed=True,
                rule_name=self.name,
                rule_type=RuleType.LIQUIDITY,
                message=f"No volume data for {symbol}, skipped",
                details={"reason": "no_volume_data"}
            )

        ratio = order_qty / volume
        passed = ratio <= self.max_ratio

        return RuleResult(
            passed=passed,
            rule_name=self.name,
            rule_type=RuleType.LIQUIDITY,
            message=f"{symbol} order ratio {ratio:.2%} {'<=' if passed else '>'} {self.max_ratio:.2%}",
            details={
                "symbol": symbol,
                "order_quantity": order_qty,
                "volume": volume,
                "ratio": ratio,
                "max_ratio": self.max_ratio,
            }
        )
