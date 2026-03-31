"""
多代理辩论框架
"""
from .base import (
    AgentRole,
    AgentType,
    Decision,
    AgentConfig,
    AnalysisResult,
    DebateResult,
    TradingDecision,
    RiskAssessment,
    BaseAgent,
    ROLE_CONFIGS
)
from .analysts import (
    FourAnalysts,
    AnalystReport,
    MarketAnalyst,
    FundamentalsAnalyst,
    NewsAnalyst,
    SentimentAnalyst
)
from .debate import (
    DebateEngine,
    BullDebater,
    BearDebater,
    ResearchManager
)
from .risk import (
    RiskAssessmentEngine,
    AggressiveRiskAnalyst,
    ConservativeRiskAnalyst,
    NeutralRiskAnalyst,
    RiskManager
)
from .reporting import (
    ReportGenerator,
    TradingDecisionMaker,
    MultiAgentDebateSystem
)

__all__ = [
    # 基础
    'AgentRole',
    'AgentType', 
    'Decision',
    'AgentConfig',
    'AnalysisResult',
    'DebateResult',
    'TradingDecision',
    'RiskAssessment',
    'BaseAgent',
    'ROLE_CONFIGS',
    # 分析器
    'FourAnalysts',
    'AnalystReport',
    'MarketAnalyst',
    'FundamentalsAnalyst',
    'NewsAnalyst',
    'SentimentAnalyst',
    # 辩论
    'DebateEngine',
    'BullDebater',
    'BearDebater',
    'ResearchManager',
    # 风险
    'RiskAssessmentEngine',
    'AggressiveRiskAnalyst',
    'ConservativeRiskAnalyst',
    'NeutralRiskAnalyst',
    'RiskManager',
    # 报告
    'ReportGenerator',
    'TradingDecisionMaker',
    'MultiAgentDebateSystem'
]