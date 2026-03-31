# TradingAgents-CN 仓位风控规则
# Position-based Risk Rules

from typing import Any, Dict
from .base import RiskRule, RuleType, RuleResult


class MaxPositionSizeRule(RiskRule):
    """单只股票最大持仓数量规则

    Args:
        max_quantity: 最大持仓数量
    """

    def __init__(self, max_quantity: int, name: str = None):
        super().__init__(name or "MaxPositionSize")
        self.max_quantity = max_quantity

    def check(self, context: Dict[str, Any]) -> RuleResult:
        portfolio = context.get("portfolio")
        symbol = context.get("order", {}).get("symbol", "")

        current_qty = 0
        if portfolio and symbol:
            position = portfolio.get_position(symbol)
            current_qty = position.quantity if position else 0

        new_qty = current_qty + context.get("order", {}).get("quantity", 0)
        passed = new_qty <= self.max_quantity

        return RuleResult(
            passed=passed,
            rule_name=self.name,
            rule_type=RuleType.POSITION,
            message=f"Symbol {symbol}: {new_qty} {'<=' if passed else '>'} {self.max_quantity}",
            details={
                "current_quantity": current_qty,
                "order_quantity": context.get("order", {}).get("quantity", 0),
                "new_quantity": new_qty,
                "max_quantity": self.max_quantity,
            }
        )


class MaxTotalPositionRule(RiskRule):
    """总持仓市值上限规则

    Args:
        max_total_value: 最大总持仓市值
        max_ratio: 最大持仓占总资金比例（与 max_total_value 二选一）
    """

    def __init__(self, max_total_value: float = None, max_ratio: float = None, name: str = None):
        super().__init__(name or "MaxTotalPosition")
        if max_total_value is None and max_ratio is None:
            raise ValueError("必须指定 max_total_value 或 max_ratio")
        self.max_total_value = max_total_value
        self.max_ratio = max_ratio

    def check(self, context: Dict[str, Any]) -> RuleResult:
        portfolio = context.get("portfolio")
        total_value = portfolio.get_total_value() if portfolio else 0
        cash = portfolio.get_cash() if portfolio else 0
        total_assets = total_value + cash

        # 计算上限
        if self.max_total_value:
            limit = self.max_total_value
        else:
            limit = total_assets * self.max_ratio

        # 订单涉及市值
        order = context.get("order", {})
        order_value = order.get("quantity", 0) * order.get("price", 0)
        if portfolio:
            # 买入时增加持仓，卖出时减少
            if order.get("side") == "BUY":
                new_total = total_value + order_value
            else:
                new_total = total_value - order_value
        else:
            new_total = total_value

        passed = new_total <= limit

        return RuleResult(
            passed=passed,
            rule_name=self.name,
            rule_type=RuleType.POSITION,
            message=f"Total position {new_total:.2f} {'<=' if passed else '>'} {limit:.2f}",
            details={
                "current_position_value": total_value,
                "order_value": order_value,
                "new_position_value": new_total,
                "limit": limit,
            }
        )


class MinCashBalanceRule(RiskRule):
    """最小现金余额规则

    Args:
        min_cash: 最小现金余额
        min_ratio: 最小现金占总资产比例（与 min_cash 二选一）
    """

    def __init__(self, min_cash: float = None, min_ratio: float = 0.05, name: str = None):
        super().__init__(name or "MinCashBalance")
        if min_cash is None and min_ratio is None:
            min_ratio = 0.05  # 默认保留 5%
        self.min_cash = min_cash
        self.min_ratio = min_ratio

    def check(self, context: Dict[str, Any]) -> RuleResult:
        portfolio = context.get("portfolio")
        cash = portfolio.get_cash() if portfolio else 0
        total_value = portfolio.get_total_value() if portfolio else 0
        total_assets = cash + total_value

        # 计算下限
        if self.min_cash:
            limit = self.min_cash
        else:
            limit = total_assets * self.min_ratio

        # 订单涉及金额
        order = context.get("order", {})
        order_value = order.get("quantity", 0) * order.get("price", 0)

        if order.get("side") == "BUY":
            new_cash = cash - order_value
        else:
            new_cash = cash + order_value

        passed = new_cash >= limit

        return RuleResult(
            passed=passed,
            rule_name=self.name,
            rule_type=RuleType.POSITION,
            message=f"Cash {new_cash:.2f} {'>=' if passed else '<'} {limit:.2f}",
            details={
                "current_cash": cash,
                "order_value": order_value,
                "new_cash": new_cash,
                "min_cash": limit,
            }
        )


class MaxSingleStockExposureRule(RiskRule):
    """单只股票最大仓位占比规则

    Args:
        max_ratio: 单只股票最大占总持仓比例
    """

    def __init__(self, max_ratio: float = 0.2, name: str = None):
        super().__init__(name or "MaxSingleStockExposure")
        self.max_ratio = max_ratio

    def check(self, context: Dict[str, Any]) -> RuleResult:
        portfolio = context.get("portfolio")
        order = context.get("order", {})
        symbol = order.get("symbol", "")

        total_value = portfolio.get_total_value() if portfolio else 0
        cash = portfolio.get_cash() if portfolio else 0
        total_assets = total_value + cash

        # 当前持仓
        current_position_value = 0
        if portfolio and symbol:
            position = portfolio.get_position(symbol)
            if position:
                current_position_value = position.quantity * position.current_price

        # 订单涉及金额
        order_value = order.get("quantity", 0) * order.get("price", 0)
        if order.get("side") == "BUY":
            new_position_value = current_position_value + order_value
        else:
            new_position_value = current_position_value - order_value

        # 计算占比
        new_ratio = new_position_value / total_assets if total_assets > 0 else 0
        passed = new_ratio <= self.max_ratio

        return RuleResult(
            passed=passed,
            rule_name=self.name,
            rule_type=RuleType.POSITION,
            message=f"Symbol {symbol} ratio {new_ratio:.2%} {'<=' if passed else '>'} {self.max_ratio:.2%}",
            details={
                "symbol": symbol,
                "current_position_value": current_position_value,
                "order_value": order_value,
                "new_position_value": new_position_value,
                "total_assets": total_assets,
                "new_ratio": new_ratio,
                "max_ratio": self.max_ratio,
            }
        )
