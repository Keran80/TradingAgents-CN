# TradingAgents-CN 文档

欢迎使用 TradingAgents-CN 量化交易智能体系统！

## 简介

TradingAgents-CN 是一个基于多 Agent 协同的量化交易系统，支持 A 股、期货等多种交易品种。

## 核心特性

- 🤖 **多 Agent 协同** - Planner/Coder/Tester/Reviewer 协同工作
- 📊 **回测引擎** - 高性能回测，支持多种策略
- 📈 **实时数据** - 支持多种数据源
- 🔒 **风险控制** - 完善的风险管理
- 📱 **可视化** - 交互式 Dashboard

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行回测
python -m tradingagents backtest --strategy momentum

# 启动 Dashboard
python -m tradingagents dashboard
```

## 文档导航

- [快速开始](quickstart.md) - 5 分钟上手
- [安装指南](installation.md) - 详细安装步骤
- [API 参考](api/core.md) - 完整 API 文档
- [开发指南](dev/architecture.md) - 架构设计和贡献指南

## 社区

- GitHub: https://github.com/TradingAgents-CN/TradingAgents-CN
- 问题反馈：https://github.com/TradingAgents-CN/TradingAgents-CN/issues
