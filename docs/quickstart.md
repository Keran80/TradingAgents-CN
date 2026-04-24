# 快速开始

## 前置要求

- Python 3.10+
- pip/uv包管理器
- Git

## 安装步骤

### 方式1：使用pip

```bash
git clone https://github.com/your-org/TradingAgents-CN.git
cd TradingAgents-CN
pip install -e .
pip install -r requirements.txt
```

### 方式2：使用uv（推荐）

```bash
uv sync
```

## 快速配置

### 1. 复制环境模板

```bash
cp .env.example .env
```

### 2. 配置API密钥

编辑`.env`文件，填入你的智谱AI API密钥：

```env
OPENAI_API_KEY=your_api_key_here
ZHIPU_API_KEY=your_api_key_here
```

**获取API密钥**：访问 [智谱AI开放平台](https://open.bigmodel.cn/)

## 运行项目

### 方式1：Streamlit Web界面

```bash
streamlit run app_streamlit.py
```

启动后访问 `http://localhost:8501` 查看Web界面。

### 方式2：CLI命令行

```bash
python main.py --ticker 000001.SZ
```

### 方式3：Python API

```python
from tradingagents.backtest import BacktestEngine, BacktestConfig

config = BacktestConfig(
    start_date="2024-01-01",
    end_date="2024-06-30",
    initial_cash=1000000
)

engine = BacktestEngine(config)
engine.load_data("000001.SZ")
result = engine.run()
print(result.to_dict())
```

## 项目结构

```
TradingAgents-CN/
├── tradingagents/          # 核心库
│   ├── backtest/          # 回测引擎
│   ├── agents/            # Agent系统
│   ├── dataflows/         # 数据接口
│   ├── strategies/        # 策略系统
│   └── ...
├── tests/                  # 测试
├── docs/                   # 文档
└── app_streamlit.py        # Web界面
```

## 下一步

- 📖 阅读 [架构设计](dev/architecture.md) 了解系统架构
- 🔧 阅读 [开发指南](dev/development.md) 参与开发
- 📚 查看 [API参考](api/index.rst) 了解API细节
