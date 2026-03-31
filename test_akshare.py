"""
A股分析测试脚本
使用智谱AI + AkShare
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.graph.trading_graph import TradingAgentsGraph

# 读取环境变量
from dotenv import load_dotenv
load_dotenv()

# 创建自定义配置（使用智谱AI）
config = {
    # 项目路径
    "project_dir": os.path.dirname(os.path.abspath(__file__)),
    
    # LLM 配置 - 智谱AI (OpenAI兼容格式)
    "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
    "deep_think_llm": os.getenv("DEEP_THINK_LLM", "glm-4-flash"),
    "quick_think_llm": os.getenv("QUICK_THINK_LLM", "glm-4-flash"),
    "backend_url": os.getenv("BACKEND_URL", "https://open.bigmodel.cn/api/paas/v4"),
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    
    # 分析设置
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 50,
    
    # 工具设置
    "online_tools": True,
    
    # 结果保存
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
}

# 打印配置信息
print("=" * 50)
print("TradingAgents-CN A股分析测试")
print("=" * 50)
print(f"LLM Provider: {config['llm_provider']}")
print(f"Model: {config['deep_think_llm']}")
print(f"Backend: {config['backend_url']}")
print(f"API Key: {config['openai_api_key'][:20]}..." if config['openai_api_key'] else "API Key: 未设置")
print("=" * 50)

# 初始化 TradingAgents
print("\n正在初始化 TradingAgents...")
ta = TradingAgentsGraph(debug=True, config=config)

# 测试分析A股股票 - 平安银行 (000001)
# 使用最近的交易日
ticker = "000001"
analysis_date = "2026-03-28"

print(f"\n开始分析: {ticker} (平安银行)")
print(f"分析日期: {analysis_date}")
print("-" * 50)

try:
    _, decision = ta.propagate(ticker, analysis_date)
    print("\n" + "=" * 50)
    print("分析结果:")
    print("=" * 50)
    print(decision)
except Exception as e:
    print(f"\n分析出错: {e}")
    import traceback
    traceback.print_exc()
