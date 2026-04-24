"""
绩效分析模块

提供完整的策略绩效评估指标：
- 收益类：总收益、年化收益、卡玛比率
- 风险类：最大回撤、波动率、VaR
- 风险调整收益：夏普比率、索提诺比率、信息比率
- 交易统计：胜率、盈亏比、持仓时间
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np


@dataclass
class PerformanceMetrics:
    """绩效指标数据类"""
    # 收益指标
    total_return: float = 0.0           # 总收益率
    annual_return: float = 0.0          # 年化收益率
    calmar_ratio: float = 0.0            # 卡玛比率 (年化收益/最大回撤)
    
    # 风险指标
    max_drawdown: float = 0.0           # 最大回撤
    max_drawdown_duration: int = 0     # 最大回撤持续天数
    volatility: float = 0.0             # 年化波动率
    var_95: float = 0.0                # 95% VaR
    cvar_95: float = 0.0               # 95% CVaR
    
    # 风险调整收益
    sharpe_ratio: float = 0.0           # 夏普比率
    sortino_ratio: float = 0.0          # 索提诺比率
    information_ratio: float = 0.0      # 信息比率
    
    # 交易统计
    total_trades: int = 0              # 总交易次数
    winning_trades: int = 0            # 盈利交易次数
    losing_trades: int = 0             # 亏损交易次数
    win_rate: float = 0.0              # 胜率
    profit_loss_ratio: float = 0.0      # 盈亏比
    avg_holding_days: float = 0.0      # 平均持仓天数
    
    # 抄底逃顶指标
    upside_capture_ratio: float = 0.0   # 上涨捕获率
    downside_capture_ratio: float = 0.0  # 下跌捕获率
    
    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {
            "total_return": f"{self.total_return:.2%}",
            "annual_return": f"{self.annual_return:.2%}",
            "calmar_ratio": f"{self.calmar_ratio:.2f}",
            "max_drawdown": f"{self.max_drawdown:.2%}",
            "max_drawdown_duration": f"{self.max_drawdown_duration}天",
            "volatility": f"{self.volatility:.2%}",
            "var_95": f"{self.var_95:.2%}",
            "sharpe_ratio": f"{self.sharpe_ratio:.2f}",
            "sortino_ratio": f"{self.sortino_ratio:.2f}",
            "win_rate": f"{self.win_rate:.2%}",
            "profit_loss_ratio": f"{self.profit_loss_ratio:.2f}",
            "avg_holding_days": f"{self.avg_holding_days:.1f}",
        }


class PerformanceAnalyzer:
    """
    绩效分析器
    
    使用示例：
    ```python
    from tradingagents.backtest import PerformanceAnalyzer, PerformanceMetrics
    
    analyzer = PerformanceAnalyzer()
    metrics = analyzer.analyze(
        equity_curve=equity_df,
        returns=daily_returns,
        trades=trade_list,
        benchmark_returns=benchmark_returns  # 可选
    )
    
    print(f"夏普比率: {metrics.sharpe_ratio:.2f}")
    print(f"最大回撤: {metrics.max_drawdown:.2%}")
    ```
    """
    
    TRADING_DAYS = 252  # 年交易日数
    RISK_FREE_RATE = 0.03  # 无风险利率 (年化)
    
    def __init__(self, risk_free_rate: float = 0.03):
        """
        初始化分析器
        
        Args:
            risk_free_rate: 年化无风险利率
        """
        self.RISK_FREE_RATE = risk_free_rate
        
    def analyze(
        self,
        equity_curve: pd.DataFrame,
        returns: Optional[pd.Series] = None,
        trades: Optional[List] = None,
        benchmark_returns: Optional[pd.Series] = None
    ) -> PerformanceMetrics:
        """
        完整绩效分析
        
        Args:
            equity_curve: 净值曲线 DataFrame，需包含 'equity' 列
            returns: 日收益率序列，如为None则从equity_curve计算
            trades: 交易记录列表
            benchmark_returns: 基准收益率序列（用于信息比率）
            
        Returns:
            PerformanceMetrics: 绩效指标对象
        """
        metrics = PerformanceMetrics()
        
        # 计算收益率
        if returns is None:
            returns = self._calculate_returns(equity_curve)
            
        # 收益率分析
        metrics.total_return = self._calculate_total_return(returns)
        metrics.annual_return = self._calculate_annual_return(returns)
        metrics.volatility = self._calculate_volatility(returns)
        
        # 风险分析
        metrics.max_drawdown, metrics.max_drawdown_duration = self._calculate_max_drawdown(equity_curve)
        metrics.var_95 = self._calculate_var(returns, confidence=0.95)
        metrics.cvar_95 = self._calculate_cvar(returns, confidence=0.95)
        
        # 风险调整收益
        metrics.sharpe_ratio = self._calculate_sharpe_ratio(returns)
        metrics.sortino_ratio = self._calculate_sortino_ratio(returns)
        
        # 卡玛比率
        if metrics.max_drawdown != 0:
            metrics.calmar_ratio = metrics.annual_return / metrics.max_drawdown
            
        # 交易统计
        if trades:
            trade_metrics = self._analyze_trades(trades)
            metrics.total_trades = trade_metrics['total']
            metrics.winning_trades = trade_metrics['winning']
            metrics.losing_trades = trade_metrics['losing']
            metrics.win_rate = trade_metrics['win_rate']
            metrics.profit_loss_ratio = trade_metrics['profit_loss_ratio']
            metrics.avg_holding_days = trade_metrics['avg_holding_days']
            
        # 信息比率
        if benchmark_returns is not None:
            metrics.information_ratio = self._calculate_information_ratio(returns, benchmark_returns)
            
        return metrics
        
    def _calculate_returns(self, equity_curve: pd.DataFrame) -> pd.Series:
        """从净值计算收益率"""
        equity = equity_curve['equity']
        returns = equity.pct_change().fillna(0)
        return returns
        
    def _calculate_total_return(self, returns: pd.Series) -> float:
        """计算总收益率"""
        return (1 + returns).prod() - 1
        
    def _calculate_annual_return(self, returns: pd.Series) -> float:
        """计算年化收益率"""
        if len(returns) == 0:
            return 0.0
        total_return = (1 + returns).prod() - 1
        years = len(returns) / self.TRADING_DAYS
        if years <= 0:
            return 0.0
        return (1 + total_return) ** (1 / years) - 1
        
    def _calculate_volatility(self, returns: pd.Series) -> float:
        """计算年化波动率"""
        if len(returns) == 0:
            return 0.0
        return returns.std() * np.sqrt(self.TRADING_DAYS)
        
    def _calculate_max_drawdown(
        self, 
        equity_curve: pd.DataFrame
    ) -> Tuple[float, int]:
        """
        计算最大回撤和回撤持续时间
        
        Returns:
            (最大回撤, 最大回撤持续天数)
        """
        if len(equity_curve) == 0:
            return 0.0, 0
            
        equity = equity_curve['equity'].values
        peak = equity[0]
        peak_idx = 0
        max_dd = 0.0
        max_dd_duration = 0
        
        current_duration = 0
        current_max_dd_duration = 0
        
        for i, value in enumerate(equity):
            if value > peak:
                peak = value
                peak_idx = i
                current_duration = 0
            else:
                current_duration += 1
                
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd
                max_dd_duration = current_duration
                
        return max_dd, max_dd_duration
        
    def _calculate_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """计算VaR (Value at Risk)"""
        if len(returns) == 0:
            return 0.0
        return -np.percentile(returns, (1 - confidence) * 100)
        
    def _calculate_cvar(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """计算CVaR (Conditional VaR)"""
        if len(returns) == 0:
            return 0.0
        var = self._calculate_var(returns, confidence)
        return -returns[returns <= -var].mean()
        
    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """计算夏普比率"""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        excess_returns = returns - self.RISK_FREE_RATE / self.TRADING_DAYS
        return excess_returns.mean() / returns.std() * np.sqrt(self.TRADING_DAYS)
        
    def _calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """计算索提诺比率"""
        if len(returns) == 0:
            return 0.0
        excess_returns = returns - self.RISK_FREE_RATE / self.TRADING_DAYS
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        return excess_returns.mean() / downside_returns.std() * np.sqrt(self.TRADING_DAYS)
        
    def _calculate_information_ratio(
        self, 
        returns: pd.Series, 
        benchmark_returns: pd.Series
    ) -> float:
        """计算信息比率"""
        if len(returns) == 0 or len(benchmark_returns) == 0:
            return 0.0
        # 对齐索引
        aligned_returns, aligned_benchmark = returns.align(benchmark_returns, join='inner')
        if len(aligned_returns) == 0:
            return 0.0
        excess_returns = aligned_returns - aligned_benchmark
        tracking_error = excess_returns.std()
        if tracking_error == 0:
            return 0.0
        return excess_returns.mean() / tracking_error * np.sqrt(self.TRADING_DAYS)
        
    def _analyze_trades(self, trades: List) -> Dict:
        """分析交易记录"""
        if not trades:
            return {
                'total': 0, 'winning': 0, 'losing': 0,
                'win_rate': 0.0, 'profit_loss_ratio': 0.0, 'avg_holding_days': 0.0
            }
            
        # 分离买卖交易
        buys = [t for t in trades if t.direction == "BUY"]
        sells = [t for t in trades if t.direction == "SELL"]
        
        winning = 0
        losing = 0
        profits = []
        losses = []
        holding_days = []
        
        # 配对买卖计算盈亏
        for i in range(min(len(buys), len(sells))):
            buy_trade = buys[i]
            sell_trade = sells[i]
            
            buy_cost = buy_trade.price * buy_trade.quantity + buy_trade.commission + buy_trade.slippage
            sell_revenue = sell_trade.price * sell_trade.quantity - sell_trade.commission - sell_trade.slippage
            
            pnl = sell_revenue - buy_cost
            if pnl > 0:
                winning += 1
                profits.append(pnl)
            else:
                losing += 1
                losses.append(abs(pnl))
                
            # 计算持仓天数
            try:
                buy_date = pd.to_datetime(buy_trade.timestamp)
                sell_date = pd.to_datetime(sell_trade.timestamp)
                holding_days.append((sell_date - buy_date).days)
            except Exception:
                pass
                
        total = winning + losing
        win_rate = winning / total if total > 0 else 0.0
        avg_profit = np.mean(profits) if profits else 0.0
        avg_loss = np.mean(losses) if losses else 0.0
        profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else 0.0
        avg_holding = np.mean(holding_days) if holding_days else 0.0
        
        return {
            'total': total,
            'winning': winning,
            'losing': losing,
            'win_rate': win_rate,
            'profit_loss_ratio': profit_loss_ratio,
            'avg_holding_days': avg_holding
        }
        
    def calculate_drawdown_series(self, equity_curve: pd.DataFrame) -> pd.Series:
        """计算回撤序列"""
        equity = equity_curve['equity']
        running_max = equity.expanding().max()
        drawdown = (equity - running_max) / running_max
        return drawdown
        
    def calculate_gains_series(self, equity_curve: pd.DataFrame) -> pd.Series:
        """计算收益序列"""
        equity = equity_curve['equity']
        gains = equity.pct_change().fillna(0)
        return gains
        
    def monthly_returns_table(self, returns: pd.Series) -> pd.DataFrame:
        """生成月度收益表"""
        if len(returns) == 0:
            return pd.DataFrame()
            
        monthly = returns.resample('ME').apply(lambda x: (1 + x).prod() - 1)
        monthly.index = monthly.index.strftime('%Y-%m')
        
        # 转为列形式
        df = pd.DataFrame({'monthly_return': monthly})
        return df
        
    def annual_returns_table(self, returns: pd.Series) -> pd.DataFrame:
        """生成年度收益表"""
        if len(returns) == 0:
            return pd.DataFrame()
            
        annual = returns.resample('YE').apply(lambda x: (1 + x).prod() - 1)
        annual.index = annual.index.strftime('%Y')
        
        # 计算累计收益
        cumulative = (1 + returns).cumprod()
        year_end_values = cumulative.resample('YE').last()
        year_start = cumulative.resample('YE').first()
        
        df = pd.DataFrame({
            'annual_return': annual,
            'cumulative': year_end_values
        })
        return df
        
    def rolling_sharpe(
        self, 
        returns: pd.Series, 
        window: int = 60
    ) -> pd.Series:
        """计算滚动夏普比率"""
        if len(returns) < window:
            return pd.Series()
            
        rolling_mean = returns.rolling(window).mean()
        rolling_std = returns.rolling(window).std()
        rolling_sharpe = (rolling_mean / rolling_std) * np.sqrt(self.TRADING_DAYS)
        
        return rolling_sharpe
        
    def summary_report(self, metrics: PerformanceMetrics) -> str:
        """生成绩效摘要报告"""
        report = []
        report.append("=" * 50)
        report.append("策略绩效摘要")
        report.append("=" * 50)
        report.append("")
        
        report.append("【收益指标】")
        report.append(f"  总收益率:      {metrics.total_return:.2%}")
        report.append(f"  年化收益率:    {metrics.annual_return:.2%}")
        report.append(f"  卡玛比率:      {metrics.calmar_ratio:.2f}")
        report.append("")
        
        report.append("【风险指标】")
        report.append(f"  最大回撤:      {metrics.max_drawdown:.2%}")
        report.append(f"  回撤持续:      {metrics.max_drawdown_duration}天")
        report.append(f"  年化波动率:    {metrics.volatility:.2%}")
        report.append(f"  VaR (95%):     {metrics.var_95:.2%}")
        report.append("")
        
        report.append("【风险调整收益】")
        report.append(f"  夏普比率:      {metrics.sharpe_ratio:.2f}")
        report.append(f"  索提诺比率:    {metrics.sortino_ratio:.2f}")
        report.append(f"  信息比率:      {metrics.information_ratio:.2f}")
        report.append("")
        
        if metrics.total_trades > 0:
            report.append("【交易统计】")
            report.append(f"  总交易次数:    {metrics.total_trades}")
            report.append(f"  盈利次数:      {metrics.winning_trades}")
            report.append(f"  亏损次数:      {metrics.losing_trades}")
            report.append(f"  胜率:          {metrics.win_rate:.2%}")
            report.append(f"  盈亏比:        {metrics.profit_loss_ratio:.2f}")
            report.append(f"  平均持仓:      {metrics.avg_holding_days:.1f}天")
            
        report.append("")
        report.append("=" * 50)
        
        return "\n".join(report)
