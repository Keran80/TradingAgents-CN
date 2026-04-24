#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最小化测试 - 只测试不依赖外部库的模块

运行: python run_minimal_tests.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("\n=== 测试模块导入 ===")
    
    try:
        # 测试config模块（不依赖pandas）
        from tradingagents.config import Settings, APISettings, DatabaseSettings, LogSettings
        print("  ✅ tradingagents.config 导入成功")
        
        # 测试agent_utils
        from tradingagents.agents.utils.agent_utils import build_context_situation, format_memories
        print("  ✅ tradingagents.agents.utils.agent_utils 导入成功")
        
        return True
    except Exception as e:
        print(f"  ❌ 导入失败: {e}")
        return False


def test_config_module():
    """测试config模块功能"""
    print("\n=== 测试 config 模块 ===")
    
    from tradingagents.config import Settings, APISettings
    
    # 测试默认值
    settings = Settings.load()
    assert settings.api.api_key == "", f"Expected empty api_key, got {settings.api.api_key}"
    print("  ✅ Settings.load() 默认值正确")
    
    # 测试APISettings
    api = APISettings()
    assert api.timeout == 30
    assert api.retry_count == 3
    print("  ✅ APISettings 默认值正确")
    
    return True


def test_agent_utils():
    """测试agent_utils模块"""
    print("\n=== 测试 agent_utils 模块 ===")
    
    from tradingagents.agents.utils.agent_utils import build_context_situation, format_memories
    
    # 测试 build_context_situation
    state = {
        "market_report": "市场报告",
        "sentiment_report": "情绪报告",
        "news_report": "新闻",
        "fundamentals_report": "基本面",
    }
    result = build_context_situation(state)
    assert "市场报告" in result
    assert "情绪报告" in result
    print("  ✅ build_context_situation 正常工作")
    
    # 测试 format_memories
    memories = [
        {"recommendation": "推荐1"},
        {"recommendation": "推荐2"},
    ]
    result = format_memories(memories)
    assert "推荐1" in result
    assert "推荐2" in result
    print("  ✅ format_memories 正常工作")
    
    # 测试空列表
    assert format_memories([]) == ""
    print("  ✅ format_memories 空列表处理正确")
    
    return True


def test_syntax_all_files():
    """测试所有修改文件的语法"""
    print("\n=== 测试文件语法 ===")
    
    import py_compile
    
    files = [
        "tradingagents/backtest/engine.py",
        "tradingagents/config.py",
        "tradingagents/event_engine.py",
        "tradingagents/agents/managers/risk_manager.py",
        "tradingagents/agents/managers/research_manager.py",
        "tradingagents/agents/utils/agent_utils.py",
        "tradingagents/agents/utils/__init__.py",
        "tradingagents/agents/trader/trader.py",
        "tradingagents/agents/researchers/__init__.py",
        "tradingagents/agents/researchers/bear_researcher.py",
        "tradingagents/agents/researchers/bull_researcher.py",
        "tradingagents/agents/risk_mgmt/__init__.py",
        "tradingagents/execution/simulators/simulator.py",
        "tradingagents/dataflows/interface/utils.py",
    ]
    
    all_ok = True
    for filepath in files:
        full_path = os.path.join(os.path.dirname(__file__), filepath)
        if not os.path.exists(full_path):
            print(f"  ⚠️  {filepath} 不存在，跳过")
            continue
        
        try:
            py_compile.compile(full_path, doraise=True)
            print(f"  ✅ {filepath}")
        except py_compile.PyCompileError as e:
            print(f"  ❌ {filepath}: {e}")
            all_ok = False
    
    return all_ok


def test_no_duplicate_code():
    """验证重复代码已被替换"""
    print("\n=== 验证重复代码替换 ===")
    
    import re
    
    # 应该不再存在的重复模式
    duplicate_pattern = r'curr_situation\s*=\s*f".*\{market_research_report\}.*\{sentiment_report\}.*\{news_report\}.*\{fundamentals_report\}.*"'
    
    files_to_check = [
        "tradingagents/agents/managers/research_manager.py",
        "tradingagents/agents/managers/risk_manager.py",
        "tradingagents/agents/trader/trader.py",
        "tradingagents/agents/researchers/bear_researcher.py",
        "tradingagents/agents/researchers/bull_researcher.py",
    ]
    
    all_clean = True
    for filepath in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), filepath)
        if not os.path.exists(full_path):
            continue
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if re.search(duplicate_pattern, content):
            print(f"  ❌ {filepath} 仍包含重复代码")
            all_clean = False
        else:
            print(f"  ✅ {filepath} 已使用通用函数")
    
    return all_clean


def main():
    """运行所有测试"""
    print("=" * 70)
    print("TradingAgents-CN 代码质量验证测试")
    print("=" * 70)
    
    tests = [
        ("模块导入", test_imports),
        ("Config模块", test_config_module),
        ("Agent Utils", test_agent_utils),
        ("文件语法", test_syntax_all_files),
        ("重复代码检查", test_no_duplicate_code),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"\n⚠️  {name} 测试未完全通过")
        except Exception as e:
            print(f"\n❌ {name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"测试总结: {passed} 通过, {failed} 失败")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
