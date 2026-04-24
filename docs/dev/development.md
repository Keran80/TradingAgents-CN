# 开发指南

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/your-org/TradingAgents-CN.git
cd TradingAgents-CN

# 安装开发依赖
pip install -e ".[dev]"

# 安装pre-commit hooks
pre-commit install
```

## 代码规范

### 格式化工具

- **ruff**: lint检查
- **mypy**: 类型检查
- **pytest**: 测试

### 运行检查

```bash
ruff check tradingagents/
mypy tradingagents/
pytest tests/ -v
```

## 提交代码

### 分支策略

- `main`: 稳定版本
- `develop`: 开发分支
- `feature/*`: 功能分支
- `fix/*`: 修复分支

### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：feat, fix, docs, style, refactor, test, chore

示例：

```
feat(backtest): 添加向量化回测引擎

实现基于numpy的向量化回测，性能提升10倍。

Closes #123
```

## 测试

### 运行测试

```bash
pytest tests/ -v
pytest tests/unit/ -v  # 只运行单元测试
pytest tests/integration/ -v  # 只运行集成测试
```

### 编写测试

```python
def test_backtest_config():
    config = BacktestConfig()
    assert config.initial_cash == 1000000.0


def test_backtest_engine():
    config = BacktestConfig(start_date="2024-01-01", end_date="2024-06-30")
    engine = BacktestEngine(config)
    engine.load_data("000001.SZ")
    result = engine.run()
    assert result.total_return > -1.0  # 亏损不超过100%
```

### 测试覆盖率

```bash
pytest --cov=tradingagents tests/
```

## 文档

### 构建API文档

```bash
cd docs
make html
```

### 文档位置

- `docs/`: 用户文档
- `docs/api/`: API参考
- `docs/dev/`: 开发文档
