# TradingAgents-CN 风控管理器
# Risk Manager

from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from .rules import (
    MaxPositionSizeRule,
    MaxTotalPositionRule,
    MinCashBalanceRule,
    MaxSingleStockExposureRule,
    MinVolumeRule,
    TimeBasedRule,
)
from .interceptor import RiskInterceptor
from .position_manager import PositionManager, PositionState
from .stop_loss import StopLossTakeProfit
from .metrics import RiskMetrics


class RiskManager:
    """风控管理器

    统一管理风控规则、仓位、止损止盈和风险指标

    使用示例:
        # 创建风控管理器
        rm = RiskManager(initial_cash=100000)

        # 配置规则
        rm.configure({
            "max_position_size": 10000,
            "max_total_position_ratio": 0.9,
            "min_cash_ratio": 0.05,
            "max_single_position_ratio": 0.2,
        })

        # 检查订单
        result = rm.check_order(order, portfolio)

        # 设置止损
        rm.set_stop_loss("000001.SZ", entry_price=10.0, stop_ratio=0.05)
    """

    def __init__(self, initial_cash: float = 100000.0):
        self.initial_cash = initial_cash
        self.interceptor = RiskInterceptor()
        self.position_manager = PositionManager(initial_cash=initial_cash)
        self.stop_loss_tp = StopLossTakeProfit()
        self.metrics = RiskMetrics()
        self._is_enabled = True
        self._custom_validators: List[Callable] = []

    def configure(self, config: Dict[str, Any]):
        """
        配置风控规则

        Args:
            config: {
                "max_position_size": int,
                "max_total_position_ratio": float,
                "min_cash_ratio": float,
                "max_single_position_ratio": float,
                "min_daily_volume": int,
                "allowed_trading_hours": list,
            }
        """
        # 清空现有规则
        self.interceptor.rules = []

        # 仓位规则
        if "max_position_size" in config:
            self.interceptor.add_rule(
                MaxPositionSizeRule(max_quantity=config["max_position_size"])
            )

        if "max_total_position_ratio" in config:
            self.interceptor.add_rule(
                MaxTotalPositionRule(max_ratio=config["max_total_position_ratio"])
            )

        if "min_cash_ratio" in config:
            self.interceptor.add_rule(
                MinCashBalanceRule(min_ratio=config["min_cash_ratio"])
            )

        if "max_single_position_ratio" in config:
            self.interceptor.add_rule(
                MaxSingleStockExposureRule(max_ratio=config["max_single_position_ratio"])
            )

        # 流动性规则
        if "min_daily_volume" in config:
            self.interceptor.add_rule(
                MinVolumeRule(min_volume=config["min_daily_volume"])
            )

        # 时段规则
        if "allowed_trading_hours" in config:
            self.interceptor.add_rule(
                TimeBasedRule(allowed_hours=config["allowed_trading_hours"])
            )

    def add_custom_rule(self, rule):
        """添加自定义规则"""
        self.interceptor.add_rule(rule)

    def check_order(
        self,
        order: Dict[str, Any],
        portfolio: Any,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        检查订单是否通过风控

        Args:
            order: 订单字典 {symbol, side, quantity, price}
            portfolio: Portfolio 对象
            market_data: 市场数据

        Returns:
            {
                "approved": bool,
                "message": str,
                "results": [...]
            }
        """
        if not self._is_enabled:
            return {
                "approved": True,
                "message": "风控已禁用",
                "results": [],
            }

        # 自定义验证器
        for validator in self._custom_validators:
            try:
                result = validator(order, portfolio, market_data)
                if not result.get("approved", True):
                    return result
            except Exception as e:
                return {
                    "approved": False,
                    "message": f"自定义验证失败: {str(e)}",
                    "results": [],
                }

        return self.interceptor.pre_check(order, portfolio, market_data)

    def set_stop_loss(
        self,
        symbol: str,
        entry_price: float,
        stop_ratio: float = 0.05,
        stop_price: float = None
    ):
        """设置固定止损"""
        self.stop_loss_tp.set_fixed_stop_loss(symbol, entry_price, stop_ratio, stop_price)

    def set_trailing_stop(
        self,
        symbol: str,
        entry_price: float,
        trailing_delta: float = 0.05
    ):
        """设置追踪止损"""
        self.stop_loss_tp.set_trailing_stop_loss(symbol, entry_price, trailing_delta)

    def set_take_profit(
        self,
        symbol: str,
        entry_price: float,
        take_ratio: float = 0.15,
        take_price: float = None
    ):
        """设置固定止盈"""
        self.stop_loss_tp.set_fixed_take_profit(symbol, entry_price, take_ratio, take_price)

    def set_trailing_take_profit(
        self,
        symbol: str,
        entry_price: float,
        trailing_delta: float = 0.03
    ):
        """设置追踪止盈"""
        self.stop_loss_tp.set_trailing_take_profit(symbol, entry_price, trailing_delta)

    def check_stop_loss_trigger(self, symbol: str, current_price: float) -> Dict:
        """检查止损止盈触发"""
        return self.stop_loss_tp.check_trigger(symbol, current_price)

    def enable(self):
        """启用风控"""
        self._is_enabled = True

    def disable(self):
        """禁用风控（用于特殊情况下绕过风控）"""
        self._is_enabled = False

    def is_enabled(self) -> bool:
        """检查风控是否启用"""
        return self._is_enabled

    def get_position_manager(self) -> PositionManager:
        """获取仓位管理器"""
        return self.position_manager

    def get_stop_loss_tp(self) -> StopLossTakeProfit:
        """获取止损止盈管理器"""
        return self.stop_loss_tp

    def get_risk_summary(self) -> Dict:
        """获取风控摘要"""
        return {
            "enabled": self._is_enabled,
            "position_summary": self.position_manager.get_summary(),
            "risk_interceptor": self.interceptor.get_risk_summary(),
            "active_stops": self.stop_loss_tp.get_all_active(),
        }

    def add_custom_validator(self, validator: Callable):
        """
        添加自定义验证函数

        Args:
            validator: 函数签名 (order, portfolio, market_data) -> {"approved": bool, "message": str}
        """
        self._custom_validators.append(validator)


def create_default_risk_manager(
    initial_cash: float = 100000.0,
    risk_level: str = "normal"
) -> RiskManager:
    """
    创建默认配置的风控管理器

    Args:
        initial_cash: 初始资金
        risk_level: 风险等级 "strict" | "normal" | "loose"

    Returns:
        配置好的 RiskManager
    """
    rm = RiskManager(initial_cash)

    configs = {
        "strict": {
            "max_position_size": 5000,
            "max_total_position_ratio": 0.7,
            "min_cash_ratio": 0.1,
            "max_single_position_ratio": 0.15,
            "min_daily_volume": 500000,
            "allowed_trading_hours": [10, 11, 14],
        },
        "normal": {
            "max_position_size": 10000,
            "max_total_position_ratio": 0.85,
            "min_cash_ratio": 0.05,
            "max_single_position_ratio": 0.2,
            "min_daily_volume": 100000,
            "allowed_trading_hours": [9, 10, 11, 13, 14, 15],
        },
        "loose": {
            "max_position_size": 20000,
            "max_total_position_ratio": 0.95,
            "min_cash_ratio": 0.02,
            "max_single_position_ratio": 0.3,
            "min_daily_volume": 50000,
            "allowed_trading_hours": [9, 10, 11, 13, 14, 15],
        },
    }

    rm.configure(configs.get(risk_level, configs["normal"]))
    return rm
