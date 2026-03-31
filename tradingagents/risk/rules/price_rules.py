# TradingAgents-CN 价格风控规则
# Price-based Risk Rules

from typing import Any, Dict
from .base import RiskRule, RuleType, RuleResult


class MaxOrderPriceDeviationRule(RiskRule):
    """订单价格偏离度规则

    检查订单价格与基准价格的偏离程度

    Args:
        max_deviation: 最大偏离比例（如 0.05 表示 5%）
    """

    def __init__(self, max_deviation: float = 0.05, name: str = None):
        super().__init__(name or "MaxPriceDeviation")
        self.max_deviation = max_deviation

    def check(self, context: Dict[str, Any]) -> RuleResult:
        order = context.get("order", {})
        market_data = context.get("market_data", {})

        order_price = order.get("price", 0)
        symbol = order.get("symbol", "")

        # 获取基准价格
        reference_price = market_data.get("close") or market_data.get("last_price")
        if not reference_price or reference_price <= 0:
            return RuleResult(
                passed=True,
                rule_name=self.name,
                rule_type=RuleType.PRICE,
                message=f"No reference price for {symbol}, skipped",
                details={"reason": "no_reference_price"}
            )

        # 计算偏离度
        deviation = abs(order_price - reference_price) / reference_price
        passed = deviation <= self.max_deviation

        return RuleResult(
            passed=passed,
            rule_name=self.name,
            rule_type=RuleType.PRICE,
            message=f"{symbol} deviation {deviation:.2%} {'<=' if passed else '>'} {self.max_deviation:.2%}",
            details={
                "order_price": order_price,
                "reference_price": reference_price,
                "deviation": deviation,
                "max_deviation": self.max_deviation,
            }
        )


class MinOrderPriceRule(RiskRule):
    """最小订单价格规则

    过滤价格过低的订单（如 ST 股、仙股）

    Args:
        min_price: 最小价格
    """

    def __init__(self, min_price: float = 0.01, name: str = None):
        super().__init__(name or "MinOrderPrice")
        self.min_price = min_price

    def check(self, context: Dict[str, Any]) -> RuleResult:
        order = context.get("order", {})
        order_price = order.get("price", 0)
        passed = order_price >= self.min_price

        return RuleResult(
            passed=passed,
            rule_name=self.name,
            rule_type=RuleType.PRICE,
            message=f"Order price {order_price} {'>=' if passed else '<'} {self.min_price}",
            details={
                "order_price": order_price,
                "min_price": self.min_price,
            }
        )


class MaxOrderPriceRule(RiskRule):
    """最大订单价格规则

    防止价格异常高的订单

    Args:
        max_price: 最大价格
    """

    def __init__(self, max_price: float = 100000.0, name: str = None):
        super().__init__(name or "MaxOrderPrice")
        self.max_price = max_price

    def check(self, context: Dict[str, Any]) -> RuleResult:
        order = context.get("order", {})
        order_price = order.get("price", 0)
        passed = order_price <= self.max_price

        return RuleResult(
            passed=passed,
            rule_name=self.name,
            rule_type=RuleType.PRICE,
            message=f"Order price {order_price} {'<=' if passed else '>'} {self.max_price}",
            details={
                "order_price": order_price,
                "max_price": self.max_price,
            }
        )
