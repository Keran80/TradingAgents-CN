#!/usr/bin/env python3
"""
MACD策略
基于MACD指标的交易策略
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime

from .ai_strategy_base import AIStrategyBase

logger = logging.getLogger(__name__)

class MACDStrategy(AIStrategyBase):
    """
    MACD策略
    
    基于MACD指标生成交易信号。
    DIF上穿DEA为买入信号，下穿为卖出信号。
    """
    
    def __init__(self):
        """初始化MACD策略"""
        super().__init__(
            name="MACD策略",
            version="1.0.0"
        )
        
        # 默认参数
        self.default_params = {
            "fast_period": 12,       # 快速EMA周期
            "slow_period": 26,       # 慢速EMA周期
            "signal_period": 9,      # 信号线周期
            "histogram_threshold": 0, # 柱状图阈值
            "position_size": 0.1,    # 仓位大小
            "stop_loss": 0.05,       # 止损比例
            "take_profit": 0.10      # 止盈比例
        }
    
    def _on_initialize(self):
        """策略初始化逻辑"""
        logger.info(f"MACD策略初始化，参数: {self.parameters}")
        
        # 确保所有必要参数都有值
        for key, default_value in self.default_params.items():
            if key not in self.parameters:
                self.parameters[key] = default_value
        
        logger.info("MACD策略初始化完成")
    
    def _calculate_macd(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        计算MACD
        
        Args:
            data: 价格数据
            
        Returns:
            MACD字典
        """
        close_prices = data["close"]
        fast_period = self.parameters["fast_period"]
        slow_period = self.parameters["slow_period"]
        signal_period = self.parameters["signal_period"]
        
        # 计算EMA
        fast_ema = close_prices.ewm(span=fast_period, adjust=False).mean()
        slow_ema = close_prices.ewm(span=slow_period, adjust=False).mean()
        
        # 计算DIF
        dif = fast_ema - slow_ema
        
        # 计算DEA
        dea = dif.ewm(span=signal_period, adjust=False).mean()
        
        # 计算MACD柱
        macd_histogram = dif - dea
        
        return {
            "dif": dif,
            "dea": dea,
            "macd_histogram": macd_histogram
        }
    
    async def analyze_market(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        分析市场数据
        
        Args:
            data: 市场数据
            
        Returns:
            市场分析结果
        """
        logger.info("开始MACD市场分析...")
        
        # 计算MACD
        macd_data = self._calculate_macd(data)
        
        current_price = data["close"].iloc[-1]
        dif = macd_data["dif"].iloc[-1]
        dea = macd_data["dea"].iloc[-1]
        histogram = macd_data["macd_histogram"].iloc[-1]
        
        # 判断MACD状态
        if pd.isna(dif) or pd.isna(dea):
            macd_status = "unknown"
            crossover = "none"
        else:
            # 判断金叉死叉
            if dif > dea and macd_data["dif"].iloc[-2] <= macd_data["dea"].iloc[-2]:
                macd_status = "golden_cross"
                crossover = "golden"
            elif dif < dea and macd_data["dif"].iloc[-2] >= macd_data["dea"].iloc[-2]:
                macd_status = "death_cross"
                crossover = "death"
            else:
                macd_status = "neutral"
                crossover = "none"
        
        # 判断趋势
        if pd.isna(histogram):
            trend = "unknown"
            trend_strength = 0.0
        elif histogram > 0:
            trend = "bullish"
            trend_strength = min(abs(histogram) / 10, 1.0)
        else:
            trend = "bearish"
            trend_strength = min(abs(histogram) / 10, 1.0)
        
        analysis_result = {
            "current_price": float(current_price),
            "dif": float(dif) if not pd.isna(dif) else None,
            "dea": float(dea) if not pd.isna(dea) else None,
            "macd_histogram": float(histogram) if not pd.isna(histogram) else None,
            "macd_status": macd_status,
            "crossover": crossover,
            "trend": trend,
            "trend_strength": float(trend_strength),
            "analysis_time": datetime.now().isoformat(),
            "data_points": len(data)
        }
        
        logger.info(f"MACD分析完成，状态: {macd_status}, 趋势: {trend}")
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
        
        macd_status = analysis_result.get("macd_status")
        current_price = analysis_result.get("current_price")
        histogram = analysis_result.get("macd_histogram")
        
        if macd_status == "unknown" or current_price <= 0:
            return signals
        
        position_size = self.parameters["position_size"]
        histogram_threshold = self.parameters["histogram_threshold"]
        
        # 生成信号
        if macd_status == "golden_cross" and histogram is not None and histogram > histogram_threshold:
            signal = {
                "timestamp": datetime.now().isoformat(),
                "symbol": "EXAMPLE",
                "action": "BUY",
                "price": current_price,
                "quantity": position_size,
                "reason": f"MACD金叉，柱状图: {histogram:.4f}",
                "confidence": min(abs(histogram) * 10, 0.95),
                "strategy": self.name,
                "parameters": {
                    "fast_period": self.parameters["fast_period"],
                    "slow_period": self.parameters["slow_period"],
                    "signal_period": self.parameters["signal_period"],
                    "histogram": histogram
                },
                "risk_metrics": {
                    "stop_loss": current_price * (1 - self.parameters["stop_loss"]),
                    "take_profit": current_price * (1 + self.parameters["take_profit"])
                }
            }
            signals.append(signal)
            
        elif macd_status == "death_cross" and histogram is not None and histogram < -histogram_threshold:
            signal = {
                "timestamp": datetime.now().isoformat(),
                "symbol": "EXAMPLE",
                "action": "SELL",
                "price": current_price,
                "quantity": position_size,
                "reason": f"MACD死叉，柱状图: {histogram:.4f}",
                "confidence": min(abs(histogram) * 10, 0.95),
                "strategy": self.name,
                "parameters": {
                    "fast_period": self.parameters["fast_period"],
                    "slow_period": self.parameters["slow_period"],
                    "signal_period": self.parameters["signal_period"],
                    "histogram": histogram
                },
                "risk_metrics": {
                    "stop_loss": current_price * (1 + self.parameters["stop_loss"]),
                    "take_profit": current_price * (1 - self.parameters["take_profit"])
                }
            }
            signals.append(signal)
        
        logger.info(f"生成 {len(signals)} 个MACD交易信号")
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
        
        # 总风险计算
        total_risk = position_risk * 0.4 + 0.2 * 0.4 + (1 - signal_quality) * 0.2
        
        risk_metrics = {
            "total_risk": float(total_risk),
            "position_risk": float(position_risk),
            "market_risk": 0.2,
            "signal_quality": float(signal_quality),
            "avg_confidence": float(avg_confidence),
            "total_position": float(total_position)
        }
        
        return risk_metrics

# 注册策略到工厂
from .ai_strategy_base import StrategyFactory
StrategyFactory.register_strategy("macd", MACDStrategy)
