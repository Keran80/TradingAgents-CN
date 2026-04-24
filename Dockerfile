# ============================================
# 阶段1: 依赖构建器
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /build

# 安装构建依赖（编译 numpy, pandas, backtrader 等需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# 安装项目本身
COPY . .
RUN pip install --no-cache-dir --prefix=/install -e .

# ============================================
# 阶段2: 运行时
# ============================================
FROM python:3.12-slim AS runtime

LABEL maintainer="TradingAgents-CN"
LABEL description="TradingAgents-CN 量化交易系统"

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 创建非root用户
RUN groupadd -r tradingagents && \
    useradd -r -g tradingagents -m tradingagents

# 从builder阶段复制安装的包
COPY --from=builder /install /usr/local

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY --chown=tradingagents:tradingagents . .

# 创建必要的目录
RUN mkdir -p /app/logs /app/results /app/data && \
    chown -R tradingagents:tradingagents /app

# 切换到非root用户
USER tradingagents

# 暴露Streamlit端口
EXPOSE 8501

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8501/_stcore/health')" || exit 1

# 默认启动Streamlit
CMD ["streamlit", "run", "app_streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]
