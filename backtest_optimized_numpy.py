"""
优化版回测引擎（纯 NumPy 版本）
不依赖 Numba，使用向量化 NumPy 计算
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple
from datetime import datetime

class NumpyBacktestEngine:
    """纯 NumPy 优化版回测引擎"""
    
    def __init__(self, initial_capital: float = 100000, commission: float = 0.0003):
        self.initial_capital = initial_capital
        self.commission = commission
    
    @staticmethod
    def _calculate_ma_vectorized(prices: np.ndarray, period: int) -> np.ndarray:
        """向量化计算移动平均线"""
        n = len(prices)
        ma = np.full(n, np.nan, dtype=np.float64)
        
        # 使用卷积计算移动平均（性能最优）
        weights = np.ones(period) / period
        ma[period-1:] = np.convolve(prices, weights, mode='valid')
        
        return ma
    
    @staticmethod
    def _calculate_rsi_vectorized(prices: np.ndarray, period: int) -> np.ndarray:
        """向量化计算 RSI"""
        n = len(prices)
        deltas = np.zeros(n, dtype=np.float64)
        deltas[1:] = prices[1:] - prices[:-1]
        
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        
        # 使用滚动窗口计算
        avg_gain = np.full(n, np.nan, dtype=np.float64)
        avg_loss = np.full(n, np.nan, dtype=np.float64)
        
        # 第一个窗口
        avg_gain[period-1] = np.mean(gains[1:period])
        avg_loss[period-1] = np.mean(losses[1:period])
        
        # 使用指数移动平均（EMA）计算后续值
        alpha = 1.0 / period
        for i in range(period, n):
            avg_gain[i] = avg_gain[i-1] * (1 - alpha) + gains[i] * alpha
            avg_loss[i] = avg_loss[i-1] * (1 - alpha) + losses[i] * alpha
        
        # 计算 RSI
        rsi = np.full(n, np.nan, dtype=np.float64)
        mask = avg_loss > 0
        rsi[mask] = 100.0 - 100.0 / (1.0 + avg_gain[mask] / avg_loss[mask])
        rsi[~mask & ~np.isnan(avg_gain)] = 100.0
        
        return rsi
    
    def run_ma_crossover_vectorized(self, df: pd.DataFrame, 
                                   fast_period: int = 5, 
                                   slow_period: int = 20) -> Dict:
        """向量化均线交叉策略回测"""
        if 'close' not in df.columns:
            return {'error': '数据缺少 close 列'}
        
        # 使用向量化计算
        prices = df['close'].values.astype(np.float64)
        
        # 计算移动平均线
        ma_fast = self._calculate_ma_vectorized(prices, fast_period)
        ma_slow = self._calculate_ma_vectorized(prices, slow_period)
        
        # 生成信号（向量化）
        signal = np.zeros(len(prices), dtype=np.int8)
        
        # 创建有效数据掩码
        valid_mask = ~np.isnan(ma_fast) & ~np.isnan(ma_slow)
        
        # 多头信号：快线在慢线上方
        long_mask = valid_mask & (ma_fast > ma_slow)
        signal[long_mask] = 1
        
        # 空头信号：快线在慢线下方
        short_mask = valid_mask & (ma_fast < ma_slow)
        signal[short_mask] = -1
        
        # 计算收益
        returns = self._calculate_returns_vectorized(prices, signal)
        
        return {
            'strategy': f'MA_Crossover_{fast_period}_{slow_period}',
            'initial_capital': self.initial_capital,
            'final_capital': self.initial_capital * (1 + returns['total_return']),
            'total_return': returns['total_return'],
            'sharpe_ratio': returns['sharpe_ratio'],
            'max_drawdown': returns['max_drawdown'],
            'win_rate': returns['win_rate'],
            'total_trades': returns['total_trades'],
            'optimization': 'vectorized_numpy'
        }
    
    @staticmethod
    def _calculate_returns_vectorized(prices: np.ndarray, signals: np.ndarray, 
                                     commission: float = 0.0003) -> Dict:
        """向量化计算收益"""
        n = len(prices)
        if n < 2:
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'total_trades': 0
            }
        
        # 计算价格变化率
        price_returns = np.zeros(n, dtype=np.float64)
        price_returns[1:] = prices[1:] / prices[:-1] - 1.0
        
        # 计算持仓收益（向量化）
        position_changes = np.diff(signals, prepend=0)
        
        # 开仓和平仓点
        open_positions = np.where(position_changes != 0)[0]
        
        # 计算每笔交易收益
        trade_returns = []
        current_position = 0
        entry_price = 0.0
        
        for i in range(1, n):
            if position_changes[i] != 0:
                # 平仓上一笔交易
                if current_position != 0 and entry_price > 0:
                    exit_return = (prices[i] / entry_price - 1.0) * current_position
                    exit_return -= commission * 2  # 买卖佣金
                    trade_returns.append(exit_return)
                
                # 开仓新交易
                current_position = signals[i]
                entry_price = prices[i]
        
        # 计算总收益
        if trade_returns:
            trade_returns_array = np.array(trade_returns)
            total_return = np.prod(1 + trade_returns_array) - 1.0
            win_rate = np.mean(trade_returns_array > 0)
        else:
            total_return = 0.0
            win_rate = 0.0
        
        # 计算权益曲线（简化版）
        equity = np.ones(n, dtype=np.float64)
        for i in range(1, n):
            if signals[i-1] != 0:
                position_return = price_returns[i] * signals[i-1]
                position_return -= commission * abs(signals[i-1]) / 252  # 每日佣金
                equity[i] = equity[i-1] * (1 + position_return)
            else:
                equity[i] = equity[i-1]
        
        # 计算夏普比率
        equity_returns = np.diff(equity) / equity[:-1]
        if len(equity_returns) > 0 and np.std(equity_returns) > 0:
            sharpe_ratio = np.mean(equity_returns) / np.std(equity_returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
        
        # 计算最大回撤
        peak = equity[0]
        max_drawdown = 0.0
        for value in equity:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': len(trade_returns)
        }

# 性能测试函数
def test_vectorized_performance():
    """测试向量化版本性能"""
    import time
    
    # 生成测试数据
    np.random.seed(42)
    n = 10000
    dates = pd.date_range('2020-01-01', periods=n, freq='D')
    data = {
        'open': np.random.randn(n).cumsum() + 100,
        'high': np.random.randn(n).cumsum() + 105,
        'low': np.random.randn(n).cumsum() + 95,
        'close': np.random.randn(n).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, n)
    }
    df = pd.DataFrame(data, index=dates)
    
    # 测试向量化版本
    print("测试向量化回测引擎...")
    start = time.time()
    engine = NumpyBacktestEngine()
    result = engine.run_ma_crossover_vectorized(df)
    vectorized_time = time.time() - start
    
    print(f"向量化耗时: {vectorized_time:.4f} 秒")
    print(f"总收益率: {result['total_return']:.2%}")
    print(f"夏普比率: {result['sharpe_ratio']:.2f}")
    print(f"最大回撤: {result['max_drawdown']:.2%}")
    print(f"胜率: {result['win_rate']:.2%}")
    print(f"交易次数: {result['total_trades']}")
    print(f"优化方式: {result['optimization']}")
    
    return vectorized_time

if __name__ == "__main__":
    test_vectorized_performance()
