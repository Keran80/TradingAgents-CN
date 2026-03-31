# TradingAgents/graph/trading_graph.py

import os
from pathlib import Path
import json
from datetime import date
from typing import Dict, Any, Tuple, List, Optional, Type

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel

from langgraph.prebuilt import ToolNode

from tradingagents.agents import *
from tradingagents.default_config import DEFAULT_CONFIG, CHINA_LLM_CONFIGS
from tradingagents.agents.utils.memory import FinancialSituationMemory
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)
from tradingagents.dataflows.interface import set_config

from .conditional_logic import ConditionalLogic
from .setup import GraphSetup
from .propagation import Propagator
from .reflection import Reflector
from .signal_processing import SignalProcessor


# LLM Provider 映射表（支持扩展）
# 注意：所有中国 LLM 都使用 OpenAI 兼容 API，通过 base_url 配置
LLM_PROVIDER_MAP: Dict[str, Tuple[Type[BaseChatModel], Dict[str, Any]]] = {
    "openai": (ChatOpenAI, {"base_url": None}),  # base_url 从配置读取
    "ollama": (ChatOpenAI, {"base_url": "http://localhost:11434/v1"}),
    "openrouter": (ChatOpenAI, {"base_url": "https://openrouter.ai/api/v1"}),
    "anthropic": (ChatAnthropic, {"base_url": None}),
    "google": (ChatGoogleGenerativeAI, {"base_url": None}),
    # 中国 LLM 提供商（均使用 OpenAI 兼容 API）
    "deepseek": (ChatOpenAI, {"base_url": "https://api.deepseek.com/v1"}),
    "zhipu": (ChatOpenAI, {"base_url": "https://open.bigmodel.cn/api/paas/v4"}),
    "qwen": (ChatOpenAI, {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"}),
    "wenxin": (ChatOpenAI, {"base_url": "https://qianfan.baidubce.com/v2"}),
    "spark": (ChatOpenAI, {"base_url": "https://spark-api.xf-yun.com/v3.5"}),
}


def _create_llm(provider: str, model: str, config: Dict[str, Any]) -> BaseChatModel:
    """根据配置创建 LLM 实例"""
    provider_lower = provider.lower()
    
    if provider_lower not in LLM_PROVIDER_MAP:
        raise ValueError(f"Unsupported LLM provider: {provider}. Supported: {list(LLM_PROVIDER_MAP.keys())}")
    
    llm_class, default_kwargs = LLM_PROVIDER_MAP[provider_lower]
    
    # 合并参数：默认参数 + 配置覆盖
    kwargs = {**default_kwargs, "model": model}
    
    # 处理 base_url（仅当默认值存在时覆盖）
    if provider_lower in ("openai", "ollama", "openrouter", "anthropic"):
        if config.get("backend_url"):
            kwargs["base_url"] = config["backend_url"]
    
    # API Key 处理
    if provider_lower == "anthropic":
        if config.get("anthropic_api_key"):
            kwargs["api_key"] = config["anthropic_api_key"]
    elif provider_lower == "deepseek":
        if config.get("deepseek_api_key"):
            kwargs["api_key"] = config["deepseek_api_key"]
    elif provider_lower == "zhipu":
        if config.get("zhipu_api_key"):
            kwargs["api_key"] = config["zhipu_api_key"]
    elif provider_lower == "qwen":
        if config.get("qwen_api_key"):
            kwargs["api_key"] = config["qwen_api_key"]
    elif provider_lower == "wenxin":
        if config.get("wenxin_api_key"):
            kwargs["api_key"] = config["wenxin_api_key"]
    elif provider_lower == "spark":
        # 讯飞星火使用特殊的认证方式
        if config.get("spark_api_key"):
            kwargs["api_key"] = config["spark_api_key"]
        # app_id 作为额外参数传递（讯飞使用自定义参数）
    else:
        if config.get("openai_api_key"):
            kwargs["api_key"] = config["openai_api_key"]
    
    return llm_class(**{k: v for k, v in kwargs.items() if v is not None})


class TradingAgentsGraph:
    """Main class that orchestrates the trading agents framework."""

    def __init__(
        self,
        selected_analysts=["market", "social", "news", "fundamentals"],
        debug=False,
        config: Dict[str, Any] = None,
    ):
        """Initialize the trading agents graph and components.

        Args:
            selected_analysts: List of analyst types to include
            debug: Whether to run in debug mode
            config: Configuration dictionary. If None, uses default config
        """
        self.debug = debug
        self.config = config or DEFAULT_CONFIG

        # Update the interface's config
        set_config(self.config)

        # Create necessary directories
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        # Initialize LLMs (使用字典映射简化)
        self.deep_thinking_llm = _create_llm(
            self.config["llm_provider"],
            self.config["deep_think_llm"],
            self.config
        )
        self.quick_thinking_llm = _create_llm(
            self.config["llm_provider"],
            self.config["quick_think_llm"],
            self.config
        )
        
        self.toolkit = Toolkit(config=self.config)

        # Initialize memories
        self.bull_memory = FinancialSituationMemory("bull_memory", self.config)
        self.bear_memory = FinancialSituationMemory("bear_memory", self.config)
        self.trader_memory = FinancialSituationMemory("trader_memory", self.config)
        self.invest_judge_memory = FinancialSituationMemory("invest_judge_memory", self.config)
        self.risk_manager_memory = FinancialSituationMemory("risk_manager_memory", self.config)

        # Create tool nodes
        self.tool_nodes = self._create_tool_nodes()

        # Initialize components
        self.conditional_logic = ConditionalLogic()
        self.graph_setup = GraphSetup(
            self.quick_thinking_llm,
            self.deep_thinking_llm,
            self.toolkit,
            self.tool_nodes,
            self.bull_memory,
            self.bear_memory,
            self.trader_memory,
            self.invest_judge_memory,
            self.risk_manager_memory,
            self.conditional_logic,
        )

        self.propagator = Propagator()
        self.reflector = Reflector(self.quick_thinking_llm)
        self.signal_processor = SignalProcessor(self.quick_thinking_llm)

        # State tracking
        self.curr_state = None
        self.ticker = None
        self.log_states_dict = {}  # date to full state dict

        # Set up the graph
        self.graph = self.graph_setup.setup_graph(selected_analysts)

    def _create_tool_nodes(self) -> Dict[str, ToolNode]:
        """Create tool nodes for different data sources."""
        return {
            "market": ToolNode(
                [
                    # online tools
                    self.toolkit.get_YFin_data_online,
                    self.toolkit.get_stockstats_indicators_report_online,
                    # offline tools
                    self.toolkit.get_YFin_data,
                    self.toolkit.get_stockstats_indicators_report,
                ]
            ),
            "social": ToolNode(
                [
                    # online tools
                    self.toolkit.get_stock_news_openai,
                    # offline tools
                    self.toolkit.get_reddit_stock_info,
                ]
            ),
            "news": ToolNode(
                [
                    # online tools
                    self.toolkit.get_global_news_openai,
                    self.toolkit.get_google_news,
                    # offline tools
                    self.toolkit.get_finnhub_news,
                    self.toolkit.get_reddit_news,
                ]
            ),
            "fundamentals": ToolNode(
                [
                    # online tools
                    self.toolkit.get_fundamentals_openai,
                    # offline tools
                    self.toolkit.get_finnhub_company_insider_sentiment,
                    self.toolkit.get_finnhub_company_insider_transactions,
                    self.toolkit.get_simfin_balance_sheet,
                    self.toolkit.get_simfin_cashflow,
                    self.toolkit.get_simfin_income_stmt,
                ]
            ),
        }

    def propagate(self, company_name, trade_date):
        """Run the trading agents graph for a company on a specific date."""

        self.ticker = company_name

        # Initialize state
        init_agent_state = self.propagator.create_initial_state(
            company_name, trade_date
        )
        args = self.propagator.get_graph_args()

        if self.debug:
            # Debug mode with tracing
            trace = []
            for chunk in self.graph.stream(init_agent_state, **args):
                if len(chunk["messages"]) == 0:
                    pass
                else:
                    chunk["messages"][-1].pretty_print()
                    trace.append(chunk)

            final_state = trace[-1]
        else:
            # Standard mode without tracing
            final_state = self.graph.invoke(init_agent_state, **args)

        # Store current state for reflection
        self.curr_state = final_state

        # Log state
        self._log_state(trade_date, final_state)

        # Return decision and processed signal
        return final_state, self.process_signal(final_state["final_trade_decision"])

    def _log_state(self, trade_date, final_state):
        """Log the final state to a JSON file."""
        self.log_states_dict[str(trade_date)] = {
            "company_of_interest": final_state["company_of_interest"],
            "trade_date": final_state["trade_date"],
            "market_report": final_state["market_report"],
            "sentiment_report": final_state["sentiment_report"],
            "news_report": final_state["news_report"],
            "fundamentals_report": final_state["fundamentals_report"],
            "investment_debate_state": {
                "bull_history": final_state["investment_debate_state"]["bull_history"],
                "bear_history": final_state["investment_debate_state"]["bear_history"],
                "history": final_state["investment_debate_state"]["history"],
                "current_response": final_state["investment_debate_state"][
                    "current_response"
                ],
                "judge_decision": final_state["investment_debate_state"][
                    "judge_decision"
                ],
            },
            "trader_investment_decision": final_state["trader_investment_plan"],
            "risk_debate_state": {
                "risky_history": final_state["risk_debate_state"]["risky_history"],
                "safe_history": final_state["risk_debate_state"]["safe_history"],
                "neutral_history": final_state["risk_debate_state"]["neutral_history"],
                "history": final_state["risk_debate_state"]["history"],
                "judge_decision": final_state["risk_debate_state"]["judge_decision"],
            },
            "investment_plan": final_state["investment_plan"],
            "final_trade_decision": final_state["final_trade_decision"],
        }

        # Save to file
        directory = Path(f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/")
        directory.mkdir(parents=True, exist_ok=True)

        with open(
            f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/full_states_log_{trade_date}.json",
            "w",
        ) as f:
            json.dump(self.log_states_dict, f, indent=4)

    def reflect_and_remember(self, returns_losses):
        """Reflect on decisions and update memory based on returns."""
        self.reflector.reflect_bull_researcher(
            self.curr_state, returns_losses, self.bull_memory
        )
        self.reflector.reflect_bear_researcher(
            self.curr_state, returns_losses, self.bear_memory
        )
        self.reflector.reflect_trader(
            self.curr_state, returns_losses, self.trader_memory
        )
        self.reflector.reflect_invest_judge(
            self.curr_state, returns_losses, self.invest_judge_memory
        )
        self.reflector.reflect_risk_manager(
            self.curr_state, returns_losses, self.risk_manager_memory
        )

    def process_signal(self, full_signal):
        """Process a signal to extract the core decision."""
        return self.signal_processor.process_signal(full_signal)

