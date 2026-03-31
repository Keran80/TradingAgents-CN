# TradingAgents-CN 风控规则基类
# Base Risk Rule Classes

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime


class RuleType(Enum):
    """风控规则类型"""
    POSITION = "position"           # 仓位相关规则
    ORDER = "order"                 # 订单相关规则
    PRICE = "price"                 # 价格相关规则
    LIQUIDITY = "liquidity"         # 流动性规则
    VOLATILITY = "volatility"       # 波动率规则
    CUSTOM = "custom"               # 自定义规则


@dataclass
class RuleResult:
    """规则检查结果"""
    passed: bool                           # 是否通过
    rule_name: str                          # 规则名称
    rule_type: RuleType                     # 规则类型
    message: str = ""                       # 检查消息
    details: Dict[str, Any] = field(default_factory=dict)  # 详细信息
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "rule_name": self.rule_name,
            "rule_type": self.rule_type.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


class RiskRule(ABC):
    """风控规则基类

    所有风控规则需继承此类并实现 check 方法。

    使用示例:
        class MaxPositionRule(RiskRule):
            def __init__(self, max_position: float):
                self.max_position = max_position

            def check(self, context: Dict) -> RuleResult:
                current = context.get("position_value", 0)
                return RuleResult(
                    passed=current <= self.max_position,
                    rule_name=self.__class__.__name__,
                    rule_type=RuleType.POSITION,
                    message=f"Position {current} <= {self.max_position}"
                )
    """

    def __init__(self, name: Optional[str] = None, enabled: bool = True):
        """
        Args:
            name: 规则名称，默认使用类名
            enabled: 是否启用，默认启用
        """
        self.name = name or self.__class__.__name__
        self.enabled = enabled

    @abstractmethod
    def check(self, context: Dict[str, Any]) -> RuleResult:
        """
        检查规则是否通过

        Args:
            context: 包含以下键的上下文字典:
                - portfolio: Portfolio 对象
                - order: Order 对象（可选）
                - market_data: 市场数据（可选）
                - timestamp: 当前时间戳

        Returns:
            RuleResult: 规则检查结果
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, enabled={self.enabled})>"
