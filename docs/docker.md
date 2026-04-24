# Docker 部署指南

## 快速开始

### 1. 构建镜像

```bash
docker build -t tradingagents:latest .
```

### 2. 运行容器

```bash
# 准备环境文件
cp .env.example .env
# 编辑 .env 填入API密钥

# 运行容器
docker run -d \
  --name tradingagents \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  tradingagents:latest
```

### 3. 访问应用

打开浏览器访问：http://localhost:8501

## Docker Compose

### 基础模式（仅应用）

```bash
docker-compose up -d
```

### 完整模式（应用+Redis）

```bash
docker-compose --profile full up -d
```

### 停止服务

```bash
docker-compose down
```

## 镜像优化

### 镜像大小

多阶段构建将镜像从 ~2GB 减少到 ~500MB。

### 构建缓存

使用BuildKit加速构建：

```bash
export DOCKER_BUILDKIT=1
docker build -t tradingagents .
```

## 生产部署

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| LLM_PROVIDER | LLM提供商 | openai |
| OPENAI_API_KEY | API密钥 | - |
| LOG_LEVEL | 日志级别 | INFO |
| STREAMLIT_SERVER_PORT | 端口 | 8501 |

### 数据持久化

挂载以下目录：
- `/app/data` - 数据文件
- `/app/results` - 分析结果
- `/app/logs` - 日志文件

### 健康检查

容器内置健康检查，30秒间隔检查应用状态。

## 故障排查

### 查看日志

```bash
docker logs -f tradingagents
```

### 进入容器

```bash
docker exec -it tradingagents bash
```

### 重新构建

```bash
docker build --no-cache -t tradingagents:latest .
```
