# 部署准备

## 环境要求
- Python 3.12+
- 内存: 2GB+
- 磁盘: 1GB+

## 部署步骤
1. 安装依赖: pip install -r requirements.txt
2. 运行测试: python -m pytest tests/
3. 启动服务: python src/main.py

## 配置文件
创建 .env 文件配置API密钥等参数

## 监控
- 健康检查: /health
- 性能指标: /metrics
- 日志文件: /var/log/tradingagents.log

## 更新时间
2026-04-10 09:09:40
