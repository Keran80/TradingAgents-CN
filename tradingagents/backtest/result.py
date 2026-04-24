"""
回测结果模块

包含交易记录和回测结果数据类。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import pandas as pd


@dataclass
class TradeRecord:
    """交易记录"""
    timestamp: str
    symbol: str
    direction: str  # BUY / SELL
    price: float
    quantity: int
    commission: float
    slippage: float


@dataclass
class BacktestResult:
    """回测结果"""
    # 基本信息
    start_date: str
    end_date: str
    initial_cash: float
    final_cash: float

    # 收益指标
    total_return: float
    annual_return: float

    # 交易统计
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    # 持仓记录
    trades: List[TradeRecord] = field(default_factory=list)

    # 每日净值
    equity_curve: Optional[pd.DataFrame] = None

    # 原始数据
    daily_returns: Optional[pd.Series] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_cash": self.initial_cash,
            "final_cash": self.final_cash,
            "total_return": f"{self.total_return:.2%}",
            "annual_return": f"{self.annual_return:.2%}",
            "total_trades": self.total_trades,
            "win_rate": f"{self.win_rate:.2%}",
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
        }
