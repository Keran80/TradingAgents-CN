# -*- coding: utf-8 -*-
"""
回测模块
集成 backtesting-trading skill 策略回测功能
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import os


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 100000, commission: float = 0.0003):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
            commission: 佣金费率（默认万三）
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.positions = []  # 持仓记录
        self.trades = []  # 交易记录
    
    def run_ma_crossover(self, df: pd.DataFrame, 
                         fast_period: int = 5, 
                         slow_period: int = 20) -> Dict:
        """
        均线交叉策略回测
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
            fast_period: 短期均线周期
            slow_period: 长期均线周期
            
        Returns:
            Dict: 回测结果
        """
        if 'close' not in df.columns:
            return {'error': '数据缺少 close 列'}
        
        # 计算均线
        data = df.copy()
        data['ma_fast'] = data['close'].rolling(window=fast_period).mean()
        data['ma_slow'] = data['close'].rolling(window=slow_period).mean()
        
        # 生成信号
        data['signal'] = 0
        data.loc[data['ma_fast'] > data['ma_slow'], 'signal'] = 1  # 多头
        data.loc[data['ma_fast'] < data['ma_slow'], 'signal'] = -1  # 空头
        
        return self._calculate_returns(data, f"MA_Crossover_{fast_period}_{slow_period}")
    
    def run_rsi(self, df: pd.DataFrame,
                period: int = 14,
                oversold: int = 30,
                overbought: int = 70) -> Dict:
        """RSI 策略回测"""
        if 'close' not in df.columns:
            return {'error': '数据缺少 close 列'}
        
        data = df.copy()
        
        # 计算 RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # 生成信号
        data['signal'] = 0
        data.loc[data['rsi'] < oversold, 'signal'] = 1  # 超卖买入
        data.loc[data['rsi'] > overbought, 'signal'] = -1  # 超买卖出
        
        return self._calculate_returns(data, f"RSI_{period}")
    
    def run_macd(self, df: pd.DataFrame,
                 fast: int = 12,
                 slow: int = 26,
                 signal: int = 9) -> Dict:
        """MACD 策略回测"""
        if 'close' not in df.columns:
            return {'error': '数据缺少 close 列'}
        
        data = df.copy()
        
        # 计算 MACD
        ema_fast = data['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = data['close'].ewm(span=slow, adjust=False).mean()
        data['macd'] = ema_fast - ema_slow
        data['macds'] = data['macd'].ewm(span=signal, adjust=False).mean()
        
        # 生成信号
        data['signal'] = 0
        data.loc[data['macd'] > data['macds'], 'signal'] = 1  # 金叉多头
        data.loc[data['macd'] < data['macds'], 'signal'] = -1  # 死叉空头
        
        return self._calculate_returns(data, f"MACD_{fast}_{slow}_{signal}")
    
    def run_bollinger(self, df: pd.DataFrame,
                     period: int = 20,
                     std_dev: float = 2.0) -> Dict:
        """布林带策略回测"""
        if 'close' not in df.columns:
            return {'error': '数据缺少 close 列'}
        
        data = df.copy()
        
        # 计算布林带
        data['boll_mid'] = data['close'].rolling(window=period).mean()
        std = data['close'].rolling(window=period).std()
        data['boll_upper'] = data['boll_mid'] + (std * std_dev)
        data['boll_lower'] = data['boll_mid'] - (std * std_dev)
        
        # 生成信号
        data['signal'] = 0
        data.loc[data['close'] <= data['boll_lower'], 'signal'] = 1  # 触及下轨买入
        data.loc[data['close'] >= data['boll_upper'], 'signal'] = -1  # 触及上轨卖出
        
        return self._calculate_returns(data, f"Bollinger_{period}_{std_dev}")
    
    def run_combined(self, df: pd.DataFrame,
                    strategies: List[str] = None) -> Dict:
        """组合策略回测"""
        if strategies is None:
            strategies = ['ma_crossover', 'rsi', 'macd']
        
        results = {}
        
        for strategy in strategies:
            if strategy == 'ma_crossover':
                results[strategy] = self.run_ma_crossover(df)
            elif strategy == 'rsi':
                results[strategy] = self.run_rsi(df)
            elif strategy == 'macd':
                results[strategy] = self.run_macd(df)
            elif strategy == 'bollinger':
                results[strategy] = self.run_bollinger(df)
        
        return results
    
    def _calculate_returns(self, data: pd.DataFrame, strategy_name: str) -> Dict:
        """计算回测收益"""
        # 过滤有效数据
        data = data.dropna()
        
        if len(data) < 2:
            return {'error': '有效数据不足'}
        
        # 计算收益率
        data['returns'] = data['close'].pct_change()
        data['strategy_returns'] = data['signal'].shift(1) * data['returns']
        
        # 扣除手续费
        data['strategy_returns'] = data['strategy_returns'] - self.commission
        
        # 累计收益
        data['cumulative_returns'] = (1 + data['strategy_returns']).cumprod()
        data['benchmark_cumulative'] = (1 + data['returns']).cumprod()
        
        # 计算各项指标
        total_return = data['cumulative_returns'].iloc[-1] - 1
        benchmark_return = data['benchmark_cumulative'].iloc[-1] - 1
        
        # 年化收益率
        years = len(data) / 252
        if years > 0:
            cagr = (1 + total_return) ** (1 / years) - 1
        else:
            cagr = 0
        
        # 夏普比率
        if data['strategy_returns'].std() > 0:
            sharpe = (data['strategy_returns'].mean() * 252) / (data['strategy_returns'].std() * np.sqrt(252))
        else:
            sharpe = 0
        
        # 最大回撤
        rolling_max = data['cumulative_returns'].cummax()
        drawdown = (data['cumulative_returns'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # 交易统计
        position_changes = data['signal'].diff().fillna(0)
        num_trades = (position_changes != 0).sum()
        
        # 胜率
        winning_trades = data['strategy_returns'] > 0
        win_rate = winning_trades.sum() / len(data) if len(data) > 0 else 0
        
        return {
            'strategy': strategy_name,
            'total_return': total_return,
            'benchmark_return': benchmark_return,
            'cagr': cagr,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'num_trades': num_trades,
            'win_rate': win_rate,
            'data': data,
        }
    
    def format_result(self, result: Dict) -> str:
        """格式化回测结果"""
        if 'error' in result:
            return f"回测错误: {result['error']}"
        
        lines = []
        lines.append(f"\n{'='*50}")
        lines.append(f"  {result['strategy']} 回测结果")
        lines.append(f"{'='*50}")
        
        lines.append("\n【收益指标】")
        lines.append(f"  总收益率: {result['total_return']*100:+.2f}%")
        lines.append(f"  基准收益: {result['benchmark_return']*100:+.2f}%")
        lines.append(f"  年化收益率(CAGR): {result['cagr']*100:+.2f}%")
        lines.append(f"  夏普比率: {result['sharpe_ratio']:.2f}")
        
        lines.append("\n【风险指标】")
        lines.append(f"  最大回撤: {result['max_drawdown']*100:.2f}%")
        
        lines.append("\n【交易统计】")
        lines.append(f"  总交易次数: {result['num_trades']}")
        lines.append(f"  胜率: {result['win_rate']*100:.1f}%")
        
        return "\n".join(lines)


def run_backtest(ticker: str, 
                start_date: str, 
                end_date: str,
                strategy: str = 'ma_crossover',
                **params) -> Dict:
    """
    运行回测的便捷函数
    
    Args:
        ticker: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        strategy: 策略类型
        **params: 策略参数
        
    Returns:
        Dict: 回测结果
    """
    # 获取数据
    try:
        from tradingagents.dataflows.astock_utils import AStockData
        
        start = start_date.replace('-', '')
        end = end_date.replace('-', '')
        
        df = AStockData.get_daily(ticker, start, end)
        
        if df.empty:
            return {'error': f'无法获取 {ticker} 的数据'}
        
        # 列名转换
        rename_map = {
            '日期': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume'
        }
        df = df.rename(columns=rename_map)
        
    except Exception as e:
        return {'error': f'数据获取失败: {str(e)}'}
    
    # 运行回测
    engine = BacktestEngine()
    
    if strategy == 'ma_crossover':
        fast = params.get('fast_period', 5)
        slow = params.get('slow_period', 20)
        result = engine.run_ma_crossover(df, fast, slow)
    elif strategy == 'rsi':
        period = params.get('period', 14)
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)
        result = engine.run_rsi(df, period, oversold, overbought)
    elif strategy == 'macd':
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal = params.get('signal', 9)
        result = engine.run_macd(df, fast, slow, signal)
    elif strategy == 'bollinger':
        period = params.get('period', 20)
        std_dev = params.get('std_dev', 2.0)
        result = engine.run_bollinger(df, period, std_dev)
    elif strategy == 'combined':
        result = engine.run_combined(df)
    else:
        return {'error': f'未知策略: {strategy}'}
    
    return result


if __name__ == "__main__":
    # 测试回测
    print("回测模块测试")
    
    # 生成模拟数据
    np.random.seed(42)
    dates = pd.date_range(end='2024-01-01', periods=252, freq='D')
    prices = 100 + np.cumsum(np.random.randn(252) * 2)
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices * 0.99,
        'close': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'volume': np.random.randint(1000000, 10000000, 252)
    })
    
    engine = BacktestEngine()
    
    # 测试各策略
    strategies = [
        ('MA_Crossover(5,20)', engine.run_ma_crossover(df, 5, 20)),
        ('RSI(14)', engine.run_rsi(df)),
        ('MACD(12,26,9)', engine.run_macd(df)),
        ('Bollinger(20,2.0)', engine.run_bollinger(df)),
    ]
    
    for name, result in strategies:
        if 'error' in result:
            print(f"{name}: {result['error']}")
        else:
            print(engine.format_result(result))
