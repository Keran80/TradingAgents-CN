#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通达信数据接口测试脚本
运行方式: python test_tdx.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_tdx_connection():
    """测试通达信服务器连接"""
    print("\n" + "="*60)
    print("🔌 测试1: 通达信服务器连接")
    print("="*60)
    try:
        from tradingagents.dataflows.tdx_utils import _pool
        api = _pool.get_api()
        server = _pool._server
        print(f"✅ 连接成功: {server[0]}:{server[1]}")
        return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


def test_stock_data():
    """测试股票日线数据获取"""
    print("\n" + "="*60)
    print("📊 测试2: 股票日线数据（000001 平安银行）")
    print("="*60)
    try:
        from tradingagents.dataflows.tdx_utils import get_stock_data
        df = get_stock_data("000001", "2026-03-01", "2026-03-29")
        if df.empty:
            print("⚠️ 数据为空")
            return False
        print(f"✅ 获取成功，共 {len(df)} 条记录")
        print(df.tail(3).to_string())
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_realtime_quotes():
    """测试实时行情"""
    print("\n" + "="*60)
    print("⚡ 测试3: 实时行情（多股）")
    print("="*60)
    try:
        from tradingagents.dataflows.tdx_utils import get_realtime_quotes
        symbols = ["000001", "600000", "000858", "300750", "000002"]
        df = get_realtime_quotes(symbols)
        if df.empty:
            print("⚠️ 数据为空")
            return False
        cols = ["market", "code", "price", "open", "high", "low", "vol", "amount"]
        print(f"✅ 获取成功，共 {len(df)} 只股票")
        print(df[[c for c in cols if c in df.columns]].to_string())
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_finance_info():
    """测试财务信息"""
    print("\n" + "="*60)
    print("💰 测试4: 财务信息（000001 平安银行）")
    print("="*60)
    try:
        from tradingagents.dataflows.tdx_utils import get_finance_info
        info = get_finance_info("000001")
        if not info:
            print("⚠️ 数据为空")
            return False
        print(f"✅ 获取成功")
        for k, v in info.items():
            if k != "symbol":
                print(f"  {k:30s}: {v}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_minute_data():
    """测试分钟线数据"""
    print("\n" + "="*60)
    print("⏱️  测试5: 分钟线数据（000001，5分钟）")
    print("="*60)
    try:
        from tradingagents.dataflows.tdx_utils import get_stock_bars
        from datetime import datetime, timedelta
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        df = get_stock_bars("000001", start, end, k_type="5min")
        if df.empty:
            print("⚠️ 数据为空（非交易时间可能为空）")
            return True
        print(f"✅ 获取成功，共 {len(df)} 条记录")
        print(df.tail(3).to_string())
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_data_source_router():
    """测试数据源路由（auto 模式）"""
    print("\n" + "="*60)
    print("🔄 测试6: 数据源路由（auto 模式）")
    print("="*60)
    try:
        from tradingagents.dataflows.data_source import get_data_source, get_current_source_name
        ds = get_data_source("auto")
        source_name = get_current_source_name()
        print(f"✅ 当前数据源: {source_name}")
        print(f"   数据源类型: {type(ds).__name__}")

        # 测试通过路由获取数据
        df = ds.get_stock_data("600519", "2026-03-01", "2026-03-29")
        if not df.empty:
            print(f"✅ 通过路由获取 600519 贵州茅台数据: {len(df)} 条")
            print(df.tail(2).to_string())
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_interface_integration():
    """测试与 TradingAgents interface 的集成"""
    print("\n" + "="*60)
    print("🤖 测试7: interface.py 集成测试")
    print("="*60)
    try:
        from tradingagents.dataflows.interface import get_YFin_data_online
        result = get_YFin_data_online("000001", "2026-03-01", "2026-03-10")
        if "No data" in result:
            print(f"⚠️ 无数据: {result}")
            return False
        lines = result.strip().split("\n")
        print(f"✅ 集成成功，返回 {len(lines)} 行数据")
        for line in lines[:6]:
            print(f"  {line}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print("  TradingAgents-CN 通达信接口测试")
    print("="*60)

    tests = [
        ("服务器连接",      test_tdx_connection),
        ("股票日线数据",    test_stock_data),
        ("实时行情",        test_realtime_quotes),
        ("财务信息",        test_finance_info),
        ("分钟线数据",      test_minute_data),
        ("数据源路由",      test_data_source_router),
        ("interface 集成", test_interface_integration),
    ]

    results = []
    for name, func in tests:
        ok = func()
        results.append((name, ok))

    print("\n" + "="*60)
    print("📋 测试汇总")
    print("="*60)
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}  {name}")
    print(f"\n总计: {passed}/{len(results)} 通过")

    if passed == len(results):
        print("\n🎉 所有测试通过！通达信数据源已就绪。")
    else:
        print("\n⚠️ 部分测试失败，请检查网络和依赖。")


if __name__ == "__main__":
    main()
