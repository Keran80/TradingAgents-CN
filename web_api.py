"""
TradingAgents Web API Server
提供股票数据和AI分析服务的REST API
"""
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows import akshare_utils as aks
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import threading
import json

app = Flask(__name__, template_folder='.')
CORS(app)

# 全局变量存储分析任务状态
analysis_tasks = {}

def get_stock_data(code):
    """获取股票数据"""
    try:
        # 获取实时行情
        quote = aks.get_stock_realtime_quote(code)
        if quote is None or len(quote) == 0:
            return None, "未找到该股票"
        
        q = quote.iloc[0]
        
        # 获取历史K线数据计算技术指标
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
        
        df_daily = aks.get_stock_daily(code, start_date, end_date)
        
        if df_daily is None or len(df_daily) == 0:
            return None, "无法获取K线数据"
        
        # 转换为中文列名（保持与前端兼容）
        df_daily = df_daily.rename(columns={
            'date': '日期',
            'symbol': '股票代码',
            'open': '开盘',
            'close': '收盘',
            'high': '最高',
            'low': '最低',
            'volume': '成交量',
            'amount': '成交额',
            'amplitude': '振幅',
            'pct_change': '涨跌幅',
            'change': '涨跌额',
            'turnover': '换手率'
        })
        
        # 计算技术指标 (使用转换后的中文列名)
        df = df_daily.copy()
        df['MA5'] = df['收盘'].rolling(window=5).mean()
        df['MA10'] = df['收盘'].rolling(window=10).mean()
        df['MA20'] = df['收盘'].rolling(window=20).mean()
        
        # RSI
        delta = df['收盘'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['收盘'].ewm(span=12, adjust=False).mean()
        exp2 = df['收盘'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # 最新数据
        latest = df.iloc[-1]
        
        # 支撑位/压力位 (简单计算)
        support = df['收盘'].min()
        resistance = df['收盘'].max()
        
        # 成交量变化
        vol_change = 0
        if len(df) >= 2:
            vol_change = (df['成交量'].iloc[-1] - df['成交量'].iloc[-2]) / df['成交量'].iloc[-2] * 100
        
        return {
            'name': q.get('名称', '未知'),  # 修正列名
            'code': code,
            'price': float(q.get('最新价', 0)),
            'change_pct': float(q.get('涨跌幅', 0)),
            'volume': float(q.get('成交量', 0)),
            'amount': float(q.get('成交额', 0)),
            'rsi': float(latest['RSI']) if pd.notna(latest['RSI']) else 50,
            'macd': float(latest['MACD']) if pd.notna(latest['MACD']) else 0,
            'signal': float(latest['Signal']) if pd.notna(latest['Signal']) else 0,
            'ma5': float(latest['MA5']) if pd.notna(latest['MA5']) else 0,
            'ma10': float(latest['MA10']) if pd.notna(latest['MA10']) else 0,
            'ma20': float(latest['MA20']) if pd.notna(latest['MA20']) else 0,
            'support': float(support),
            'resistance': float(resistance),
            'vol_change': float(vol_change),
            'trend': '上涨' if latest['收盘'] > df['收盘'].iloc[-20] else '下跌',
            'kline': df[['日期', '开盘', '最高', '最低', '收盘', '成交量']].tail(60).to_dict('records')
        }, None
        
    except Exception as e:
        return None, str(e)

def run_ai_analysis(task_id, stock_code, stock_data):
    """在后台线程运行AI分析"""
    try:
        # 创建TradingAgents实例
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "google"
        config["deep_think_llm"] = "gemini-2.0-flash"
        config["quick_think_llm"] = "gemini-2.0-flash"
        config["max_debate_rounds"] = 1
        config["online_tools"] = True
        
        ta = TradingAgentsGraph(debug=False, config=config)
        
        # 获取当前日期
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # 运行分析
        _, decision = ta.propagate(stock_code, current_date)
        
        analysis_tasks[task_id] = {
            'status': 'completed',
            'result': decision,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        analysis_tasks[task_id] = {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@app.route('/')
def index():
    return render_template('interactive_stock_v2.html')

@app.route('/api/health')
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'service': 'TradingAgents-CN Stock API'
    })

@app.route('/api/stock/<code>')
def get_stock(code):
    """获取股票数据API"""
    data, error = get_stock_data(code)
    if error:
        return jsonify({'error': error}), 404
    return jsonify(data)

@app.route('/api/analyze', methods=['POST'])
def analyze_stock():
    """AI分析API"""
    req = request.json
    stock_code = req.get('code')
    stock_data = req.get('data', {})
    
    if not stock_code:
        return jsonify({'error': '股票代码不能为空'}), 400
    
    # 创建任务ID
    task_id = f"{stock_code}_{datetime.now().timestamp()}"
    
    # 立即返回任务ID
    analysis_tasks[task_id] = {'status': 'processing'}
    
    # 在后台线程运行分析
    thread = threading.Thread(target=run_ai_analysis, args=(task_id, stock_code, stock_data))
    thread.start()
    
    return jsonify({'task_id': task_id, 'status': 'processing'})

@app.route('/api/analyze/<task_id>')
def get_analysis_result(task_id):
    """获取AI分析结果"""
    if task_id not in analysis_tasks:
        return jsonify({'error': '任务不存在'}), 404
    
    return jsonify(analysis_tasks[task_id])

@app.route('/api/analyze/sync', methods=['POST'])
def analyze_stock_sync():
    """同步AI分析API（直接返回结果）"""
    req = request.json
    stock_code = req.get('code')
    stock_data = req.get('data', {})
    
    if not stock_code:
        return jsonify({'error': '股票代码不能为空'}), 400
    
    try:
        # 创建TradingAgents实例
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "google"
        config["deep_think_llm"] = "gemini-2.0-flash"
        config["quick_think_llm"] = "gemini-2.0-flash"
        config["max_debate_rounds"] = 1
        config["online_tools"] = True
        
        ta = TradingAgentsGraph(debug=False, config=config)
        
        # 获取当前日期
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # 运行分析
        _, decision = ta.propagate(stock_code, current_date)
        
        return jsonify({
            'status': 'completed',
            'result': decision,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("TradingAgents Web API Server")
    print("=" * 50)
    print("启动服务: http://localhost:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
