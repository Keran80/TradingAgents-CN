#!/usr/bin/env python3
"""
布林带策略
基于布林带指标的交易策略
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime

from .ai_strategy_base import AIStrategyBase

logger = logging.getLogger(__name__)

class BollingerBandsStrategy(AIStrategyBase):
    """
    布林带策略
    
    基于布林带指标生成交易信号。
    价格触及下轨为买入信号，触及上轨为卖出信号。
    """
    
    def __init__(self):
        """初始化布林带策略"""
        super().__init__(
            name="布林带策略",
            version="1.0.0"
        )
        
        # 默认参数
        self.default_params = {
            "period": 20,           # 移动平均线周期
            "std_dev": 2,           # 标准差倍数
            "position_size": 0.1,   # 仓位大小
            "stop_loss": 0.05,      # 止损比例
            "take_profit": 0.10,    # 止盈比例
            "band_width_threshold": 0.1  # 带宽阈值
        }
    
    def _on_initialize(self):
        """策略初始化逻辑"""
        logger.info(f"布林带策略初始化，参数: {self.parameters}")
        
        # 确保所有必要参数都有值
        for key, default_value in self.default_params.items():
            if key not in self.parameters:
                self.parameters[key] = default_value
        
        logger.info("布林带策略初始化完成")
    
    def _calculate_bollinger_bands(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        计算布林带
        
        Args:
            data: 价格数据
            
        Returns:
            布林带字典
        """
        close_prices = data["close"]
        period = self.parameters["period"]
        std_dev = self.parameters["std_dev"]
        
        # 计算移动平均线
        middle_band = close_prices.rolling(window=period).mean()
        
        # 计算标准差
        std = close_prices.rolling(window=period).std()
        
        # 计算上下轨
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        # 计算带宽
        band_width = (upper_band - lower_band) / middle_band
        
        return {
            "upper_band": upper_band,
            "middle_band": middle_band,
            "lower_band": lower_band,
            "band_width": band_width
        }
    
    async def analyze_market(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        分析市场数据
        
        Args:
            data: 市场数据
            
        Returns:
            市场分析结果
        """
        logger.info("开始布林带市场分析...")
        
        # 计算布林带
        bands = self._calculate_bollinger_bands(data)
        
        current_price = data["close"].iloc[-1]
        upper_band = bands["upper_band"].iloc[-1]
        middle_band = bands["middle_band"].iloc[-1]
        lower_band = bands["lower_band"].iloc[-1]
        band_width = bands["band_width"].iloc[-1]
        
        # 判断价格位置
        if pd.isna(upper_band) or pd.isna(lower_band):
            band_position = "unknown"
        elif current_price <= lower_band:
            band_position = "at_lower_band"
        elif current_price >= upper_band:
            band_position = "at_upper_band"
        elif current_price > middle_band:
            band_position = "above_middle"
        else:
            band_position = "below_middle"
        
        # 判断波动率
        volatility_status = "high" if band_width > self.parameters["band_width_threshold"] else "low"
        
        analysis_result = {
            "current_price": float(current_price),
            "upper_band": float(upper_band) if not pd.isna(upper_band) else None,
            "middle_band": float(middle_band) if not pd.isna(middle_band) else None,
            "lower_band": float(lower_band) if not pd.isna(lower_band) else None,
            "band_width": float(band_width) if not pd.isna(band_width) else None,
            "band_position": band_position,
            "volatility_status": volatility_status,
            "analysis_time": datetime.now().isoformat(),
            "data_points": len(data)
        }
        
        logger.info(f"布林带分析完成，位置: {band_position}, 波动率: {volatility_status}")
        return analysis_result
    
    async def generate_signals(self, analysis_result: Dict[str, Any]) -> List[Dict]:
        """
        生成交易信号
        
        Args:
            analysis_result: 市场分析结果
            
        Returns:
            交易信号列表
        """
        signals = []
        
        band_position = analysis_result.get("band_position")
        current_price = analysis_result.get("current_price")
        lower_band = analysis_result.get("lower_band")
        upper_band = analysis_result.get("upper_band")
        
        if band_position == "unknown" or current_price <= 0:
            return signals
        
        position_size = self.parameters["position_size"]
        
        # 生成信号
        if band_position == "at_lower_band" and lower_band is not None:
            signal = {
                "timestamp": datetime.now().isoformat(),
                "symbol": "EXAMPLE",
                "action": "BUY",
                "price": current_price,
                "quantity": position_size,
                "reason": f"价格触及布林带下轨: {current_price:.2f} ≤ {lower_band:.2f}",
                "confidence": 0.7,
                "strategy": self.name,
                "parameters": {
                    "period": self.parameters["period"],
                    "std_dev": self.parameters["std_dev"],
                    "band_width": analysis_result.get("band_width")
                },
                "risk_metrics": {
                    "stop_loss": current_price * (1 - self.parameters["stop_loss"]),
                    "take_profit": current_price * (1 + self.parameters["take_profit"])
                }
            }
            signals.append(signal)
            
        elif band_position == "at_upper_band" and upper_band is not None:
            signal = {
                "timestamp": datetime.now().isoformat(),
                "symbol": "EXAMPLE",
                "action": "SELL",
                "price": current_price,
                "quantity": position_size,
                "reason": f"价格触及布林带上轨: {current_price:.2f} ≥ {upper_band:.2f}",
                "confidence": 0.7,
                "strategy": self.name,
                "parameters": {
                    "period": self.parameters["period"],
                    "std_dev": self.parameters["std_dev"],
                    "band_width": analysis_result.get("band_width")
                },
                "risk_metrics": {
                    "stop_loss": current_price * (1 + self.parameters["stop_loss"]),
                    "take_profit": current_price * (1 - self.parameters["take_profit"])
                }
            }
            signals.append(signal)
        
        logger.info(f"生成 {len(signals)} 个布林带交易信号")
        return signals
    
    def calculate_risk(self, signals: List[Dict], portfolio_value: float) -> Dict[str, float]:
        """
        计算交易风险
        
        Args:
            signals: 交易信号列表
            portfolio_value: 投资组合价值
            
        Returns:
            风险指标字典
        """
        if not signals:
            return {
                "total_risk": 0.0,
                "position_risk": 0.0,
                "market_risk": 0.2,
                "signal_quality": 0.0
            }
        
        # 计算信号质量
        avg_confidence = np.mean([signal.get("confidence", 0) for signal in signals])
        signal_quality = avg_confidence
        
        # 计算仓位风险
        total_position = sum(signal.get("quantity", 0) for signal in signals)
        position_risk = min(total_position / 0.3, 1.0)
        
        # 根据波动率调整市场风险
        market_risk = 0.3 if analysis_result.get("volatility_status") == "high" else 0.2
        
        # 总风险计算
        total_risk = position_risk * 0.4 + market_risk * 0.4 + (1 - signal_quality) * 0.2
        
        risk_metrics = {
            "total_risk": float(total_risk),
            "position_risk": float(position_risk),
            "market_risk": float(market_risk),
            "signal_quality": float(signal_quality),
            "avg_confidence": float(avg_confidence),
            "total_position": float(total_position)
        }
        
        return risk_metrics

# 注册策略到工厂
from .ai_strategy_base import StrategyFactory
StrategyFactory.register_strategy("bollinger", BollingerBandsStrategy)
