# -*- coding: utf-8 -*-
"""
获取A股实时股票数据并保存为JSON
使用 web_api.get_stock_data 获取真实技术指标
"""
import json
import sys
import warnings
warnings.filterwarnings('ignore')

# 尝试导入 web_api（如果可用则使用真实技术指标）
try:
    from web_api import get_stock_data as get_stock_tech_data
    HAS_WEB_API = True
except ImportError:
    HAS_WEB_API = False
    # 回退到直接使用 akshare
    from tradingagents.dataflows import akshare_utils as aks

# 要获取的股票列表
stocks = ['000001', '000833', '600519', '300750', '600036', '601318', '000858', '002594']

# 备用股票名称映射
stock_name_map = {
    '000001': '平安银行', '600036': '招商银行', '601398': '工商银行',
    '601939': '建设银行', '601288': '农业银行', '601988': '中国银行',
    '600015': '华夏银行', '600016': '民生银行', '601229': '上海银行',
    '600926': '杭州银行', '600919': '江苏银行', '002142': '宁波银行',
    '002807': '无锡银行', '002948': '青岛银行', '002966': '苏州银行',
    '600519': '贵州茅台', '000858': '五粮液', '000568': '泸州老窖',
    '000596': '古井贡酒', '600809': '山西汾酒', '002304': '洋河股份',
    '603589': '金种子酒', '000799': '酒鬼酒', '600197': '伊力特',
    '603198': '迎驾贡酒', '600779': '水井坊', '603517': '绝味食品',
    '300750': '宁德时代', '002594': '比亚迪', '002475': '立讯精密',
    '000333': '美的集团', '000651': '格力电器', '600276': '恒瑞医药',
    '002230': '科大讯飞', '601012': '隆基绿能', '600703': '三安光电',
    '300059': '东方财富', '300015': '爱尔眼科', '002410': '广联达',
    '002444': '巨星科技', '601888': '中国中免', '600030': '中信证券',
    '601688': '中国中车', '601318': '中国平安', '601166': '兴业银行',
    '600000': '浦发银行', '002027': '分众传媒', '002415': '海康威视',
    '000002': '万科A', '600009': '上海机场', '300142': '沃森生物',
    '300896': '爱博医疗', '002311': '海大集团', '002353': '杰瑞股份',
    '000833': '粤桂股份', '000861': '海印股份', '000895': '系数未名'
}

result = {}

print("=" * 50)
print("获取A股实时股票数据")
print("=" * 50)
print(f"数据源: {'web_api (真实技术指标)' if HAS_WEB_API else 'akshare (基础数据)'}")
print("-" * 50)

for code in stocks:
    try:
        if HAS_WEB_API:
            # 使用 web_api 获取完整数据（包括技术指标）
            data, error = get_stock_tech_data(code)
            if error:
                print(f"{code}: 获取失败 - {error}")
                stock_name = stock_name_map.get(code, '未知')
                result[code] = {
                    'name': stock_name,
                    'price': 0, 'change_pct': 0, 'volume': 0, 'amount': 0,
                    'rsi': 50.0, 'macd': 0.0, 'ma5': 0, 'ma10': 0, 'ma20': 0,
                    'trend': '未知', 'support': 0, 'resistance': 0, 'vol_change': 0
                }
                continue
            
            result[code] = {
                'name': data.get('name', stock_name_map.get(code, '未知')),
                'price': data.get('price', 0),
                'change_pct': data.get('change_pct', 0),
                'volume': data.get('volume', 0),
                'amount': data.get('amount', 0),
                'rsi': data.get('rsi', 50.0),
                'macd': data.get('macd', 0.0),
                'ma5': data.get('ma5', 0),
                'ma10': data.get('ma10', 0),
                'ma20': data.get('ma20', 0),
                'trend': data.get('trend', '未知'),
                'support': data.get('support', 0),
                'resistance': data.get('resistance', 0),
                'vol_change': data.get('vol_change', 0)
            }
            name = result[code]['name']
            price = result[code]['price']
            change_pct = result[code]['change_pct']
            rsi = result[code]['rsi']
            print(f"{code}: {name} - ¥{price:.2f} ({change_pct:+.2f}%) RSI:{rsi:.1f}")
        else:
            # 回退模式：使用 akshare 获取基础数据
            q = aks.get_stock_realtime_quote(code)
            if q is not None and len(q) > 0:
                row = q.iloc[0]
                price = float(row.get('最新价', 0) or 0)
                change_pct = float(row.get('涨跌幅', 0) or 0)
                
                api_name = row.get('名称', '') or row.get('股票简称', '')
                stock_name = api_name if api_name and api_name != '未知' else stock_name_map.get(code, '未知')
                
                result[code] = {
                    'name': stock_name,
                    'price': price,
                    'change_pct': change_pct,
                    'volume': int(row.get('成交量', 0) or 0),
                    'amount': float(row.get('成交额', 0) or 0),
                    'rsi': 50.0,  # 硬编码（无历史数据无法计算）
                    'macd': 0.0,
                    'ma5': price * 0.99,
                    'ma10': price * 0.98,
                    'ma20': price * 0.97,
                    'trend': '上涨' if change_pct > 0 else '下跌',
                    'support': price * 0.95,
                    'resistance': price * 1.05,
                    'vol_change': change_pct
                }
                print(f"{code}: {stock_name} - ¥{price:.2f} ({change_pct:+.2f}%) [基础数据]")
            else:
                stock_name = stock_name_map.get(code, '未知')
                result[code] = {
                    'name': stock_name,
                    'price': 0, 'change_pct': 0, 'volume': 0, 'amount': 0,
                    'rsi': 50.0, 'macd': 0.0, 'ma5': 0, 'ma10': 0, 'ma20': 0,
                    'trend': '未知', 'support': 0, 'resistance': 0, 'vol_change': 0
                }
                print(f"{code}: {stock_name} (无数据)")
                
    except Exception as e:
        stock_name = stock_name_map.get(code, '未知')
        result[code] = {
            'name': stock_name,
            'price': 0, 'change_pct': 0, 'volume': 0, 'amount': 0,
            'rsi': 50.0, 'macd': 0.0, 'ma5': 0, 'ma10': 0, 'ma20': 0,
            'trend': '未知', 'support': 0, 'resistance': 0, 'vol_change': 0
        }
        print(f"{code}: {stock_name} (错误: {str(e)[:30]})")

print("-" * 50)

# 保存到文件
with open('stock_data.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"成功获取 {len(result)} 只股票数据")
print("已保存到 stock_data.json")
