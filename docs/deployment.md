# 部署指南

## 开发环境

### 本地开发

```bash
git clone https://github.com/your-org/TradingAgents-CN.git
cd TradingAgents-CN
pip install -e ".[dev]"
pre-commit install
```

### Docker部署（计划中）

```bash
docker build -t tradingagents .
docker run -p 8501:8501 tradingagents
```

## 生产环境

### 环境变量配置

创建`.env.production`:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=<production_key>
LOG_LEVEL=WARNING
```

### 日志配置

系统使用标准Python logging，配置在`config.py`中。

日志级别说明：

- `DEBUG`: 开发调试，输出详细信息
- `INFO`: 生产环境默认级别，输出关键操作
- `WARNING`: 仅输出警告和错误
- `ERROR`: 仅输出错误信息

### 性能调优

1. 使用Redis缓存数据
2. 数据库连接池
3. 异步I/O优化

## CI/CD

项目使用GitHub Actions：

- **lint**: ruff代码检查
- **type**: mypy类型检查
- **test**: pytest单元测试

## 监控

### 应用监控

- 回测性能指标
- API调用延迟
- 错误率监控

### 日志聚合

日志输出到：

- 控制台（开发环境）
- 文件（生产环境）

日志文件位置：`logs/`目录
