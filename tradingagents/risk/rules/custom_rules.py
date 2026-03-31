# TradingAgents-CN 自定义风控规则
# Custom Risk Rules

from typing import Any, Callable, Dict
from .base import RiskRule, RuleType, RuleResult


class CustomRiskRule(RiskRule):
    """自定义风控规则

    使用函数定义复杂的风控逻辑

    Args:
        check_func: 检查函数，签名为 (context: Dict) -> RuleResult
        name: 规则名称
    """

    def __init__(
        self,
        check_func: Callable[[Dict[str, Any]], RuleResult],
        name: str = "CustomRiskRule"
    ):
        super().__init__(name)
        self.check_func = check_func

    def check(self, context: Dict[str, Any]) -> RuleResult:
        try:
            return self.check_func(context)
        except Exception as e:
            return RuleResult(
                passed=False,
                rule_name=self.name,
                rule_type=RuleType.CUSTOM,
                message=f"Custom rule error: {str(e)}",
                details={"error": str(e)}
            )


class TimeBasedRule(RiskRule):
    """时段限制规则

    限制交易时段

    Args:
        allowed_hours: 允许交易的小时列表，如 [9, 10, 11, 13, 14, 15]
        timezone: 时区，默认 "Asia/Shanghai"
    """

    def __init__(
        self,
        allowed_hours: list = None,
        timezone: str = "Asia/Shanghai",
        name: str = None
    ):
        super().__init__(name or "TimeBased")
        self.allowed_hours = allowed_hours or [9, 10, 11, 13, 14, 15]  # A股交易时段
        self.timezone = timezone

    def check(self, context: Dict[str, Any]) -> RuleResult:
        from datetime import datetime
        import pytz

        timestamp = context.get("timestamp", datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        # 转换为上海时区
        if timestamp.tzinfo is None:
            tz = pytz.timezone(self.timezone)
            timestamp = tz.localize(timestamp)
        else:
            timestamp = timestamp.astimezone(pytz.timezone(self.timezone))

        current_hour = timestamp.hour
        passed = current_hour in self.allowed_hours

        return RuleResult(
            passed=passed,
            rule_name=self.name,
            rule_type=RuleType.CUSTOM,
            message=f"Current hour {current_hour} {'in' if passed else 'not in'} allowed hours {self.allowed_hours}",
            details={
                "current_hour": current_hour,
                "allowed_hours": self.allowed_hours,
            }
        )


class MaxDailyTradeCountRule(RiskRule):
    """每日最大交易次数规则

    Args:
        max_count: 每日最大交易次数
    """

    def __init__(self, max_count: int = 20, name: str = None):
        super().__init__(name or "MaxDailyTradeCount")
        self.max_count = max_count
        self._daily_counts: Dict[str, int] = {}  # {date: count}

    def check(self, context: Dict[str, Any]) -> RuleResult:
        from datetime import datetime

        timestamp = context.get("timestamp", datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        date_key = timestamp.strftime("%Y-%m-%d")

        # 获取当前计数
        current_count = self._daily_counts.get(date_key, 0)

        # 如果是新的一天，重置计数
        today_key = datetime.now().strftime("%Y-%m-%d")
        if date_key != today_key:
            self._daily_counts = {date_key: current_count}

        # 检查是否超过限制
        passed = current_count < self.max_count

        return RuleResult(
            passed=passed,
            rule_name=self.name,
            rule_type=RuleType.CUSTOM,
            message=f"Daily trades {current_count} {'<' if passed else '>='} {self.max_count}",
            details={
                "date": date_key,
                "current_count": current_count,
                "max_count": self.max_count,
            }
        )

    def record_trade(self):
        """记录一笔交易"""
        from datetime import datetime
        date_key = datetime.now().strftime("%Y-%m-%d")
        self._daily_counts[date_key] = self._daily_counts.get(date_key, 0) + 1
