"""
回测引擎核心模块

支持两种回测模式：
1. 事件驱动模式 (Event-driven)：逐K线执行，适合复杂策略
2. 向量化模式 (Vectorized)：利用pandas批量计算，适合简单策略

主要类：
- BacktestEngine: 回测引擎主类

使用示例：
    >>> from .config import BacktestConfig, BacktestMode
    >>> config = BacktestConfig(
    ...     start_date="2024-01-01",
    ...     end_date="2024-06-30",
    ...     initial_cash=1000000,
    ...     mode=BacktestMode.VECTORIZED
    ... )
    >>> engine = BacktestEngine(config)
    >>> engine.load_data("000001.SZ")
    >>> result = engine.run()
    >>> print(result.to_dict())
"""

from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict
import logging
import pandas as pd

from .config import BacktestConfig, BacktestMode
from .result import BacktestResult, TradeRecord

logger = logging.getLogger(__name__)

from ..execution.broker import OrderType, OrderSide
from ..risk import RiskManager
from ..monitoring import MonitorManager


class BacktestEngine:
    """
    回测引擎

    使用示例：
    ```python
    from tradingagents.backtest import BacktestEngine, BacktestConfig, BacktestMode

    config = BacktestConfig(
        start_date="2024-01-01",
        end_date="2024-06-30",
        initial_cash=1000000,
        mode=BacktestMode.EVENT_DRIVEN,
    )

    engine = BacktestEngine(config)
    engine.load_data("000001.SZ")
    engine.set_strategy(my_strategy)
    result = engine.run()
    ```
    """

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.strategy = None
        self.data: Dict[str, pd.DataFrame] = {}
        self.signals: Dict[str, pd.DataFrame] = {}

        # 初始化组件
        self._init_components()

        # 回测状态
        self._current_date = None
        self._positions: Dict[str, int] = {}
        self._trades: List[TradeRecord] = []
        self._equity_curve: List[Dict] = []

    def _init_components(self):
        """初始化组件"""
        # 简化实现：使用内部现金追踪
        self._cash = self.config.initial_cash

        # 风控管理器
        self.risk_manager = None
        if self.config.enable_risk:
            try:
                self.risk_manager = RiskManager(
                    initial_cash=self.config.initial_cash,
                    max_position_ratio=self.config.max_position_ratio
                )
            except Exception as e:
                logger.warning(f"Failed to initialize RiskManager: {e}")
                self.risk_manager = None

        # 监控管理器
        self.monitor_manager = None
        if self.config.enable_monitoring:
            try:
                self.monitor_manager = MonitorManager()
            except Exception as e:
                logger.warning(f"Failed to initialize MonitorManager: {e}")
                self.monitor_manager = None

    def load_data(self, symbol: str, data: Optional[pd.DataFrame] = None):
        """
        加载数据

        Args:
            symbol: 股票代码
            data: 数据DataFrame，如为None则自动获取
        """
        if data is not None:
            self.data[symbol] = data
        else:
            # 使用AkShare获取数据
            from ..dataflows import get_akshare_stock_data
            df = get_akshare_stock_data(
                symbol=symbol,
                start_date=self.config.start_date,
                end_date=self.config.end_date
            )
            self.data[symbol] = df

    def set_strategy(self, strategy: Callable):
        """
        设置策略函数

        Args:
            strategy: 策略函数，签名: (data, current_date, positions) -> List[Signal]
        """
        self.strategy = strategy

    def set_signals(self, symbol: str, signals: pd.DataFrame):
        """
        设置预计算的信号

        Args:
            symbol: 股票代码
            signals: 信号DataFrame，包含 'signal' 列（1=买入, -1=卖出, 0=持有）
        """
        self.signals[symbol] = signals

    def run(self) -> BacktestResult:
        """
        运行回测

        Returns:
            BacktestResult: 回测结果
        """
        if self.config.mode == BacktestMode.EVENT_DRIVEN:
            return self._run_event_driven()
        else:
            return self._run_vectorized()

    def _run_event_driven(self) -> BacktestResult:
        """事件驱动回测"""
        if not self.data:
            raise ValueError("No data loaded. Call load_data() first.")

        # 合并所有股票数据
        combined_data = self._merge_data()

        # 逐行回测
        for idx, row in combined_data.iterrows():
            self._current_date = idx
            self._process_bar(row)

            # 记录净值
            self._record_equity()

        return self._generate_result()

    def _run_vectorized(self) -> BacktestResult:
        """向量化回测"""
        if not self.data:
            raise ValueError("No data loaded. Call load_data() first.")

        # 简化处理：只处理第一只股票
        symbol = list(self.data.keys())[0]
        data = self.data[symbol]

        # 计算收益率
        returns = data['close'].pct_change().fillna(0)

        # 生成信号
        if symbol in self.signals:
            signals = self.signals[symbol]['signal']
        else:
            # 默认均线策略
            ma5 = data['close'].rolling(5).mean()
            ma20 = data['close'].rolling(20).mean()
            signals = (ma5 > ma20).astype(int) * 2 - 1

        # 应用信号
        strategy_returns = returns * signals.shift(1).fillna(0)

        # 累计收益
        cumulative_returns = (1 + strategy_returns).cumprod() - 1

        # 模拟交易（使用简化版本）
        self._simulate_simple_trades(signals)

        # 生成结果
        return self._generate_result_from_returns(
            cumulative_returns,
            strategy_returns
        )

    def _simulate_simple_trades(self, signals: pd.Series):
        """简化交易模拟"""
        positions = 0

        for date in signals.index:
            signal = signals.loc[date]

            if signal > 0 and positions == 0:
                # 买入
                price = self.data[list(self.data.keys())[0]].loc[date, 'close']
                max_qty = int(self._cash * 0.1 / price / 100) * 100
                quantity = max_qty
                if quantity > 0:
                    cost = price * quantity * (1 + self.config.commission_rate)
                    self._cash -= cost
                    positions = quantity
                    self._trades.append(TradeRecord(
                        timestamp=str(date),
                        symbol=list(self.data.keys())[0],
                        direction="BUY",
                        price=price,
                        quantity=quantity,
                        commission=price * quantity * self.config.commission_rate,
                        slippage=price * quantity * self.config.slippage_rate
                    ))

            elif signal < 0 and positions > 0:
                # 卖出
                price = self.data[list(self.data.keys())[0]].loc[date, 'close']
                quantity = positions
                revenue = price * quantity * (1 - self.config.commission_rate - self.config.slippage_rate)
                self._cash += revenue
                self._trades.append(TradeRecord(
                    timestamp=str(date),
                    symbol=list(self.data.keys())[0],
                    direction="SELL",
                    price=price,
                    quantity=quantity,
                    commission=price * quantity * self.config.commission_rate,
                    slippage=price * quantity * self.config.slippage_rate
                ))
                positions = 0

    def _merge_data(self) -> pd.DataFrame:
        """合并多只股票数据"""
        dfs = []
        for symbol, df in self.data.items():
            df = df.copy()
            df['symbol'] = symbol
            dfs.append(df)

        combined = pd.concat(dfs, ignore_index=False)
        combined = combined.sort_index()
        return combined

    def _process_bar(self, bar: pd.Series) -> None:
        """处理单个K线"""
        symbol = bar.get('symbol')
        if symbol is None:
            return

        # 获取当前持仓
        current_position = self._positions.get(symbol, 0)

        # 如果有策略函数，执行策略
        if self.strategy:
            signals = self.strategy(
                data=self.data,
                current_date=self._current_date,
                positions=self._positions
            )
            for signal in signals:
                self._execute_signal(signal, bar)
        else:
            # 使用预计算信号
            signal_data = self.signals.get(symbol)
            if signal_data is not None and self._current_date in signal_data.index:
                signal_value = signal_data.loc[self._current_date, 'signal']
                if signal_value != 0:
                    self._execute_signal_from_value(
                        symbol, signal_value, bar['close'], current_position
                    )

    def _execute_buy(self, symbol: str, price: float, quantity: int) -> Optional[TradeRecord]:
        """
        执行买入交易

        Args:
            symbol: 股票代码
            price: 价格
            quantity: 数量

        Returns:
            TradeRecord 或 None
        """
        if quantity <= 0:
            return None

        cost = price * quantity * (1 + self.config.commission_rate + self.config.slippage_rate)
        if cost > self._cash:
            return None

        self._cash -= cost
        self._positions[symbol] = self._positions.get(symbol, 0) + quantity

        trade = TradeRecord(
            timestamp=str(self._current_date),
            symbol=symbol,
            direction="BUY",
            price=price,
            quantity=quantity,
            commission=price * quantity * self.config.commission_rate,
            slippage=price * quantity * self.config.slippage_rate
        )
        self._trades.append(trade)
        return trade

    def _execute_sell(self, symbol: str, price: float, quantity: int) -> Optional[TradeRecord]:
        """
        执行卖出交易

        Args:
            symbol: 股票代码
            price: 价格
            quantity: 数量

        Returns:
            TradeRecord 或 None
        """
        if quantity <= 0:
            return None

        revenue = price * quantity * (1 - self.config.commission_rate - self.config.slippage_rate)
        self._cash += revenue
        self._positions[symbol] = max(0, self._positions.get(symbol, 0) - quantity)

        trade = TradeRecord(
            timestamp=str(self._current_date),
            symbol=symbol,
            direction="SELL",
            price=price,
            quantity=quantity,
            commission=price * quantity * self.config.commission_rate,
            slippage=price * quantity * self.config.slippage_rate
        )
        self._trades.append(trade)
        return trade

    def _execute_signal(self, signal, bar):
        """执行信号"""
        symbol = bar.get('symbol')
        price = bar['close']

        if signal.action == "BUY":
            # 计算可买入数量
            available_cash = self._cash
            max_shares = int(available_cash / (price * (1 + self.config.commission_rate)))
            quantity = min(signal.quantity, max_shares) if signal.quantity else max_shares
            self._execute_buy(symbol, price, quantity)
        elif signal.action == "SELL":
            current_position = self._positions.get(symbol, 0)
            self._execute_sell(symbol, price, current_position)

    def _execute_signal_from_value(self, symbol: str, signal_value: int, price: float, current_position: int):
        """根据信号值执行"""
        if signal_value > 0:  # 买入信号
            available_cash = self._cash
            max_shares = int(available_cash / (price * (1 + self.config.commission_rate)))
            quantity = max_shares
            self._execute_buy(symbol, price, quantity)
        elif signal_value < 0 and current_position > 0:  # 卖出信号
            self._execute_sell(symbol, price, current_position)

    def _generate_vectorized_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成向量化信号"""
        # 使用 groupby 替代逐行过滤，提升性能
        signals = pd.DataFrame(index=data.index)

        # 按symbol分组，一次性处理所有数据
        if 'symbol' in data.columns:
            grouped = data.groupby('symbol')
            for symbol, symbol_data in grouped:
                if symbol in self.signals:
                    signals[symbol] = self.signals[symbol]['signal']
                else:
                    # 默认：简单均线策略
                    ma5 = symbol_data['close'].rolling(5).mean()
                    ma20 = symbol_data['close'].rolling(20).mean()
                    signals[symbol] = (ma5 > ma20).astype(int) * 2 - 1
        else:
            # 单只股票情况
            symbol = list(self.data.keys())[0]
            if symbol in self.signals:
                signals[symbol] = self.signals[symbol]['signal']
            else:
                ma5 = data['close'].rolling(5).mean()
                ma20 = data['close'].rolling(20).mean()
                signals[symbol] = (ma5 > ma20).astype(int) * 2 - 1

        return signals.fillna(0)

    def _simulate_vectorized_trades(self, signals: pd.DataFrame):
        """模拟向量化交易"""
        positions = {}

        for date in signals.index:
            for symbol in signals.columns:
                signal = signals.loc[date, symbol]
                if symbol not in positions:
                    positions[symbol] = 0

                if signal > 0 and positions[symbol] == 0:
                    # 买入
                    price = self.data[symbol].loc[date, 'close']
                    max_qty = int(self._cash * 0.1 / price / 100) * 100
                    quantity = max_qty
                    if quantity > 0:
                        cost = price * quantity * (1 + self.config.commission_rate)
                        self._cash -= cost
                        positions[symbol] = quantity
                        self._trades.append(TradeRecord(
                            timestamp=str(date),
                            symbol=symbol,
                            direction="BUY",
                            price=price,
                            quantity=quantity,
                            commission=price * quantity * self.config.commission_rate,
                            slippage=price * quantity * self.config.slippage_rate
                        ))

                elif signal < 0 and positions[symbol] > 0:
                    # 卖出
                    price = self.data[symbol].loc[date, 'close']
                    quantity = positions[symbol]
                    revenue = price * quantity * (1 - self.config.commission_rate - self.config.slippage_rate)
                    self._cash += revenue
                    self._trades.append(TradeRecord(
                        timestamp=str(date),
                        symbol=symbol,
                        direction="SELL",
                        price=price,
                        quantity=quantity,
                        commission=price * quantity * self.config.commission_rate,
                        slippage=price * quantity * self.config.slippage_rate
                    ))
                    positions[symbol] = 0

    def _record_equity(self) -> None:
        """记录当前净值"""
        total_value = self._cash

        for symbol, position in self._positions.items():
            if position > 0 and symbol in self.data:
                try:
                    current_price = self.data[symbol].loc[self._current_date, 'close']
                    total_value += position * current_price
                except KeyError:
                    pass

        self._equity_curve.append({
            'date': self._current_date,
            'equity': total_value
        })

    def _generate_result(self) -> BacktestResult:
        """生成回测结果"""
        final_equity = self._equity_curve[-1]['equity'] if self._equity_curve else self.config.initial_cash

        # 计算收益
        total_return = (final_equity - self.config.initial_cash) / self.config.initial_cash

        # 交易日数
        trading_days = len(self._equity_curve) if self._equity_curve else 1
        years = trading_days / 252
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        # 交易统计
        buy_trades = [t for t in self._trades if t.direction == "BUY"]
        sell_trades = [t for t in self._trades if t.direction == "SELL"]

        # 计算胜率
        winning = 0
        losing = 0
        for i in range(0, len(sell_trades)):
            if i < len(buy_trades):
                buy_price = buy_trades[i].price
                sell_price = sell_trades[i].price
                if sell_price > buy_price:
                    winning += 1
                else:
                    losing += 1

        win_rate = winning / (winning + losing) if (winning + losing) > 0 else 0

        # 生成净值曲线
        equity_df = pd.DataFrame(self._equity_curve)
        if not equity_df.empty:
            equity_df.set_index('date', inplace=True)

        return BacktestResult(
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            initial_cash=self.config.initial_cash,
            final_cash=final_equity,
            total_return=total_return,
            annual_return=annual_return,
            total_trades=len(self._trades),
            winning_trades=winning,
            losing_trades=losing,
            win_rate=win_rate,
            trades=self._trades,
            equity_curve=equity_df
        )

    def _generate_result_from_returns(self, cumulative_returns: pd.Series,
                                      daily_returns: pd.Series) -> BacktestResult:
        """从收益率序列生成结果"""
        final_return = cumulative_returns.iloc[-1] if len(cumulative_returns) > 0 else 0
        final_equity = self.config.initial_cash * (1 + final_return)

        # 年化收益
        trading_days = len(cumulative_returns)
        years = trading_days / 252
        annual_return = (1 + final_return) ** (1 / years) - 1 if years > 0 else 0

        return BacktestResult(
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            initial_cash=self.config.initial_cash,
            final_cash=final_equity,
            total_return=final_return,
            annual_return=annual_return,
            total_trades=len(self._trades),
            winning_trades=0,  # 向量化模式不追踪胜负
            losing_trades=0,
            win_rate=0,
            trades=self._trades,
            daily_returns=daily_returns
        )

    def get_current_positions(self) -> Dict[str, int]:
        """获取当前持仓"""
        return self._positions.copy()

    def get_trades(self) -> List[TradeRecord]:
        """获取交易记录"""
        return self._trades.copy()

    def get_equity_curve(self) -> pd.DataFrame:
        """获取净值曲线"""
        return pd.DataFrame(self._equity_curve)
