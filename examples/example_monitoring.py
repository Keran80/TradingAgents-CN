# -*- coding: utf-8 -*-
"""
监控告警模块测试示例
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from tradingagents.monitoring import MonitorManager, MonitorDashboard
from tradingagents.monitoring.triggers.base import (
    AlertTrigger, TriggerResult, AlertLevel, TriggerType
)
from tradingagents.monitoring.triggers import (
    PriceChangeTrigger, PriceCrossTrigger,
    UpperLimitTrigger, LowerLimitTrigger,
    VolumeSpikeTrigger, PnLThresholdTrigger, DrawdownTrigger,
    MarketOpenTrigger
)
from tradingagents.monitoring.notifiers import (
    ConsoleNotifier, FileNotifier, WebhookNotifier
)


def test_price_triggers():
    """测试价格触发器"""
    print("\n=== Test Price Triggers ===")

    # 测试价格变动触发器
    trigger = PriceChangeTrigger(
        symbol="000001.SZ",
        threshold=-5.0,  # 下跌超过5%
        reference_price=10.0
    )

    # 模拟下跌
    context = {
        'prices': {'000001.SZ': 9.4},
        'symbols': {'000001.SZ': '平安银行'},
    }
    result = trigger.check(context)
    print(f"PriceChange (down 6%): triggered={result.triggered}")
    print(f"  Message: {result.message}")

    # 模拟小幅下跌（不触发）
    trigger2 = PriceChangeTrigger(
        symbol="000001.SZ",
        threshold=-5.0,
        reference_price=10.0
    )
    context2 = {'prices': {'000001.SZ': 9.8}, 'symbols': {'000001.SZ': '平安银行'}}
    result2 = trigger2.check(context2)
    print(f"PriceChange (down 2%): triggered={result2.triggered}")

    # 测试价格穿越触发器
    cross = PriceCrossTrigger(
        symbol="000001.SZ",
        trigger_price=10.0,
        direction="down"
    )

    # 第一次检查
    ctx1 = {'prices': {'000001.SZ': 10.5}, 'symbols': {'000001.SZ': '平安银行'}}
    cross.check(ctx1)

    # 第二次检查：向下穿越
    ctx2 = {'prices': {'000001.SZ': 9.5}, 'symbols': {'000001.SZ': '平安银行'}}
    result3 = cross.check(ctx2)
    print(f"PriceCross (down through 10.0): triggered={result3.triggered}")


def test_volume_triggers():
    """测试成交量触发器"""
    print("\n=== Test Volume Triggers ===")

    # 测试成交量放大
    trigger = VolumeSpikeTrigger(
        symbol="000001.SZ",
        multiplier=2.0
    )

    context = {
        'volumes': {'000001.SZ': 15000000},
        'avg_volumes': {'000001.SZ': 5000000},
        'prices': {'000001.SZ': 10.0},
        'symbols': {'000001.SZ': '平安银行'}
    }
    result = trigger.check(context)
    print(f"VolumeSpike (3x avg): triggered={result.triggered}")
    print(f"  Ratio: {result.data.get('ratio', 0):.1f}x")


def test_position_triggers():
    """测试持仓触发器"""
    print("\n=== Test Position Triggers ===")

    # 测试盈亏阈值
    pnl_trigger = PnLThresholdTrigger(
        symbol="000001.SZ",
        profit_threshold=20.0,
        loss_threshold=-10.0
    )

    context = {
        'positions': {'000001.SZ': {'quantity': 1000, 'pnl_pct': 25.5}},
        'symbols': {'000001.SZ': '平安银行'}
    }
    result = pnl_trigger.check(context)
    print(f"PnLThreshold (profit 25.5%): triggered={result.triggered}")

    # 测试回撤
    dd_trigger = DrawdownTrigger(drawdown_threshold=15.0)

    context2 = {
        'portfolio': {
            'total_value': 85000,
            'high_water_mark': 100000
        }
    }
    result2 = dd_trigger.check(context2)
    print(f"Drawdown (15%): triggered={result2.triggered}")
    print(f"  Message: {result2.message}")


def test_monitor_manager():
    """测试监控管理器"""
    print("\n=== Test Monitor Manager ===")

    # 创建管理器
    manager = MonitorManager(name="test_monitor")

    # 添加控制台通知器
    manager.add_notifier(
        ConsoleNotifier(min_level=AlertLevel.WARNING)
    )

    # 添加触发器
    manager.add_trigger(
        PriceChangeTrigger(
            symbol="000001.SZ",
            threshold=-3.0,
            level=AlertLevel.WARNING
        )
    )

    manager.add_trigger(
        PnLThresholdTrigger(
            symbol="000001.SZ",
            profit_threshold=10.0,
            loss_threshold=-5.0
        )
    )

    # 设置监控面板
    dashboard = MonitorDashboard()
    manager.set_dashboard(dashboard)

    # 执行检查 - 模拟亏损
    context = {
        'prices': {'000001.SZ': 9.6},
        'positions': {'000001.SZ': {'quantity': 1000, 'pnl_pct': 5.0}},
        'symbols': {'000001.SZ': '平安银行'},
        'datetime': datetime.now()
    }
    results = manager.check(context)
    print(f"Check results: {len(results)} alerts triggered")

    # 执行检查 - 触发盈利告警
    context2 = {
        'prices': {'000001.SZ': 11.0},
        'positions': {'000001.SZ': {'quantity': 1000, 'pnl_pct': 12.0}},
        'symbols': {'000001.SZ': '平安银行'},
        'datetime': datetime.now()
    }
    results2 = manager.check(context2)
    print(f"Check results: {len(results2)} alerts triggered")

    # 获取面板概览
    overview = dashboard.get_overview()
    print(f"\nDashboard Overview:")
    print(f"  Total alerts: {overview['total_alerts']}")
    print(f"  Level counts: {overview['level_counts']}")

    # 生成报告
    print("\n" + manager.get_report())


def test_file_notifier():
    """测试文件通知器"""
    print("\n=== Test File Notifier ===")

    # 临时日志目录
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs', 'monitoring')

    notifier = FileNotifier(
        name="test_file",
        log_dir=log_dir,
        min_level=AlertLevel.INFO
    )

    # 创建测试结果
    result = TriggerResult(
        triggered=True,
        trigger_name="test_trigger",
        alert_level=AlertLevel.WARNING,
        title="Test Alert",
        message="This is a test alert message"
    )

    # 发送通知
    notification = notifier.notify(result)
    print(f"FileNotifier: success={notification.success}")
    print(f"  Message: {notification.message}")


def test_webhook_notifier():
    """测试Webhook通知器"""
    print("\n=== Test Webhook Notifier (dry run) ===")

    # 不实际发送，只测试格式化
    notifier = WebhookNotifier(
        name="test_webhook",
        url="https://example.com/webhook"  # 不存在的URL
    )

    result = TriggerResult(
        triggered=True,
        trigger_name="test",
        alert_level=AlertLevel.CRITICAL,
        title="Critical Alert",
        message="Test message"
    )

    # 测试格式化
    payload = notifier._default_formatter(result)
    print(f"Payload: {payload}")


def main():
    """运行所有测试"""
    print("=" * 50)
    print("  TradingAgents-CN Monitoring Module Tests")
    print("=" * 50)

    try:
        test_price_triggers()
        test_volume_triggers()
        test_position_triggers()
        test_monitor_manager()
        test_file_notifier()
        test_webhook_notifier()

        print("\n" + "=" * 50)
        print("  All monitoring tests passed!")
        print("=" * 50)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
