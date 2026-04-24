"""
风险评估器 - Aggressive/Conservative/Neutral + Risk Manager
"""
import asyncio
from typing import Dict, Any, List, Optional

from ..base import (
    AgentRole,
    AgentConfig,
    AnalysisResult,
    RiskAssessment,
    BaseAgent,
    ROLE_CONFIGS
)


class AggressiveRiskAnalyst(BaseAgent):
    """激进风险分析师"""
    
    def __init__(self, llm_client=None):
        config = ROLE_CONFIGS[AgentRole.AGGRESSIVE_RISK]
        super().__init__(config)
        self._llm_client = llm_client
    
    async def run(self, context: Dict[str, Any]) -> AnalysisResult:
        prompt = self._build_risk_prompt(context)
        
        if self._llm_client:
            content = await self._call_llm(prompt)
        else:
            content = self._generate_mock_analysis(context)
        
        return AnalysisResult(
            agent_role=self.role,
            agent_name=self.name,
            content=content,
            confidence=0.8,
            evidence=self._extract_evidence(content),
            metadata={"risk_perspective": "aggressive"}
        )
    
    def _build_risk_prompt(self, context: Dict[str, Any]) -> str:
        base = self.config.system_prompt
        base += "\n\n## 交易信息\n"
        
        if "decision" in context:
            base += f"\n决策建议：{context['decision']}"
        if "target_price" in context:
            base += f"\n目标价：{context['target_price']}"
        if "stop_loss" in context:
            base += f"\n止损位：{context['stop_loss']}"
        if "position_size" in context:
            base += f"\n仓位：{context['position_size']:.0%}"
        if "conviction_score" in context:
            base += f"\nConviction Score：{context['conviction_score']:.0%}"
        
        return base
    
    def _generate_mock_analysis(self, context: Dict[str, Any]) -> str:
        price = context.get("current_price", 100)
        target = context.get("target_price", price * 1.2)
        stop = context.get("stop_loss", price * 0.95)
        
        return f"""## 激进风险评估

### 最大亏损场景
- 买入后股价下跌 10% 触发止损，最大亏损 10%
- 极端情况：如果遇到黑天鹅事件，可能亏损 20%

### 波动性评估
- 历史波动率 30%，高于市场平均
- 近期股价波动加大，需关注日内风险

### 尾部风险
- 行业政策突变风险
- 业绩大幅不及预期风险
- 竞争对手重大突破风险

### 风险评估结论
从激进视角看，当前交易的潜在收益(20%)远大于潜在风险(10%)，风险收益比 2:1，符合激进策略要求。

### 建议
- 建议仓位：40%（激进）
- 止损位：{stop:.2f} 元
- 止盈位：{target:.2f} 元
- 如果对冲，可以使用 5% 资金买入看跌期权"""
    
    def _extract_evidence(self, content: str) -> List[str]:
        evidence = []
        if "止损" in content:
            evidence.append("有止损策略")
        if "仓位" in content:
            evidence.append("有仓位建议")
        if "对冲" in content:
            evidence.append("有对冲建议")
        return evidence


class ConservativeRiskAnalyst(BaseAgent):
    """保守风险分析师"""
    
    def __init__(self, llm_client=None):
        config = ROLE_CONFIGS[AgentRole.CONSERVATIVE_RISK]
        super().__init__(config)
        self._llm_client = llm_client
    
    async def run(self, context: Dict[str, Any]) -> AnalysisResult:
        prompt = self._build_risk_prompt(context)
        
        if self._llm_client:
            content = await self._call_llm(prompt)
        else:
            content = self._generate_mock_analysis(context)
        
        return AnalysisResult(
            agent_role=self.role,
            agent_name=self.name,
            content=content,
            confidence=0.85,
            evidence=self._extract_evidence(content),
            metadata={"risk_perspective": "conservative"}
        )
    
    def _build_risk_prompt(self, context: Dict[str, Any]) -> str:
        base = self.config.system_prompt
        base += "\n\n## 交易信息\n"
        
        if "decision" in context:
            base += f"\n决策建议：{context['decision']}"
        if "target_price" in context:
            base += f"\n目标价：{context['target_price']}"
        if "stop_loss" in context:
            base += f"\n止损位：{context['stop_loss']}"
        if "position_size" in context:
            base += f"\n仓位：{context['position_size']:.0%}"
        
        return base
    
    def _generate_mock_analysis(self, context: Dict[str, Any]) -> str:
        price = context.get("current_price", 100)
        target = context.get("target_price", price * 1.15)
        stop = context.get("stop_loss", price * 0.92)
        
        return f"""## 保守风险评估

### 本金保护分析
- 最大可承受亏损：10%
- 建议止损位：{stop:.2f} 元（亏损 8%）
- 距离止损空间：8%

### 回撤容忍度
- 最大回撤容忍：15%
- 当前策略潜在回撤：10%
- 在容忍范围内

### 收益稳定性
- 预期收益：15%
- 收益确定性：中等到高
- 风险调整后收益(夏普)：1.2

### 分散化建议
- 单票仓位不超过 20%
- 建议配置 3-5 只不同行业股票
- 可以配置 30% 仓位在低风险资产

### 风险缓释措施
1. 分批建仓：首次 10%，回调再加 10%
2. 严格止损：8% 止损线
3. 盈利保护：涨 10% 后上调止损至成本价

### 建议
- 建议仓位：20%（保守）
- 止损位：{stop:.2f} 元
- 止盈位：{target:.2f} 元
- 等待更确定的机会"""
    
    def _extract_evidence(self, content: str) -> List[str]:
        evidence = []
        if "止损" in content:
            evidence.append("严格止损")
        if "分批" in content:
            evidence.append("分批建仓")
        if "分散" in content:
            evidence.append("分散配置")
        if "保护" in content:
            evidence.append("盈利保护")
        return evidence


class NeutralRiskAnalyst(BaseAgent):
    """中性风险分析师"""
    
    def __init__(self, llm_client=None):
        config = ROLE_CONFIGS[AgentRole.NEUTRAL_RISK]
        super().__init__(config)
        self._llm_client = llm_client
    
    async def run(self, context: Dict[str, Any]) -> AnalysisResult:
        prompt = self._build_risk_prompt(context)
        
        if self._llm_client:
            content = await self._call_llm(prompt)
        else:
            content = self._generate_mock_analysis(context)
        
        return AnalysisResult(
            agent_role=self.role,
            agent_name=self.name,
            content=content,
            confidence=0.8,
            evidence=self._extract_evidence(content),
            metadata={"risk_perspective": "neutral"}
        )
    
    def _build_risk_prompt(self, context: Dict[str, Any]) -> str:
        base = self.config.system_prompt
        base += "\n\n## 交易信息\n"
        
        if "decision" in context:
            base += f"\n决策建议：{context['decision']}"
        if "target_price" in context:
            base += f"\n目标价：{context['target_price']}"
        if "stop_loss" in context:
            base += f"\n止损位：{context['stop_loss']}"
        
        return base
    
    def _generate_mock_analysis(self, context: Dict[str, Any]) -> str:
        price = context.get("current_price", 100)
        target = context.get("target_price", price * 1.15)
        stop = context.get("stop_loss", price * 0.93)
        
        return f"""## 中性风险评估

### 风险收益平衡
- 预期收益：15%
- 最大风险：7%
- 收益风险比：2.14:1

### 最优仓位
- 基于凯利公式，最优仓位 25%
- 考虑到风险厌恶，建议实际仓位 20%

### 场景分析
- 乐观情况（30%概率）：上涨 20%
- 中性情况（50%概率）：上涨 10%
- 悲观情况（20%概率）：下跌 7%

### 退出策略
- 止盈策略：达到目标价 80% 后分批卖出
- 止损策略：跌破 {stop:.2f} 元止损
- 时间止损：持有 1 个月无涨幅考虑卖出

### 风险评估
- 综合风险评分：0.45（中等）
- 可接受风险等级：中等
- 建议执行

### 建议
- 建议仓位：20-25%
- 止损位：{stop:.2f} 元
- 止盈位：{target:.2f} 元
- 持有期：1-3 个月"""
    
    def _extract_evidence(self, content: str) -> List[str]:
        evidence = []
        if "仓位" in content:
            evidence.append("有仓位建议")
        if "场景" in content:
            evidence.append("场景分析")
        if "退出" in content:
            evidence.append("有退出策略")
        if "评分" in content:
            evidence.append("有风险评分")
        return evidence


class RiskManager(BaseAgent):
    """风险管理经理 - 综合三方评估"""
    
    def __init__(self, llm_client=None):
        config = ROLE_CONFIGS[AgentRole.RISK_MANAGER]
        super().__init__(config)
        self._llm_client = llm_client
    
    async def run(self, context: Dict[str, Any]) -> RiskAssessment:
        """运行风险管理评估"""
        
        # 获取三方风险观点
        aggressive = AggressiveRiskAnalyst(self._llm_client)
        conservative = ConservativeRiskAnalyst(self._llm_client)
        neutral = NeutralRiskAnalyst(self._llm_client)
        
        if self._llm_client:
            results = await asyncio.gather(
                aggressive.run(context),
                conservative.run(context),
                neutral.run(context)
            )
            aggressive_result, conservative_result, neutral_result = results
        else:
            aggressive_result = await aggressive.run(context)
            conservative_result = await conservative.run(context)
            neutral_result = await neutral.run(context)
        
        # 综合判断
        final_assessment = self._make_assessment(
            aggressive_result, 
            conservative_result, 
            neutral_result
        )
        risk_score = self._calculate_risk_score(
            aggressive_result,
            conservative_result,
            neutral_result
        )
        recommendation = self._create_recommendation(
            aggressive_result,
            conservative_result,
            neutral_result,
            risk_score
        )
        
        return RiskAssessment(
            aggressive_result=aggressive_result,
            conservative_result=conservative_result,
            neutral_result=neutral_result,
            final_assessment=final_assessment,
            risk_score=risk_score,
            recommendation=recommendation
        )
    
    def _make_assessment(self, aggressive: AnalysisResult, 
                        conservative: AnalysisResult, 
                        neutral: AnalysisResult) -> str:
        """综合评估"""
        
        # 简单规则：取中性观点的主要结论
        if "建议仓位" in neutral.content:
            # 提取仓位建议
            lines = neutral.content.split("\n")
            for line in lines:
                if "建议仓位" in line:
                    return f"综合三方评估：{line.strip()}"
        
        return "中等风险，建议执行"
    
    def _calculate_risk_score(self, aggressive: AnalysisResult,
                            conservative: AnalysisResult,
                            neutral: AnalysisResult) -> float:
        """计算风险评分 (0-1, 0=低风险, 1=高风险)"""
        
        # 从中性分析中提取风险评分
        if "风险评分" in neutral.content:
            for line in neutral.content.split("\n"):
                if "风险评分" in line and "0." in line:
                    try:
                        score = float(line.split("0.")[1].split(")")[0]) / 10
                        return score
                    except Exception:
                        pass
        
        # 默认中等风险
        return 0.45
    
    def _create_recommendation(self, aggressive: AnalysisResult,
                              conservative: AnalysisResult,
                              neutral: AnalysisResult,
                              risk_score: float) -> str:
        """创建风险管理建议"""
        
        if risk_score < 0.3:
            return """低风险，可适度参与
- 建议仓位：30%
- 止损：7%
- 止盈：15%
- 持有期：1-3个月"""
        elif risk_score < 0.6:
            return """中等风险，建议谨慎参与
- 建议仓位：20%
- 止损：8%
- 止盈：15%
- 持有期：1-2个月"""
        else:
            return """高风险，建议观望或轻仓
- 建议仓位：10%以下
- 严格止损：5%
- 缩短持有期：2-4周"""


class RiskAssessmentEngine:
    """风险评估引擎"""
    
    def __init__(self, llm_client=None, use_mock: bool = True):
        self.risk_manager = RiskManager(llm_client)
        self.use_mock = use_mock
    
    async def run(self, context: Dict[str, Any]) -> RiskAssessment:
        """运行风险评估"""
        return await self.risk_manager.run(context)
    
    async def run_with_debate_result(self, debate_result, price: float) -> RiskAssessment:
        """基于辩论结果运行风险评估"""
        context = {
            "current_price": price,
            "decision": debate_result.manager_decision,
            "conviction_score": debate_result.conviction_score
        }
        
        # 解析投资计划获取目标价和止损
        if debate_result.investment_plan:
            lines = debate_result.investment_plan.split("\n")
            for line in lines:
                if "目标价" in line:
                    try:
                        context["target_price"] = float(line.split("：")[-1].replace("元", ""))
                    except Exception:
                        pass
                if "止损" in line:
                    try:
                        context["stop_loss"] = float(line.split("：")[-1].replace("元", ""))
                    except Exception:
                        pass
        
        return await self.run(context)