"""
优化版回测引擎
使用 Numba 加速关键计算，减少内存使用
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import numba as nb

class OptimizedBacktestEngine:
    """优化版回测引擎"""
    
    def __init__(self, initial_capital: float = 100000, commission: float = 0.0003):
        self.initial_capital = initial_capital
        self.commission = commission
    
    @staticmethod
    @nb.jit(nopython=True, cache=True)
    def _calculate_ma_numba(prices: np.ndarray, period: int) -> np.ndarray:
        """使用 Numba 加速计算移动平均线"""
        n = len(prices)
        ma = np.empty(n)
        ma[:period-1] = np.nan
        
        # 计算第一个窗口
        window_sum = 0.0
        for i in range(period):
            window_sum += prices[i]
        ma[period-1] = window_sum / period
        
        # 滑动窗口计算
        for i in range(period, n):
            window_sum = window_sum - prices[i-period] + prices[i]
            ma[i] = window_sum / period
        
        return ma
    
    @staticmethod
    @nb.jit(nopython=True, cache=True)
    def _calculate_rsi_numba(prices: np.ndarray, period: int) -> np.ndarray:
        """使用 Numba 加速计算 RSI"""
        n = len(prices)
        deltas = np.zeros(n)
        deltas[1:] = prices[1:] - prices[:-1]
        
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        
        avg_gain = np.empty(n)
        avg_loss = np.empty(n)
        rsi = np.empty(n)
        
        # 初始化
        avg_gain[:period] = np.nan
        avg_loss[:period] = np.nan
        rsi[:period] = np.nan
        
        # 第一个窗口
        avg_gain[period-1] = np.mean(gains[1:period])
        avg_loss[period-1] = np.mean(losses[1:period])
        
        if avg_loss[period-1] == 0:
            rsi[period-1] = 100.0
        else:
            rs = avg_gain[period-1] / avg_loss[period-1]
            rsi[period-1] = 100.0 - (100.0 / (1.0 + rs))
        
        # 滑动窗口
        for i in range(period, n):
            avg_gain[i] = (avg_gain[i-1] * (period-1) + gains[i]) / period
            avg_loss[i] = (avg_loss[i-1] * (period-1) + losses[i]) / period
            
            if avg_loss[i] == 0:
                rsi[i] = 100.0
            else:
                rs = avg_gain[i] / avg_loss[i]
                rsi[i] = 100.0 - (100.0 / (1.0 + rs))
        
        return rsi
    
    def run_ma_crossover_optimized(self, df: pd.DataFrame, 
                                  fast_period: int = 5, 
                                  slow_period: int = 20) -> Dict:
        """优化版均线交叉策略回测"""
        if 'close' not in df.columns:
            return {'error': '数据缺少 close 列'}
        
        # 使用 Numba 加速计算
        prices = df['close'].values.astype(np.float64)
        
        # 计算移动平均线
        ma_fast = self._calculate_ma_numba(prices, fast_period)
        ma_slow = self._calculate_ma_numba(prices, slow_period)
        
        # 生成信号（向量化）
        signal = np.zeros(len(prices))
        signal[(ma_fast > ma_slow) & (~np.isnan(ma_fast)) & (~np.isnan(ma_slow))] = 1
        signal[(ma_fast < ma_slow) & (~np.isnan(ma_fast)) & (~np.isnan(ma_slow))] = -1
        
        # 计算收益
        returns = self._calculate_returns_optimized(prices, signal)
        
        return {
            'strategy': f'MA_Crossover_{fast_period}_{slow_period}',
            'initial_capital': self.initial_capital,
            'final_capital': self.initial_capital * (1 + returns['total_return']),
            'total_return': returns['total_return'],
            'sharpe_ratio': returns['sharpe_ratio'],
            'max_drawdown': returns['max_drawdown'],
            'win_rate': returns['win_rate'],
            'total_trades': returns['total_trades']
        }
    
    @staticmethod
    @nb.jit(nopython=True, cache=True)
    def _calculate_returns_optimized(prices: np.ndarray, signals: np.ndarray, 
                                    commission: float = 0.0003) -> Dict:
        """使用 Numba 加速计算收益"""
        n = len(prices)
        if n == 0:
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'total_trades': 0
            }
        
        # 初始化
        position = 0  # 0: 空仓, 1: 多头, -1: 空头
        capital = 1.0  # 归一化初始资金
        equity_curve = np.ones(n)
        trades = []
        
        for i in range(1, n):
            # 信号变化
            if signals[i] != signals[i-1]:
                if position != 0:
                    # 平仓
                    return_rate = (prices[i] / prices[i-1]) - 1
                    if position == -1:
                        return_rate = -return_rate
                    
                    # 扣除佣金
                    return_rate -= commission * 2
                    capital *= (1 + return_rate)
                    
                    trades.append({
                        'return': return_rate,
                        'win': return_rate > 0
                    })
                
                # 开仓
                position = int(signals[i])
            
            # 更新权益曲线
            equity_curve[i] = capital
        
        # 计算绩效指标
        returns = np.diff(equity_curve) / equity_curve[:-1]
        total_return = equity_curve[-1] - 1.0
        
        # 夏普比率（假设无风险利率为0）
        if len(returns) > 0 and np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
        
        # 最大回撤
        peak = equity_curve[0]
        max_drawdown = 0.0
        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # 胜率
        if len(trades) > 0:
            win_trades = sum(1 for trade in trades if trade['win'])
            win_rate = win_trades / len(trades)
        else:
            win_rate = 0.0
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': len(trades)
        }

# 性能测试函数
def test_performance():
    """测试优化前后的性能对比"""
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
    
    # 测试优化版
    print("测试优化版回测引擎...")
    start = time.time()
    engine = OptimizedBacktestEngine()
    result = engine.run_ma_crossover_optimized(df)
    optimized_time = time.time() - start
    
    print(f"优化版耗时: {optimized_time:.4f} 秒")
    print(f"总收益率: {result['total_return']:.2%}")
    print(f"夏普比率: {result['sharpe_ratio']:.2f}")
    print(f"最大回撤: {result['max_drawdown']:.2%}")
    print(f"胜率: {result['win_rate']:.2%}")
    print(f"交易次数: {result['total_trades']}")
    
    return optimized_time

if __name__ == "__main__":
    test_performance()
