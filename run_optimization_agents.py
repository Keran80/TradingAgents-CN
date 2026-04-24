#!/usr/bin/env python3
"""
TradingAgents-CN 代码优化任务执行脚本
并行启动多个优化 agents 进行代码修复
"""

import subprocess
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# 项目根目录 - 自动检测
PROJECT_ROOT = Path(__file__).resolve().parent
OPTIMIZATION_DIR = PROJECT_ROOT / "optimization_tasks"

# 任务定义
TASKS = [
    {
        "name": "Agent-Architecture-Fix",
        "description": "架构修复 - 重构 __init__.py",
        "files": ["tradingagents/__init__.py"],
        "priority": "P0",
        "estimated_time": "2h"
    },
    {
        "name": "Agent-Strategy-Optimizer", 
        "description": "策略优化 - 修复买入逻辑和性能",
        "files": ["tradingagents/strategies/optimizer.py", "tradingagents/strategies/templates.py"],
        "priority": "P0",
        "estimated_time": "3h"
    },
    {
        "name": "Agent-Concurrency-Expert",
        "description": "并发安全 - 修复线程安全和异常处理",
        "files": ["tradingagents/dataflows/cache.py", "tradingagents/distributed/isolator.py"],
        "priority": "P0",
        "estimated_time": "2h"
    },
    {
        "name": "Agent-Code-Refactor",
        "description": "代码重构 - 抽取基类消除重复",
        "files": ["tradingagents/agents/analysts/__init__.py", "tradingagents/agents/debate/__init__.py"],
        "priority": "P1",
        "estimated_time": "4h"
    },
    {
        "name": "Agent-Network-Expert",
        "description": "网络通信 - 修复 TCP 消息截断",
        "files": ["tradingagents/distributed/rpc.py"],
        "priority": "P1",
        "estimated_time": "3h"
    }
]

def create_agent_prompt(task: dict) -> str:
    """为每个 agent 创建详细的任务提示词"""
    prompt = f"""# {task['name']} 任务指令

## 任务描述
{task['description']}

## 目标文件
{chr(10).join(f"- {f}" for f in task['files'])}

## 优先级
{task['priority']}

## 详细要求
请阅读以下文档获取完整的修复方案：
1. 优化路线图: {PROJECT_ROOT}/CODE_OPTIMIZATION_ROADMAP.md
2. 任务分配: {PROJECT_ROOT}/optimization_tasks/task_assignment.md

## 执行步骤
1. 阅读目标文件，理解当前代码
2. 根据路线图中的修复方案进行修改
3. 确保修改后的代码能通过基本语法检查
4. 创建修改报告

## 报告要求
请在完成后创建报告文件：
{OPTIMIZATION_DIR}/report_{task['name'].lower().replace('-', '_')}.md

报告内容应包括：
- 修复的问题列表
- 修改的文件清单  
- 关键代码变更
- 验证结果

## 注意事项
- 保持向后兼容
- 添加必要的注释
- 遵循 PEP8 规范
"""
    return prompt

def run_agent(task: dict) -> dict:
    """运行单个 agent 任务"""
    print(f"\n{'='*60}")
    print(f"启动: {task['name']}")
    print(f"描述: {task['description']}")
    print(f"优先级: {task['priority']}")
    print(f"预计时间: {task['estimated_time']}")
    print(f"{'='*60}\n")
    
    # 创建 agent 提示词文件
    prompt_file = OPTIMIZATION_DIR / f"prompt_{task['name'].lower().replace('-', '_')}.md"
    prompt_file.write_text(create_agent_prompt(task), encoding='utf-8')
    
    print(f"提示词已保存: {prompt_file}")
    print(f"请将此提示词交给 Claude Code 或其他 coding agent 执行\n")
    
    return {
        "task": task,
        "prompt_file": str(prompt_file),
        "status": "prompt_created"
    }

def main():
    """主函数 - 并行启动所有 agents"""
    print("""
============================================================
     TradingAgents-CN 代码优化任务分发系统

  发现问题: 34 个 (P0: 5, P1: 8, P2/P3: 21)
  任务数量: 5 个并行任务
============================================================
""")
    
    # 创建优化任务目录
    OPTIMIZATION_DIR.mkdir(exist_ok=True)
    
    # 按优先级分组
    p0_tasks = [t for t in TASKS if t['priority'] == 'P0']
    p1_tasks = [t for t in TASKS if t['priority'] == 'P1']
    
    print(f"\n[Phase 1] P0 级任务 (必须修复): {len(p0_tasks)} 个")
    for task in p0_tasks:
        print(f"   - {task['name']}: {task['description']}")
    
    print(f"\n[Phase 2] P1 级任务 (强烈建议): {len(p1_tasks)} 个")
    for task in p1_tasks:
        print(f"   - {task['name']}: {task['description']}")
    
    # 并行执行所有任务（创建提示词）
    print("\n" + "="*60)
    print("开始创建 Agent 任务提示词...")
    print("="*60 + "\n")
    
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(run_agent, task): task for task in TASKS}
        
        for future in as_completed(futures):
            task = futures[future]
            try:
                result = future.result()
                results.append(result)
                print(f"[OK] {task['name']} 提示词已创建")
            except Exception as e:
                print(f"[FAIL] {task['name']} 失败: {e}")
    
    # 生成汇总报告
    print("\n" + "="*60)
    print("任务分发完成！")
    print("="*60 + "\n")
    
    print("[文件] 生成的文件:")
    print(f"   优化路线图: {PROJECT_ROOT}/CODE_OPTIMIZATION_ROADMAP.md")
    print(f"   任务分配: {PROJECT_ROOT}/optimization_tasks/task_assignment.md")
    print(f"   Agent 提示词目录: {OPTIMIZATION_DIR}/")
    
    print("\n[下一步] 操作指南:")
    print("   1. 打开 5 个独立的 Claude Code / Cursor / Windsurf 窗口")
    print("   2. 将对应的 prompt_*.md 文件内容复制给每个 agent")
    print("   3. 各 agent 并行执行修复任务")
    print("   4. 完成后查看 optimization_tasks/report_*.md 报告")
    
    print("\n[优先级] 任务安排:")
    print("   Phase 1 (Week 1): P0 级任务 - 架构、策略、并发安全")
    print("   Phase 2 (Week 2): P1 级任务 - 代码重构、网络通信")
    print("   Phase 3 (Week 3): 集成验证和性能测试")
    
    # 创建执行脚本
    create_execution_scripts()
    
    print("\n[完成] 所有任务提示词已准备就绪！")

def create_execution_scripts():
    """创建便捷的执行脚本"""
    
    # Windows PowerShell 脚本
    ps_script = OPTIMIZATION_DIR / "run_all_agents.ps1"
    ps_script.write_text('''# TradingAgents-CN 代码优化 - 批量启动 Agents
# 用法: powershell -ExecutionPolicy Bypass -File run_all_agents.ps1

$tasks = @(
    @{Name="Agent-Architecture-Fix"; Prompt="prompt_agent_architecture_fix.md"},
    @{Name="Agent-Strategy-Optimizer"; Prompt="prompt_agent_strategy_optimizer.md"},
    @{Name="Agent-Concurrency-Expert"; Prompt="prompt_agent_concurrency_expert.md"},
    @{Name="Agent-Code-Refactor"; Prompt="prompt_agent_code_refactor.md"},
    @{Name="Agent-Network-Expert"; Prompt="prompt_agent_network_expert.md"}
)

Write-Host "TradingAgents-CN 代码优化任务" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

foreach ($task in $tasks) {
    Write-Host "`n任务: $($task.Name)" -ForegroundColor Yellow
    Write-Host "提示词文件: $($task.Prompt)" -ForegroundColor Gray
    Write-Host "操作: 将此提示词内容复制给 Claude Code" -ForegroundColor Green
}

Write-Host "`n==============================" -ForegroundColor Cyan
Write-Host "所有任务已准备就绪！" -ForegroundColor Green
''', encoding='utf-8')
    
    print(f"\n[脚本] 执行脚本已创建: {ps_script}")

if __name__ == "__main__":
    main()
