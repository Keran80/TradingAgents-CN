"""
四角色分析器 - Market/Fundamentals/News/Sentiment
"""
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..base import (
    AgentRole,
    AgentConfig,
    AnalysisResult,
    BaseAgent,
    ROLE_CONFIGS
)


class MarketAnalyst(BaseAgent):
    """市场技术分析 Agent"""
    
    def __init__(self, llm_client=None):
        config = ROLE_CONFIGS[AgentRole.MARKET_ANALYST]
        super().__init__(config)
        self._llm_client = llm_client
    
    async def run(self, context: Dict[str, Any]) -> AnalysisResult:
        prompt = self.build_prompt(context)
        
        if self._llm_client:
            content = await self._call_llm(prompt)
        else:
            # Mock 模式
            content = self._generate_mock_analysis(context)
        
        return AnalysisResult(
            agent_role=self.role,
            agent_name=self.name,
            content=content,
            confidence=0.8,
            evidence=self._extract_evidence(content),
            metadata=context.get("metadata", {})
        )
    
    def _generate_mock_analysis(self, context: Dict[str, Any]) -> str:
        stock = context.get("stock_code", "Unknown")
        price = context.get("current_price", 0)
        
        return f"""## {stock} 技术分析

### 趋势判断
当前价格 {price} 元，处于上升趋势中的回调阶段。均线系统呈现多头排列，20日均线向上发散，对股价形成支撑。

### K线形态
近期出现缩量十字星形态，显示卖压减轻，短期有望企稳回升。

### 技术指标
- MACD：DIF 与 DEA 在零轴上方形成金叉，红柱放大
- RSI：处于 65 附近，强势区域
- KDJ：J 值触及 80 后回落，短期内有调整需求

### 支撑阻力
- 支撑位：{price * 0.95:.2f} 元（20日均线）
- 阻力位：{price * 1.10:.2f} 元（前高）

### 结论
技术面偏多，建议关注回调至均线支撑位的买入机会。"""
    
    def _extract_evidence(self, content: str) -> List[str]:
        evidence = []
        if "MACD" in content:
            evidence.append("MACD金叉")
        if "RSI" in content:
            evidence.append("RSI强势区域")
        if "均线" in content:
            evidence.append("均线多头排列")
        if "支撑" in content:
            evidence.append("技术面支撑位")
        return evidence


class FundamentalsAnalyst(BaseAgent):
    """基本面分析 Agent"""
    
    def __init__(self, llm_client=None):
        config = ROLE_CONFIGS[AgentRole.FUNDAMENTALS_ANALYST]
        super().__init__(config)
        self._llm_client = llm_client
    
    async def run(self, context: Dict[str, Any]) -> AnalysisResult:
        prompt = self.build_prompt(context)
        
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
            metadata=context.get("metadata", {})
        )
    
    def _generate_mock_analysis(self, context: Dict[str, Any]) -> str:
        stock = context.get("stock_code", "Unknown")
        
        return f"""## {stock} 基本面分析

### 财务概况
公司盈利能力良好，近三年营收复合增长率 15%，净利润复合增长率 20%。

### 关键财务指标
- ROE：18%，高于行业平均 12%
- 毛利率：35%，具有较强的定价能力
- 资产负债率：40%，财务结构稳健
- 现金流：经营现金流为正，资金充裕

### 估值分析
- PE：15倍，处于历史低位
- PB：2.5倍，低于行业平均
- DCF：当前价格较内在价值低 20%

### 行业地位
细分行业龙头，市场份额 30%，具有品牌和渠道优势。

### 风险提示
- 原材料价格波动风险
- 下游需求周期性风险
- 行业竞争加剧风险

### 结论
基本面良好，估值具有吸引力，建议关注。"""
    
    def _extract_evidence(self, content: str) -> List[str]:
        evidence = []
        if "ROE" in content:
            evidence.append("ROE高于行业平均")
        if "PE" in content:
            evidence.append("PE估值低位")
        if "龙头" in content:
            evidence.append("行业龙头地位")
        if "现金流" in content:
            evidence.append("经营现金流为正")
        return evidence


class NewsAnalyst(BaseAgent):
    """新闻分析 Agent"""
    
    def __init__(self, llm_client=None):
        config = ROLE_CONFIGS[AgentRole.NEWS_ANALYST]
        super().__init__(config)
        self._llm_client = llm_client
    
    async def run(self, context: Dict[str, Any]) -> AnalysisResult:
        prompt = self.build_prompt(context)
        
        if self._llm_client:
            content = await self._call_llm(prompt)
        else:
            content = self._generate_mock_analysis(context)
        
        return AnalysisResult(
            agent_role=self.role,
            agent_name=self.name,
            content=content,
            confidence=0.75,
            evidence=self._extract_evidence(content),
            metadata=context.get("metadata", {})
        )
    
    def _generate_mock_analysis(self, context: Dict[str, Any]) -> str:
        stock = context.get("stock_code", "Unknown")
        
        return f"""## {stock} 新闻分析

### 近期重要新闻
1. 公司发布2024年度业绩预告，净利润同比增长 25%
2. 与某头部企业签订战略合作协议
3. 获得某省重点项目支持，金额约 2 亿元

### 政策影响
国家政策大力支持行业发展，公司有望受益于政策红利。

### 事件驱动
- 业绩预增：短期利好，股价有望提振
- 战略合作：中长期利好，提升估值预期

### 媒体情绪
近期媒体关注度上升，市场情绪偏多。

### 风险提示
- 业绩预告可能存在修正风险
- 合作项目落地时间不确定

### 结论
新闻面偏多，建议关注相关催化剂。"""
    
    def _extract_evidence(self, content: str) -> List[str]:
        evidence = []
        if "业绩" in content:
            evidence.append("业绩预增")
        if "合作" in content:
            evidence.append("战略合作")
        if "政策" in content:
            evidence.append("政策支持")
        if "媒体" in content:
            evidence.append("媒体关注")
        return evidence


class SentimentAnalyst(BaseAgent):
    """情绪分析 Agent"""
    
    def __init__(self, llm_client=None):
        config = ROLE_CONFIGS[AgentRole.SENTIMENT_ANALYST]
        super().__init__(config)
        self._llm_client = llm_client
    
    async def run(self, context: Dict[str, Any]) -> AnalysisResult:
        prompt = self.build_prompt(context)
        
        if self._llm_client:
            content = await self._call_llm(prompt)
        else:
            content = self._generate_mock_analysis(context)
        
        return AnalysisResult(
            agent_role=self.role,
            agent_name=self.name,
            content=content,
            confidence=0.7,
            evidence=self._extract_evidence(content),
            metadata=context.get("metadata", {})
        )
    
    def _generate_mock_analysis(self, context: Dict[str, Any]) -> str:
        stock = context.get("stock_code", "Unknown")
        
        return f"""## {stock} 情绪分析

### 资金流向
- 北向资金：近 5 日净流入 1.2 亿元
- 主力资金：近 10 日净流入 3.5 亿元
- 融资融券：融资余额增加，融资买入活跃

### 机构持仓
- 公募基金：持仓比例 5%，环比增加
- 社保基金：新进前十大流通股东
- 机构关注度：近期接待多批机构调研

### 舆情监控
- 股吧活跃度：较高
- 社交媒体情绪：偏多
- 研报覆盖：近一个月新增 3 篇研报，全部给出"买入"评级

### 筹码分布
股东人数连续 3 个季度下降，筹码集中度提升。

### 情绪指标
- 市场情绪指数：75（偏多）
- 个股情绪得分：80（多头）

### 结论
情绪面偏多，资金面和机构面均支持股价上涨。"""
    
    def _extract_evidence(self, content: str) -> List[str]:
        evidence = []
        if "北向" in content or "主力" in content:
            evidence.append("资金净流入")
        if "机构" in content:
            evidence.append("机构增持")
        if "研报" in content:
            evidence.append("研报买入评级")
        if "筹码" in content:
            evidence.append("筹码集中")
        return evidence


@dataclass
class AnalystReport:
    """分析师报告"""
    market: Optional[AnalysisResult] = None
    fundamentals: Optional[AnalysisResult] = None
    news: Optional[AnalysisResult] = None
    sentiment: Optional[AnalysisResult] = None
    
    def get_all_results(self) -> List[AnalysisResult]:
        results = []
        if self.market:
            results.append(self.market)
        if self.fundamentals:
            results.append(self.fundamentals)
        if self.news:
            results.append(self.news)
        if self.sentiment:
            results.append(self.sentiment)
        return results
    
    def summary(self) -> str:
        lines = ["=" * 60, "四维度分析报告", "=" * 60]
        
        for result in self.get_all_results():
            lines.append(f"\n### {result.agent_name}")
            lines.append(f"置信度: {result.confidence:.0%}")
            lines.append(f"观点: {result.content[:200]}...")
            lines.append(f"证据: {', '.join(result.evidence)}")
        
        return "\n".join(lines)


class FourAnalysts:
    """四角色分析器 - 整合四位分析师"""
    
    def __init__(self, llm_client=None, use_mock: bool = True):
        self.market = MarketAnalyst(llm_client)
        self.fundamentals = FundamentalsAnalyst(llm_client)
        self.news = NewsAnalyst(llm_client)
        self.sentiment = SentimentAnalyst(llm_client)
        self.use_mock = use_mock
    
    async def run(self, context: Dict[str, Any]) -> AnalystReport:
        """并行运行四位分析师"""
        
        if self.use_mock or not self.market._llm_client:
            # Mock 模式 - 串行执行
            market_result = await self.market.run(context)
            fundamentals_result = await self.fundamentals.run(context)
            news_result = await self.news.run(context)
            sentiment_result = await self.sentiment.run(context)
        else:
            # LLM 模式 - 并行执行
            tasks = [
                self.market.run(context),
                self.fundamentals.run(context),
                self.news.run(context),
                self.sentiment.run(context)
            ]
            results = await asyncio.gather(*tasks)
            market_result, fundamentals_result, news_result, sentiment_result = results
        
        return AnalystReport(
            market=market_result,
            fundamentals=fundamentals_result,
            news=news_result,
            sentiment=sentiment_result
        )
    
    async def run_sequential(self, context: Dict[str, Any]) -> AnalystReport:
        """串行执行（用于调试）"""
        market_result = await self.market.run(context)
        fundamentals_result = await self.fundamentals.run(context)
        news_result = await self.news.run(context)
        sentiment_result = await self.sentiment.run(context)
        
        return AnalystReport(
            market=market_result,
            fundamentals=fundamentals_result,
            news=news_result,
            sentiment=sentiment_result
        )