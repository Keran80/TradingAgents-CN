#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试运行器 - 不依赖pytest

直接运行: python run_simple_tests.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from tradingagents.config import Settings, APISettings
from tradingagents.backtest.engine import BacktestConfig, BacktestResult, TradeRecord, BacktestMode
from tradingagents.event_engine import Event, EventType, TickEvent
from tradingagents.agents.utils.agent_utils import build_context_situation, format_memories


def test_agent_utils():
    """测试agent_utils函数"""
    print("\n=== 测试 agent_utils ===")
    
    # 测试 build_context_situation
    state = {
        "market_report": "市场报告",
        "sentiment_report": "情绪报告",
        "news_report": "新闻报道",
        "fundamentals_report": "基本面",
    }
    result = build_context_situation(state)
    assert "市场报告" in result
    assert "情绪报告" in result
    print("  ✅ build_context_situation - 完整状态")
    
    # 测试部分缺失
    partial_state = {"market_report": "市场"}
    result = build_context_situation(partial_state)
    assert "市场" in result
    print("  ✅ build_context_situation - 部分状态")
    
    # 测试 format_memories
    memories = [
        {"recommendation": "推荐1"},
        {"recommendation": "推荐2"},
    ]
    result = format_memories(memories)
    assert "推荐1" in result
    assert "推荐2" in result
    print("  ✅ format_memories - 正常情况")
    
    # 测试空记忆
    result = format_memories([])
    assert result == ""
    print("  ✅ format_memories - 空列表")


def test_config():
    """测试config模块"""
    print("\n=== 测试 config ===")
    
    # 测试默认值
    settings = Settings.load()
    assert settings.api.api_key == ""
    assert settings.database.url == "sqlite:///trading.db"
    print("  ✅ Settings.load() - 默认值")
    
    # 测试APISettings
    api = APISettings()
    assert api.timeout == 30
    assert api.retry_count == 3
    print("  ✅ APISettings - 默认值")


def test_backtest_engine():
    """测试backtest engine数据类"""
    print("\n=== 测试 backtest engine ===")
    
    # 测试BacktestConfig
    config = BacktestConfig()
    assert config.initial_cash == 1000000.0
    assert config.mode == BacktestMode.EVENT_DRIVEN
    print("  ✅ BacktestConfig - 默认值")
    
    # 测试自定义配置
    custom_config = BacktestConfig(
        start_date="2023-01-01",
        mode=BacktestMode.VECTORIZED,
    )
    assert custom_config.start_date == "2023-01-01"
    assert custom_config.mode == BacktestMode.VECTORIZED
    print("  ✅ BacktestConfig - 自定义值")
    
    # 测试BacktestResult
    result = BacktestResult(
        start_date="2024-01-01",
        end_date="2024-06-30",
        initial_cash=100000,
        final_cash=110000,
        total_return=0.10,
        annual_return=0.20,
        total_trades=10,
        winning_trades=6,
        losing_trades=4,
        win_rate=0.6,
    )
    result_dict = result.to_dict()
    assert result_dict["total_return"] == "10.00%"
    assert result_dict["win_rate"] == "60.00%"
    print("  ✅ BacktestResult - to_dict()")
    
    # 测试可选字段为None
    result_none = BacktestResult(
        start_date="2024-01-01",
        end_date="2024-01-31",
        initial_cash=100000,
        final_cash=101000,
        total_return=0.01,
        annual_return=0.12,
        total_trades=0,
        winning_trades=0,
        losing_trades=0,
        win_rate=0.0,
        equity_curve=None,
        daily_returns=None,
    )
    assert result_none.equity_curve is None
    assert result_none.daily_returns is None
    print("  ✅ BacktestResult - Optional字段为None")
    
    # 测试TradeRecord
    trade = TradeRecord(
        timestamp="2024-01-02",
        symbol="000001.SZ",
        direction="BUY",
        price=15.25,
        quantity=100,
        commission=4.58,
        slippage=1.53,
    )
    assert trade.direction == "BUY"
    assert trade.quantity == 100
    print("  ✅ TradeRecord - 创建")


def test_event_engine():
    """测试event_engine数据类"""
    print("\n=== 测试 event_engine ===")
    
    # 测试Event
    event = Event()
    assert event.event_type == EventType.CUSTOM
    assert isinstance(event.timestamp, datetime)
    print("  ✅ Event - 默认值")
    
    # 测试None时间戳
    event_none = Event(timestamp=None)
    assert event_none.timestamp is not None
    print("  ✅ Event - None时间戳自动修正")
    
    # 测试TickEvent
    tick = TickEvent(
        symbol="000001.SZ",
        last_price=10.50,
        volume=1000000,
    )
    assert tick.symbol == "000001.SZ"
    assert tick.event_type == EventType.TICK
    print("  ✅ TickEvent - 创建")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("TradingAgents-CN 单元测试")
    print("=" * 60)
    
    tests = [
        ("agent_utils", test_agent_utils),
        ("config", test_config),
        ("backtest_engine", test_backtest_engine),
        ("event_engine", test_event_engine),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {name} 测试失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
