# TradingAgents-CN 中国 LLM 使用指南

## 概述

TradingAgents-CN 已全面支持中国主流 LLM 提供商，包括 DeepSeek、智谱清言、通义千问、文心一言和讯飞星火。这些提供商都通过 OpenAI 兼容 API 提供服务，国内访问稳定，价格相对优惠。

## 支持的 LLM 提供商

### 1. DeepSeek（深度求索）
- **官网**: https://platform.deepseek.com
- **API 文档**: https://help.deepseek.com/zh/api
- **模型**: deepseek-chat（推荐）, deepseek-coder
- **特点**: 性价比高，支持长上下文，代码能力强
- **价格**: 约 $0.14/1M tokens（输入）

### 2. 智谱清言（ZhipuAI）
- **官网**: https://open.bigmodel.cn
- **模型**: glm-4（推荐）, glm-4-flash, glm-4-plus, glm-3-turbo
- **特点**: 清华技术背景，中文理解能力强
- **价格**: glm-4-flash 免费，glm-4 约 ¥1/1M tokens

### 3. 通义千问（Qwen/阿里云）
- **官网**: https://dashscope.console.aliyun.com
- **模型**: qwen-plus（推荐）, qwen-turbo, qwen-max
- **特点**: 阿里云背书，生态丰富
- **价格**: qwen-turbo 约 ¥0.002/1K tokens

### 4. 文心一言（ERNIE/百度）
- **官网**: https://console.baiducloud.com
- **模型**: ernie-3.5-8k（推荐）, ernie-speed-8k
- **特点**: 百度技术积累，搜索增强
- **价格**: 约 ¥0.012/1K tokens

### 5. 讯飞星火（Spark）
- **官网**: https://console.xfyun.cn
- **模型**: spark-v3.5（推荐）, spark-v3.1
- **特点**: 语音技术领先，多方言支持
- **价格**: 约 ¥0.032/1K tokens

## 快速配置

### 方式一：环境变量配置（推荐）

```bash
# 设置 API Key
export DEEPSEEK_API_KEY="your-deepseek-api-key"
export ZHIPU_API_KEY="your-zhipu-api-key"
export QWEN_API_KEY="your-qwen-api-key"
export WENXIN_API_KEY="your-wenxin-api-key"
export SPARK_API_KEY="your-spark-api-key"

# 选择 LLM 提供商
export TRADINGAGENTS_LLM_PROVIDER="deepseek"
export TRADINGAGENTS_DEEP_LLM="deepseek-chat"
export TRADINGAGENTS_QUICK_LLM="deepseek-chat"
```

### 方式二：代码配置

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# 方式 1: DeepSeek
config = DEFAULT_CONFIG.copy()
config.update({
    "llm_provider": "deepseek",
    "deep_think_llm": "deepseek-chat",
    "quick_think_llm": "deepseek-chat",
    "deepseek_api_key": "your-api-key",
})

ta = TradingAgentsGraph(debug=True, config=config)

# 方式 2: 智谱清言
config = DEFAULT_CONFIG.copy()
config.update({
    "llm_provider": "zhipu",
    "deep_think_llm": "glm-4",
    "quick_think_llm": "glm-4-flash",
    "zhipu_api_key": "your-api-key",
})

# 方式 3: 通义千问
config = DEFAULT_CONFIG.copy()
config.update({
    "llm_provider": "qwen",
    "deep_think_llm": "qwen-plus",
    "quick_think_llm": "qwen-turbo",
    "qwen_api_key": "your-api-key",
})

# 方式 4: 文心一言
config = DEFAULT_CONFIG.copy()
config.update({
    "llm_provider": "wenxin",
    "deep_think_llm": "ernie-3.5-8k",
    "quick_think_llm": "ernie-speed-8k",
    "wenxin_api_key": "your-api-key",
})

# 方式 5: 讯飞星火
config = DEFAULT_CONFIG.copy()
config.update({
    "llm_provider": "spark",
    "deep_think_llm": "spark-v3.5",
    "quick_think_llm": "spark-v3.5",
    "spark_api_key": "your-api-key",
})
```

## 使用示例

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# 配置 DeepSeek
config = DEFAULT_CONFIG.copy()
config.update({
    "llm_provider": "deepseek",
    "deep_think_llm": "deepseek-chat",
    "quick_think_llm": "deepseek-chat",
    "deepseek_api_key": "your-key",
    "online_tools": True,  # 启用在线工具获取实时数据
})

# 初始化
ta = TradingAgentsGraph(debug=True, config=config)

# 分析股票
result, decision = ta.propagate("600519", "2026-03-29")
print(f"决策: {decision}")
```

## API Key 获取方式

### DeepSeek
1. 访问 https://platform.deepseek.com
2. 注册/登录账号
3. 进入「API Keys」创建新密钥
4. 充值后即可使用

### 智谱清言
1. 访问 https://open.bigmodel.cn
2. 注册/登录
3. 进入「API Keys」创建
4. 充值后使用

### 通义千问
1. 访问 https://dashscope.console.aliyun.com
2. 开通模型服务
3. 创建 API Key
4. 按量付费

### 文心一言
1. 访问 https://console.baiducloud.com
2. 开通千帆大模型平台
3. 创建应用获取 API Key
4. 计费模式

### 讯飞星火
1. 访问 https://console.xfyun.cn
2. 开通星火认知大模型
3. 创建 API Key 和 APP ID
4. 按调用量计费

## 模型选择建议

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| 快速测试 | qwen-turbo / glm-4-flash | 免费或低价 |
| 综合分析 | deepseek-chat / glm-4 | 性价比高 |
| 深度研究 | qwen-max / deepseek-chat | 能力强 |
| 中文优化 | glm-4 / ernie-3.5 | 中文理解好 |

## 注意事项

1. **API Key 安全**: 不要将 API Key 提交到公开仓库
2. **额度监控**: 定期检查 API 使用量，避免超额
3. **网络访问**: 国内 LLM 无需代理，直连即可
4. **模型版本**: 关注模型更新，选择稳定版本
5. **并发限制**: 遵守各平台的 QPS 限制
