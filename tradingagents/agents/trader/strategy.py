# -*- coding: utf-8 -*-
"""
A股量化策略库
提供常用技术分析策略的信号生成
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from enum import Enum


class Signal(Enum):
    """交易信号枚举"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Strategy:
    """策略基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """
        生成交易信号
        
        Args:
            df: 包含OHLCV数据的DataFrame
            
        Returns:
            Dict: {
                'signal': Signal,
                'reason': str,  # 信号原因
                'confidence': float  # 置信度 0-1
            }
        """
        raise NotImplementedError


class MACrossoverStrategy(Strategy):
    """均线交叉策略"""
    
    def __init__(self, short_period: int = 5, long_period: int = 20):
        super().__init__(f"MA_Crossover_{short_period}_{long_period}")
        self.short_period = short_period
        self.long_period = long_period
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        if len(df) < self.long_period + 1:
            return {'signal': Signal.HOLD, 'reason': '数据不足', 'confidence': 0}
        
        # 计算均线
        df = df.copy()
        df['ma_short'] = df['close'].rolling(window=self.short_period).mean()
        df['ma_long'] = df['close'].rolling(window=self.long_period).mean()
        
        # 获取最近两天的均线值
        current_short = df['ma_short'].iloc[-1]
        current_long = df['ma_long'].iloc[-1]
        prev_short = df['ma_short'].iloc[-2]
        prev_long = df['ma_long'].iloc[-2]
        
        if pd.isna(current_short) or pd.isna(current_long):
            return {'signal': Signal.HOLD, 'reason': '均线数据不足', 'confidence': 0}
        
        # 金叉：短均线从下方穿过长均线
        if prev_short <= prev_long and current_short > current_long:
            # 计算涨幅增强置信度
            change_pct = (current_short - prev_short) / prev_short * 100
            confidence = min(0.7 + abs(change_pct) / 10, 1.0)
            return {
                'signal': Signal.BUY,
                'reason': f'金叉信号：MA{self.short_period}({current_short:.2f})上穿MA{self.long_period}({current_long:.2f})',
                'confidence': confidence
            }
        
        # 死叉：短均线从上方穿过长均线
        elif prev_short >= prev_long and current_short < current_long:
            change_pct = (prev_short - current_short) / prev_short * 100
            confidence = min(0.7 + abs(change_pct) / 10, 1.0)
            return {
                'signal': Signal.SELL,
                'reason': f'死叉信号：MA{self.short_period}({current_short:.2f})下穿MA{self.long_period}({current_long:.2f})',
                'confidence': confidence
            }
        
        # 持续多头：短均线在长均线上方
        elif current_short > current_long:
            return {
                'signal': Signal.HOLD,
                'reason': f'多头排列：MA{self.short_period}({current_short:.2f}) > MA{self.long_period}({current_long:.2f})',
                'confidence': 0.6
            }
        
        # 持续空头：短均线在长均线下方
        else:
            return {
                'signal': Signal.HOLD,
                'reason': f'空头排列：MA{self.short_period}({current_short:.2f}) < MA{self.long_period}({current_long:.2f})',
                'confidence': 0.6
            }


class RSIStrategy(Strategy):
    """RSI 策略"""
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__(f"RSI_{period}")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        if len(df) < self.period + 1:
            return {'signal': Signal.HOLD, 'reason': '数据不足', 'confidence': 0}
        
        df = df.copy()
        
        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        current_rsi = df['rsi'].iloc[-1]
        
        if pd.isna(current_rsi):
            return {'signal': Signal.HOLD, 'reason': 'RSI计算失败', 'confidence': 0}
        
        # 超卖买入信号
        if current_rsi < self.oversold:
            confidence = 0.7 + (self.oversold - current_rsi) / self.oversold * 0.3
            return {
                'signal': Signal.BUY,
                'reason': f'超卖信号：RSI({current_rsi:.1f}) < {self.oversold}',
                'confidence': min(confidence, 1.0)
            }
        
        # 超买卖出信号
        elif current_rsi > self.overbought:
            confidence = 0.7 + (current_rsi - self.overbought) / (100 - self.overbought) * 0.3
            return {
                'signal': Signal.SELL,
                'reason': f'超买信号：RSI({current_rsi:.1f}) > {self.overbought}',
                'confidence': min(confidence, 1.0)
            }
        
        # 50中轴判断
        elif current_rsi > 50:
            return {
                'signal': Signal.HOLD,
                'reason': f'偏强区域：RSI({current_rsi:.1f}) > 50',
                'confidence': 0.5
            }
        
        else:
            return {
                'signal': Signal.HOLD,
                'reason': f'偏弱区域：RSI({current_rsi:.1f}) < 50',
                'confidence': 0.5
            }


class MACDStrategy(Strategy):
    """MACD 策略"""
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__(f"MACD_{fast}_{slow}_{signal}")
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        if len(df) < self.slow + self.signal + 1:
            return {'signal': Signal.HOLD, 'reason': '数据不足', 'confidence': 0}
        
        df = df.copy()
        
        # 计算MACD
        ema_fast = df['close'].ewm(span=self.fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=self.slow, adjust=False).mean()
        df['macd'] = ema_fast - ema_slow
        df['macds'] = df['macd'].ewm(span=self.signal, adjust=False).mean()
        df['macdh'] = (df['macd'] - df['macds']) * 2
        
        current_macd = df['macd'].iloc[-1]
        current_signal = df['macds'].iloc[-1]
        current_hist = df['macdh'].iloc[-1]
        
        prev_macd = df['macd'].iloc[-2]
        prev_signal = df['macds'].iloc[-2]
        
        if pd.isna(current_macd) or pd.isna(current_signal):
            return {'signal': Signal.HOLD, 'reason': 'MACD计算失败', 'confidence': 0}
        
        # 金叉：MACD线从下方穿过Signal线
        if prev_macd <= prev_signal and current_macd > current_signal:
            confidence = min(0.7 + abs(current_hist) / 10, 1.0)
            return {
                'signal': Signal.BUY,
                'reason': f'金叉：MACD({current_macd:.4f})上穿Signal({current_signal:.4f})，柱状图={current_hist:.4f}',
                'confidence': confidence
            }
        
        # 死叉：MACD线从上方穿过Signal线
        elif prev_macd >= prev_signal and current_macd < current_signal:
            confidence = min(0.7 + abs(current_hist) / 10, 1.0)
            return {
                'signal': Signal.SELL,
                'reason': f'死叉：MACD({current_macd:.4f})下穿Signal({current_signal:.4f})，柱状图={current_hist:.4f}',
                'confidence': confidence
            }
        
        # 零轴上方多头
        elif current_macd > 0 and current_signal > 0:
            return {
                'signal': Signal.HOLD,
                'reason': f'多头区域：MACD({current_macd:.4f}) > 0',
                'confidence': 0.6
            }
        
        # 零轴下方空头
        else:
            return {
                'signal': Signal.HOLD,
                'reason': f'空头区域：MACD({current_macd:.4f}) < 0',
                'confidence': 0.6
            }


class BollingerStrategy(Strategy):
    """布林带策略"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__(f"Bollinger_{period}_{std_dev}")
        self.period = period
        self.std_dev = std_dev
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        if len(df) < self.period:
            return {'signal': Signal.HOLD, 'reason': '数据不足', 'confidence': 0}
        
        df = df.copy()
        
        # 计算布林带
        df['boll_mid'] = df['close'].rolling(window=self.period).mean()
        std = df['close'].rolling(window=self.period).std()
        df['boll_upper'] = df['boll_mid'] + (std * self.std_dev)
        df['boll_lower'] = df['boll_mid'] - (std * self.std_dev)
        
        current_close = df['close'].iloc[-1]
        upper = df['boll_upper'].iloc[-1]
        lower = df['boll_lower'].iloc[-1]
        mid = df['boll_mid'].iloc[-1]
        
        if pd.isna(upper) or pd.isna(lower):
            return {'signal': Signal.HOLD, 'reason': '布林带计算失败', 'confidence': 0}
        
        # 触及下轨买入
        if current_close <= lower:
            distance = (lower - current_close) / lower
            confidence = min(0.7 + distance * 0.3, 1.0)
            return {
                'signal': Signal.BUY,
                'reason': f'触及下轨：收盘价({current_close:.2f}) <= 下轨({lower:.2f})',
                'confidence': confidence
            }
        
        # 触及上轨卖出
        elif current_close >= upper:
            distance = (current_close - upper) / upper
            confidence = min(0.7 + distance * 0.3, 1.0)
            return {
                'signal': Signal.SELL,
                'reason': f'触及上轨：收盘价({current_close:.2f}) >= 上轨({upper:.2f})',
                'confidence': confidence
            }
        
        # 中轨上方偏多
        elif current_close > mid:
            return {
                'signal': Signal.HOLD,
                'reason': f'偏多：收盘价({current_close:.2f}) > 中轨({mid:.2f})',
                'confidence': 0.5
            }
        
        # 中轨下方偏空
        else:
            return {
                'signal': Signal.HOLD,
                'reason': f'偏空：收盘价({current_close:.2f}) < 中轨({mid:.2f})',
                'confidence': 0.5
            }


class CombinedStrategy(Strategy):
    """组合策略：多策略信号加权"""
    
    def __init__(self, strategies: List[Strategy], weights: Optional[List[float]] = None):
        super().__init__("Combined")
        self.strategies = strategies
        self.weights = weights or [1.0] * len(strategies)
        
        # 归一化权重
        total = sum(self.weights)
        self.weights = [w / total for w in self.weights]
    
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        signals = []
        
        for strategy in self.strategies:
            result = strategy.generate_signal(df)
            signals.append(result)
        
        # 统计信号
        buy_count = sum(1 for s in signals if s['signal'] == Signal.BUY)
        sell_count = sum(1 for s in signals if s['signal'] == Signal.SELL)
        
        # 加权置信度
        buy_confidence = sum(
            s['confidence'] * w 
            for s, w in zip(signals, self.weights) 
            if s['signal'] == Signal.BUY
        ) / max(buy_count, 1)
        
        sell_confidence = sum(
            s['confidence'] * w 
            for s, w in zip(signals, self.weights) 
            if s['signal'] == Signal.SELL
        ) / max(sell_count, 1)
        
        # 多数投票
        if buy_count > sell_count and buy_count >= len(self.strategies) / 2:
            return {
                'signal': Signal.BUY,
                'reason': f'组合买入：{buy_count}/{len(self.strategies)} 策略看多',
                'confidence': buy_confidence,
                'details': signals
            }
        elif sell_count > buy_count and sell_count >= len(self.strategies) / 2:
            return {
                'signal': Signal.SELL,
                'reason': f'组合卖出：{sell_count}/{len(self.strategies)} 策略看空',
                'confidence': sell_confidence,
                'details': signals
            }
        else:
            return {
                'signal': Signal.HOLD,
                'reason': f'组合观望：多空平衡 ({buy_count} vs {sell_count})',
                'confidence': 0.5,
                'details': signals
            }


# 便捷函数
def create_strategy(strategy_type: str, **params) -> Strategy:
    """
    创建策略实例
    
    Args:
        strategy_type: 策略类型 ('ma_crossover', 'rsi', 'macd', 'bollinger', 'combined')
        **params: 策略参数
        
    Returns:
        Strategy: 策略实例
    """
    strategy_type = strategy_type.lower()
    
    if strategy_type == 'ma_crossover':
        short = params.get('short_period', 5)
        long = params.get('long_period', 20)
        return MACrossoverStrategy(short, long)
    
    elif strategy_type == 'rsi':
        period = params.get('period', 14)
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)
        return RSIStrategy(period, oversold, overbought)
    
    elif strategy_type == 'macd':
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal = params.get('signal', 9)
        return MACDStrategy(fast, slow, signal)
    
    elif strategy_type == 'bollinger':
        period = params.get('period', 20)
        std_dev = params.get('std_dev', 2.0)
        return BollingerStrategy(period, std_dev)
    
    elif strategy_type == 'combined':
        # 组合默认策略
        strategies = [
            MACrossoverStrategy(5, 20),
            RSIStrategy(),
            MACDStrategy(),
        ]
        return CombinedStrategy(strategies)
    
    else:
        raise ValueError(f"Unknown strategy type: {strategy_type}")


def analyze_stock(df: pd.DataFrame, strategy_type: str = 'combined') -> Dict:
    """
    分析股票生成交易信号
    
    Args:
        df: OHLCV数据
        strategy_type: 策略类型
        
    Returns:
        Dict: 包含信号、置信度和详细分析
    """
    strategy = create_strategy(strategy_type)
    result = strategy.generate_signal(df)
    
    # 添加最新价格信息
    if not df.empty:
        result['price'] = round(df['close'].iloc[-1], 2)
        result['volume'] = int(df['volume'].iloc[-1]) if 'volume' in df.columns else None
    
    return result
