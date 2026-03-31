# TradingAgents-CN 风控拦截器
# Risk Interceptor

from typing import Any, Dict, List, Optional
from datetime import datetime

from .rules.base import RiskRule, RuleResult, RuleType
from .position_manager import PositionManager
from .stop_loss import StopLossTakeProfit
from .metrics import RiskMetrics


class RiskInterceptor:
    """风控拦截器

    在订单执行前/后进行风控检查

    使用示例:
        interceptor = RiskInterceptor()

        # 添加风控规则
        interceptor.add_rule(MaxPositionSizeRule(max_quantity=10000))
        interceptor.add_rule(MinCashBalanceRule(min_ratio=0.05))

        # 订单前检查
        result = interceptor.pre_check(order, portfolio, market_data)

        # 订单后检查
        interceptor.post_check(order, portfolio)
    """

    def __init__(self):
        self.rules: List[RiskRule] = []
        self.position_manager = PositionManager()
        self.stop_loss_tp = StopLossTakeProfit()
        self.metrics = RiskMetrics()
        self._check_history: List[Dict] = []

    def add_rule(self, rule: RiskRule):
        """添加风控规则"""
        self.rules.append(rule)

    def remove_rule(self, rule_name: str):
        """移除风控规则"""
        self.rules = [r for r in self.rules if r.name != rule_name]

    def get_enabled_rules(self) -> List[RiskRule]:
        """获取已启用的规则"""
        return [r for r in self.rules if r.enabled]

    def pre_check(
        self,
        order: Dict[str, Any],
        portfolio: Any,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        订单执行前风控检查

        Args:
            order: 订单字典，包含 symbol, side, quantity, price
            portfolio: Portfolio 对象
            market_data: 市场数据

        Returns:
            {
                "approved": bool,
                "results": [RuleResult],
                "failed_rules": [RuleResult],
                "message": str
            }
        """
        timestamp = datetime.now()
        context = {
            "order": order,
            "portfolio": portfolio,
            "market_data": market_data or {},
            "timestamp": timestamp,
        }

        results = []
        failed_rules = []

        for rule in self.get_enabled_rules():
            result = rule.check(context)
            results.append(result)
            if not result.passed:
                failed_rules.append(result)

        approved = len(failed_rules) == 0

        # 记录检查结果
        check_record = {
            "timestamp": timestamp,
            "order": order,
            "approved": approved,
            "total_rules": len(results),
            "passed": len(results) - len(failed_rules),
            "failed": len(failed_rules),
            "failed_rules": [r.rule_name for r in failed_rules],
        }
        self._check_history.append(check_record)

        # 生成消息
        if approved:
            message = f"订单通过风控检查 ({len(results)} 项规则全部通过)"
        else:
            message = f"订单被风控拦截 ({len(failed_rules)}/{len(results)} 项规则失败): "
            message += "; ".join([r.message for r in failed_rules[:3]])

        return {
            "approved": approved,
            "results": [r.to_dict() for r in results],
            "failed_rules": [r.to_dict() for r in failed_rules],
            "message": message,
        }

    def post_check(
        self,
        order: Dict[str, Any],
        portfolio: Any,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        订单执行后风控检查

        检查止损止盈是否触发等

        Args:
            order: 订单字典
            portfolio: Portfolio 对象
            market_data: 市场数据

        Returns:
            {
                "actions": [action],
                "stop_triggered": bool,
                "take_profit_triggered": bool
            }
        """
        symbol = order.get("symbol")
        actions = []

        # 检查止损止盈
        if market_data and symbol:
            current_price = market_data.get("close") or market_data.get("last_price")
            if current_price:
                triggered = self.stop_loss_tp.check_trigger(symbol, current_price)

                if triggered["action"] == "stop":
                    actions.append({
                        "type": "stop_loss",
                        "symbol": symbol,
                        "price": triggered["stop_price"],
                        "message": f"止损触发: {symbol}@{triggered['stop_price']}",
                    })

                elif triggered["action"] == "profit":
                    actions.append({
                        "type": "take_profit",
                        "symbol": symbol,
                        "price": triggered["take_price"],
                        "message": f"止盈触发: {symbol}@{triggered['take_price']}",
                    })

        return {
            "actions": actions,
            "stop_triggered": any(a["type"] == "stop_loss" for a in actions),
            "take_profit_triggered": any(a["type"] == "take_profit" for a in actions),
        }

    def check_all_positions(
        self,
        positions: Dict[str, float],
        prices: Dict[str, float]
    ) -> List[Dict]:
        """
        检查所有持仓的风险状态

        Args:
            positions: {symbol: quantity}
            prices: {symbol: current_price}

        Returns:
            风险信号列表
        """
        signals = []

        for symbol, quantity in positions.items():
            if symbol not in prices:
                continue

            price = prices[symbol]
            triggered = self.stop_loss_tp.check_trigger(symbol, price)

            if triggered["stop_triggered"]:
                signals.append({
                    "symbol": symbol,
                    "type": "stop_loss",
                    "price": price,
                    "stop_price": triggered["stop_price"],
                    "message": f"止损触发: {symbol} 当前价 {price}",
                })

            if triggered["take_profit_triggered"]:
                signals.append({
                    "symbol": symbol,
                    "type": "take_profit",
                    "price": price,
                    "take_price": triggered["take_price"],
                    "message": f"止盈触发: {symbol} 当前价 {price}",
                })

        return signals

    def get_check_history(self) -> List[Dict]:
        """获取检查历史"""
        return self._check_history.copy()

    def get_risk_summary(self) -> Dict:
        """获取风控摘要"""
        return {
            "total_rules": len(self.rules),
            "enabled_rules": len(self.get_enabled_rules()),
            "total_checks": len(self._check_history),
            "approved_checks": sum(1 for c in self._check_history if c["approved"]),
            "rejected_checks": sum(1 for c in self._check_history if not c["approved"]),
            "active_stops": len(self.stop_loss_tp.get_all_active()),
        }
