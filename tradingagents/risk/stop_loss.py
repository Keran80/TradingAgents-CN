# TradingAgents-CN 止损止盈模块
# Stop Loss / Take Profit Module

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class StopType(Enum):
    """止损止盈类型"""
    FIXED = "fixed"
    TRAILING = "trailing"
    ATR = "atr"


@dataclass
class StopLossTakeProfit:
    """止损止盈管理器

    使用示例:
        st = StopLossTakeProfit()
        st.set_fixed_stop_loss("000001.SZ", entry_price=10.0, stop_ratio=0.05)
        triggered = st.check_trigger("000001.SZ", current_price=9.4)
    """

    def __init__(self):
        self._stops: Dict[str, Dict] = {}
        self._profit_takes: Dict[str, Dict] = {}
        self._highest_prices: Dict[str, float] = {}

    def set_fixed_stop_loss(
        self,
        symbol: str,
        entry_price: float,
        stop_ratio: float = 0.05,
        stop_price: float = None
    ):
        if stop_price is None:
            stop_price = entry_price * (1 - stop_ratio)
        self._stops[symbol] = {
            "type": StopType.FIXED,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "stop_ratio": stop_ratio,
            "enabled": True,
        }

    def set_trailing_stop_loss(
        self,
        symbol: str,
        entry_price: float,
        trailing_delta: float = 0.05
    ):
        self._stops[symbol] = {
            "type": StopType.TRAILING,
            "entry_price": entry_price,
            "current_stop": entry_price,
            "trailing_delta": trailing_delta,
            "highest_price": entry_price,
            "enabled": True,
        }
        self._highest_prices[symbol] = entry_price

    def set_atr_stop_loss(
        self,
        symbol: str,
        entry_price: float,
        atr: float,
        atr_multiplier: float = 2.0
    ):
        stop_price = entry_price - atr * atr_multiplier
        self._stops[symbol] = {
            "type": StopType.ATR,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "atr": atr,
            "atr_multiplier": atr_multiplier,
            "enabled": True,
        }

    def set_fixed_take_profit(
        self,
        symbol: str,
        entry_price: float,
        take_ratio: float = 0.15,
        take_price: float = None
    ):
        if take_price is None:
            take_price = entry_price * (1 + take_ratio)
        self._profit_takes[symbol] = {
            "type": StopType.FIXED,
            "entry_price": entry_price,
            "take_price": take_price,
            "take_ratio": take_ratio,
            "enabled": True,
        }

    def set_trailing_take_profit(
        self,
        symbol: str,
        entry_price: float,
        trailing_delta: float = 0.03
    ):
        self._profit_takes[symbol] = {
            "type": StopType.TRAILING,
            "entry_price": entry_price,
            "current_take": entry_price,
            "trailing_delta": trailing_delta,
            "highest_price": entry_price,
            "enabled": True,
        }
        if symbol not in self._highest_prices:
            self._highest_prices[symbol] = entry_price

    def check_trigger(self, symbol: str, current_price: float) -> Dict:
        result = {
            "stop_triggered": False,
            "profit_triggered": False,
            "stop_price": None,
            "take_price": None,
            "action": None,
        }

        # 检查止损
        if symbol in self._stops and self._stops[symbol].get("enabled", True):
            stop_info = self._stops[symbol]
            stop_type = stop_info["type"]

            if stop_type == StopType.FIXED:
                if current_price <= stop_info["stop_price"]:
                    result["stop_triggered"] = True
                    result["stop_price"] = stop_info["stop_price"]
                    result["action"] = "stop"

            elif stop_type == StopType.TRAILING:
                if current_price > self._highest_prices.get(symbol, 0):
                    self._highest_prices[symbol] = current_price
                    stop_info["current_stop"] = current_price * (1 - stop_info["trailing_delta"])
                    stop_info["highest_price"] = current_price

                if current_price <= stop_info["current_stop"]:
                    result["stop_triggered"] = True
                    result["stop_price"] = stop_info["current_stop"]
                    result["action"] = "stop"

            elif stop_type == StopType.ATR:
                if current_price <= stop_info["stop_price"]:
                    result["stop_triggered"] = True
                    result["stop_price"] = stop_info["stop_price"]
                    result["action"] = "stop"

        # 检查止盈
        if symbol in self._profit_takes and self._profit_takes[symbol].get("enabled", True):
            profit_info = self._profit_takes[symbol]
            take_type = profit_info["type"]

            if take_type == StopType.FIXED:
                if current_price >= profit_info["take_price"]:
                    result["profit_triggered"] = True
                    result["take_price"] = profit_info["take_price"]
                    result["action"] = "profit"

            elif take_type == StopType.TRAILING:
                if current_price > self._highest_prices.get(symbol, 0):
                    self._highest_prices[symbol] = current_price
                    profit_info["current_take"] = current_price * (1 - profit_info["trailing_delta"])
                    profit_info["highest_price"] = current_price

                if current_price <= profit_info["current_take"]:
                    result["profit_triggered"] = True
                    result["take_price"] = profit_info["current_take"]
                    result["action"] = "profit"

        return result

    def disable_stop(self, symbol: str):
        if symbol in self._stops:
            self._stops[symbol]["enabled"] = False

    def disable_take_profit(self, symbol: str):
        if symbol in self._profit_takes:
            self._profit_takes[symbol]["enabled"] = False

    def remove(self, symbol: str):
        self._stops.pop(symbol, None)
        self._profit_takes.pop(symbol, None)
        self._highest_prices.pop(symbol, None)

    def get_stop_info(self, symbol: str) -> Optional[Dict]:
        return self._stops.get(symbol)

    def get_take_profit_info(self, symbol: str) -> Optional[Dict]:
        return self._profit_takes.get(symbol)

    def get_all_active(self) -> List[Dict]:
        result = []
        for symbol in set(list(self._stops.keys()) + list(self._profit_takes.keys())):
            info = {"symbol": symbol}
            if symbol in self._stops:
                info["stop"] = self._stops[symbol]
            if symbol in self._profit_takes:
                info["take_profit"] = self._profit_takes[symbol]
            result.append(info)
        return result
