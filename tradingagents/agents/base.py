"""
多代理辩论框架 - Agent 基类和角色定义
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import json
import time


class AgentRole(Enum):
    """Agent 角色枚举"""
    # Phase 1 - 四角色分析器
    MARKET_ANALYST = "market_analyst"      # 市场技术分析
    FUNDAMENTALS_ANALYST = "fundamentals_analyst"  # 基本面分析
    NEWS_ANALYST = "news_analyst"          # 新闻分析
    SENTIMENT_ANALYST = "sentiment_analyst" # 情绪分析
    
    # Phase 2 - 辩论阶段
    BULL_ARGUMENT = "bull"                  # 多头观点
    BEAR_ARGUMENT = "bear"                 # 空头观点
    RESEARCH_MANAGER = "research_manager"  # 研究经理（仲裁）
    
    # Phase 3 - 交易决策
    TRADER = "trader"                       # 交易员
    
    # Phase 4 - 风险评估
    AGGRESSIVE_RISK = "aggressive_risk"     # 激进风险评估
    CONSERVATIVE_RISK = "conservative_risk" # 保守风险评估
    NEUTRAL_RISK = "neutral_risk"          # 中性风险评估
    RISK_MANAGER = "risk_manager"           # 风险管理经理


class AgentType(Enum):
    """Agent 类型"""
    ANALYST = "analyst"        # 分析型
    DEBATER = "debater"       # 辩论型
    MANAGER = "manager"       # 管理型
    TRADER = "trader"          # 交易型
    RISK = "risk"             # 风险型


class Decision(Enum):
    """投资决策"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class AgentConfig:
    """Agent 配置"""
    name: str
    role: AgentRole
    agent_type: AgentType
    description: str
    system_prompt: str
    max_turns: int = 10
    temperature: float = 0.7
    model: str = "claude-sonnet-4-20250514"
    provider: str = "anthropic"


@dataclass
class AnalysisResult:
    """分析结果"""
    agent_role: AgentRole
    agent_name: str
    content: str
    confidence: float  # 0-1
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_role": self.agent_role.value,
            "agent_name": self.agent_name,
            "content": self.content,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


@dataclass
class DebateResult:
    """辩论结果"""
    bull_result: Optional[AnalysisResult] = None
    bear_result: Optional[AnalysisResult] = None
    manager_decision: Optional[str] = None
    investment_plan: Optional[str] = None
    conviction_score: float = 0.0  # 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bull": self.bull_result.to_dict() if self.bull_result else None,
            "bear": self.bear_result.to_dict() if self.bear_result else None,
            "manager_decision": self.manager_decision,
            "investment_plan": self.investment_plan,
            "conviction_score": self.conviction_score
        }


@dataclass
class TradingDecision:
    """交易决策"""
    decision: Decision
    rationale: str
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    position_size: Optional[float] = None  # 0-1
    confidence: float = 0.0
    risk_level: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "rationale": self.rationale,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
            "position_size": self.position_size,
            "confidence": self.confidence,
            "risk_level": self.risk_level
        }


@dataclass
class RiskAssessment:
    """风险评估结果"""
    aggressive_result: Optional[AnalysisResult] = None
    conservative_result: Optional[AnalysisResult] = None
    neutral_result: Optional[AnalysisResult] = None
    final_assessment: Optional[str] = None
    risk_score: float = 0.0  # 0-1 (0=低风险, 1=高风险)
    recommendation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "aggressive": self.aggressive_result.to_dict() if self.aggressive_result else None,
            "conservative": self.conservative_result.to_dict() if self.conservative_result else None,
            "neutral": self.neutral_result.to_dict() if self.neutral_result else None,
            "final_assessment": self.final_assessment,
            "risk_score": self.risk_score,
            "recommendation": self.recommendation
        }


class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.conversation_history: List[Dict[str, str]] = []
        self._llm_client = None
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def role(self) -> AgentRole:
        return self.config.role
    
    def add_message(self, role: str, content: str):
        """添加消息到历史"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def clear_history(self):
        """清空历史"""
        self.conversation_history = []
    
    def set_llm_client(self, client):
        """设置 LLM 客户端"""
        self._llm_client = client
    
    @abstractmethod
    async def run(self, context: Dict[str, Any]) -> AnalysisResult:
        """运行 Agent"""
        pass
    
    def build_prompt(self, context: Dict[str, Any]) -> str:
        """构建提示词"""
        base_prompt = self.config.system_prompt
        
        # 添加上下文
        if "stock_code" in context:
            base_prompt += f"\n\n## 目标股票\n{context['stock_code']}"
        if "stock_name" in context:
            base_prompt += f"\n股票名称: {context['stock_name']}"
        if "current_price" in context:
            base_prompt += f"\n当前价格: {context['current_price']}"
        if "market_data" in context:
            base_prompt += f"\n\n## 市场数据\n{context['market_data']}"
        if "fundamental_data" in context:
            base_prompt += f"\n\n## 基本面数据\n{context['fundamental_data']}"
        if "news_data" in context:
            base_prompt += f"\n\n## 新闻数据\n{context['news_data']}"
        if "sentiment_data" in context:
            base_prompt += f"\n\n## 情绪数据\n{context['sentiment_data']}"
        if "previous_analyses" in context:
            base_prompt += f"\n\n## 其他分析\n{context['previous_analyses']}"
            
        return base_prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        if self._llm_client is None:
            return "LLM client not initialized"
        
        response = await self._llm_client.chat(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=2000
        )
        
        return response.get("content", "")


# 角色配置预定义
ROLE_CONFIGS = {
    AgentRole.MARKET_ANALYST: AgentConfig(
        name="Market Analyst",
        role=AgentRole.MARKET_ANALYST,
        agent_type=AgentType.ANALYST,
        description="技术分析专家，擅长K线形态、均线系统、成交量分析",
        system_prompt="""你是一位资深的技术分析专家。你的职责是基于市场数据（K线、均线、成交量、技术指标）提供专业的技术分析。

分析框架：
1. 趋势判断：识别当前趋势（上升/下降/震荡）
2. 形态识别：识别关键K线形态（吞没、十字星、锤子线等）
3. 指标分析：分析MACD、RSI、KDJ、布林带等指标
4. 支撑阻力：识别关键支撑位和阻力位
5. 量价关系：分析成交量与价格的关系

输出要求：
- 提供明确的技术面观点
- 给出置信度评分（0-1）
- 列出支持你观点的关键证据"""
    ),
    
    AgentRole.FUNDAMENTALS_ANALYST: AgentConfig(
        name="Fundamentals Analyst",
        role=AgentRole.FUNDAMENTALS_ANALYST,
        agent_type=AgentType.ANALYST,
        description="基本面分析专家，擅长财务指标、行业分析、估值模型",
        system_prompt="""你是一位资深的基本面分析专家。你的职责是基于公司财务数据、行业状况、宏观经济提供专业的基本面分析。

分析框架：
1. 财务分析：营收增长、利润水平、ROE、现金流
2. 估值分析：PE、PB、DCF、自由现金流折现
3. 行业分析：行业周期、竞争格局、成长空间
4. 护城河分析：品牌、技术、渠道、成本优势
5. 风险识别：经营风险、财务风险、行业风险

输出要求：
- 提供明确的基本面观点
- 给出置信度评分（0-1）
- 列出关键财务数据和估值依据"""
    ),
    
    AgentRole.NEWS_ANALYST: AgentConfig(
        name="News Analyst",
        role=AgentRole.NEWS_ANALYST,
        agent_type=AgentType.ANALYST,
        description="新闻分析专家，擅长政策解读、事件驱动、媒体情绪",
        system_prompt="""你是一位资深的新闻分析专家。你的职责是基于新闻资讯、政策动向、媒体报道提供专业的新闻分析。

分析框架：
1. 新闻摘要：提取关键信息要点
2. 政策影响：评估政策对公司和行业的影响
3. 事件驱动：识别可能影响股价的催化事件
4. 媒体情绪：分析媒体对该股票的整体态度
5. 时间线：梳理重要新闻的时间顺序

输出要求：
- 提供明确的新闻面观点
- 给出置信度评分（0-1）
- 列出关键新闻事件及其影响"""
    ),
    
    AgentRole.SENTIMENT_ANALYST: AgentConfig(
        name="Sentiment Analyst",
        role=AgentRole.SENTIMENT_ANALYST,
        agent_type=AgentType.ANALYST,
        description="情绪分析专家，擅长市场情绪、资金流向、社交媒体",
        system_prompt="""你是一位资深的情绪分析专家。你的职责是基于市场情绪、资金流向、投资者行为提供专业的情绪分析。

分析框架：
1. 资金流向：分析主力资金、北向资金、融资融券
2. 情绪指标：情绪指数、恐慌指数、期权持仓
3. 机构持仓：分析公募、私募、社保持仓变化
4. 舆情监控：社交媒体、股吧、论坛情绪
5. 持仓结构：股东人数、筹码分布分析

输出要求：
- 提供明确的情绪面观点
- 给出置信度评分（0-1）
- 列出关键情绪指标和资金数据"""
    ),
    
    AgentRole.BULL_ARGUMENT: AgentConfig(
        name="Bull Argument",
        role=AgentRole.BULL_ARGUMENT,
        agent_type=AgentType.DEBATER,
        description="多头观点代表，提出看涨论据",
        system_prompt="""你是多头观点的代表。你的任务是综合所有分析信息，提出看涨的投资理由。

论证框架：
1. 上涨催化剂：识别推动股价上涨的关键因素
2. 预期涨幅：给出合理的目标价和上涨空间
3. 风险收益比：评估上涨概率与下跌风险的比例
4. 上涨逻辑：阐述股价上涨的核心逻辑
5. 对冲策略：提出风险管理建议

输出要求：
- 提出强有力的看涨论点
- 给出置信度评分（0-1）
- 列出支持上涨的关键证据"""
    ),
    
    AgentRole.BEAR_ARGUMENT: AgentConfig(
        name="Bear Argument",
        role=AgentRole.BEAR_ARGUMENT,
        agent_type=AgentType.DEBATER,
        description="空头观点代表，提出看跌论据",
        system_prompt="""你是空头观点的代表。你的任务是综合所有分析信息，提出看跌的投资理由。

论证框架：
1. 下跌催化剂：识别可能导致股价下跌的因素
2. 预期跌幅：给出合理的下跌目标和空间
3. 风险收益比：评估下跌概率与上涨机会的比例
4. 下跌逻辑：阐述股价下跌的核心逻辑
5. 对冲策略：提出风险规避建议

输出要求：
- 提出强有力的看跌论点
- 给出置信度评分（0-1）
- 列出支持下跌的关键证据"""
    ),
    
    AgentRole.RESEARCH_MANAGER: AgentConfig(
        name="Research Manager",
        role=AgentRole.RESEARCH_MANAGER,
        agent_type=AgentType.MANAGER,
        description="研究经理，仲裁多头与空头观点，给出投资计划",
        system_prompt="""你是研究经理，负责仲裁多头和空头的观点，并制定投资计划。

职责：
1. 客观评估多头和空头的论点
2. 识别双方论点的 strengths 和 weaknesses
3. 基于证据权重做出判断
4. 制定明确的投资计划（买入/卖出/持有）
5. 给出置信度和 conviction score

决策框架：
- 如果多头证据明显更强 → 建议买入/增持
- 如果空头证据明显更强 → 建议卖出/减持
- 如果双方证据相当 → 建议持有/观望
- 给出清晰的投资逻辑和目标"""
    ),
    
    AgentRole.TRADER: AgentConfig(
        name="Trader",
        role=AgentRole.TRADER,
        agent_type=AgentType.TRADER,
        description="交易员，基于分析结果做出具体交易决策",
        system_prompt="""你是专业交易员，负责基于综合分析制定具体的交易决策。

决策要素：
1. 交易方向：买入/卖出/持有
2. 目标价：合理的目标价格
3. 止损位：风险控制止损价格
4. 仓位建议：建议的持仓比例
5. 入场时机：具体的买入时机

决策原则：
- 追求风险收益比最优
- 强调执行纪律
- 考虑流动性风险
- 给出明确的操作建议"""
    ),
    
    AgentRole.AGGRESSIVE_RISK: AgentConfig(
        name="Aggressive Risk Analyst",
        role=AgentRole.AGGRESSIVE_RISK,
        agent_type=AgentType.RISK,
        description="激进风险评估，从高风险角度评估交易",
        system_prompt="""你是激进型风险分析师。你的任务是从最坏情况出发评估交易风险。

分析视角：
1. 最大亏损：假设最不利情况下的亏损
2. 波动性：高波动对组合的影响
3. 黑天鹅：尾部风险的识别
4. 杠杆风险：如果使用杠杆的风险
5. 流动性风险：大额持仓的退出难度

输出要求：
- 给出高风险视角的评估
- 识别潜在的重大风险点
- 评估风险是否可控"""
    ),
    
    AgentRole.CONSERVATIVE_RISK: AgentConfig(
        name="Conservative Risk Analyst",
        role=AgentRole.CONSERVATIVE_RISK,
        agent_type=AgentType.RISK,
        description="保守风险评估，从低风险角度评估交易",
        system_prompt="""你是保守型风险分析师。你的任务是从稳健角度评估交易风险。

分析视角：
1. 本金保护：优先考虑亏损控制
2. 回撤容忍：可接受的最大回撤
3. 收益稳定性：收益的确定性
4. 分散化：持仓分散程度
5. 时间成本：资金的时间价值

输出要求：
- 给出稳健风险视角的评估
- 强调风险控制的重要性
- 建议的风险缓释措施"""
    ),
    
    AgentRole.NEUTRAL_RISK: AgentConfig(
        name="Neutral Risk Analyst",
        role=AgentRole.NEUTRAL_RISK,
        agent_type=AgentType.RISK,
        description="中性风险评估，平衡收益与风险",
        system_prompt="""你是中性风险分析师。你的任务是平衡评估收益与风险。

分析视角：
1. 风险收益平衡：收益与风险的权衡
2. 性价比：风险调整后收益
3. 最优仓位：风险合适的仓位大小
4. 场景分析：不同市场情况下的表现
5. 退出策略：止盈止损策略

输出要求：
- 给出中性平衡的风险评估
- 给出合理的仓位建议
- 评估风险调整后的收益"""
    ),
    
    AgentRole.RISK_MANAGER: AgentConfig(
        name="Risk Manager",
        role=AgentRole.RISK_MANAGER,
        agent_type=AgentType.MANAGER,
        description="风险管理经理，综合三方风险评估给出最终决策",
        system_prompt="""你是风险管理经理，负责综合激进、保守、中性的风险评估，给出最终风险决策。

职责：
1. 汇总三方风险观点
2. 识别共识和分歧
3. 给出最终风险评分（0-1）
4. 制定风险管理建议
5. 确认仓位和止损建议

决策框架：
- 激进观点：关注潜在收益
- 保守观点：关注潜在风险
- 中性观点：寻求平衡
- 综合判断，给出最终建议"""
    ),
}