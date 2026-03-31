"""
策略参数优化器 - TradingAgents-CN
=================================

提供策略参数优化功能：
- GridOptimizer: 网格搜索优化器
- WalkForwardOptimizer:  Walk-Forward 优化器
"""

from __future__ import annotations

import logging
from typing import Dict, List, Type, Any, Callable, Optional, Tuple
from dataclasses import dataclass
from itertools import product
from datetime import datetime

import numpy as np
import pandas as pd

from .templates import StrategyTemplate, StrategyConfig

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """回测结果"""
    params: Dict[str, Any]
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    profit_factor: float = 0.0
    calmar_ratio: float = 0.0

    def score(self, metric: str = "sharpe_ratio") -> float:
        """获取评分指标"""
        return getattr(self, metric, 0.0)


class GridOptimizer:
    """
    网格搜索优化器
    ==============

    通过遍历参数网格寻找最优参数组合。

    使用示例：
    ```python
    optimizer = GridOptimizer(
        strategy_class=MomentumStrategy,
        param_grid={
            "fast_period": [5, 10, 20],
            "slow_period": [20, 30, 60]
        }
    )

    best_params, results = optimizer.optimize(data)
    ```
    """

    def __init__(
        self,
        strategy_class: Type[StrategyTemplate],
        param_grid: Dict[str, List[Any]],
        metric: str = "sharpe_ratio"
    ):
        """
        初始化优化器

        Args:
            strategy_class: 策略类
            param_grid: 参数网格
            metric: 优化指标 (sharpe_ratio, total_return, max_drawdown)
        """
        self.strategy_class = strategy_class
        self.param_grid = param_grid
        self.metric = metric
        self.results: List[BacktestResult] = []

        # 生成参数组合
        self.param_names = list(param_grid.keys())
        self.param_values = list(param_grid.values())
        self.param_combinations = list(product(*self.param_values))

        logger.info(
            f"GridOptimizer initialized: {len(self.param_combinations)} combinations"
        )

    def optimize(
        self,
        data: pd.DataFrame,
        initial_capital: float = 1000000.0,
        show_progress: bool = True
    ) -> Tuple[Dict[str, Any], List[BacktestResult]]:
        """
        执行网格搜索优化

        Args:
            data: 历史数据
            initial_capital: 初始资金
            show_progress: 显示进度

        Returns:
            (最优参数, 所有结果)
        """
        self.results = []
        total = len(self.param_combinations)

        for i, param_values in enumerate(self.param_combinations):
            params = dict(zip(self.param_names, param_values))

            if show_progress and (i + 1) % 10 == 0:
                logger.info(f"Progress: {i + 1}/{total}")

            # 创建策略实例
            config = StrategyConfig(
                name=f"Optimize_{i}",
                initial_capital=initial_capital
            )

            try:
                strategy = self.strategy_class(config=config, **params)
                result = self._backtest(strategy, data, params)
                self.results.append(result)
            except Exception as e:
                logger.warning(f"Backtest failed for params {params}: {e}")
                continue

        # 找最优
        if not self.results:
            logger.warning("No successful backtests")
            return {}, []

        best_result = max(self.results, key=lambda x: x.score(self.metric))

        logger.info(
            f"Optimization complete. Best {self.metric}={best_result.score(self.metric):.4f}"
        )

        return best_result.params, self.results

    def _backtest(
        self,
        strategy: StrategyTemplate,
        data: pd.DataFrame,
        params: Dict[str, Any]
    ) -> BacktestResult:
        """执行回测"""
        from ..event_engine import BarEvent

        cash = strategy.config.initial_capital
        position = 0
        avg_cost = 0.0
        equity_curve = [cash]
        trades = []

        for idx, row in data.iterrows():
            bar = BarEvent(
                symbol=row.get("symbol", "UNKNOWN"),
                interval="1d",
                open_price=row["open"],
                high_price=row["high"],
                low_price=row["low"],
                close_price=row["close"],
                volume=int(row.get("volume", 0)),
                datetime=idx if isinstance(idx, datetime) else pd.to_datetime(idx)
            )

            # 策略处理
            strategy.on_bar(bar)

            # 简单撮合（只用收盘价）
            signal = self._check_signal(strategy, bar)
            if signal and position == 0 and signal["action"] == "buy":
                cost = bar.close_price * signal["quantity"]
                commission = cost * strategy.config.commission_rate
                if cash >= cost + commission:
                    position = signal["quantity"]
                    avg_cost = bar.close_price
                    cash -= (cost + commission)
                    trades.append({"type": "buy", "price": bar.close_price, "qty": position})

            elif signal and position > 0 and signal["action"] == "sell":
                revenue = bar.close_price * position
                commission = revenue * strategy.config.commission_rate
                stamp_tax = revenue * 0.001  # 印花税
                pnl = revenue - avg_cost * position - commission - stamp_tax
                cash += (revenue - commission - stamp_tax)
                trades.append({"type": "sell", "price": bar.close_price, "qty": position, "pnl": pnl})
                position = 0

            # 更新权益
            equity = cash + position * bar.close_price
            equity_curve.append(equity)

        # 计算结果
        equity_curve = np.array(equity_curve)
        returns = np.diff(equity_curve) / equity_curve[:-1]

        total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]

        # Sharpe Ratio
        if len(returns) > 0 and np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0

        # 最大回撤
        cummax = np.maximum.accumulate(equity_curve)
        drawdowns = (cummax - equity_curve) / cummax
        max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0.0

        # 胜率
        win_trades = [t for t in trades if t.get("type") == "sell" and t.get("pnl", 0) > 0]
        win_rate = len(win_trades) / len([t for t in trades if t.get("type") == "sell"]) if trades else 0.0

        # 盈亏比
        sell_trades = [t for t in trades if t.get("type") == "sell"]
        wins = [t["pnl"] for t in sell_trades if t.get("pnl", 0) > 0]
        losses = [abs(t["pnl"]) for t in sell_trades if t.get("pnl", 0) < 0]
        profit_factor = np.sum(wins) / np.sum(losses) if losses and np.sum(losses) > 0 else 0.0

        # Calmar Ratio
        anual_return = total_return * 252 / max(len(data), 1)
        calmar_ratio = anual_return / max_drawdown if max_drawdown > 0 else 0.0

        return BacktestResult(
            params=params,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=len(sell_trades),
            profit_factor=profit_factor,
            calmar_ratio=calmar_ratio
        )

    def _check_signal(
        self,
        strategy: StrategyTemplate,
        bar: BarEvent
    ) -> Optional[Dict[str, Any]]:
        """检查策略信号"""
        # 简化实现：检查策略状态
        state = strategy.state.get(bar.symbol)
        if not state:
            return None

        if state.position == 0:
            # 无持仓，检查是否有买入信号
            return None  # 简化处理
        else:
            return {"action": "sell", "quantity": state.position}


class WalkForwardOptimizer:
    """
    Walk-Forward 优化器
    ==================

    将数据分为样本内和样本外，用样本内优化参数，样本外验证。
    """

    def __init__(
        self,
        strategy_class: Type[StrategyTemplate],
        param_grid: Dict[str, List[Any]],
        train_ratio: float = 0.6,
        n_splits: int = 3
    ):
        self.strategy_class = strategy_class
        self.param_grid = param_grid
        self.train_ratio = train_ratio
        self.n_splits = n_splits
        self.grid_optimizer = GridOptimizer(strategy_class, param_grid)

    def optimize(
        self,
        data: pd.DataFrame,
        initial_capital: float = 1000000.0
    ) -> Dict[str, Any]:
        """
        执行 Walk-Forward 优化

        Returns:
            优化结果统计
        """
        n = len(data)
        train_size = int(n * self.train_ratio)

        results = {
            "train_results": [],
            "test_results": [],
            "best_params_history": []
        }

        for i in range(self.n_splits):
            train_start = i * (n - train_size) // max(self.n_splits - 1, 1)
            train_end = train_start + train_size
            test_start = train_end
            test_end = min(test_start + (n - train_size), n)

            if test_start >= n:
                break

            train_data = data.iloc[train_start:train_end]
            test_data = data.iloc[test_start:test_end]

            logger.info(f"Walk-Forward {i+1}: Train={train_start}-{train_end}, Test={test_start}-{test_end}")

            # 样本内优化
            best_params, train_results = self.grid_optimizer.optimize(
                train_data,
                initial_capital,
                show_progress=False
            )

            # 样本外测试
            config = StrategyConfig(initial_capital=initial_capital)
            strategy = self.strategy_class(config=config, **best_params)

            _, test_result = self.grid_optimizer._backtest(strategy, test_data, best_params)

            results["train_results"].append(train_results[0] if train_results else None)
            results["test_results"].append(test_result)
            results["best_params_history"].append(best_params)

        # 计算样本外平均表现
        test_sharpe = [r.sharpe_ratio for r in results["test_results"] if r]
        avg_out_of_sample_sharpe = np.mean(test_sharpe) if test_sharpe else 0.0

        logger.info(f"Walk-Forward complete. Avg OOS Sharpe: {avg_out_of_sample_sharpe:.4f}")

        return results
