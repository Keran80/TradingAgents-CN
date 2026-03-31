# -*- coding: utf-8 -*-
"""
实时行情示例

演示如何使用实时行情模块
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def test_akshare_realtime():
    """测试 AkShare 实时行情"""
    print("\n=== Test: AkShare Realtime ===")
    
    try:
        from tradingagents.data.realtime import AkShareRealtimeAdapter
        
        adapter = AkShareRealtimeAdapter()
        
        # 获取单只股票行情
        quote = adapter.get_realtime_quote("000001.SZ")
        if quote:
            print(f"股票: {quote['name']} ({quote['symbol']})")
            print(f"价格: {quote['price']}")
            print(f"涨跌: {quote['change']} ({quote['change_pct']:.2f}%)")
            print(f"成交额: {quote['turnover']/1e8:.2f}亿")
        else:
            print("获取行情失败（可能网络问题）")
            
        # 获取涨停股
        print("\n获取今日涨停股...")
        limit_list = adapter.get_limit_list()
        print(f"涨停股数量: {len(limit_list)}")
        if limit_list:
            print(f"前3只: {[l['name'] for l in limit_list[:3]]}")
            
    except Exception as e:
        print(f"AkShare 测试跳过: {e}")


def test_tdx_realtime():
    """测试通达信实时行情"""
    print("\n=== Test: TDX Realtime ===")
    
    try:
        from tradingagents.data.realtime import TDXRealtimeAdapter
        
        adapter = TDXRealtimeAdapter()
        
        # 同步连接
        import asyncio
        
        async def test():
            connected = await adapter.connect()
            if connected:
                print("TDX 连接成功")
                
                # 获取行情
                # 深圳市场代码0，上海市场代码1
                quote = adapter.get_security_quote("000001", market=0)
                if quote:
                    print(f"股票: {quote['name']}")
                    print(f"价格: {quote['price']}")
                    
                await adapter.disconnect()
            else:
                print("TDX 连接失败")
                
        asyncio.run(test())
        
    except ImportError:
        print("pytdx 未安装，跳过测试")
    except Exception as e:
        print(f"TDX 测试失败: {e}")


def test_realtime_manager():
    """测试实时行情管理器"""
    print("\n=== Test: RealtimeManager ===")
    
    from tradingagents.data.realtime import RealtimeDataManager, MarketType
    
    def on_tick(tick):
        print(f"Tick: {tick.symbol} = {tick.last_price}")
    
    manager = RealtimeDataManager(primary_source="akshare")
    manager.subscribe("000001.SZ", on_tick, MarketType.A_STOCK)
    
    print("开始接收实时行情（5秒后自动停止）...")
    manager.start()
    
    import time
    time.sleep(5)
    
    manager.stop()
    print("测试完成")


def test_futures():
    """测试期货数据"""
    print("\n=== Test: Futures Data ===")
    
    try:
        from tradingagents.data.futures import FuturesDataManager, FuturesCalculator
        
        manager = FuturesDataManager()
        
        # 获取主力合约行情
        print("获取期货行情...")
        quote = manager.get_quote("IF2404")
        if quote:
            print(f"合约: {quote['symbol']}")
            print(f"价格: {quote['price']}")
            print(f"持仓: {quote.get('position', 0)}")
        else:
            print("获取行情失败（可能网络问题）")
            
        # 计算保证金
        calc = FuturesCalculator()
        
        # 模拟计算
        margin = calc.calculate_margin("IF2404", 4000)
        print(f"保证金(4000点位): {margin:.2f}")
        
        pnl = calc.calculate_profit("IF2404", "long", 4000, 4040)
        print(f"1%涨幅盈亏: {pnl:.2f}")
        
        # 获取品种信息
        info = calc.get_product_info("IF")
        print(f"IF品种信息: {info}")
        
    except Exception as e:
        print(f"期货测试跳过: {e}")


def test_options():
    """测试期权数据"""
    print("\n=== Test: Options Data ===")
    
    from tradingagents.data.options import OptionsCalculator, OptionContract
    from datetime import datetime
    
    calc = OptionsCalculator()
    
    # Black-Scholes 定价
    S = 3.0     # 标的价格
    K = 3.0     # 行权价
    T = 30/365  # 30天后到期
    r = 0.03    # 无风险利率
    sigma = 0.2 # 波动率
    
    # 认购期权
    call_price = calc.calc_bs_price(S, K, T, r, sigma, "call")
    print(f"认购期权价格: {call_price:.4f}")
    
    # 认沽期权
    put_price = calc.calc_bs_price(S, K, T, r, sigma, "put")
    print(f"认沽期权价格: {put_price:.4f}")
    
    # 希腊字母
    greeks = calc.calc_greeks(S, K, T, r, sigma, "call")
    print(f"Delta: {greeks.delta:.4f}")
    print(f"Gamma: {greeks.gamma:.4f}")
    print(f"Vega: {greeks.vega:.4f}")
    print(f"Theta: {greeks.theta:.4f}")


def test_live_broker():
    """测试实盘券商接口"""
    print("\n=== Test: Live Broker ===")
    
    from tradingagents.execution.live import LiveBroker, LiveOrderManager
    from tradingagents.execution.live.broker import Side, OrderType
    
    # 创建模拟券商
    broker = LiveBroker.create("simulator", initial_cash=100000)
    broker.connect()
    
    print(f"账户余额: {broker.get_account().cash}")
    
    # 创建订单管理器
    manager = LiveOrderManager(broker)
    
    # 买入
    print("\n买入 100 股...")
    result = manager.buy_limit("000001.SZ", 10.0, 100)
    print(f"下单结果: {'成功' if result.success else '失败'}")
    
    if result.order:
        print(f"订单ID: {result.order.order_id}")
        
    # 查询持仓
    positions = broker.get_positions()
    print(f"\n当前持仓: {len(positions)} 只")
    for pos in positions:
        print(f"  {pos.symbol}: {pos.quantity}股, 成本 {pos.avg_cost}")
        
    # 卖出
    print("\n卖出 50 股...")
    result = manager.sell_limit("000001.SZ", 10.5, 50)
    print(f"下单结果: {'成功' if result.success else '失败'}")
    
    # 查询账户
    account = broker.get_account()
    print(f"\n账户余额: {account.cash:.2f}")
    print(f"总资产: {account.total_assets:.2f}")
    
    manager.stop()
    
    broker.disconnect()
    print("\n模拟交易测试完成")


if __name__ == "__main__":
    print("=" * 50)
    print("TradingAgents-CN 数据层与实盘模块测试")
    print("=" * 50)
    
    # 数据层测试
    test_akshare_realtime()
    # test_tdx_realtime()  # 需要 pytdx
    # test_realtime_manager()  # 需要持续运行
    
    test_futures()
    test_options()
    
    # 实盘测试
    test_live_broker()
    
    print("\n" + "=" * 50)
    print("所有测试完成!")
    print("=" * 50)
