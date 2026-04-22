# TradingAgents-CN 快速配置指南

## 1. 安装依赖

```bash
cd /tmp/TradingAgents-CN

# 使用 uv 安装依赖 (推荐使用 uv)
uv pip install pre-commit pytest-cov mkdocs mkdocs-material mkdocstrings[python]

# 或者使用 pip3
pip3 install pre-commit pytest-cov mkdocs mkdocs-material mkdocstrings[python]
```

## 2. 启用 pre-commit

```bash
# 安装 pre-commit hooks
pre-commit install
```

## 3. 提交并推送

```bash
# 添加更改
git add .

# 提交
git commit -m "优化项目结构：添加错误处理/依赖注入/配置管理，拆分大文件，配置 CI/CD"

# 推送到 GitHub (需要配置认证)
git push origin main
```

## 4. GitHub 认证配置

### 方法 1: 使用 SSH (推荐)
```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 添加公钥到 GitHub
# https://github.com/settings/keys

# 更改远程仓库为 SSH
git remote set-url origin git@github.com:YOUR_USERNAME/TradingAgents-CN.git

# 推送
git push origin main
```

### 方法 2: 使用 Personal Access Token
```bash
# 创建 Token: https://github.com/settings/tokens
# 权限：repo, workflow

# 推送时使用 Token
git push https://YOUR_TOKEN@github.com/YOUR_USERNAME/TradingAgents-CN.git main
```

### 方法 3: 配置 Git 凭据助手
```bash
# 配置凭据缓存 (15 分钟)
git config --global credential.helper cache

# 或配置凭据存储
git config --global credential.helper store

# 然后推送 (会提示输入一次用户名密码)
git push origin main
```

## 5. 验证 CI/CD

推送后访问:
```
https://github.com/YOUR_USERNAME/TradingAgents-CN/actions
```

查看 CI 运行状态。

## 6. 查看文档

```bash
# 本地预览文档
uv run mkdocs serve

# 或
pip3 install mkdocs mkdocs-material mkdocstrings[python]
mkdocs serve
```

访问 http://127.0.0.1:8000 查看文档站点。

## 7. 运行测试

```bash
# 运行测试并生成覆盖率报告
uv run pytest tests/ -v --cov=tradingagents --cov-report=html

# 查看覆盖率报告
# 打开 htmlcov/index.html
```

## 快速验证清单

- [ ] 依赖安装完成
- [ ] pre-commit hooks 安装完成
- [ ] Git 推送成功
- [ ] CI/CD 运行成功
- [ ] 测试全部通过
- [ ] 文档站点可访问

## 问题排查

### pip 未找到
使用 `uv pip` 或 `pip3` 代替 `pip`

### pre-commit 未找到
```bash
uv pip install pre-commit
```

### Git 推送认证失败
配置 SSH 密钥或 Personal Access Token

### 测试失败
```bash
uv run pytest tests/ -v
```

查看具体失败原因。
