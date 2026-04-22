# 测试覆盖率提升方案

**当前覆盖率**: 100.0%
**目标覆盖率**: 80%
**差距**: 0.0%

## 测试文件统计

- 现有测试文件：2522 个
- 核心模块：168 个
- 测试目录：296 个

## 优先级矩阵

| 优先级 | 模块 | 当前覆盖 | 目标覆盖 | 需补充测试 |
|--------|------|----------|----------|-----------|
| P0 | core/* | 低 | 90% | 高 |
| P0 | dataflows/* | 中 | 85% | 中 |
| P1 | strategies/* | 中 | 80% | 中 |
| P1 | backtest/* | 高 | 85% | 低 |
| P2 | dashboard/* | 低 | 70% | 中 |
| P2 | utils/* | 中 | 80% | 低 |

## 实施步骤

### 第 1 周：核心模块 (P0)
- [ ] core/engine.py - 添加单元测试
- [ ] core/config.py - 添加配置测试
- [ ] dataflows/interface.py - 添加接口测试

### 第 2 周：策略模块 (P1)
- [ ] strategies/builder/ - 添加构建器测试
- [ ] strategies/base.py - 添加基类测试

### 第 3 周：回测模块 (P1)
- [ ] backtest/engine.py - 添加回测测试
- [ ] backtest/analysis.py - 添加分析测试

### 第 4 周：UI 和工具 (P2)
- [ ] dashboard/ - 添加 UI 测试
- [ ] utils/ - 添加工具测试

## 测试模板

```python
# tests/core/test_engine.py
import pytest
from tradingagents.core import Engine

class TestEngine:
    """引擎测试"""
    
    def test_initialization(self):
        """测试初始化"""
        engine = Engine()
        assert engine is not None
    
    def test_start(self):
        """测试启动"""
        engine = Engine()
        engine.start()
        assert engine.is_running
    
    def test_stop(self):
        """测试停止"""
        engine = Engine()
        engine.start()
        engine.stop()
        assert not engine.is_running
```

## 工具配置

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --cov=tradingagents --cov-report=html
```

### 覆盖率报告
```bash
# 生成 HTML 报告
pytest --cov=tradingagents --cov-report=html

# 生成终端报告
pytest --cov=tradingagents --cov-report=term-missing

# 生成 XML (用于 CI)
pytest --cov=tradingagents --cov-report=xml
```

## 预期时间表

| 周次 | 目标 | 预期覆盖率 |
|------|------|-----------|
| 第 1 周 | P0 核心模块 | 60% |
| 第 2 周 | P1 策略模块 | 70% |
| 第 3 周 | P1 回测模块 | 75% |
| 第 4 周 | P2 UI 和工具 | 80% |
