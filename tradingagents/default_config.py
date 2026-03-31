import os

# 获取项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DEFAULT_CONFIG = {
    "project_dir": PROJECT_ROOT,
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", os.path.join(PROJECT_ROOT, "results")),
    "data_dir": os.getenv("TRADINGAGENTS_DATA_DIR", os.path.join(PROJECT_ROOT, "data")),
    "data_cache_dir": os.getenv(
        "TRADINGAGENTS_CACHE_DIR",
        os.path.join(PROJECT_ROOT, "dataflows", "data_cache")
    ),
    # LLM settings
    "llm_provider": os.getenv("TRADINGAGENTS_LLM_PROVIDER", "openai"),
    "deep_think_llm": os.getenv("TRADINGAGENTS_DEEP_LLM", "o4-mini"),
    "quick_think_llm": os.getenv("TRADINGAGENTS_QUICK_LLM", "gpt-4o-mini"),
    "backend_url": os.getenv("TRADINGAGENTS_BACKEND_URL", "https://api.openai.com/v1"),
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Tool settings
    "online_tools": True,
    # 数据源配置 (data_source: "tdx" | "akshare" | "auto")
    # tdx    = 通达信直连，速度最快，无需 API Key，适合实时交易场景
    # akshare = AkShare HTTP 数据源，数据更丰富（新闻/情绪/宏观）
    # auto   = 自动选择（优先 TDX，失败时回退 AkShare）
    "data_source": os.getenv("TRADINGAGENTS_DATA_SOURCE", "auto"),
    # 通达信服务器配置（auto 模式会自动选择最优服务器）
    "tdx_server": os.getenv("TRADINGAGENTS_TDX_SERVER", "auto"),
    "tdx_port": int(os.getenv("TRADINGAGENTS_TDX_PORT", "7709")),
    # API Key settings (支持环境变量覆盖)
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
    # 中国 LLM 提供商配置
    "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY", ""),
    "zhipu_api_key": os.getenv("ZHIPU_API_KEY", ""),
    "qwen_api_key": os.getenv("QWEN_API_KEY", ""),
    "wenxin_api_key": os.getenv("WENXIN_API_KEY", ""),
    "spark_api_key": os.getenv("SPARK_API_KEY", ""),
    "spark_app_id": os.getenv("SPARK_APP_ID", ""),
}


# 中国 LLM 提供商配置模板
CHINA_LLM_CONFIGS = {
    # DeepSeek (深度求索)
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model_map": {
            "deepseek-chat": "DeepSeek Chat",
            "deepseek-coder": "DeepSeek Coder",
        },
        "env_key": "DEEPSEEK_API_KEY",
    },
    # 智谱清言 (ZhipuAI)
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model_map": {
            "glm-4": "GLM-4",
            "glm-4-flash": "GLM-4 Flash",
            "glm-4-plus": "GLM-4 Plus",
            "glm-3-turbo": "GLM-3 Turbo",
        },
        "env_key": "ZHIPU_API_KEY",
    },
    # 通义千问 (Qwen/阿里云)
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model_map": {
            "qwen-turbo": "Qwen Turbo",
            "qwen-plus": "Qwen Plus",
            "qwen-max": "Qwen Max",
            "qwen-max-longcontext": "Qwen Max LongContext",
        },
        "env_key": "QWEN_API_KEY",
    },
    # 文心一言 (ERNIE/百度)
    "wenxin": {
        "base_url": "https://qianfan.baidubce.com/v2",
        "model_map": {
            "ernie-4.0-8k": "ERNIE-4.0-8K",
            "ernie-3.5-8k": "ERNIE-3.5-8K",
            "ernie-speed-8k": "ERNIE-Speed-8K",
            "ernie-speed-128k": "ERNIE-Speed-128K",
        },
        "env_key": "WENXIN_API_KEY",
    },
    # 讯飞星火 (Spark/科大讯飞)
    "spark": {
        "base_url": "https://spark-api.xf-yun.com/v3.5",
        "model_map": {
            "spark-v3.5": "Spark V3.5",
            "spark-v3.1": "Spark V3.1",
            "spark-v2.1": "Spark V2.1",
        },
        "env_key": "SPARK_API_KEY",
        "extra_config": "app_id",  # 需要额外的 app_id
    },
}

