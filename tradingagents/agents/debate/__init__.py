"""
多代理辩论引擎 - Bull/Bear/Research Manager
"""
import asyncio
from typing import Dict, Any, List, Optional

from ..base import (
    AgentRole,
    AgentConfig,
    AnalysisResult,
    DebateResult,
    BaseAgent,
    ROLE_CONFIGS
)


class BullDebater(BaseAgent):
    """多头辩论 Agent"""
    
    def __init__(self, llm_client=None):
        config = ROLE_CONFIGS[AgentRole.BULL_ARGUMENT]
        super().__init__(config)
        self._llm_client = llm_client
    
    async def run(self, context: Dict[str, Any]) -> AnalysisResult:
        # 构建包含所有分析结果的提示词
        prompt = self._build_bull_prompt(context)
        
        if self._llm_client:
            content = await self._call_llm(prompt)
        else:
            content = self._generate_mock_bull(context)
        
        return AnalysisResult(
            agent_role=self.role,
            agent_name=self.name,
            content=content,
            confidence=self._extract_confidence(content),
            evidence=self._extract_evidence(content),
            metadata=context.get("metadata", {})
        )
    
    def _build_bull_prompt(self, context: Dict[str, Any]) -> str:
        base = self.config.system_prompt
        base += "\n\n## 已有分析\n"
        
        if "market_analysis" in context:
            base += f"\n### 技术面分析\n{context['market_analysis']}"
        if "fundamentals_analysis" in context:
            base += f"\n### 基本面分析\n{context['fundamentals_analysis']}"
        if "news_analysis" in context:
            base += f"\n### 新闻面分析\n{context['news_analysis']}"
        if "sentiment_analysis" in context:
            base += f"\n### 情绪面分析\n{context['sentiment_analysis']}"
        
        base += "\n\n请综合以上分析，提出看涨观点。"
        return base
    
    def _generate_mock_bull(self, context: Dict[str, Any]) -> str:
        stock = context.get("stock_code", "Unknown")
        
        return f"""## {stock} 多头观点

### 看涨催化剂
1. 技术面：MACD金叉，均线多头排列，短期趋势向好
2. 基本面：业绩预增25%，ROE 18%高于行业平均
3. 情绪面：北向资金净流入，机构增持，研报一致看多

### 预期涨幅
目标价 {context.get('current_price', 100) * 1.2:.2f} 元，上涨空间 20%。

### 风险收益比
上涨概率：70%
下跌风险：15%
风险收益比：4.7:1

### 上涨逻辑
1. 业绩驱动：净利润增长推动估值修复
2. 资金推动：内外资持续买入形成合力
3. 预期修复：市场对公司认知从周期股向成长股切换

### 风险控制建议
- 止损位：{context.get('current_price', 100) * 0.95:.2f} 元
- 仓位建议：不超过30%

### 结论
建议买入，目标价 {context.get('current_price', 100) * 1.2:.2f} 元。"""
    
    def _extract_confidence(self, content: str) -> float:
        if "建议买入" in content:
            return 0.8
        elif "增持" in content:
            return 0.7
        return 0.5
    
    def _extract_evidence(self, content: str) -> List[str]:
        evidence = []
        if "MACD" in content or "金叉" in content:
            evidence.append("技术面MACD金叉")
        if "业绩" in content:
            evidence.append("业绩预增")
        if "资金" in content:
            evidence.append("资金净流入")
        if "目标价" in content:
            evidence.append("有目标价")
        return evidence


class BearDebater(BaseAgent):
    """空头辩论 Agent"""
    
    def __init__(self, llm_client=None):
        config = ROLE_CONFIGS[AgentRole.BEAR_ARGUMENT]
        super().__init__(config)
        self._llm_client = llm_client
    
    async def run(self, context: Dict[str, Any]) -> AnalysisResult:
        prompt = self._build_bear_prompt(context)
        
        if self._llm_client:
            content = await self._call_llm(prompt)
        else:
            content = self._generate_mock_bear(context)
        
        return AnalysisResult(
            agent_role=self.role,
            agent_name=self.name,
            content=content,
            confidence=self._extract_confidence(content),
            evidence=self._extract_evidence(content),
            metadata=context.get("metadata", {})
        )
    
    def _build_bear_prompt(self, context: Dict[str, Any]) -> str:
        base = self.config.system_prompt
        base += "\n\n## 已有分析\n"
        
        if "market_analysis" in context:
            base += f"\n### 技术面分析\n{context['market_analysis']}"
        if "fundamentals_analysis" in context:
            base += f"\n### 基本面分析\n{context['fundamentals_analysis']}"
        if "news_analysis" in context:
            base += f"\n### 新闻面分析\n{context['news_analysis']}"
        if "sentiment_analysis" in context:
            base += f"\n### 情绪面分析\n{context['sentiment_analysis']}"
        
        base += "\n\n请综合以上分析，提出看跌观点。"
        return base
    
    def _generate_mock_bear(self, context: Dict[str, Any]) -> str:
        stock = context.get("stock_code", "Unknown")
        
        return f"""## {stock} 空头观点

### 看跌催化剂
1. 技术面：KDJ 超买，J 值 90，短线有回调压力
2. 基本面：行业周期下行，产能过剩风险
3. 估值：PE 15 倍处于历史高位，盈利无法支撑

### 预期跌幅
目标价 {context.get('current_price', 100) * 0.85:.2f} 元，下跌空间 15%。

### 风险收益比
上涨概率：30%
下跌风险：70%
风险收益比：0.43:1

### 下跌逻辑
1. 估值回归：当前估值无法支撑，后续面临收缩
2. 业绩风险：下游需求疲软，未来业绩承压
3. 筹码松动：股东人数增加，机构开始减持

### 风险控制建议
- 止盈位：{context.get('current_price', 100) * 1.05:.2f} 元
- 建议观望或卖出

### 结论
建议卖出或减持，目标价 {context.get('current_price', 100) * 0.85:.2f} 元。"""
    
    def _extract_confidence(self, content: str) -> float:
        if "建议卖出" in content:
            return 0.75
        elif "减持" in content:
            return 0.65
        return 0.5
    
    def _extract_evidence(self, content: str) -> List[str]:
        evidence = []
        if "KDJ" in content or "超买" in content:
            evidence.append("技术面超买")
        if "周期" in content or "下行" in content:
            evidence.append("行业周期下行")
        if "估值" in content:
            evidence.append("估值偏高")
        if "减持" in content:
            evidence.append("机构减持")
        return evidence


class ResearchManager(BaseAgent):
    """研究经理 - 仲裁多头与空头观点"""
    
    def __init__(self, llm_client=None):
        config = ROLE_CONFIGS[AgentRole.RESEARCH_MANAGER]
        super().__init__(config)
        self._llm_client = llm_client
    
    async def run(self, context: Dict[str, Any]) -> DebateResult:
        # 获取多头和空头观点
        bull_context = self._prepare_debate_context(context, "bull")
        bear_context = self._prepare_debate_context(context, "bear")
        
        bull = BullDebater(self._llm_client)
        bear = BearDebater(self._llm_client)
        
        if self._llm_client:
            bull_result, bear_result = await asyncio.gather(
                bull.run(bull_context),
                bear.run(bear_context)
            )
        else:
            bull_result = await bull.run(bull_context)
            bear_result = await bear.run(bear_context)
        
        # 仲裁决策
        decision = self._make_decision(bull_result, bear_result)
        investment_plan = self._create_investment_plan(bull_result, bear_result, decision)
        conviction = self._calculate_conviction(bull_result, bear_result)
        
        return DebateResult(
            bull_result=bull_result,
            bear_result=bear_result,
            manager_decision=decision,
            investment_plan=investment_plan,
            conviction_score=conviction
        )
    
    def _prepare_debate_context(self, context: Dict[str, Any], side: str) -> Dict[str, Any]:
        """准备辩论上下文"""
        ctx = context.copy()
        ctx["metadata"] = {"debate_side": side}
        return ctx
    
    def _make_decision(self, bull: AnalysisResult, bear: AnalysisResult) -> str:
        """做出仲裁决策"""
        bull_score = bull.confidence * (1.0 if "买入" in bull.content else 0.5)
        bear_score = bear.confidence * (1.0 if "卖出" in bear.content else 0.5)
        
        diff = bull_score - bear_score
        
        if diff > 0.3:
            return "STRONG_BUY"
        elif diff > 0.1:
            return "BUY"
        elif diff < -0.3:
            return "STRONG_SELL"
        elif diff < -0.1:
            return "SELL"
        else:
            return "HOLD"
    
    def _create_investment_plan(self, bull: AnalysisResult, bear: AnalysisResult, decision: str) -> str:
        """创建投资计划"""
        plans = {
            "STRONG_BUY": """建议强势买入
- 首次建仓：30%仓位
- 加仓条件：回调至5日均线
- 目标价：上涨20%
- 止损位：买入价下方5%""",
            "BUY": """建议买入
- 首次建仓：20%仓位
- 加仓条件：突破前高
- 目标价：上涨15%
- 止损位：买入价下方8%""",
            "HOLD": """建议持有观望
- 当前仓位保持不变
- 等待更明确信号
- 关注关键技术位""",
            "SELL": """建议卖出
- 建议减仓50%
- 剩余仓位设止损
- 等待更好的买入时机""",
            "STRONG_SELL": """建议清仓卖出
- 建议全部清仓
- 规避短期风险
- 等待估值回归后再考虑"""
        }
        return plans.get(decision, "暂无建议")
    
    def _calculate_conviction(self, bull: AnalysisResult, bear: AnalysisResult) -> float:
        """计算 conviction score"""
        confidence_diff = abs(bull.confidence - bear.confidence)
        evidence_count = len(bull.evidence) + len(bear.evidence)
        
        # 基于置信度差异和证据数量
        conviction = min(1.0, confidence_diff * 0.5 + evidence_count * 0.05)
        return conviction


class DebateEngine:
    """辩论引擎 - 整合多头、空头、研究经理"""
    
    def __init__(self, llm_client=None, use_mock: bool = True):
        self.manager = ResearchManager(llm_client)
        self.use_mock = use_mock
    
    async def run(self, context: Dict[str, Any]) -> DebateResult:
        """运行完整的辩论流程"""
        
        # 如果是 Mock 模式，直接返回预设结果
        if self.use_mock:
            return await self._run_mock_debate(context)
        
        # LLM 模式
        return await self.manager.run(context)
    
    async def _run_mock_debate(self, context: Dict[str, Any]) -> DebateResult:
        """Mock 辩论"""
        # 多头观点
        bull = BullDebater(None)
        bull_result = await bull.run(context)
        
        # 空头观点
        bear = BearDebater(None)
        bear_result = await bear.run(context)
        
        # 仲裁
        decision = "BUY"  # 默认为多头
        conviction = 0.75
        
        # 检查空头是否更强
        if "卖出" in bear_result.content:
            decision = "SELL"
            conviction = 0.7
        
        investment_plan = f"""投资计划：
- 决策：{decision}
- 仓位建议：25%
- 目标价：{context.get('current_price', 100) * 1.15:.2f}
- 止损：{context.get('current_price', 100) * 0.95:.2f}"""
        
        return DebateResult(
            bull_result=bull_result,
            bear_result=bear_result,
            manager_decision=decision,
            investment_plan=investment_plan,
            conviction_score=conviction
        )
    
    async def run_with_analyst_report(self, report) -> DebateResult:
        """基于四维分析报告运行辩论"""
        context = {}
        
        if report.market:
            context["market_analysis"] = report.market.content
        if report.fundamentals:
            context["fundamentals_analysis"] = report.fundamentals.content
        if report.news:
            context["news_analysis"] = report.news.content
        if report.sentiment:
            context["sentiment_analysis"] = report.sentiment.content
        
        return await self.run(context)