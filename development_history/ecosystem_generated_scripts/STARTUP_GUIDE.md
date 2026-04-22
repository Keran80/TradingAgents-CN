# TradingAgents-CN 项目启动指南

## 🚀 快速启动（推荐）

### 方法 1：使用快速启动脚本
```bash
cd /tmp/TradingAgents-CN
chmod +x quick_start.sh
./quick_start.sh
```

**选择启动方式**：
1. **Streamlit 仪表板** (推荐) - 可视化界面
2. **Web API** - RESTful API 服务
3. **CLI 命令行** - 命令行工具
4. **Python 脚本测试** - 测试脚本
5. **运行测试套件** - 运行所有测试

### 方法 2：直接启动 Streamlit 仪表板
```bash
cd /tmp/TradingAgents-CN
uv run streamlit run app_streamlit.py
```

访问：http://localhost:8501

## 🛠️ 开发环境启动

### 方法 1：开发启动脚本
```bash
cd /tmp/TradingAgents-CN
chmod +x start_development.sh
./start_development.sh
```

### 方法 2：手动启动开发环境
```bash
cd /tmp/TradingAgents-CN

# 1. 激活虚拟环境
source .venv/bin/activate

# 2. 安装依赖
uv pip install -e .

# 3. 启动 Streamlit
streamlit run app_streamlit.py
```

## 📊 不同启动方式详解

### 1. **Streamlit 仪表板** (推荐)
- **文件**: `app_streamlit.py`
- **功能**: 可视化股票分析、AI 分析结论、数据可视化
- **特点**: 交互式界面，适合日常使用
- **启动**: `uv run streamlit run app_streamlit.py`

### 2. **Web API 服务**
- **文件**: `web_api.py`
- **功能**: RESTful API 接口，支持程序化调用
- **特点**: 适合集成到其他系统
- **启动**: `uv run python web_api.py`

### 3. **CLI 命令行工具**
- **文件**: `main.py`
- **功能**: 命令行股票分析、回测、数据获取
- **特点**: 适合脚本化操作
- **启动**: `uv run python main.py --help`

### 4. **回测引擎**
- **文件**: `analyze_backtest_engine.py`
- **功能**: 量化策略回测分析
- **特点**: 专业量化分析
- **启动**: `uv run python analyze_backtest_engine.py`

## 🔧 环境准备

### 检查环境
```bash
# 检查 Python 版本
python3 --version

# 检查 uv 是否安装
uv --version

# 检查项目依赖
uv pip list | grep tradingagents
```

### 安装依赖
```bash
# 如果未安装依赖
cd /tmp/TradingAgents-CN
uv pip install -e .
```

## 📈 功能模块

### 核心功能
1. **股票数据获取** - A 股、港股、美股
2. **AI 分析结论** - 智能股票分析
3. **量化回测** - 策略回测引擎
4. **风险管理** - 风险监控系统
5. **数据可视化** - 图表展示

### 智能模块
1. **AI 策略扩展** - 机器学习趋势预测
2. **多数据源适配** - 股票、期货、基金
3. **高级风险监控** - 实时风险预警

## 🧪 测试启动

### 运行测试
```bash
# 运行所有测试
./run_tests.sh

# 运行智能测试
./run_smart_tests.sh

# 运行快速测试
./run_quick_tests.sh
```

### 验证项目
```bash
# 验证项目结构
./validate_cicd.sh

# 验证测试框架
./verify_test_framework.sh
```

## 🚨 常见问题

### 问题 1：依赖安装失败
```bash
# 清理并重新安装
rm -rf .venv
uv venv
uv pip install -e .
```

### 问题 2：Streamlit 启动失败
```bash
# 检查端口占用
lsof -i :8501

# 使用不同端口
streamlit run app_streamlit.py --server.port 8502
```

### 问题 3：缺少数据源
```bash
# 安装 akshare
uv pip install akshare

# 测试数据源
uv run python test_akshare.py
```

## 📞 技术支持

### 项目状态
- **版本**: 最新稳定版
- **测试状态**: 46/46 测试通过 (100%)
- **AI 分析结论**: ✅ 已修复动态生成
- **依赖管理**: ✅ uv 虚拟环境

### 获取帮助
1. 查看 `README.md` - 项目文档
2. 查看 `INSTALL_DEPLOY_START_GUIDE.md` - 详细安装指南
3. 运行 `./quick_start.sh` - 交互式启动向导

---

**启动命令总结**：
```bash
# 最简单的方式
cd /tmp/TradingAgents-CN
./quick_start.sh

# 或直接启动仪表板
uv run streamlit run app_streamlit.py
```

项目已准备就绪，请选择适合您的启动方式！ 🚀
