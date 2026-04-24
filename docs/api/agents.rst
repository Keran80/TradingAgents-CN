Agent 系统 API
===============

.. module:: tradingagents.agents

多Agent协作分析系统，支持市场分析、辩论、交易决策和风险评估。

快速开始
--------

.. code-block:: python

    from tradingagents.agents.base import BaseAgent, AgentConfig, AgentRole
    
    # 创建配置
    config = AgentConfig(
        name="Market Analyst",
        role=AgentRole.MARKET_ANALYST,
        agent_type=AgentType.ANALYST,
        description="技术分析专家",
        system_prompt="你是技术分析专家..."
    )
    
    # 创建 Agent
    agent = MyAgent(config)
    agent.set_llm_client(client)
    
    # 运行
    result = await agent.run({"stock_code": "000001.SZ"})

基础类
------

BaseAgent
~~~~~~~~~

.. autoclass:: tradingagents.agents.base.BaseAgent
   :members:
   :undoc-members:
   :special-members: __init__

AgentRole
~~~~~~~~~

.. autoclass:: tradingagents.agents.base.AgentRole
   :members:
   :undoc-members:
   :member-order: bysource

AgentType
~~~~~~~~~

.. autoclass:: tradingagents.agents.base.AgentType
   :members:
   :undoc-members:
   :member-order: bysource

Decision
~~~~~~~~

.. autoclass:: tradingagents.agents.base.Decision
   :members:
   :undoc-members:
   :member-order: bysource

数据类
------

AgentConfig
~~~~~~~~~~~

.. autoclass:: tradingagents.agents.base.AgentConfig
   :members:
   :undoc-members:
   :special-members: __init__

AnalysisResult
~~~~~~~~~~~~~~

.. autoclass:: tradingagents.agents.base.AnalysisResult
   :members:
   :undoc-members:
   :special-members: __init__

DebateResult
~~~~~~~~~~~~

.. autoclass:: tradingagents.agents.base.DebateResult
   :members:
   :undoc-members:
   :special-members: __init__

TradingDecision
~~~~~~~~~~~~~~~

.. autoclass:: tradingagents.agents.base.TradingDecision
   :members:
   :undoc-members:
   :special-members: __init__

RiskAssessment
~~~~~~~~~~~~~~

.. autoclass:: tradingagents.agents.base.RiskAssessment
   :members:
   :undoc-members:
   :special-members: __init__

工具函数
--------

build_context_situation
~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: tradingagents.agents.utils.agent_utils.build_context_situation

format_memories
~~~~~~~~~~~~~~~

.. autofunction:: tradingagents.agents.utils.agent_utils.format_memories

Toolkit
~~~~~~~

.. autoclass:: tradingagents.agents.utils.agent_utils.Toolkit
   :members:
   :undoc-members:
   :special-members: __init__

预定义角色配置
--------------

系统预定义了 ``ROLE_CONFIGS`` 字典，包含所有标准角色的配置：

- ``AgentRole.MARKET_ANALYST`` - 市场技术分析
- ``AgentRole.FUNDAMENTALS_ANALYST`` - 基本面分析
- ``AgentRole.NEWS_ANALYST`` - 新闻分析
- ``AgentRole.SENTIMENT_ANALYST`` - 情绪分析
- ``AgentRole.BULL_ARGUMENT`` - 多头观点
- ``AgentRole.BEAR_ARGUMENT`` - 空头观点
- ``AgentRole.RESEARCH_MANAGER`` - 研究经理
- ``AgentRole.TRADER`` - 交易员
- ``AgentRole.AGGRESSIVE_RISK`` - 激进风险评估
- ``AgentRole.CONSERVATIVE_RISK`` - 保守风险评估
- ``AgentRole.NEUTRAL_RISK`` - 中性风险评估
- ``AgentRole.RISK_MANAGER`` - 风险管理经理

使用示例：

.. code-block:: python

    from tradingagents.agents.base import ROLE_CONFIGS, AgentRole
    
    # 获取预定义配置
    config = ROLE_CONFIGS[AgentRole.MARKET_ANALYST]
    agent = MyAgent(config)
