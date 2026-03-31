# -*- coding: utf-8 -*-
"""
TradingAgents-CN - Technical Factors
技术因子模块

包含：
- 趋势指标 (MA, MACD, ADX)
- 动量指标 (RSI, KDJ, CCI)
- 波动率指标 (BOLL, ATR)
- 量价指标 (Volume, OBV)
"""

from typing import Dict
import pandas as pd
import numpy as np
from ..base import BaseFactor, FactorCategory, FactorType, FactorRegistry


_registry_registered = False


def _register_factors():
    global _registry_registered
    if _registry_registered:
        return
    
    # 趋势
    FactorRegistry.register(MA5_Slope)
    FactorRegistry.register(MA10_Slope)
    FactorRegistry.register(MA20_Slope)
    FactorRegistry.register(MA60_Slope)
    FactorRegistry.register(MACD_Value)
    FactorRegistry.register(MACD_Signal)
    FactorRegistry.register(MACD_Histogram)
    FactorRegistry.register(ADX)
    
    # 动量
    FactorRegistry.register(RSI_14)
    FactorRegistry.register(RSI_6)
    FactorRegistry.register(KDJ_K)
    FactorRegistry.register(KDJ_D)
    FactorRegistry.register(KDJ_J)
    FactorRegistry.register(CCI)
    FactorRegistry.register(WR)
    
    # 波动率
    FactorRegistry.register(BOLL_Upper)
    FactorRegistry.register(BOLL_Middle)
    FactorRegistry.register(BOLL_Lower)
    FactorRegistry.register(BOLL_Position)
    FactorRegistry.register(ATR)
    
    # 量价
    FactorRegistry.register(Volume_Ratio_5D)
    FactorRegistry.register(Volume_Ratio_10D)
    FactorRegistry.register(OBV)
    FactorRegistry.register(VR)
    FactorRegistry.register(Amihud_Illiquidity)
    
    _registry_registered = True


# ============== 趋势因子 ==============

class MA5_Slope(BaseFactor):
    """MA5 斜率"""
    name = "MA5_Slope"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "5日均线斜率"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        def calc_slope(group):
            if len(group) < 5:
                return np.nan
            prices = group['close'].tail(5).values
            x = np.arange(5)
            slope = np.polyfit(x, prices, 1)[0]
            return slope / prices.mean()
        
        return daily.groupby('ts_code').apply(calc_slope)


class MA10_Slope(BaseFactor):
    """MA10 斜率"""
    name = "MA10_Slope"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "10日均线斜率"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        def calc_slope(group):
            if len(group) < 10:
                return np.nan
            prices = group['close'].tail(10).values
            x = np.arange(10)
            slope = np.polyfit(x, prices, 1)[0]
            return slope / prices.mean()
        
        return daily.groupby('ts_code').apply(calc_slope)


class MA20_Slope(BaseFactor):
    """MA20 斜率"""
    name = "MA20_Slope"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "20日均线斜率"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        def calc_slope(group):
            if len(group) < 20:
                return np.nan
            prices = group['close'].tail(20).values
            x = np.arange(20)
            slope = np.polyfit(x, prices, 1)[0]
            return slope / prices.mean()
        
        return daily.groupby('ts_code').apply(calc_slope)


class MA60_Slope(BaseFactor):
    """MA60 斜率"""
    name = "MA60_Slope"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "60日均线斜率"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        def calc_slope(group):
            if len(group) < 60:
                return np.nan
            prices = group['close'].tail(60).values
            x = np.arange(60)
            slope = np.polyfit(x, prices, 1)[0]
            return slope / prices.mean()
        
        return daily.groupby('ts_code').apply(calc_slope)


class MACD_Value(BaseFactor):
    """MACD 值 (DIF)"""
    name = "MACD_Value"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "MACD 快线 (DIF)"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        def calc_macd(group):
            if len(group) < 26:
                return np.nan
            ema12 = group['close'].ewm(span=12).mean()
            ema26 = group['close'].ewm(span=26).mean()
            return (ema12 - ema26).iloc[-1]
        
        return daily.groupby('ts_code').apply(calc_macd)


class MACD_Signal(BaseFactor):
    """MACD 信号线 (DEA)"""
    name = "MACD_Signal"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "MACD 信号线 (DEA)"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        def calc_signal(group):
            if len(group) < 34:
                return np.nan
            ema12 = group['close'].ewm(span=12).mean()
            ema26 = group['close'].ewm(span=26).mean()
            dif = ema12 - ema26
            signal = dif.ewm(span=9).mean()
            return signal.iloc[-1]
        
        return daily.groupby('ts_code').apply(calc_signal)


class MACD_Histogram(BaseFactor):
    """MACD 柱状图"""
    name = "MACD_Histogram"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "MACD 柱状图 (DIF - DEA)"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        def calc_hist(group):
            if len(group) < 35:
                return np.nan
            ema12 = group['close'].ewm(span=12).mean()
            ema26 = group['close'].ewm(span=26).mean()
            dif = ema12 - ema26
            signal = dif.ewm(span=9).mean()
            return (dif - signal).iloc[-1]
        
        return daily.groupby('ts_code').apply(calc_hist)


class ADX(BaseFactor):
    """ADX 趋势强度"""
    name = "ADX"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "ADX 趋势强度指标"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'high' not in daily.columns or 'low' not in daily.columns:
            return pd.Series(dtype=float)
        
        def calc_adx(group):
            if len(group) < 28:
                return np.nan
            high = group['high']
            low = group['low']
            close = group['close']
            
            plus_dm = high.diff()
            minus_dm = -low.diff()
            
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm < 0] = 0
            
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            atr = tr.ewm(span=14).mean()
            plus_di = 100 * (plus_dm.ewm(span=14).mean() / atr)
            minus_di = 100 * (minus_dm.ewm(span=14).mean() / atr)
            
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.ewm(span=14).mean()
            return adx.iloc[-1]
        
        return daily.groupby('ts_code').apply(calc_adx)


# ============== 动量因子 ==============

class RSI_14(BaseFactor):
    """RSI (14日)"""
    name = "RSI_14"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "14日相对强弱指数"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        def calc_rsi(group):
            if len(group) < 15:
                return np.nan
            delta = group['close'].diff()
            gain = delta.where(delta > 0, 0).ewm(span=14).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(span=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]
        
        return daily.groupby('ts_code').apply(calc_rsi)


class RSI_6(BaseFactor):
    """RSI (6日)"""
    name = "RSI_6"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "6日相对强弱指数"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        def calc_rsi(group):
            if len(group) < 7:
                return np.nan
            delta = group['close'].diff()
            gain = delta.where(delta > 0, 0).ewm(span=6).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(span=6).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]
        
        return daily.groupby('ts_code').apply(calc_rsi)


class KDJ_K(BaseFactor):
    """KDJ K 值"""
    name = "KDJ_K"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "KDJ 指标 K 值"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'high' not in daily.columns or 'low' not in daily.columns:
            return pd.Series(dtype=float)
        
        def calc_kdj(group):
            if len(group) < 9:
                return np.nan
            low_n = group['low'].rolling(9).min()
            high_n = group['high'].rolling(9).max()
            rsv = 100 * (group['close'] - low_n) / (high_n - low_n)
            k = rsv.ewm(span=3).mean()
            d = k.ewm(span=3).mean()
            return k.iloc[-1]
        
        return daily.groupby('ts_code').apply(calc_kdj)


class KDJ_D(BaseFactor):
    """KDJ D 值"""
    name = "KDJ_D"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "KDJ 指标 D 值"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'high' not in daily.columns or 'low' not in daily.columns:
            return pd.Series(dtype=float)
        
        def calc_kdj(group):
            if len(group) < 9:
                return np.nan
            low_n = group['low'].rolling(9).min()
            high_n = group['high'].rolling(9).max()
            rsv = 100 * (group['close'] - low_n) / (high_n - low_n)
            k = rsv.ewm(span=3).mean()
            d = k.ewm(span=3).mean()
            return d.iloc[-1]
        
        return daily.groupby('ts_code').apply(calc_kdj)


class KDJ_J(BaseFactor):
    """KDJ J 值"""
    name = "KDJ_J"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "KDJ 指标 J 值"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'high' not in daily.columns or 'low' not in daily.columns:
            return pd.Series(dtype=float)
        
        def calc_kdj(group):
            if len(group) < 9:
                return np.nan
            low_n = group['low'].rolling(9).min()
            high_n = group['high'].rolling(9).max()
            rsv = 100 * (group['close'] - low_n) / (high_n - low_n)
            k = rsv.ewm(span=3).mean()
            d = k.ewm(span=3).mean()
            j = 3 * k - 2 * d
            return j.iloc[-1]
        
        return daily.groupby('ts_code').apply(calc_kdj)


class CCI(BaseFactor):
    """CCI 商品通道指数"""
    name = "CCI"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "商品通道指数"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'high' not in daily.columns or 'low' not in daily.columns:
            return pd.Series(dtype=float)
        
        def calc_cci(group):
            if len(group) < 14:
                return np.nan
            tp = (group['high'] + group['low'] + group['close']) / 3
            sma = tp.rolling(14).mean()
            mad = tp.rolling(14).apply(lambda x: np.abs(x - x.mean()).mean())
            cci = (tp - sma) / (0.015 * mad)
            return cci.iloc[-1]
        
        return daily.groupby('ts_code').apply(calc_cci)


class WR(BaseFactor):
    """Williams %R"""
    name = "WR"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "威廉指标"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'high' not in daily.columns or 'low' not in daily.columns:
            return pd.Series(dtype=float)
        
        def calc_wr(group):
            if len(group) < 14:
                return np.nan
            high_n = group['high'].rolling(14).max()
            low_n = group['low'].rolling(14).min()
            wr = -100 * (high_n - group['close']) / (high_n - low_n)
            return wr.iloc[-1]
        
        return daily.groupby('ts_code').apply(calc_wr)


# ============== 波动率因子 ==============

class BOLL_Upper(BaseFactor):
    """布林带上轨"""
    name = "BOLL_Upper"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "布林带上轨"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        def calc_boll(group):
            if len(group) < 20:
                return np.nan
            ma = group['close'].rolling(20).mean()
            std = group['close'].rolling(20).std()
            upper = ma + 2 * std
            return upper.iloc[-1]
        
        return daily.groupby('ts_code').apply(calc_boll)


class BOLL_Middle(BaseFactor):
    """布林带中轨"""
    name = "BOLL_Middle"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "布林带中轨 (20日均线)"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        return daily.groupby('ts_code')['close'].rolling(20).mean().droplevel(0)


class BOLL_Lower(BaseFactor):
    """布林带下轨"""
    name = "BOLL_Lower"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "布林带下轨"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        def calc_boll(group):
            if len(group) < 20:
                return np.nan
            ma = group['close'].rolling(20).mean()
            std = group['close'].rolling(20).std()
            lower = ma - 2 * std
            return lower.iloc[-1]
        
        return daily.groupby('ts_code').apply(calc_boll)


class BOLL_Position(BaseFactor):
    """布林带位置"""
    name = "BOLL_Position"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "价格在布林带中的位置 (0-1)"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None:
            raise ValueError("需要 daily 数据")
        
        def calc_pos(group):
            if len(group) < 20:
                return np.nan
            ma = group['close'].rolling(20).mean()
            std = group['close'].rolling(20).std()
            upper = ma + 2 * std
            lower = ma - 2 * std
            pos = (group['close'] - lower) / (upper - lower)
            return pos.iloc[-1]
        
        return daily.groupby('ts_code').apply(calc_pos)


class ATR(BaseFactor):
    """ATR 平均真实波幅"""
    name = "ATR"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "平均真实波幅"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'high' not in daily.columns or 'low' not in daily.columns:
            return pd.Series(dtype=float)
        
        def calc_atr(group):
            if len(group) < 14:
                return np.nan
            high = group['high']
            low = group['low']
            close = group['close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.ewm(span=14).mean()
            return atr.iloc[-1]
        
        return daily.groupby('ts_code').apply(calc_atr)


# ============== 量价因子 ==============

class Volume_Ratio_5D(BaseFactor):
    """5日量比"""
    name = "Volume_Ratio_5D"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "当前成交量与5日均量的比值"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'volume' not in daily.columns:
            return pd.Series(dtype=float)
        
        def calc_ratio(group):
            if len(group) < 5:
                return np.nan
            avg_vol = group['volume'].tail(5).mean()
            current_vol = group['volume'].iloc[-1]
            if avg_vol == 0:
                return np.nan
            return current_vol / avg_vol
        
        return daily.groupby('ts_code').apply(calc_ratio)


class Volume_Ratio_10D(BaseFactor):
    """10日量比"""
    name = "Volume_Ratio_10D"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "当前成交量与10日均量的比值"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'volume' not in daily.columns:
            return pd.Series(dtype=float)
        
        def calc_ratio(group):
            if len(group) < 10:
                return np.nan
            avg_vol = group['volume'].tail(10).mean()
            current_vol = group['volume'].iloc[-1]
            if avg_vol == 0:
                return np.nan
            return current_vol / avg_vol
        
        return daily.groupby('ts_code').apply(calc_ratio)


class OBV(BaseFactor):
    """OBV 能量潮"""
    name = "OBV"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "能量潮指标"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'volume' not in daily.columns:
            return pd.Series(dtype=float)
        
        def calc_obv(group):
            if len(group) < 2:
                return np.nan
            close_diff = group['close'].diff()
            volume = group['volume']
            obv = (close_diff > 0) * volume - (close_diff < 0) * volume
            return obv.cumsum().iloc[-1]
        
        return daily.groupby('ts_code').apply(calc_obv)


class VR(BaseFactor):
    """VR 成交量比率"""
    name = "VR"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "成交量比率"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'volume' not in daily.columns or 'close' not in daily.columns:
            return pd.Series(dtype=float)
        
        def calc_vr(group):
            if len(group) < 26:
                return np.nan
            up_vol = group[group['close'] > group['close'].shift(1)]['volume'].sum()
            down_vol = group[group['close'] < group['close'].shift(1)]['volume'].sum()
            if down_vol == 0:
                return np.nan
            return (up_vol + 0.5 * group[group['close'] == group['close'].shift(1)]['volume'].sum()) / down_vol * 100
        
        return daily.groupby('ts_code').apply(calc_vr)


class Amihud_Illiquidity(BaseFactor):
    """Amihud 非流动性因子"""
    name = "Amihud_Illiquidity"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.TECHNICAL
    description = "Amihud 非流动性比率"
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        daily = data.get('daily')
        if daily is None or 'volume' not in daily.columns or 'close' not in daily.columns:
            return pd.Series(dtype=float)
        
        def calc_amihud(group):
            if len(group) < 20:
                return np.nan
            returns = group['close'].pct_change().abs()
            volume = group['volume']
            illiq = (returns / volume).mean()
            return illiq * 1e6
        
        return daily.groupby('ts_code').apply(calc_amihud)


# 导出
__all__ = [
    # 趋势
    "MA5_Slope", "MA10_Slope", "MA20_Slope", "MA60_Slope",
    "MACD_Value", "MACD_Signal", "MACD_Histogram",
    "ADX",
    # 动量
    "RSI_14", "RSI_6",
    "KDJ_K", "KDJ_D", "KDJ_J",
    "CCI", "WR",
    # 波动率
    "BOLL_Upper", "BOLL_Middle", "BOLL_Lower", "BOLL_Position",
    "ATR",
    # 量价
    "Volume_Ratio_5D", "Volume_Ratio_10D",
    "OBV", "VR", "Amihud_Illiquidity",
]

_register_factors()