# -*- coding: utf-8 -*-
"""
A股数据全面获取工具
用于测试和验证A股数据适配
"""

from tradingagents.dataflows.astock_utils import AStockData
from tradingagents.dataflows.astock_technical import AStockTechnical
import json
from datetime import datetime

def test_realtime_quote():
    """测试实时行情"""
    print("=" * 50)
    print("测试1: 获取实时行情")
    print("=" * 50)
    
    # 获取单只股票
    df = AStockData.get_realtime_quote('000001')
    if not df.empty:
        print(f"平安银行: {df.iloc[0]['最新价']}, 涨跌幅: {df.iloc[0]['涨跌幅']}%")
    
    # 获取多只股票
    stocks = ['000001', '600519', '300750']
    for code in stocks:
        df = AStockData.get_realtime_quote(code)
        if not df.empty:
            row = df.iloc[0]
            print(f"{row['代码']}: {row['股票简称']} - ¥{row['最新价']} ({row['涨跌幅']}%)")
    print()


def test_daily_data():
    """测试日线数据"""
    print("=" * 50)
    print("测试2: 获取日线数据")
    print("=" * 50)
    
    df = AStockData.get_daily('000001', '20250101', '20250328')
    if not df.empty:
        print(f"获取到 {len(df)} 条日线数据")
        print(df.tail(5)[['日期', '开盘', '收盘', '成交量']])
    print()


def test_technical():
    """测试技术指标"""
    print("=" * 50)
    print("测试3: 计算技术指标")
    print("=" * 50)
    
    # 获取数据
    df = AStockData.get_daily('600519', '20250101', '20250328')
    
    if not df.empty:
        # 计算所有指标
        df = AStockTechnical.calculate_all(df)
        
        # 获取最新值
        latest = AStockTechnical.get_latest_indicators(df)
        
        print("贵州茅台技术指标:")
        print(f"  收盘价: ¥{latest.get('close')}")
        print(f"  成交量: {latest.get('volume')}")
        print(f"  MA5: {latest.get('ma5')}")
        print(f"  MA10: {latest.get('ma10')}")
        print(f"  MA20: {latest.get('ma20')}")
        print(f"  RSI: {latest.get('rsi')}")
        print(f"  MACD: {latest.get('macd')}")
        print(f"  KDJ: K={latest.get('kdj_k')}, D={latest.get('kdj_d')}, J={latest.get('kdj_j')}")
    print()


def test_moneyflow():
    """测试资金流向"""
    print("=" * 50)
    print("测试4: 北向资金流向")
    print("=" * 50)
    
    df = AStockData.get_moneyflow_hsgt()
    if not df.empty:
        print(df.head())
    print()


def test_lhb():
    """测试龙虎榜"""
    print("=" * 50)
    print("测试5: 龙虎榜数据")
    print("=" * 50)
    
    df = AStockData.get_lhb_stocks()
    if not df.empty:
        print(f"获取到 {len(df)} 条龙虎榜数据")
        print(df.head())
    print()


def test_margin():
    """测试融资融券"""
    print("=" * 50)
    print("测试6: 融资融券数据")
    print("=" * 50)
    
    df = AStockData.get_margin_detail()
    if not df.empty:
        print(f"获取到 {len(df)} 条融资融券数据")
        print(df.head())
    print()


def test_news():
    """测试新闻数据"""
    print("=" * 50)
    print("测试7: A股新闻")
    print("=" * 50)
    
    df = AStockData.get_stock_news()
    if not df.empty:
        print(f"获取到 {len(df)} 条新闻")
        for i, row in df.head(5).iterrows():
            print(f"  - {row.get('标题', 'N/A')[:50]}")
    print()


def test_index():
    """测试指数数据"""
    print("=" * 50)
    print("测试8: 指数数据")
    print("=" * 50)
    
    # 获取沪深300指数
    df = AStockData.get_index_daily('000300', '20250101', '20250328')
    if not df.empty:
        print(f"沪深300最近5天:")
        print(df.tail(5)[['date', 'open', 'close', 'volume']])
    print()


def test_stock_info():
    """测试股票基本信息"""
    print("=" * 50)
    print("测试9: 股票基本信息")
    print("=" * 50)
    
    info = AStockData.get_stock_info('600519')
    if info:
        print("贵州茅台基本信息:")
        for k, v in list(info.items())[:10]:
            print(f"  {k}: {v}")
    print()


def export_stock_json():
    """导出股票数据到JSON"""
    print("=" * 50)
    print("导出股票数据到JSON")
    print("=" * 50)
    
    stocks = {
        '000001': '平安银行',
        '000833': '粤桂股份', 
        '600519': '贵州茅台',
        '300750': '宁德时代',
        '600036': '招商银行',
        '601318': '中国平安',
        '000858': '五粮液',
        '002594': '比亚迪',
    }
    
    result = {}
    
    for code, name in stocks.items():
        try:
            # 实时行情
            quote = AStockData.get_realtime_quote(code)
            if not quote.empty:
                q = quote.iloc[0]
                
                # 日线数据计算技术指标
                daily = AStockData.get_daily(code, '20250101', '20250328')
                if not daily.empty:
                    daily = AStockTechnical.calculate_all(daily)
                    tech = AStockTechnical.get_latest_indicators(daily)
                else:
                    tech = {}
                
                result[code] = {
                    'name': name,
                    'price': float(q.get('最新价', 0) or 0),
                    'change_pct': float(q.get('涨跌幅', 0) or 0),
                    'volume': int(q.get('成交量', 0) or 0),
                    'amount': float(q.get('成交额', 0) or 0),
                    'rsi': tech.get('rsi', 50.0),
                    'macd': tech.get('macd', 0.0),
                    'ma5': tech.get('ma5', 0),
                    'ma10': tech.get('ma10', 0),
                    'ma20': tech.get('ma20', 0),
                    'trend': '上涨' if q.get('涨跌幅', 0) > 0 else '下跌',
                    'support': tech.get('ma20', 0) * 0.95,
                    'resistance': tech.get('ma20', 0) * 1.05,
                    'vol_change': float(q.get('涨跌幅', 0) or 0)
                }
                
                print(f"{code}: {name} - ¥{result[code]['price']}")
        except Exception as e:
            print(f"{code}: 获取失败 - {e}")
    
    # 保存到文件
    with open('stock_data.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n成功导出 {len(result)} 只股票数据到 stock_data.json")


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("TradingAgents-CN A股数据适配测试")
    print("=" * 50 + "\n")
    
    # 运行所有测试
    # test_realtime_quote()
    # test_daily_data()
    # test_technical()
    # test_moneyflow()
    # test_lhb()
    # test_margin()
    # test_news()
    # test_index()
    # test_stock_info()
    
    # 导出JSON
    export_stock_json()
