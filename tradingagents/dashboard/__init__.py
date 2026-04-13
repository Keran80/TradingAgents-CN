# -*- coding: utf-8 -*-
"""
Dashboard Web 服务
提供交互式监控界面
"""

from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO
from datetime import datetime
import threading
import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

# 导入 Dashboard 组件
from .heatmap import HeatmapGenerator, PortfolioHeatmap
from .charts import ChartGenerator
from .metrics import MetricsCalculator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tradingagents-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ============== 数据模型 ==============

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    URGENT = "urgent"

@dataclass
class Position:
    """持仓"""
    symbol: str
    name: str
    quantity: float
    avg_cost: float
    current_price: float
    change_pct: float
    market_value: float
    profit_loss: float
    profit_pct: float

@dataclass
class Account:
    """账户"""
    account_id: str
    name: str
    total_assets: float
    cash: float
    positions_value: float
    total_profit: float
    profit_pct: float
    positions: List[Position] = field(default_factory=list)

@dataclass
class Performance:
    """策略表现"""
    strategy_name: str
    total_return: float
    daily_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trade_count: int
    period: str

@dataclass
class AlertRecord:
    """告警记录"""
    id: str
    time: str
    level: str
    title: str
    message: str
    symbol: Optional[str] = None

# ============== Dashboard 状态 ==============

class DashboardState:
    """Dashboard 全局状态"""
    
    def __init__(self):
        self.accounts: Dict[str, Account] = {}
        self.performance: Dict[str, Performance] = {}
        self.alerts: List[AlertRecord] = []
        self.market_data: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._update_thread: Optional[threading.Thread] = None
        self._running = False
    
    def update_account(self, account: Account):
        with self._lock:
            self.accounts[account.account_id] = account
    
    def update_performance(self, perf: Performance):
        with self._lock:
            self.performance[perf.strategy_name] = perf
    
    def add_alert(self, alert: AlertRecord):
        with self._lock:
            self.alerts.append(alert)
            # 保持最近100条
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
    
    def update_market_data(self, data: Dict[str, Any]):
        with self._lock:
            self.market_data = data
    
    def get_state(self) -> Dict[str, Any]:
        with self._lock:
            return {
                'accounts': {
                    k: {
                        'account_id': v.account_id,
                        'name': v.name,
                        'total_assets': v.total_assets,
                        'cash': v.cash,
                        'positions_value': v.positions_value,
                        'total_profit': v.total_profit,
                        'profit_pct': v.profit_pct,
                        'positions': [
                            {
                                'symbol': p.symbol,
                                'name': p.name,
                                'quantity': p.quantity,
                                'avg_cost': p.avg_cost,
                                'current_price': p.current_price,
                                'change_pct': p.change_pct,
                                'market_value': p.market_value,
                                'profit_loss': p.profit_loss,
                                'profit_pct': p.profit_pct,
                            }
                            for p in v.positions
                        ]
                    }
                    for k, v in self.accounts.items()
                },
                'performance': {k: asdict(v) for k, v in self.performance.items()},
                'alerts': [
                    {
                        'id': a.id,
                        'time': a.time,
                        'level': a.level,
                        'title': a.title,
                        'message': a.message,
                        'symbol': a.symbol,
                    }
                    for a in self.alerts[-50:]
                ],
                'market_data': self.market_data,
                'timestamp': datetime.now().isoformat()
            }

# 全局状态
dashboard_state = DashboardState()

# ============== 演示数据 ==============

def generate_demo_data():
    """生成演示数据"""
    # 模拟账户
    positions = [
        Position(
            symbol="000001.SZ",
            name="平安银行",
            quantity=10000,
            avg_cost=12.50,
            current_price=13.20,
            change_pct=1.25,
            market_value=132000,
            profit_loss=7000,
            profit_pct=5.6
        ),
        Position(
            symbol="600519.SH",
            name="贵州茅台",
            quantity=100,
            avg_cost=1650.0,
            current_price=1720.0,
            change_pct=-0.5,
            market_value=172000,
            profit_loss=7000,
            profit_pct=4.24
        ),
        Position(
            symbol="000858.SZ",
            name="五粮液",
            quantity=2000,
            avg_cost=145.0,
            current_price=152.5,
            change_pct=2.1,
            market_value=305000,
            profit_loss=15000,
            profit_pct=5.17
        ),
    ]
    
    account = Account(
        account_id="demo_account",
        name="模拟实盘账户",
        total_assets=1000000,
        cash=391000,
        positions_value=609000,
        total_profit=50000,
        profit_pct=5.26,
        positions=positions
    )
    dashboard_state.update_account(account)
    
    # 模拟策略表现
    perf = Performance(
        strategy_name="趋势跟随策略",
        total_return=25.8,
        daily_return=0.35,
        sharpe_ratio=1.85,
        max_drawdown=-8.5,
        win_rate=0.62,
        trade_count=156,
        period="近30日"
    )
    dashboard_state.update_performance(perf)
    
    perf2 = Performance(
        strategy_name="均值回归策略",
        total_return=18.2,
        daily_return=-0.12,
        sharpe_ratio=1.42,
        max_drawdown=-12.3,
        win_rate=0.58,
        trade_count=89,
        period="近30日"
    )
    dashboard_state.update_performance(perf2)
    
    # 模拟告警
    alerts = [
        AlertRecord(
            id="1",
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            level="warning",
            title="价格异动",
            message="贵州茅台5分钟内涨幅超过3%",
            symbol="600519.SH"
        ),
        AlertRecord(
            id="2",
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            level="info",
            title="策略信号",
            message="趋势策略发出买入信号: 平安银行",
            symbol="000001.SZ"
        ),
        AlertRecord(
            id="3",
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            level="critical",
            title="止损触发",
            message="五粮液触及止损线，已自动平仓",
            symbol="000858.SZ"
        ),
    ]
    for a in alerts:
        dashboard_state.add_alert(a)
    
    # 模拟行情
    dashboard_state.update_market_data({
        "000001.SZ": {"price": 13.20, "change": 0.16},
        "600519.SH": {"price": 1720.0, "change": -8.6},
        "000858.SZ": {"price": 152.5, "change": 3.14},
    })

# ============== Web 路由 ==============

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TradingAgents Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #1a1d23;
            --bg-card: #242830;
            --text-primary: #e8eaed;
            --text-secondary: #9aa0a6;
            --accent-green: #34d399;
            --accent-red: #f87171;
            --accent-blue: #60a5fa;
            --accent-yellow: #fbbf24;
            --border-color: #3c4043;
        }
        
        body {
            background: var(--bg-dark);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .navbar {
            background: var(--bg-card);
            border-bottom: 1px solid var(--border-color);
        }
        
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            margin-bottom: 20px;
        }
        
        .card-header {
            background: transparent;
            border-bottom: 1px solid var(--border-color);
            font-weight: 600;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
        }
        
        .metric-label {
            color: var(--text-secondary);
            font-size: 0.875rem;
        }
        
        .profit-positive { color: var(--accent-green); }
        .profit-negative { color: var(--accent-red); }
        
        .alert-info { background: rgba(96, 165, 250, 0.1); border-color: var(--accent-blue); }
        .alert-warning { background: rgba(251, 191, 36, 0.1); border-color: var(--accent-yellow); }
        .alert-critical { background: rgba(248, 113, 113, 0.1); border-color: var(--accent-red); }
        
        .position-row:hover {
            background: rgba(255,255,255,0.05);
        }
        
        .tab-content {
            padding: 20px 0;
        }
        
        .nav-tabs .nav-link {
            color: var(--text-secondary);
            border: none;
        }
        
        .nav-tabs .nav-link.active {
            color: var(--text-primary);
            background: transparent;
            border-bottom: 2px solid var(--accent-blue);
        }
        
        .strategy-card {
            border-left: 4px solid var(--accent-blue);
        }
        
        .loading-spinner {
            display: inline-block;
            width: 1rem;
            height: 1rem;
            border: 2px solid var(--border-color);
            border-top-color: var(--accent-blue);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .last-update {
            color: var(--text-secondary);
            font-size: 0.75rem;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">
                <i class="bi bi-graph-up-arrow me-2"></i>
                TradingAgents Dashboard
            </a>
            <span class="navbar-text">
                <span class="last-update">最后更新: <span id="lastUpdate">--</span></span>
            </span>
        </div>
    </nav>
    
    <div class="container-fluid py-4">
        <!-- 账户概览 -->
        <div class="row">
            <div class="col-md-3">
                <div class="card">
                    <div class="card-body text-center">
                        <div class="metric-label">总资产</div>
                        <div class="metric-value" id="totalAssets">--</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card">
                    <div class="card-body text-center">
                        <div class="metric-label">持仓市值</div>
                        <div class="metric-value" id="positionsValue">--</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card">
                    <div class="card-body text-center">
                        <div class="metric-label">总收益</div>
                        <div class="metric-value" id="totalProfit">--</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card">
                    <div class="card-body text-center">
                        <div class="metric-label">收益率</div>
                        <div class="metric-value" id="profitPct">--</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Tabs -->
        <ul class="nav nav-tabs" id="dashboardTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="positions-tab" data-bs-toggle="tab" data-bs-target="#positions" type="button">
                    <i class="bi bi-list-ul me-1"></i>持仓监控
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="performance-tab" data-bs-toggle="tab" data-bs-target="#performance" type="button">
                    <i class="bi bi-bar-chart me-1"></i>策略表现
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="alerts-tab" data-bs-toggle="tab" data-bs-target="#alerts" type="button">
                    <i class="bi bi-bell me-1"></i>告警历史
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="heatmap-tab" data-bs-toggle="tab" data-bs-target="#heatmap" type="button">
                    <i class="bi bi-grid-3x3 me-1"></i>热力图
                </button>
            </li>
        </ul>
        
        <div class="tab-content" id="dashboardTabsContent">
            <!-- 持仓监控 -->
            <div class="tab-pane fade show active" id="positions" role="tabpanel">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <span>实时持仓</span>
                        <span class="badge bg-primary" id="positionCount">0</span>
                    </div>
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-dark table-hover mb-0">
                                <thead>
                                    <tr>
                                        <th>股票</th>
                                        <th class="text-end">持仓量</th>
                                        <th class="text-end">成本价</th>
                                        <th class="text-end">现价</th>
                                        <th class="text-end">涨跌幅</th>
                                        <th class="text-end">市值</th>
                                        <th class="text-end">盈亏</th>
                                        <th class="text-end">盈亏%</th>
                                    </tr>
                                </thead>
                                <tbody id="positionsTable">
                                    <tr><td colspan="8" class="text-center text-muted">加载中...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 策略表现 -->
            <div class="tab-pane fade" id="performance" role="tabpanel">
                <div class="row" id="performanceCards">
                    <!-- 策略卡片将通过 JS 注入 -->
                </div>
            </div>
            
            <!-- 告警历史 -->
            <div class="tab-pane fade" id="alerts" role="tabpanel">
                <div class="card">
                    <div class="card-header">最近告警</div>
                    <div class="card-body p-0">
                        <div class="list-group list-group-flush" id="alertsList">
                            <div class="list-group-item text-muted text-center">加载中...</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 热力图 -->
            <div class="tab-pane fade" id="heatmap" role="tabpanel">
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">行业分布热力图</div>
                            <div class="card-body">
                                <canvas id="sectorHeatmap" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">收益日历</div>
                            <div class="card-body">
                                <canvas id="returnCalendar" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let updateInterval = null;
        
        async function fetchData() {
            try {
                const resp = await fetch('/api/state');
                const data = await resp.json();
                updateDashboard(data);
            } catch (e) {
                console.error('获取数据失败:', e);
            }
        }
        
        function updateDashboard(data) {
            // 更新时间
            document.getElementById('lastUpdate').textContent = new Date(data.timestamp).toLocaleTimeString();
            
            // 更新账户概览
            const accounts = Object.values(data.accounts)[0];
            if (accounts) {
                document.getElementById('totalAssets').textContent = formatNumber(accounts.total_assets);
                document.getElementById('positionsValue').textContent = formatNumber(accounts.positions_value);
                document.getElementById('totalProfit').textContent = formatNumber(accounts.total_profit);
                const profitEl = document.getElementById('profitPct');
                profitEl.textContent = accounts.profit_pct.toFixed(2) + '%';
                profitEl.className = 'metric-value ' + (accounts.profit_pct >= 0 ? 'profit-positive' : 'profit-negative');
            }
            
            // 更新持仓表格
            updatePositionsTable(accounts?.positions || []);
            
            // 更新策略表现
            updatePerformanceCards(data.performance);
            
            // 更新告警
            updateAlertsList(data.alerts);
            
            // 更新热力图
            updateHeatmaps(data);
        }
        
        function formatNumber(num) {
            if (num >= 10000) {
                return (num / 10000).toFixed(2) + '万';
            }
            return num?.toFixed(2) || '0';
        }
        
        function updatePositionsTable(positions) {
            const tbody = document.getElementById('positionsTable');
            document.getElementById('positionCount').textContent = positions.length;
            
            if (positions.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">暂无持仓</td></tr>';
                return;
            }
            
            tbody.innerHTML = positions.map(p => `
                <tr class="position-row">
                    <td>
                        <strong>${p.symbol}</strong><br>
                        <small class="text-muted">${p.name}</small>
                    </td>
                    <td class="text-end">${p.quantity.toLocaleString()}</td>
                    <td class="text-end">${p.avg_cost.toFixed(2)}</td>
                    <td class="text-end">${p.current_price.toFixed(2)}</td>
                    <td class="text-end ${p.change_pct >= 0 ? 'profit-positive' : 'profit-negative'}">
                        ${p.change_pct >= 0 ? '+' : ''}${p.change_pct.toFixed(2)}%
                    </td>
                    <td class="text-end">${formatNumber(p.market_value)}</td>
                    <td class="text-end ${p.profit_loss >= 0 ? 'profit-positive' : 'profit-negative'}">
                        ${p.profit_loss >= 0 ? '+' : ''}${formatNumber(p.profit_loss)}
                    </td>
                    <td class="text-end ${p.profit_pct >= 0 ? 'profit-positive' : 'profit-negative'}">
                        ${p.profit_pct >= 0 ? '+' : ''}${p.profit_pct.toFixed(2)}%
                    </td>
                </tr>
            `).join('');
        }
        
        function updatePerformanceCards(performance) {
            const container = document.getElementById('performanceCards');
            const strategies = Object.values(performance);
            
            if (strategies.length === 0) {
                container.innerHTML = '<div class="col-12 text-center text-muted">暂无策略数据</div>';
                return;
            }
            
            container.innerHTML = strategies.map(s => `
                <div class="col-md-6">
                    <div class="card strategy-card">
                        <div class="card-header">${s.strategy_name} <span class="badge bg-secondary">${s.period}</span></div>
                        <div class="card-body">
                            <div class="row text-center">
                                <div class="col-4">
                                    <div class="metric-label">总收益</div>
                                    <div class="metric-value ${s.total_return >= 0 ? 'profit-positive' : 'profit-negative'}">
                                        ${s.total_return >= 0 ? '+' : ''}${s.total_return.toFixed(2)}%
                                    </div>
                                </div>
                                <div class="col-4">
                                    <div class="metric-label">夏普比率</div>
                                    <div class="metric-value">${s.sharpe_ratio.toFixed(2)}</div>
                                </div>
                                <div class="col-4">
                                    <div class="metric-label">胜率</div>
                                    <div class="metric-value">${(s.win_rate * 100).toFixed(1)}%</div>
                                </div>
                            </div>
                            <hr>
                            <div class="row text-center text-muted">
                                <div class="col-4"><small>最大回撤: ${s.max_drawdown.toFixed(1)}%</small></div>
                                <div class="col-4"><small>交易次数: ${s.trade_count}</small></div>
                                <div class="col-4"><small>日收益: ${s.daily_return >= 0 ? '+' : ''}${s.daily_return.toFixed(2)}%</small></div>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }
        
        function updateAlertsList(alerts) {
            const container = document.getElementById('alertsList');
            
            if (!alerts || alerts.length === 0) {
                container.innerHTML = '<div class="list-group-item text-muted text-center">暂无告警</div>';
                return;
            }
            
            const levelColors = {
                'info': 'alert-info',
                'warning': 'alert-warning', 
                'critical': 'alert-critical',
                'urgent': 'alert-danger'
            };
            
            const levelIcons = {
                'info': '<i class="bi bi-info-circle text-info"></i>',
                'warning': '<i class="bi bi-exclamation-triangle text-warning"></i>',
                'critical': '<i class="bi bi-exclamation-octagon text-danger"></i>',
                'urgent': '<i class="bi bi-x-circle text-danger"></i>'
            };
            
            container.innerHTML = alerts.map(a => `
                <div class="list-group-item ${levelColors[a.level] || ''}">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">${levelIcons[a.level] || ''} ${a.title}</h6>
                        <small class="text-muted">${a.time}</small>
                    </div>
                    <p class="mb-1">${a.message}</p>
                    ${a.symbol ? `<small class="text-muted">股票: ${a.symbol}</small>` : ''}
                </div>
            `).join('');
        }
        
        function updateHeatmaps(data) {
            // 行业热力图
            const sectorCtx = document.getElementById('sectorHeatmap');
            if (sectorCtx && window.sectorChart) {
                window.sectorChart.destroy();
            }
            if (sectorCtx) {
                window.sectorChart = new Chart(sectorCtx, {
                    type: 'bar',
                    data: {
                        labels: ['银行', '白酒', '新能源', '医药', '科技', '消费'],
                        datasets: [{
                            label: '持仓占比%',
                            data: [15, 25, 12, 8, 20, 20],
                            backgroundColor: [
                                'rgba(96, 165, 250, 0.8)',
                                'rgba(52, 211, 153, 0.8)',
                                'rgba(251, 191, 36, 0.8)',
                                'rgba(248, 113, 113, 0.8)',
                                'rgba(167, 139, 250, 0.8)',
                                'rgba(251, 146, 60, 0.8)',
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { beginAtZero: true, grid: { color: '#3c4043' } },
                            x: { grid: { display: false } }
                        }
                    }
                });
            }
            
            // 收益日历
            const calendarCtx = document.getElementById('returnCalendar');
            if (calendarCtx && window.calendarChart) {
                window.calendarChart.destroy();
            }
            if (calendarCtx) {
                window.calendarChart = new Chart(calendarCtx, {
                    type: 'line',
                    data: {
                        labels: Array.from({length: 30}, (_, i) => `${i+1}日`),
                        datasets: [{
                            label: '每日收益%',
                            data: Array.from({length: 30}, () => (Math.random() - 0.4) * 3),
                            borderColor: '#60a5fa',
                            backgroundColor: 'rgba(96, 165, 250, 0.1)',
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { grid: { color: '#3c4043' } },
                            x: { grid: { display: false } }
                        }
                    }
                });
            }
        }
        
        // 启动自动刷新
        function startAutoUpdate() {
            fetchData(); // 立即获取一次
            updateInterval = setInterval(fetchData, 5000); // 每5秒刷新
        }
        
        document.addEventListener('DOMContentLoaded', startAutoUpdate);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/state')
def get_state():
    """获取Dashboard状态"""
    return jsonify(dashboard_state.get_state())

@app.route('/api/positions', methods=['POST'])
def update_positions():
    """更新持仓数据"""
    data = request.json
    account_id = data.get('account_id', 'default')
    
    positions = []
    for p in data.get('positions', []):
        position = Position(
            symbol=p['symbol'],
            name=p.get('name', p['symbol']),
            quantity=p['quantity'],
            avg_cost=p['avg_cost'],
            current_price=p['current_price'],
            change_pct=p.get('change_pct', 0),
            market_value=p.get('market_value', p['quantity'] * p['current_price']),
            profit_loss=p.get('profit_loss', 0),
            profit_pct=p.get('profit_pct', 0)
        )
        positions.append(position)
    
    account = Account(
        account_id=account_id,
        name=data.get('name', '账户'),
        total_assets=data.get('total_assets', 0),
        cash=data.get('cash', 0),
        positions_value=data.get('positions_value', 0),
        total_profit=data.get('total_profit', 0),
        profit_pct=data.get('profit_pct', 0),
        positions=positions
    )
    dashboard_state.update_account(account)
    
    # 广播更新
    socketio.emit('data_update', dashboard_state.get_state())
    
    return jsonify({'status': 'ok'})

@app.route('/api/alerts', methods=['POST'])
def add_alert():
    """添加告警"""
    data = request.json
    alert = AlertRecord(
        id=str(int(time.time())),
        time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        level=data.get('level', 'info'),
        title=data.get('title', ''),
        message=data.get('message', ''),
        symbol=data.get('symbol')
    )
    dashboard_state.add_alert(alert)
    
    # 广播更新
    socketio.emit('alert_new', asdict(alert))
    
    return jsonify({'status': 'ok', 'alert_id': alert.id})

# ============== 启动函数 ==============

def run_dashboard(host='0.0.0.0', port=8888, debug=False):
    """运行Dashboard服务"""
    # 生成演示数据
    generate_demo_data()
    
    print(f"\n{'='*50}")
    print(f"TradingAgents Dashboard 启动中...")
    print(f"访问地址: http://localhost:{port}")
    print(f"{'='*50}\n")
    
    socketio.run(app, host=host, port=port, debug=debug)

# 直接运行
if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    run_dashboard(port=port, debug=True)