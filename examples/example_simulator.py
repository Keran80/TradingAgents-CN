# -*- coding: utf-8 -*-
"""
TradingAgents-CN Phase 1 示例脚本

演示如何：
1. 初始化模拟交易券商
2. 更新行情数据
3. 执行买入/卖出信号
4. 查看账户和持仓状态
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradingagents.execution import (
    SimulatorBroker,
    TradingEngine,
    Signal,
    SignalType,
    OrderSide,
    OrderType,
    Account,
    Portfolio
)


def main():
    print("=" * 60)
    print("TradingAgents-CN Phase 1 模拟交易示例")
    print("=" * 60)

    # 1. 创建模拟券商
    print("\n[1] 初始化模拟券商...")
    broker = SimulatorBroker(
        commission_rate=0.0003,   # 万三佣金
        stamp_tax=0.001,          # 千一印花税
        slippage=0.001,          # 0.1% 滑点
        price_limit_ratio=0.10,  # 10% 涨跌停
    )
    broker.connect()
    print(f"    券商连接状态: {broker.is_connected}")

    # 2. 创建交易引擎
    print("\n[2] 创建交易引擎...")
    engine = TradingEngine(
        broker=broker,
        initial_capital=1000000.0,  # 100万初始资金
        max_position_ratio=0.3,      # 单股最大30%仓位
        max_total_position=0.8,      # 总仓位上限80%
    )
    print(f"    初始资金: {engine.initial_capital:,.2f}")

    # 3. 更新行情数据
    print("\n[3] 更新行情数据...")
    broker.set_prev_close("000001.SZ", 12.50)  # 设置昨收价
    broker.update_price("000001.SZ", 12.80)    # 更新实时价格
    quote = broker.get_quote("000001.SZ")
    print(f"    000001.SZ 行情: 现价={quote.last_price:.2f}")

    broker.set_prev_close("000002.SZ", 28.00)
    broker.update_price("000002.SZ", 28.50)
    quote2 = broker.get_quote("000002.SZ")
    print(f"    000002.SZ 行情: 现价={quote2.last_price:.2f}")

    # 4. 执行买入信号
    print("\n[4] 执行买入信号...")
    signal = Signal(
        symbol="000001.SZ",
        signal_type=SignalType.BUY,
        price=12.80,
        quantity=1000,  # 买入1000股
        confidence=0.85,
        reason="MA金叉突破",
        strategy_name="MAStrategy"
    )
    result = engine.execute_signal(signal)
    print(f"    买入结果: {result.message}")
    print(f"    订单ID: {result.order_id}")

    # 等待撮合
    import time
    time.sleep(0.5)

    # 5. 查看账户状态
    print("\n[5] 账户状态:")
    status = engine.get_portfolio_status()
    account = status["account"]
    print(f"    可用资金: {account['available_cash']:,.2f}")
    print(f"    持仓市值: {account['market_value']:,.2f}")
    print(f"    总资产: {account['total_assets']:,.2f}")
    print(f"    累计盈亏: {account['total_pnl']:,.2f}")

    # 6. 查看持仓
    print("\n[6] 当前持仓:")
    positions = engine.portfolio.get_all_positions()
    if positions:
        for pos in positions:
            print(f"    {pos.symbol}: 数量={pos.quantity}, 成本={pos.avg_cost:.2f}, 现价={pos.last_price:.2f}, 盈亏={pos.unrealized_pnl:,.2f}")
    else:
        print("    无持仓")

    # 7. 执行卖出信号（演示风控拒绝）
    print("\n[7] 执行卖出信号（000002.SZ，无持仓）...")
    sell_signal = Signal(
        symbol="000002.SZ",
        signal_type=SignalType.SELL,
        price=28.50,
        quantity=100,
        confidence=0.9,
        reason="MA死叉",
        strategy_name="MAStrategy"
    )
    result2 = engine.execute_signal(sell_signal)
    print(f"    卖出结果: {result2.message}")

    # 8. 查看完整状态
    print("\n[8] 完整组合状态:")
    status = engine.get_portfolio_status()
    print(f"    总市值: {status['total_value']:,.2f}")
    print(f"    仓位占比: {status['position_ratio']:.2%}")

    # 9. 取消订单示例（如果有待成交订单）
    print("\n[9] 待成交订单:")
    pending = engine.get_pending_orders()
    if pending:
        for order in pending:
            print(f"    {order.order_id}: {order.symbol} {order.side.value} {order.quantity}@{order.price}")
    else:
        print("    无待成交订单")

    # 10. 断开连接
    print("\n[10] 断开连接...")
    broker.disconnect()
    print("    完成!")

    print("\n" + "=" * 60)
    print("Phase 1 模拟交易示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
