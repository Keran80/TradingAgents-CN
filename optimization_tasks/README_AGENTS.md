# TradingAgents-CN 代码优化 - 5 Agents 并行执行指南

## 快速启动

双击以下 5 个批处理文件，分别在 5 个独立的 Claude Code / Cursor / Windsurf 窗口中执行：

| Agent | 批处理文件 | 优先级 | 任务描述 |
|-------|-----------|--------|----------|
| Agent 1 | `start_agent_1_architecture.bat` | P0 | 重构 __init__.py 架构 |
| Agent 2 | `start_agent_2_strategy.bat` | P0 | 修复策略优化器逻辑 |
| Agent 3 | `start_agent_3_concurrency.bat` | P0 | 修复线程安全 |
| Agent 4 | `start_agent_4_refactor.bat` | P1 | 抽取基类消除重复 |
| Agent 5 | `start_agent_5_network.bat` | P1 | 修复 TCP 消息截断 |

## 执行步骤

1. **打开 5 个终端窗口**
   - 可以使用 Windows Terminal 或 PowerShell

2. **分别运行批处理文件**
   ```
   窗口1: 双击 start_agent_1_architecture.bat
   窗口2: 双击 start_agent_2_strategy.bat
   窗口3: 双击 start_agent_3_concurrency.bat
   窗口4: 双击 start_agent_4_refactor.bat
   窗口5: 双击 start_agent_5_network.bat
   ```

3. **复制提示词内容**
   - 每个批处理会显示对应的 prompt 文件内容
   - 将内容复制到 Claude Code / Cursor / Windsurf 的聊天窗口

4. **并行执行**
   - 5 个 agents 同时工作
   - 每个 agent 独立修改不同的文件，不会冲突

## 报告文件位置

每个 agent 完成后会在以下位置创建报告：

```
optimization_tasks/
├── report_agent_architecture_fix.md    (Agent 1)
├── report_agent_strategy_optimizer.md   (Agent 2)
├── report_agent_concurrency_expert.md   (Agent 3)
├── report_agent_code_refactor.md        (Agent 4)
└── report_agent_network_expert.md       (Agent 5)
```

## 优化路线图参考

详细修复方案见：`CODE_OPTIMIZATION_ROADMAP.md`

## 注意事项

- P0 级任务（Agent 1-3）优先执行
- P1 级任务（Agent 4-5）可以稍后执行
- 每个 agent 只修改分配给它的文件
- 修改前请确保已备份或代码已提交到 GitHub
