# TradingAgents-CN 代码优化 - 批量启动 Agents
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
