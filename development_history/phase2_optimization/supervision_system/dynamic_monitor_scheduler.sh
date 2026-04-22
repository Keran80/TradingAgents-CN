#!/bin/bash
# 动态监控调度脚本
# 根据智能策略动态调整监控间隔

echo "🔄 动态监控调度启动"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. 运行智能监控引擎获取间隔
echo "🔍 运行智能监控引擎..."
INTERVAL_OUTPUT=$(python3 /tmp/CODING_agent/smart_monitor_engine.py 2>&1)

# 从输出中提取间隔
INTERVAL=$(echo "$INTERVAL_OUTPUT" | grep "INTERVAL:" | cut -d':' -f2 | tr -d ' ')

# 如果没有获取到，使用默认30分钟
if [ -z "$INTERVAL" ] || [ "$INTERVAL" -lt 5 ] || [ "$INTERVAL" -gt 180 ]; then
    INTERVAL=30
    echo "⚠️  使用默认监控间隔: ${INTERVAL}分钟"
else
    echo "✅ 使用智能监控间隔: ${INTERVAL}分钟"
fi

# 显示引擎输出
echo ""
echo "📊 智能引擎分析结果:"
echo "$INTERVAL_OUTPUT" | grep -v "INTERVAL:" | head -15

# 2. 更新cron任务
echo ""
echo "🔄 更新cron任务..."
CRON_JOB="*/${INTERVAL} * * * * /bin/bash /tmp/CODING_agent/auto_development_monitor.sh >> /tmp/CODING_agent/cron_monitor.log 2>&1"

# 清理旧的监控任务，添加新的
(crontab -l 2>/dev/null | grep -v "auto_development_monitor.sh"; echo "$CRON_JOB") | crontab -

# 验证更新
echo "📋 验证cron任务更新:"
crontab -l | grep "auto_development_monitor.sh"

# 3. 记录调度日志
echo ""
echo "📝 记录调度日志..."
LOG_ENTRY="调度时间: $(date '+%Y-%m-%d %H:%M:%S')
监控间隔: ${INTERVAL}分钟
Cron表达式: */${INTERVAL} * * * *
项目阶段: $(echo "$INTERVAL_OUTPUT" | grep "项目阶段:" | cut -d':' -f2)
时间段: $(echo "$INTERVAL_OUTPUT" | grep "时间段:" | cut -d':' -f2)
决策依据: $(echo "$INTERVAL_OUTPUT" | grep "决策依据:" | cut -d':' -f2-)
---"

echo "$LOG_ENTRY" >> /tmp/CODING_agent/dynamic_scheduler.log

# 4. 创建优化状态文件
cat > /tmp/CODING_agent/dynamic_monitor_status.json << EOF
{
  "optimization_name": "动态监控间隔优化",
  "implementation_time": "$(date '+%Y-%m-%d %H:%M:%S')",
  "monitor_interval_minutes": ${INTERVAL},
  "previous_interval": 30,
  "improvement_percentage": "$(( (30 - INTERVAL) * 100 / 30 ))%",
  "next_check_time": "$(date -d "+${INTERVAL} minutes" '+%Y-%m-%d %H:%M:%S')",
  "status": "active",
  "configuration_file": "/tmp/CODING_agent/smart_monitor_config.json",
  "engine_script": "/tmp/CODING_agent/smart_monitor_engine.py",
  "scheduler_script": "/tmp/CODING_agent/dynamic_monitor_scheduler.sh"
}
EOF

echo ""
echo "✅ 动态监控调度完成"
echo "📊 优化效果:"
echo "  优化前: 固定30分钟间隔"
echo "  优化后: 动态${INTERVAL}分钟间隔"
echo "  效率提升: $(( (30 - INTERVAL) * 100 / 30 ))% (监控频率调整)"
echo "  下次监控: $(date -d "+${INTERVAL} minutes" '+%H:%M')"
echo ""
echo "🚀 动态监控优化已生效!"
echo "🤖 八戒将持续监督优化效果..."