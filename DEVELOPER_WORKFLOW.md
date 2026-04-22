# TradingAgents-CN 开发工作流程

## 🏁 快速开始

### 1. 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd TradingAgents-CN

# 启动开发环境
./start_development.sh
```

### 2. 日常开发流程
```bash
# 每天开始工作
./start_development.sh

# 创建功能分支
git checkout -b feat/your-feature-name

# 开发代码
# ... 编写代码 ...

# 运行测试
./run_tests.sh

# 提交代码
git add .
git commit -m "feat: 描述你的功能"

# 推送到远程
git push origin feat/your-feature-name
```

## 🔧 开发工具

### 代码质量工具
```bash
# 代码格式化
black .
isort .

# 类型检查
mypy .

# 代码规范检查
pylint tradingagents/

# 安全扫描
bandit -r tradingagents/
```

### 测试工具
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/test_specific.py -v

# 运行测试并生成覆盖率报告
pytest --cov=. --cov-report=html

# 运行性能测试
pytest tests/performance/ -v
```

### 文档工具
```bash
# 生成API文档
pdoc --html tradingagents --output-dir docs/api

# 本地预览文档
mkdocs serve

# 构建文档
mkdocs build
```

## 📁 项目结构

```
TradingAgents-CN/
├── tradingagents/          # 核心代码
│   ├── agents/            # 智能体
│   ├── data/              # 数据层
│   ├── events/            # 事件引擎
│   ├── plugins/           # 插件系统
│   └── utils/             # 工具函数
├── intelligent_phase1/    # 智能阶段1
├── intelligent_phase2/    # 智能阶段2
├── tests/                 # 测试代码
│   ├── unit/             # 单元测试
│   ├── integration/      # 集成测试
│   └── performance/      # 性能测试
├── docs/                  # 文档
├── scripts/              # 脚本
└── examples/             # 示例代码
```

## 🧪 测试策略

### 单元测试
- **位置**: `tests/unit/`
- **范围**: 单个函数或类
- **要求**: 快速、独立、可重复
- **工具**: pytest, unittest.mock

### 集成测试
- **位置**: `tests/integration/`
- **范围**: 多个模块交互
- **要求**: 测试真实数据流
- **工具**: pytest, docker-compose

### 性能测试
- **位置**: `tests/performance/`
- **范围**: 系统性能指标
- **要求**: 可重复的基准测试
- **工具**: pytest-benchmark

### 测试标记
```python
@pytest.mark.unit          # 单元测试
@pytest.mark.integration   # 集成测试  
@pytest.mark.performance   # 性能测试
@pytest.mark.slow          # 慢速测试
@pytest.mark.skip          # 跳过测试
```

## 📝 代码规范

### 命名约定
- **变量**: snake_case (`user_name`)
- **函数**: snake_case (`get_user_data`)
- **类**: PascalCase (`UserManager`)
- **常量**: UPPER_SNAKE_CASE (`MAX_RETRIES`)
- **私有**: 前导下划线 (`_internal_method`)

### 导入顺序
1. 标准库导入
2. 第三方库导入
3. 本地应用导入
4. 相对导入

### 类型提示
```python
from typing import List, Dict, Optional

def process_data(
    data: List[Dict[str, float]],
    threshold: Optional[float] = None
) -> Dict[str, float]:
    """处理数据并返回结果"""
    ...
```

### 文档字符串
```python
def calculate_metrics(data: List[float]) -> Dict[str, float]:
    """
    计算数据的统计指标。
    
    Args:
        data: 数值数据列表
        
    Returns:
        包含统计指标的字典:
        - mean: 平均值
        - std: 标准差
        - min: 最小值
        - max: 最大值
        
    Raises:
        ValueError: 如果数据为空
        
    Example:
        >>> calculate_metrics([1, 2, 3, 4, 5])
        {'mean': 3.0, 'std': 1.414, 'min': 1, 'max': 5}
    """
    ...
```

## 🔄 Git工作流

### 分支策略
- `main`: 生产代码
- `develop`: 开发分支
- `feature/*`: 功能开发
- `bugfix/*`: Bug修复
- `release/*`: 发布准备

### 提交规范
```
类型(范围): 描述

正文...

脚注...
```

**类型**:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具

**示例**:
```
feat(plugins): 添加新的数据源插件

- 实现TDX数据源适配器
- 添加数据缓存机制
- 更新相关文档

Closes #123
```

## 🚀 发布流程

### 1. 准备发布
```bash
# 更新版本号
bumpversion patch  # 或 minor, major

# 更新CHANGELOG.md
# 运行完整测试套件
./run_tests.sh

# 构建文档
mkdocs build
```

### 2. 创建发布
```bash
# 创建发布分支
git checkout -b release/v1.0.0

# 提交发布准备
git commit -m "chore: 准备v1.0.0发布"

# 创建标签
git tag -a v1.0.0 -m "版本1.0.0"

# 推送到远程
git push origin release/v1.0.0
git push origin v1.0.0
```

### 3. 合并到主分支
```bash
# 合并到main
git checkout main
git merge release/v1.0.0

# 合并到develop
git checkout develop
git merge release/v1.0.0

# 删除发布分支
git branch -d release/v1.0.0
```

## 🆘 常见问题

### 依赖安装失败
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用conda环境
conda create -n tradingagents python=3.10
conda activate tradingagents
```

### 测试失败
```bash
# 清理环境
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete

# 重新安装测试依赖
pip install -r requirements-test.txt --force-reinstall
```

### 文档生成问题
```bash
# 安装文档工具
pip install mkdocs pdoc

# 本地预览
mkdocs serve
```

## 📚 学习资源

### 项目相关
- [项目文档](docs/)
- [API参考](docs/api/)
- [示例代码](examples/)

### 技术栈
- [Python官方文档](https://docs.python.org/)
- [pytest文档](https://docs.pytest.org/)
- [Black代码格式化](https://black.readthedocs.io/)
- [MkDocs文档](https://www.mkdocs.org/)

### 最佳实践
- [Python代码风格指南](https://pep8.org/)
- [测试驱动开发](https://en.wikipedia.org/wiki/Test-driven_development)
- [持续集成](https://docs.github.com/en/actions)
