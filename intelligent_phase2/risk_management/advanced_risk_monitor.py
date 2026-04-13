#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级风险监控器
监控投资组合风险，提供风险预警和建议
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """风险等级"""
    LOW = "低风险"
    MEDIUM = "中风险"
    HIGH = "高风险"
    CRITICAL = "极高风险"

@dataclass
class RiskMetric:
    """风险指标"""
    name: str
    value: float
    threshold: float
    severity: RiskLevel
    description: str = ""
    
    @property
    def is_breached(self) -> bool:
        """是否突破阈值"""
        return abs(self.value) > self.threshold

@dataclass
class PortfolioRisk:
    """投资组合风险"""
    portfolio_id: str
    overall_risk: RiskLevel
    metrics: List[RiskMetric]
    recommendations: List[str]
    assessment_time: datetime
    confidence: float = 0.0

class AdvancedRiskMonitor:
    """高级风险监控器"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            "var_confidence": 0.95,
            "max_drawdown_threshold": 0.20,
            "concentration_threshold": 0.30,
            "leverage_threshold": 2.0,
            "volatility_threshold": 0.30
        }
        
    def calculate_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """计算在险价值 (Value at Risk)"""
        if len(returns) < 30:
            logger.warning("数据不足，无法计算VaR")
            return 0.0
        
        # 历史模拟法
        var_historical = -np.percentile(returns, (1 - confidence) * 100)
        
        # 参数法（假设正态分布）
        mean = returns.mean()
        std = returns.std()
        var_param = -(mean + std * np.percentile(np.random.randn(10000), (1 - confidence) * 100))
        
        # 使用两者中较保守的值
        var = max(var_historical, var_param)
        
        return var
    
    def calculate_max_drawdown(self, prices: pd.Series) -> Tuple[float, pd.Timestamp, pd.Timestamp]:
        """计算最大回撤"""
        if len(prices) < 10:
            return 0.0, None, None
        
        # 计算累积最大值
        cumulative_max = prices.expanding().max()
        
        # 计算回撤
        drawdown = (prices - cumulative_max) / cumulative_max
        
        # 最大回撤
        max_dd = drawdown.min()
        max_dd_idx = drawdown.idxmin()
        
        # 找到回撤开始点（累积最大值对应的点）
        peak_idx = cumulative_max[cumulative_max.index <= max_dd_idx].idxmax()
        
        return max_dd, peak_idx, max_dd_idx
    
    def calculate_concentration(self, weights: Dict[str, float]) -> float:
        """计算集中度风险（赫芬达尔指数）"""
        if not weights:
            return 0.0
        
        # 赫芬达尔-赫希曼指数 (HHI)
        hhi = sum(w ** 2 for w in weights.values())
        
        # 归一化到0-1
        n = len(weights)
        normalized_hhi = (hhi - 1/n) / (1 - 1/n) if n > 1 else 1.0
        
        return normalized_hhi
    
    def calculate_leverage_risk(self, portfolio_value: float, borrowed_amount: float) -> float:
        """计算杠杆风险"""
        if portfolio_value <= 0:
            return 0.0
        
        leverage_ratio = borrowed_amount / portfolio_value
        return leverage_ratio
    
    def calculate_volatility(self, returns: pd.Series) -> float:
        """计算波动率"""
        if len(returns) < 20:
            return 0.0
        
        annual_volatility = returns.std() * np.sqrt(252)
        return annual_volatility
    
    async def assess_single_position(self, position_data: Dict[str, Any]) -> List[RiskMetric]:
        """评估单个头寸风险"""
        metrics = []
        
        try:
            # 提取数据
            symbol = position_data.get("symbol", "")
            returns = position_data.get("returns", pd.Series(dtype=float))
            prices = position_data.get("prices", pd.Series(dtype=float))
            weight = position_data.get("weight", 0.0)
            
            # 1. 在险价值 (VaR)
            var = self.calculate_var(returns, self.config["var_confidence"])
            var_metric = RiskMetric(
                name="在险价值(VaR-95%)",
                value=var,
                threshold=0.05,  # 5% VaR阈值
                severity=RiskLevel.HIGH if var > 0.05 else RiskLevel.MEDIUM,
                description=f"{symbol} 95%置信度下的最大可能损失"
            )
            metrics.append(var_metric)
            
            # 2. 最大回撤
            if len(prices) > 10:
                max_dd, peak, trough = self.calculate_max_drawdown(prices)
                max_dd_metric = RiskMetric(
                    name="最大回撤",
                    value=abs(max_dd),
                    threshold=self.config["max_drawdown_threshold"],
                    severity=RiskLevel.CRITICAL if abs(max_dd) > 0.30 else 
                            RiskLevel.HIGH if abs(max_dd) > 0.20 else
                            RiskLevel.MEDIUM,
                    description=f"{symbol} 历史最大回撤 {abs(max_dd):.2%}"
                )
                metrics.append(max_dd_metric)
            
            # 3. 波动率风险
            volatility = self.calculate_volatility(returns)
            if volatility > 0:
                vol_metric = RiskMetric(
                    name="年化波动率",
                    value=volatility,
                    threshold=self.config["volatility_threshold"],
                    severity=RiskLevel.HIGH if volatility > 0.40 else
                            RiskLevel.MEDIUM if volatility > 0.30 else
                            RiskLevel.LOW,
                    description=f"{symbol} 年化波动率 {volatility:.2%}"
                )
                metrics.append(vol_metric)
            
            # 4. 权重风险（如果权重过高）
            if weight > 0.20:  # 单个头寸超过20%
                weight_metric = RiskMetric(
                    name="头寸集中度",
                    value=weight,
                    threshold=0.20,
                    severity=RiskLevel.HIGH if weight > 0.30 else RiskLevel.MEDIUM,
                    description=f"{symbol} 权重 {weight:.2%} 可能过高"
                )
                metrics.append(weight_metric)
                
        except Exception as e:
            logger.error(f"❌ 评估头寸风险失败: {e}")
        
        return metrics
    
    def generate_recommendations(self, metrics: List[RiskMetric]) -> List[str]:
        """生成风险建议"""
        recommendations = []
        
        # 根据具体风险指标添加建议
        for metric in metrics:
            if metric.severity in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                if metric.name == "最大回撤":
                    recommendations.append(f"📉 {metric.name} 过高 ({metric.value:.2%})，建议设置止损")
                elif metric.name == "在险价值(VaR-95%)":
                    recommendations.append(f"💰 {metric.name} 突破阈值 ({metric.value:.2%})，减少风险敞口")
                elif metric.name == "集中度风险":
                    recommendations.append(f"🎯 {metric.name} 过高 ({metric.value:.2%})，分散投资")
                elif metric.name == "杠杆风险":
                    recommendations.append(f"⚖️  {metric.name} 过高 ({metric.value:.2f})，降低杠杆")
        
        # 去重
        recommendations = list(dict.fromkeys(recommendations))
        
        return recommendations[:5]  # 只返回前5条建议
    
    async def assess_portfolio_risk(self, portfolio_data: Dict[str, Any]) -> PortfolioRisk:
        """
        评估投资组合风险
        """
        assessment_time = datetime.now()
        
        try:
            portfolio_id = portfolio_data.get("portfolio_id", "default")
            positions = portfolio_data.get("positions", [])
            total_value = portfolio_data.get("total_value", 0.0)
            borrowed_amount = portfolio_data.get("borrowed_amount", 0.0)
            
            all_metrics = []
            
            # 评估每个头寸
            for position in positions:
                position_metrics = await self.assess_single_position(position)
                all_metrics.extend(position_metrics)
            
            # 计算组合级风险指标
            portfolio_metrics = []
            
            # 1. 组合集中度风险
            weights = {pos.get("symbol", f"pos_{i}"): pos.get("weight", 0.0) 
                      for i, pos in enumerate(positions)}
            concentration = self.calculate_concentration(weights)
            concentration_metric = RiskMetric(
                name="集中度风险",
                value=concentration,
                threshold=self.config["concentration_threshold"],
                severity=RiskLevel.HIGH if concentration > 0.40 else
                        RiskLevel.MEDIUM if concentration > 0.30 else
                        RiskLevel.LOW,
                description=f"投资组合集中度指数 {concentration:.2%}"
            )
            portfolio_metrics.append(concentration_metric)
            
            # 2. 杠杆风险
            leverage_ratio = self.calculate_leverage_risk(total_value, borrowed_amount)
            leverage_metric = RiskMetric(
                name="杠杆风险",
                value=leverage_ratio,
                threshold=self.config["leverage_threshold"],
                severity=RiskLevel.CRITICAL if leverage_ratio > 3.0 else
                        RiskLevel.HIGH if leverage_ratio > 2.0 else
                        RiskLevel.MEDIUM if leverage_ratio > 1.0 else
                        RiskLevel.LOW,
                description=f"杠杆比率 {leverage_ratio:.2f}"
            )
            portfolio_metrics.append(leverage_metric)
            
            # 合并所有指标
            all_metrics.extend(portfolio_metrics)
            
            # 确定总体风险等级
            severity_scores = {
                RiskLevel.CRITICAL: 4,
                RiskLevel.HIGH: 3,
                RiskLevel.MEDIUM: 2,
                RiskLevel.LOW: 1
            }
            
            if not all_metrics:
                overall_risk = RiskLevel.LOW
            else:
                avg_score = sum(severity_scores[m.severity] for m in all_metrics) / len(all_metrics)
                if avg_score >= 3.5:
                    overall_risk = RiskLevel.CRITICAL
                elif avg_score >= 2.5:
                    overall_risk = RiskLevel.HIGH
                elif avg_score >= 1.5:
                    overall_risk = RiskLevel.MEDIUM
                else:
                    overall_risk = RiskLevel.LOW
            
            # 生成建议
            recommendations = self.generate_recommendations(all_metrics)
            
            # 计算置信度（基于数据质量）
            confidence = min(0.9, len(positions) / 10) if positions else 0.5
            
            return PortfolioRisk(
                portfolio_id=portfolio_id,
                overall_risk=overall_risk,
                metrics=all_metrics,
                recommendations=recommendations,
                assessment_time=assessment_time,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"❌ 评估投资组合风险失败: {e}")
            return PortfolioRisk(
                portfolio_id="error",
                overall_risk=RiskLevel.HIGH,
                metrics=[],
                recommendations=["风险评估失败，请检查数据"],
                assessment_time=assessment_time,
                confidence=0.0
            )
    
    async def monitor_realtime(self, portfolio_data: Dict[str, Any], interval_seconds: int = 60):
        """实时监控（模拟）"""
        logger.info(f"开始实时风险监控，间隔: {interval_seconds}秒")
        
        try:
            while True:
                risk_assessment = await self.assess_portfolio_risk(portfolio_data)
                
                # 如果有高风险，发出警告
                if risk_assessment.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    logger.warning(f"⚠️ 高风险警报: {risk_assessment.portfolio_id}")
                    for rec in risk_assessment.recommendations:
                        logger.warning(f"  建议: {rec}")
                
                await asyncio.sleep(interval_seconds)
                
        except asyncio.CancelledError:
            logger.info("实时监控已停止")
        except Exception as e:
            logger.error(f"❌ 实时监控失败: {e}")

# 示例使用
async def example_usage():
    """示例用法"""
    print("🚀 高级风险监控器示例")
    print("=" * 50)
    
    # 创建风险监控器
    monitor = AdvancedRiskMonitor()
    
    # 创建模拟投资组合数据
    np.random.seed(42)
    
    # 生成模拟价格数据
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    prices_stock_a = 100 * (1 + np.random.randn(100).cumsum() / 100)
    prices_stock_b = 50 * (1 + np.random.randn(100).cumsum() / 80)
    
    # 计算收益率
    returns_stock_a = pd.Series(np.diff(prices_stock_a) / prices_stock_a[:-1], index=dates[1:])
    returns_stock_b = pd.Series(np.diff(prices_stock_b) / prices_stock_b[:-1], index=dates[1:])
    
    portfolio_data = {
        "portfolio_id": "示例组合",
        "total_value": 1000000,
        "borrowed_amount": 200000,  # 20万借款
        "positions": [
            {
                "symbol": "STOCK_A",
                "weight": 0.40,  # 40%权重
                "prices": pd.Series(prices_stock_a, index=dates),
                "returns": returns_stock_a
            },
            {
                "symbol": "STOCK_B", 
                "weight": 0.60,  # 60%权重
                "prices": pd.Series(prices_stock_b, index=dates),
                "returns": returns_stock_b
            }
        ]
    }
    
    # 评估风险
    print("评估投资组合风险...")
    risk_assessment = await monitor.assess_portfolio_risk(portfolio_data)
    
    print(f"\n📊 风险评估结果:")
    print(f"投资组合: {risk_assessment.portfolio_id}")
    print(f"总体风险: {risk_assessment.overall_risk.value}")
    print(f"评估时间: {risk_assessment.assessment_time}")
    print(f"置信度: {risk_assessment.confidence:.2%}")
    
    print(f"\n📈 风险指标:")
    print("=" * 80)
    print(f"{'指标':<25} {'数值':<12} {'阈值':<12} {'风险等级':<12} {'描述':<30}")
    print("-" * 80)
    
    for metric in risk_assessment.metrics:
        print(f"{metric.name:<25} {metric.value:>11.2%} {metric.threshold:>11.2%} "
              f"{metric.severity.value:>12} {metric.description:<30}")
    
    print(f"\n💡 风险建议:")
    if risk_assessment.recommendations:
        for i, rec in enumerate(risk_assessment.recommendations, 1):
            print(f"{i}. {rec}")
    else:
        print("✅ 无高风险项目，投资组合风险可控")
    
    print("\n✅ 示例完成！")

if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())