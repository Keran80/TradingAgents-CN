# 贡献指南

欢迎为 TradingAgents-CN 项目做出贡献！本指南将帮助您了解如何参与项目开发。

## 开发环境设置

### 1. 克隆仓库
```bash
git clone https://github.com/your-org/TradingAgents-CN.git
cd TradingAgents-CN
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
pip install -r requirements-test.txt  # 测试依赖
```

### 3. 设置开发环境
```bash
# 安装预提交钩子
pre-commit install

# 运行测试确保环境正常
./run_tests.sh
```

## 代码规范

### Python 代码风格
- 遵循 PEP 8 规范
- 使用 Black 进行代码格式化
- 使用 isort 进行导入排序
- 类型提示：尽可能使用类型注解

### 提交规范
- 提交信息使用 Conventional Commits 格式
- 示例：`feat: 添加新的数据源适配器`
- 类型：feat, fix, docs, style, refactor, test, chore

## 开发流程

### 1. 创建分支
```bash
git checkout -b feat/your-feature-name
```

### 2. 开发与测试
- 编写代码
- 添加或更新测试
- 运行测试确保通过
- 更新文档（如有需要）

### 3. 提交代码
```bash
git add .
git commit -m "feat: 描述你的功能"
```

### 4. 创建 Pull Request
- 在 GitHub 上创建 PR
- 描述变更内容
- 关联相关 Issue
- 等待代码审查

## 测试要求

### 单元测试
- 新功能必须包含单元测试
- 测试覆盖率不应降低
- 使用 pytest 框架

### 集成测试
- 涉及多个模块的功能需要集成测试
- 测试真实的数据流和交互

## 文档要求

### 代码文档
- 公共函数和类必须有文档字符串
- 使用 Google 风格文档字符串
- 示例代码应可运行

### API 文档
- 新增 API 必须更新 API 文档
- 提供使用示例

## 问题反馈

### 报告 Bug
1. 在 Issues 中搜索是否已存在
2. 创建新的 Issue
3. 提供复现步骤和环境信息

### 功能请求
1. 描述功能需求和使用场景
2. 讨论技术实现方案
3. 等待核心团队评估

## 行为准则

- 尊重所有贡献者
- 建设性的代码审查
- 遵守开源社区规范

感谢您的贡献！🎉
