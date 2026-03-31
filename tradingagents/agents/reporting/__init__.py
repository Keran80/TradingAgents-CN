"""
决策整合与报告生成
"""
import json
from typing import Dict, Any, Optional
from dataclasses import asdict
from datetime import datetime

from ..base import (
    AnalysisResult,
    DebateResult,
    RiskAssessment,
    TradingDecision,
    Decision
)


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        self.template = self._get_report_template()
    
    def _get_report_template(self) -> str:
        return """
# 投资分析报告

## 基本信息
- 股票代码：{stock_code}
- 股票名称：{stock_name}
- 分析日期：{date}
- 目标价：{target_price}
- 当前价：{current_price}

## 一、四维分析

### 1.1 技术面分析
{market_analysis}

### 1.2 基本面分析
{fundamentals_analysis}

### 1.3 新闻面分析
{news_analysis}

### 1.4 情绪面分析
{sentiment_analysis}

## 二、多空辩论

### 2.1 多头观点
{bull_analysis}

### 2.2 空头观点
{bear_analysis}

### 2.3 研究经理仲裁
- 决策：{manager_decision}
- Conviction Score：{conviction:.0%}

### 2.4 投资计划
{investment_plan}

## 三、风险评估

### 3.1 激进视角
{aggressive_risk}

### 3.2 保守视角
{conservative_risk}

### 3.3 中性视角
{neutral_risk}

### 3.4 风险管理建议
- 风险评分：{risk_score:.0%}
- 建议仓位：{recommended_position}
- 止损位：{stop_loss}
- 止盈位：{take_profit}

## 四、最终决策

### 4.1 交易决策
- 决策：{final_decision}
- 置信度：{confidence:.0%}

### 4.2 操作建议
{action_plan}

### 4.3 风险提示
{risk_warning}

---
报告生成时间：{timestamp}
本报告仅供参考，不构成投资建议
"""
    
    def generate(self, 
                 stock_code: str,
                 stock_name: str,
                 current_price: float,
                 analyst_report,
                 debate_result: DebateResult,
                 risk_assessment: RiskAssessment) -> str:
        """生成完整报告"""
        
        # 提取各部分内容
        market = analyst_report.market.content if analyst_report.market else "无"
        fundamentals = analyst_report.fundamentals.content if analyst_report.fundamentals else "无"
        news = analyst_report.news.content if analyst_report.news else "无"
        sentiment = analyst_report.sentiment.content if analyst_report.sentiment else "无"
        
        bull = debate_result.bull_result.content if debate_result.bull_result else "无"
        bear = debate_result.bear_result.content if debate_result.bear_result else "无"
        
        aggressive = risk_assessment.aggressive_result.content if risk_assessment.aggressive_result else "无"
        conservative = risk_assessment.conservative_result.content if risk_assessment.conservative_result else "无"
        neutral = risk_assessment.neutral_result.content if risk_assessment.neutral_result else "无"
        
        # 计算目标价和止损
        target_price = current_price * 1.15
        stop_loss = current_price * 0.93
        take_profit = current_price * 1.20
        
        # 决策
        decision = debate_result.manager_decision
        final_decision = self._format_decision(decision)
        
        # 填充模板
        report = self.template.format(
            stock_code=stock_code,
            stock_name=stock_name,
            date=datetime.now().strftime("%Y-%m-%d"),
            target_price=f"{target_price:.2f}",
            current_price=f"{current_price:.2f}",
            market_analysis=market[:500] + "..." if len(market) > 500 else market,
            fundamentals_analysis=fundamentals[:500] + "..." if len(fundamentals) > 500 else fundamentals,
            news_analysis=news[:500] + "..." if len(news) > 500 else news,
            sentiment_analysis=sentiment[:500] + "..." if len(sentiment) > 500 else sentiment,
            bull_analysis=bull[:500] + "..." if len(bull) > 500 else bull,
            bear_analysis=bear[:500] + "..." if len(bear) > 500 else bear,
            manager_decision=decision,
            conviction=debate_result.conviction_score,
            investment_plan=debate_result.investment_plan or "无",
            aggressive_risk=aggressive[:300] + "..." if len(aggressive) > 300 else aggressive,
            conservative_risk=conservative[:300] + "..." if len(conservative) > 300 else conservative,
            neutral_risk=neutral[:300] + "..." if len(neutral) > 300 else neutral,
            risk_score=risk_assessment.risk_score,
            recommended_position="20%",
            stop_loss=f"{stop_loss:.2f}",
            take_profit=f"{take_profit:.2f}",
            final_decision=final_decision,
            confidence=debate_result.conviction_score,
            action_plan=self._format_action(decision),
            risk_warning=self._format_risk_warning(risk_assessment.risk_score),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return report
    
    def _format_decision(self, decision: str) -> str:
        """格式化决策"""
        mapping = {
            "STRONG_BUY": "强烈买入",
            "BUY": "买入",
            "HOLD": "持有",
            "SELL": "卖出",
            "STRONG_SELL": "强烈卖出"
        }
        return mapping.get(decision, decision)
    
    def _format_action(self, decision: str) -> str:
        """格式化操作建议"""
        mapping = {
            "STRONG_BUY": """1. 首次建仓 30% 仓位
2. 股价回调至 5 日均线附近加仓 20%
3. 止损位设置在当前价格下方 7%
4. 目标价达到后分批止盈""",
            "BUY": """1. 首次建仓 20% 仓位
2. 突破前高后加仓 10%
3. 止损位设置在当前价格下方 8%
4. 目标价达到后分批止盈""",
            "HOLD": """1. 保持现有仓位不变
2. 等待更明确的方向信号
3. 关注关键技术位的突破情况
4. 如有持仓可设置保护性止损""",
            "SELL": """1. 建议减持 50% 仓位
2. 剩余仓位设置保护性止损
3. 等待更好的买入时机
4. 关注估值回归后的机会""",
            "STRONG_SELL": """1. 建议清仓全部持仓
2. 规避短期市场风险
3. 等待估值回归后再考虑介入
4. 可配置低风险资产"""
        }
        return mapping.get(decision, "暂无建议")
    
    def _format_risk_warning(self, risk_score: float) -> str:
        """格式化风险提示"""
        if risk_score < 0.3:
            return "风险较低，但仍需注意市场波动风险"
        elif risk_score < 0.6:
            return "中等风险，需关注仓位管理和止损纪律"
        else:
            return "风险较高，建议轻仓操作或观望"


class TradingDecisionMaker:
    """交易决策整合器"""
    
    def __init__(self):
        self.report_generator = ReportGenerator()
    
    def make_decision(self,
                      stock_code: str,
                      stock_name: str,
                      current_price: float,
                      analyst_report,
                      debate_result: DebateResult,
                      risk_assessment: RiskAssessment) -> Dict[str, Any]:
        """整合所有分析，生成最终决策"""
        
        # 生成报告
        report = self.report_generator.generate(
            stock_code=stock_code,
            stock_name=stock_name,
            current_price=current_price,
            analyst_report=analyst_report,
            debate_result=debate_result,
            risk_assessment=risk_assessment
        )
        
        # 生成交易决策
        decision_mapping = {
            "STRONG_BUY": Decision.STRONG_BUY,
            "BUY": Decision.BUY,
            "HOLD": Decision.HOLD,
            "SELL": Decision.SELL,
            "STRONG_SELL": Decision.STRONG_SELL
        }
        
        decision_enum = decision_mapping.get(
            debate_result.manager_decision, 
            Decision.HOLD
        )
        
        # 计算仓位
        position_size = self._calculate_position(risk_assessment.risk_score)
        
        # 计算目标价和止损
        if decision_enum in [Decision.BUY, Decision.STRONG_BUY]:
            target_price = current_price * 1.20
            stop_loss = current_price * (1 - 0.07)
        elif decision_enum in [Decision.SELL, Decision.STRONG_SELL]:
            target_price = current_price * 0.80
            stop_loss = current_price * 1.03
        else:
            target_price = current_price * 1.10
            stop_loss = current_price * 0.95
        
        trading_decision = TradingDecision(
            decision=decision_enum,
            rationale=self._generate_rationale(debate_result, risk_assessment),
            target_price=target_price,
            stop_loss=stop_loss,
            position_size=position_size,
            confidence=debate_result.conviction_score,
            risk_level=self._format_risk_level(risk_assessment.risk_score)
        )
        
        return {
            "report": report,
            "decision": trading_decision,
            "decision_dict": trading_decision.to_dict(),
            "risk_assessment": risk_assessment.to_dict(),
            "debate_result": debate_result.to_dict()
        }
    
    def _calculate_position(self, risk_score: float) -> float:
        """根据风险评分计算仓位"""
        if risk_score < 0.3:
            return 0.30
        elif risk_score < 0.5:
            return 0.20
        elif risk_score < 0.7:
            return 0.10
        else:
            return 0.05
    
    def _generate_rationale(self, debate_result: DebateResult, 
                           risk_assessment: RiskAssessment) -> str:
        """生成决策理由"""
        decision = debate_result.manager_decision
        conviction = debate_result.conviction_score
        risk = risk_assessment.risk_score
        
        if decision in ["STRONG_BUY", "BUY"]:
            return f"""基于多维度分析：
1. 多头观点 conviction {conviction:.0%}，占优
2. 风险评估 {risk:.0%}，在可接受范围
3. 技术面/基本面/情绪面共振
4. 建议仓位 {self._calculate_position(risk):.0%}"""
        elif decision in ["STRONG_SELL", "SELL"]:
            return f"""基于多维度分析：
1. 空头观点占优，风险收益比不佳
2. 风险评分 {risk:.0%} 较高
3. 建议减仓或清仓规避风险"""
        else:
            return f"""基于多维度分析：
1. 多空双方观点焦灼
2. conviction score {conviction:.0%} 较低
3. 建议观望，等待更明确信号"""
    
    def _format_risk_level(self, risk_score: float) -> str:
        """格式化风险等级"""
        if risk_score < 0.3:
            return "低风险"
        elif risk_score < 0.6:
            return "中等风险"
        else:
            return "高风险"


class MultiAgentDebateSystem:
    """多代理辩论系统 - 整合整个工作流"""
    
    def __init__(self, llm_client=None, use_mock: bool = True):
        from ..analysts import FourAnalysts
        from ..debate import DebateEngine
        from ..risk import RiskAssessmentEngine
        
        self.analysts = FourAnalysts(llm_client, use_mock)
        self.debate = DebateEngine(llm_client, use_mock)
        self.risk_engine = RiskAssessmentEngine(llm_client, use_mock)
        self.decision_maker = TradingDecisionMaker()
        self.use_mock = use_mock
    
    async def analyze(self, 
                      stock_code: str,
                      stock_name: str = "",
                      current_price: float = 0.0,
                      market_data: str = "",
                      fundamental_data: str = "",
                      news_data: str = "",
                      sentiment_data: str = "") -> Dict[str, Any]:
        """完整分析流程"""
        
        # 构建上下文
        context = {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "current_price": current_price,
            "market_data": market_data,
            "fundamental_data": fundamental_data,
            "news_data": news_data,
            "sentiment_data": sentiment_data
        }
        
        # Phase 1: 四维分析
        print("=" * 50)
        print(f"Phase 1: Running 4-Analyzers for {stock_code}")
        analyst_report = await self.analysts.run(context)
        
        # Phase 2: 多空辩论
        print("Phase 2: Running Bull/Bear Debate")
        debate_result = await self.debate.run_with_analyst_report(analyst_report)
        
        # Phase 3: 风险评估
        print("Phase 3: Running Risk Assessment")
        risk_assessment = await self.risk_engine.run_with_debate_result(
            debate_result, 
            current_price
        )
        
        # Phase 4: 生成最终决策
        print("Phase 4: Generating Final Decision")
        result = self.decision_maker.make_decision(
            stock_code=stock_code,
            stock_name=stock_name,
            current_price=current_price,
            analyst_report=analyst_report,
            debate_result=debate_result,
            risk_assessment=risk_assessment
        )
        
        # 添加元数据
        result["metadata"] = {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "current_price": current_price,
            "timestamp": datetime.now().isoformat(),
            "use_mock": self.use_mock
        }
        
        print("=" * 50)
        print("Analysis Complete!")
        
        return result
    
    async def quick_analyze(self, 
                           stock_code: str,
                           current_price: float) -> Dict[str, Any]:
        """快速分析（使用默认数据）"""
        return await self.analyze(
            stock_code=stock_code,
            stock_name=stock_code,
            current_price=current_price
        )