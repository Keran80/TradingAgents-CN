# TradingAgents-CN 部署指南

## 部署方式

### 方式 1: Docker 部署 (推荐)

```bash
# 构建并启动
cd docker
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

**访问地址**:
- Dashboard: http://localhost:8501
- API: http://localhost:8000

### 方式 2: 直接部署

```bash
# 安装依赖
pip install -e .

# 启动 Dashboard
streamlit run app_streamlit.py

# 启动 API
python web_api.py
```

### 方式 3: 开发环境部署

```bash
# 创建虚拟环境
uv venv
source .venv/bin/activate

# 安装依赖
uv pip install -e .

# 启动开发服务器
streamlit run app_streamlit.py --server.port 8501
```

## 生产环境配置

### 环境变量

```bash
# 复制生产配置
cp .env.production .env

# 编辑配置
vim .env
```

### 关键配置项

- `ENV=production` - 生产环境
- `DEBUG=False` - 关闭调试模式
- `LOG_LEVEL=WARNING` - 日志级别
- `SECRET_KEY` - 安全密钥 (必须修改)

## 监控和维护

### 健康检查

```bash
curl http://localhost:8000/api/v1/health
```

### 日志查看

```bash
# Docker 日志
docker-compose logs -f

# 系统日志
tail -f logs/app.log
```

### 性能监控

- CPU 使用率
- 内存使用率
- 请求响应时间
- 错误率

## 备份和恢复

### 数据备份

```bash
# 备份数据库
pg_dump tradingagents > backup.sql

# 备份日志
tar -czf logs-backup.tar.gz logs/
```

### 数据恢复

```bash
# 恢复数据库
psql tradingagents < backup.sql
```

---

*部署指南版本：1.0.0*
*最后更新：2026-04-13*
