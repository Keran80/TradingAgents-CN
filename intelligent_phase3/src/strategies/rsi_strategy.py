#!/usr/bin/env python3
"""
RSI策略
基于相对强弱指数的交易策略
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime

from .ai_strategy_base import AIStrategyBase

logger = logging.getLogger(__name__)

class RSIStrategy(AIStrategyBase):
    """
    RSI策略
    
    基于相对强弱指数(RSI)生成交易信号。
    RSI低于30为超卖(买入信号)，高于70为超买(卖出信号)。
    """
    
    def __init__(self):
        """初始化RSI策略"""
        super().__init__(
            name="RSI策略",
            version="1.0.0"
        )
        
        # 默认参数
        self.default_params = {
            "rsi_period": 14,          # RSI计算周期
            "oversold_threshold": 30,   # 超卖阈值
            "overbought_threshold": 70, # 超买阈值
            "position_size": 0.1,       # 仓位大小
            "stop_loss": 0.05,          # 止损比例
            "take_profit": 0.10,        # 止盈比例
            "enable_divergence": True   # 启用背离检测
        }
    
    def _on_initialize(self):
        """策略初始化逻辑"""
        logger.info(f"RSI策略初始化，参数: {self.parameters}")
        
        # 确保所有必要参数都有值
        for key, default_value in self.default_params.items():
            if key not in self.parameters:
                self.parameters[key] = default_value
        
        logger.info("RSI策略初始化完成")
    
    def _calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """
        计算RSI
        
        Args:
            data: 价格数据
            
        Returns:
            RSI序列
        """
        close_prices = data["close"]
        period = self.parameters["rsi_period"]
        
        # 计算价格变化
        delta = close_prices.diff()
        
        # 分离上涨和下跌
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # 计算RS
        rs = gain / loss
        
        # 计算RSI
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    async def analyze_market(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        分析市场数据
        
        Args:
            data: 市场数据
            
        Returns:
            市场分析结果
        """
        logger.info("开始RSI市场分析...")
        
        # 计算RSI
        rsi_series = self._calculate_rsi(data)
        current_rsi = rsi_series.iloc[-1] if not rsi_series.empty else None
        
        # 判断市场状态
        if pd.isna(current_rsi):
            rsi_status = "unknown"
        elif current_rsi < self.parameters["oversold_threshold"]:
            rsi_status = "oversold"
        elif current_rsi > self.parameters["overbought_threshold"]:
            rsi_status = "overbought"
        else:
            rsi_status = "neutral"
        
        # 计算RSI趋势
        rsi_trend = "unknown"
        if len(rsi_series) >= 3:
            recent_rsi = rsi_series.iloc[-3:]
            if recent_rsi.is_monotonic_increasing:
                rsi_trend = "rising"
            elif recent_rsi.is_monotonic_decreasing:
                rsi_trend = "falling"
            else:
                rsi_trend = "oscillating"
        
        analysis_result = {
            "current_price": float(data["close"].iloc[-1]),
            "current_rsi": float(current_rsi) if not pd.isna(current_rsi) else None,
            "rsi_status": rsi_status,
            "rsi_trend": rsi_trend,
            "oversold_threshold": self.parameters["oversold_threshold"],
            "overbought_threshold": self.parameters["overbought_threshold"],
            "analysis_time": datetime.now().isoformat(),
            "data_points": len(data)
        }
        
        logger.info(f"RSI分析完成，状态: {rsi_status}, 趋势: {rsi_trend}")
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
        
        current_rsi = analysis_result.get("current_rsi")
        rsi_status = analysis_result.get("rsi_status")
        current_price = analysis_result.get("current_price")
        
        if current_rsi is None or current_price <= 0:
            return signals
        
        position_size = self.parameters["position_size"]
        
        # 生成信号
        if rsi_status == "oversold":
            signal = {
                "timestamp": datetime.now().isoformat(),
                "symbol": "EXAMPLE",
                "action": "BUY",
                "price": current_price,
                "quantity": position_size,
                "reason": f"RSI超卖: {current_rsi:.1f} < {self.parameters['oversold_threshold']}",
                "confidence": min((self.parameters['oversold_threshold'] - current_rsi) / 30, 0.95),
                "strategy": self.name,
                "parameters": {
                    "rsi_period": self.parameters["rsi_period"],
                    "current_rsi": current_rsi
                },
                "risk_metrics": {
                    "stop_loss": current_price * (1 - self.parameters["stop_loss"]),
                    "take_profit": current_price * (1 + self.parameters["take_profit"])
                }
            }
            signals.append(signal)
            
        elif rsi_status == "overbought":
            signal = {
                "timestamp": datetime.now().isoformat(),
                "symbol": "EXAMPLE",
                "action": "SELL",
                "price": current_price,
                "quantity": position_size,
                "reason": f"RSI超买: {current_rsi:.1f} > {self.parameters['overbought_threshold']}",
                "confidence": min((current_rsi - self.parameters['overbought_threshold']) / 30, 0.95),
                "strategy": self.name,
                "parameters": {
                    "rsi_period": self.parameters["rsi_period"],
                    "current_rsi": current_rsi
                },
                "risk_metrics": {
                    "stop_loss": current_price * (1 + self.parameters["stop_loss"]),
                    "take_profit": current_price * (1 - self.parameters["take_profit"])
                }
            }
            signals.append(signal)
        
        logger.info(f"生成 {len(signals)} 个RSI交易信号")
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
                "market_risk": 0.2,  # 默认市场风险
                "signal_quality": 0.0
            }
        
        # 计算信号质量 (基于置信度)
        avg_confidence = np.mean([signal.get("confidence", 0) for signal in signals])
        signal_quality = avg_confidence
        
        # 计算仓位风险
        total_position = sum(signal.get("quantity", 0) for signal in signals)
        position_risk = min(total_position / 0.3, 1.0)  # 最大仓位30%
        
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
StrategyFactory.register_strategy("rsi", RSIStrategy)
