#!/usr/bin/env python3
"""
移动平均线交叉策略
智能阶段3 - 具体AI策略实现
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .ai_strategy_base import AIStrategyBase

logger = logging.getLogger(__name__)

class MACrossoverStrategy(AIStrategyBase):
    """
    移动平均线交叉策略
    
    基于快速移动平均线和慢速移动平均线的交叉生成交易信号。
    """
    
    def __init__(self):
        """初始化移动平均线交叉策略"""
        super().__init__(
            name="移动平均线交叉策略",
            version="2.0.0"
        )
        
        # 默认参数
        self.default_params = {
            "fast_period": 10,      # 快速移动平均线周期
            "slow_period": 30,      # 慢速移动平均线周期
            "signal_threshold": 0.02,  # 信号阈值
            "position_size": 0.1,   # 仓位大小 (10%)
            "stop_loss": 0.05,      # 止损比例 (5%)
            "take_profit": 0.10,    # 止盈比例 (10%)
            "max_position": 0.3,    # 最大仓位 (30%)
            "enable_ai_optimization": True  # 启用AI优化
        }
    
    def _on_initialize(self):
        """策略初始化逻辑"""
        logger.info(f"移动平均线交叉策略初始化，参数: {self.parameters}")
        
        # 确保所有必要参数都有值
        for key, default_value in self.default_params.items():
            if key not in self.parameters:
                self.parameters[key] = default_value
        
        # 初始化内部状态
        self.previous_fast_ma = None
        self.previous_slow_ma = None
        self.signal_history = []
        self.performance_history = []
        
        logger.info("移动平均线交叉策略初始化完成")
    
    def _calculate_moving_averages(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        计算移动平均线
        
        Args:
            data: 价格数据
            
        Returns:
            移动平均线字典
        """
        close_prices = data["close"]
        
        fast_period = self.parameters["fast_period"]
        slow_period = self.parameters["slow_period"]
        
        # 计算移动平均线
        fast_ma = close_prices.rolling(window=fast_period).mean()
        slow_ma = close_prices.rolling(window=slow_period).mean()
        
        # 计算移动平均线差值
        ma_diff = fast_ma - slow_ma
        ma_diff_pct = ma_diff / slow_ma * 100
        
        return {
            "fast_ma": fast_ma,
            "slow_ma": slow_ma,
            "ma_diff": ma_diff,
            "ma_diff_pct": ma_diff_pct
        }
    
    def _detect_crossover(self, fast_ma: pd.Series, slow_ma: pd.Series) -> pd.Series:
        """
        检测移动平均线交叉
        
        Args:
            fast_ma: 快速移动平均线
            slow_ma: 慢速移动平均线
            
        Returns:
            交叉信号序列 (1: 金叉, -1: 死叉, 0: 无交叉)
        """
        # 计算交叉信号
        crossover_signal = pd.Series(0, index=fast_ma.index)
        
        # 金叉: 快速线上穿慢速线
        golden_cross = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))
        
        # 死叉: 快速线下穿慢速线
        death_cross = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))
        
        crossover_signal[golden_cross] = 1
        crossover_signal[death_cross] = -1
        
        return crossover_signal
    
    async def analyze_market(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        分析市场数据
        
        Args:
            data: 市场数据
            
        Returns:
            市场分析结果
        """
        logger.info("开始市场分析...")
        
        # 计算移动平均线
        ma_results = self._calculate_moving_averages(data)
        
        # 检测交叉信号
        crossover_signal = self._detect_crossover(
            ma_results["fast_ma"], 
            ma_results["slow_ma"]
        )
        
        # 计算技术指标
        current_price = data["close"].iloc[-1]
        fast_ma_current = ma_results["fast_ma"].iloc[-1]
        slow_ma_current = ma_results["slow_ma"].iloc[-1]
        ma_diff_pct_current = ma_results["ma_diff_pct"].iloc[-1]
        
        # 判断当前趋势
        if pd.isna(fast_ma_current) or pd.isna(slow_ma_current):
            trend = "unknown"
            trend_strength = 0.0
        else:
            if fast_ma_current > slow_ma_current:
                trend = "bullish"
                trend_strength = abs(ma_diff_pct_current) / 100.0
            else:
                trend = "bearish"
                trend_strength = abs(ma_diff_pct_current) / 100.0
        
        # 计算波动率
        volatility = data["close"].pct_change().std() * np.sqrt(252)  # 年化波动率
        
        # 如果有AI优化，可以在这里添加AI分析
        ai_insight = None
        if self.parameters.get("enable_ai_optimization", False):
            ai_insight = await self._ai_analyze_trend(data, ma_results)
        
        analysis_result = {
            "current_price": float(current_price),
            "fast_ma": float(fast_ma_current) if not pd.isna(fast_ma_current) else None,
            "slow_ma": float(slow_ma_current) if not pd.isna(slow_ma_current) else None,
            "ma_diff_pct": float(ma_diff_pct_current) if not pd.isna(ma_diff_pct_current) else None,
            "trend": trend,
            "trend_strength": float(trend_strength),
            "volatility": float(volatility) if not pd.isna(volatility) else 0.0,
            "crossover_signals": crossover_signal.tolist(),
            "signal_count": int(crossover_signal.abs().sum()),
            "ai_insight": ai_insight,
            "analysis_time": datetime.now().isoformat(),
            "data_points": len(data)
        }
        
        # 记录性能
        self.record_performance("last_analysis_time", datetime.now().timestamp())
        self.record_performance("analysis_data_points", len(data))
        
        logger.info(f"市场分析完成，趋势: {trend}, 强度: {trend_strength:.2%}")
        return analysis_result
    
    async def _ai_analyze_trend(self, data: pd.DataFrame, ma_results: Dict) -> Optional[Dict]:
        """
        AI分析趋势 (占位函数，实际项目中可以集成真正的AI模型)
        
        Args:
            data: 市场数据
            ma_results: 移动平均线结果
            
        Returns:
            AI分析结果
        """
        # 这里可以集成真正的AI模型
        # 例如: 使用机器学习模型预测趋势
        
        # 简单的规则引擎示例
        fast_ma = ma_results["fast_ma"]
        slow_ma = ma_results["slow_ma"]
        ma_diff_pct = ma_results["ma_diff_pct"]
        
        if len(fast_ma) < 2 or len(slow_ma) < 2:
            return None
        
        current_diff = ma_diff_pct.iloc[-1]
        previous_diff = ma_diff_pct.iloc[-2] if len(ma_diff_pct) > 1 else 0
        
        if pd.isna(current_diff) or pd.isna(previous_diff):
            return None
        
        # 简单的趋势分析
        trend_change = current_diff - previous_diff
        trend_acceleration = "accelerating" if abs(trend_change) > 0.1 else "stable"
        
        # 置信度计算
        confidence = min(abs(current_diff) / 10.0, 1.0)  # 简单的置信度计算
        
        return {
            "trend_change": float(trend_change),
            "trend_acceleration": trend_acceleration,
            "confidence": float(confidence),
            "ai_model": "rule_based_v1",
            "recommendation": "buy" if current_diff > 0.5 else "sell" if current_diff < -0.5 else "hold"
        }
    
    async def generate_signals(self, analysis_result: Dict[str, Any]) -> List[Dict]:
        """
        生成交易信号
        
        Args:
            analysis_result: 市场分析结果
            
        Returns:
            交易信号列表
        """
        signals = []
        
        # 获取分析结果
        trend = analysis_result.get("trend", "unknown")
        trend_strength = analysis_result.get("trend_strength", 0.0)
        ma_diff_pct = analysis_result.get("ma_diff_pct", 0.0)
        crossover_signals = analysis_result.get("crossover_signals", [])
        current_price = analysis_result.get("current_price", 0.0)
        
        if not crossover_signals or current_price <= 0:
            return signals
        
        # 获取最近的交叉信号
        recent_signals = crossover_signals[-5:]  # 最近5个信号
        latest_signal = recent_signals[-1] if recent_signals else 0
        
        # 生成信号
        signal_threshold = self.parameters["signal_threshold"]
        position_size = self.parameters["position_size"]
        
        if latest_signal == 1 and abs(ma_diff_pct) > signal_threshold:  # 金叉
            signal = {
                "timestamp": datetime.now().isoformat(),
                "symbol": "EXAMPLE",  # 实际使用时替换为具体标的
                "action": "BUY",
                "price": current_price,
                "quantity": position_size,  # 仓位比例
                "reason": f"移动平均线金叉，快速线在慢速线之上 {ma_diff_pct:.2%}",
                "confidence": min(trend_strength * 2, 0.95),  # 置信度计算
                "strategy": self.name,
                "parameters": {
                    "fast_period": self.parameters["fast_period"],
                    "slow_period": self.parameters["slow_period"],
                    "ma_diff_pct": ma_diff_pct
                },
                "risk_metrics": {
                    "stop_loss": current_price * (1 - self.parameters["stop_loss"]),
                    "take_profit": current_price * (1 + self.parameters["take_profit"])
                }
            }
            signals.append(signal)
            
        elif latest_signal == -1 and abs(ma_diff_pct) > signal_threshold:  # 死叉
            signal = {
                "timestamp": datetime.now().isoformat(),
                "symbol": "EXAMPLE",
                "action": "SELL",
                "price": current_price,
                "quantity": position_size,
                "reason": f"移动平均线死叉，快速线在慢速线之下 {ma_diff_pct:.2%}",
                "confidence": min(trend_strength * 2, 0.95),
                "strategy": self.name,
                "parameters": {
                    "fast_period": self.parameters["fast_period"],
                    "slow_period": self.parameters["slow_period"],
                    "ma_diff_pct": ma_diff_pct
                },
                "risk_metrics": {
                    "stop_loss": current_price * (1 + self.parameters["stop_loss"]),
                    "take_profit": current_price * (1 - self.parameters["take_profit"])
                }
            }
            signals.append(signal)
        
        # 记录信号历史
        for signal in signals:
            self.signal_history.append({
                "time": signal["timestamp"],
                "action": signal["action"],
                "price": signal["price"],
                "confidence": signal["confidence"]
            })
        
        # 限制历史记录长度
        if len(self.signal_history) > 100:
            self.signal_history = self.signal_history[-100:]
        
        logger.info(f"生成 {len(signals)} 个交易信号")
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
                "market_risk": 0.0,
                "signal_quality": 0.0
            }
        
        # 计算总仓位风险
        total_position = sum(signal.get("quantity", 0) for signal in signals)
        position_risk = min(total_position / self.parameters["max_position"], 1.0)
        
        # 计算信号质量 (基于置信度)
        avg_confidence = np.mean([signal.get("confidence", 0) for signal in signals])
        signal_quality = avg_confidence
        
        # 计算市场风险 (简化)
        market_risk = 0.2  # 默认20%市场风险，实际应该基于波动率计算
        
        # 总风险计算
        total_risk = position_risk * 0.4 + market_risk * 0.4 + (1 - signal_quality) * 0.2
        
        risk_metrics = {
            "total_risk": float(total_risk),
            "position_risk": float(position_risk),
            "market_risk": float(market_risk),
            "signal_quality": float(signal_quality),
            "avg_confidence": float(avg_confidence),
            "total_position": float(total_position),
            "max_allowed_position": float(self.parameters["max_position"])
        }
        
        # 记录风险指标
        self.record_performance("last_risk_assessment", total_risk)
        self.record_performance("avg_signal_confidence", avg_confidence)
        
        return risk_metrics
    
    def _on_parameters_updated(self, old_params: Dict, new_params: Dict):
        """参数更新处理"""
        changed_params = {}
        for key, new_value in new_params.items():
            old_value = old_params.get(key)
            if old_value != new_value:
                changed_params[key] = {"old": old_value, "new": new_value}
        
        if changed_params:
            logger.info(f"策略参数更新: {changed_params}")
            
            # 如果移动平均线周期改变，重置状态
            if "fast_period" in changed_params or "slow_period" in changed_params:
                self.previous_fast_ma = None
                self.previous_slow_ma = None
                logger.info("移动平均线周期更新，重置计算状态")

# 注册策略到工厂
from .ai_strategy_base import StrategyFactory
StrategyFactory.register_strategy("ma_crossover", MACrossoverStrategy)

# 使用示例
async def example_usage():
    """使用示例"""
    print("移动平均线交叉策略示例")
    
    # 创建策略实例
    strategy = MACrossoverStrategy()
    
    # 初始化策略
    strategy.initialize(
        fast_period=10,
        slow_period=30,
        signal_threshold=0.02
    )
    
    # 创建示例数据
    dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
    data = pd.DataFrame({
        "open": np.random.randn(len(dates)) * 10 + 100,
        "high": np.random.randn(len(dates)) * 10 + 105,
        "low": np.random.randn(len(dates)) * 10 + 95,
        "close": np.random.randn(len(dates)) * 10 + 100,
        "volume": np.random.randint(1000, 10000, len(dates))
    }, index=dates)
    
    # 执行完整分析
    result = await strategy.execute_full_analysis(data)
    
    if result.get("success"):
        print(f"分析成功，生成 {len(result['signals'])} 个信号")
        print(f"趋势: {result['analysis_result']['trend']}")
        print(f"趋势强度: {result['analysis_result']['trend_strength']:.2%}")
        print(f"总风险: {result['risk_metrics']['total_risk']:.2%}")
    else:
        print(f"分析失败: {result.get('error')}")
    
    # 获取性能报告
    report = strategy.get_performance_report()
    print(f"\n性能报告:")
    print(f"  策略名称: {report['strategy_name']}")
    print(f"  分析次数: {report['performance_metrics'].get('analysis_count', 0)}")
    print(f"  信号数量: {report['performance_metrics'].get('signal_count', 0)}")

if __name__ == "__main__":
    asyncio.run(example_usage())
