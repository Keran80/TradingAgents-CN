"""
回测报告生成模块

支持生成多种格式的回测报告：
- HTML交互式报告
- JSON数据导出
- Markdown文本报告
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import json
import pandas as pd
from datetime import datetime


@dataclass
class ReportConfig:
    """报告配置"""
    strategy_name: str = "策略"
    include_charts: bool = True
    include_trades: bool = True
    include_equity_curve: bool = True
    chart_width: int = 800
    chart_height: int = 400


class ReportGenerator:
    """
    回测报告生成器
    
    使用示例：
    ```python
    from tradingagents.backtest import ReportGenerator, ReportConfig
    
    generator = ReportGenerator()
    
    # 生成HTML报告
    html_report = generator.generate_html_report(
        metrics=metrics,
        equity_curve=equity_df,
        trades=trades
    )
    
    # 保存报告
    with open('backtest_report.html', 'w', encoding='utf-8') as f:
        f.write(html_report)
        
    # 生成JSON导出
    json_data = generator.generate_json_export(
        metrics=metrics,
        equity_curve=equity_df,
        trades=trades
    )
    ```
    """
    
    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or ReportConfig()
        
    def generate_html_report(
        self,
        metrics,
        equity_curve: pd.DataFrame,
        trades: Optional[List] = None
    ) -> str:
        """
        生成HTML交互式报告
        
        Args:
            metrics: PerformanceMetrics对象
            equity_curve: 净值曲线 DataFrame
            trades: 交易记录列表
            
        Returns:
            HTML字符串
        """
        # 序列化metrics
        if hasattr(metrics, 'to_dict'):
            metrics_dict = metrics.to_dict()
        else:
            metrics_dict = metrics
            
        # 生成图表数据
        equity_json = self._serialize_equity_curve(equity_curve)
        trades_json = self._serialize_trades(trades) if trades else "[]"
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config.strategy_name} - 回测报告</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 24px;
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
        .header .subtitle {{ opacity: 0.9; }}
        .card {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .card h2 {{ 
            color: #333;
            font-size: 18px;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #667eea;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }}
        .metric {{
            background: #f8f9fa;
            padding: 16px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric .value {{
            font-size: 24px;
            font-weight: 700;
            color: #667eea;
        }}
        .metric .label {{
            color: #666;
            font-size: 14px;
            margin-top: 4px;
        }}
        .metric.positive .value {{ color: #e74c3c; }}
        .metric.negative .value {{ color: #27ae60; }}
        .chart-container {{
            width: 100%;
            height: 400px;
        }}
        .trade-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .trade-table th, .trade-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .trade-table th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .trade-table tr:hover {{
            background: #f8f9fa;
        }}
        .buy {{ color: #e74c3c; }}
        .sell {{ color: #27ae60; }}
        .footer {{
            text-align: center;
            color: #999;
            padding: 20px;
            font-size: 14px;
        }}
        @media (max-width: 768px) {{
            .metrics-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self.config.strategy_name}</h1>
            <div class="subtitle">回测报告 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        <!-- 绩效指标 -->
        <div class="card">
            <h2>绩效指标</h2>
            <div class="metrics-grid">
                <div class="metric {'positive' if '总收益率' in str(metrics_dict.get('total_return', '0%')) and float(str(metrics_dict.get('total_return', '0%')).replace('%','')) > 0 else 'negative'}">
                    <div class="value">{metrics_dict.get('total_return', 'N/A')}</div>
                    <div class="label">总收益率</div>
                </div>
                <div class="metric">
                    <div class="value">{metrics_dict.get('annual_return', 'N/A')}</div>
                    <div class="label">年化收益率</div>
                </div>
                <div class="metric">
                    <div class="value">{metrics_dict.get('sharpe_ratio', 'N/A')}</div>
                    <div class="label">夏普比率</div>
                </div>
                <div class="metric negative">
                    <div class="value">{metrics_dict.get('max_drawdown', 'N/A')}</div>
                    <div class="label">最大回撤</div>
                </div>
                <div class="metric">
                    <div class="value">{metrics_dict.get('win_rate', 'N/A')}</div>
                    <div class="label">胜率</div>
                </div>
                <div class="metric">
                    <div class="value">{metrics_dict.get('calmar_ratio', 'N/A')}</div>
                    <div class="label">卡玛比率</div>
                </div>
            </div>
        </div>
        
        <!-- 净值曲线 -->
        <div class="card">
            <h2>净值曲线</h2>
            <div id="equity-chart" class="chart-container"></div>
        </div>
        
        <!-- 回撤曲线 -->
        <div class="card">
            <h2>回撤曲线</h2>
            <div id="drawdown-chart" class="chart-container"></div>
        </div>
"""
        
        # 添加交易记录
        if trades and len(trades) > 0:
            html += """
        <!-- 交易记录 -->
        <div class="card">
            <h2>交易记录</h2>
            <table class="trade-table">
                <thead>
                    <tr>
                        <th>时间</th>
                        <th>股票</th>
                        <th>方向</th>
                        <th>价格</th>
                        <th>数量</th>
                        <th>金额</th>
                    </tr>
                </thead>
                <tbody>
"""
            for trade in trades[:50]:  # 只显示前50条
                direction_class = "buy" if trade.direction == "BUY" else "sell"
                html += f"""
                    <tr>
                        <td>{trade.timestamp}</td>
                        <td>{trade.symbol}</td>
                        <td class="{direction_class}">{trade.direction}</td>
                        <td>{trade.price:.2f}</td>
                        <td>{trade.quantity}</td>
                        <td>{trade.price * trade.quantity:.2f}</td>
                    </tr>
"""
            html += """
                </tbody>
            </table>
        </div>
"""
            
        # 添加JavaScript图表
        html += f"""
        <div class="footer">
            Generated by TradingAgents-CN
        </div>
    </div>
    
    <script>
        // 净值曲线数据
        const equityData = {equity_json};
        
        // 绘制净值曲线
        const equityTrace = {{
            x: equityData.dates,
            y: equityData.values,
            type: 'scatter',
            mode: 'lines',
            name: '策略净值',
            line: {{ color: '#667eea', width: 2 }},
            fill: 'tozeroy',
            fillcolor: 'rgba(102, 126, 234, 0.1)'
        }};
        
        const equityLayout = {{
            title: '',
            xaxis: {{ title: '日期', gridcolor: '#f0f0f0' }},
            yaxis: {{ title: '净值', gridcolor: '#f0f0f0' }},
            paper_bgcolor: 'white',
            plot_bgcolor: 'white',
            hovermode: 'x unified'
        }};
        
        Plotly.newPlot('equity-chart', [equityTrace], equityLayout, {{responsive: true}});
        
        // 计算并绘制回撤曲线
        const values = equityData.values;
        const runningMax = [];
        const drawdowns = [];
        
        let max = values[0];
        for (let v of values) {{
            if (v > max) max = v;
            runningMax.push(max);
            drawdowns.push(((v - max) / max) * 100);
        }}
        
        const drawdownTrace = {{
            x: equityData.dates,
            y: drawdowns,
            type: 'scatter',
            mode: 'lines',
            name: '回撤',
            line: {{ color: '#e74c3c', width: 2 }},
            fill: 'tozeroy',
            fillcolor: 'rgba(231, 76, 60, 0.1)'
        }};
        
        const drawdownLayout = {{
            title: '',
            xaxis: {{ title: '日期', gridcolor: '#f0f0f0' }},
            yaxis: {{ title: '回撤 (%)', gridcolor: '#f0f0f0', zeroline: true, zerolinecolor: '#ccc' }},
            paper_bgcolor: 'white',
            plot_bgcolor: 'white',
            hovermode: 'x unified'
        }};
        
        Plotly.newPlot('drawdown-chart', [drawdownTrace], drawdownLayout, {{responsive: true}});
    </script>
</body>
</html>"""
        
        return html
        
    def _serialize_equity_curve(self, equity_curve: pd.DataFrame) -> str:
        """序列化净值曲线为JSON"""
        if equity_curve is None or len(equity_curve) == 0:
            return '{"dates": [], "values": []}'
            
        dates = equity_curve.index.strftime('%Y-%m-%d').tolist()
        values = equity_curve['equity'].tolist()
        
        return json.dumps({'dates': dates, 'values': values}, ensure_ascii=False)
        
    def _serialize_trades(self, trades: List) -> str:
        """序列化交易记录为JSON"""
        if not trades:
            return "[]"
            
        trade_list = []
        for t in trades:
            trade_list.append({
                'timestamp': str(t.timestamp),
                'symbol': t.symbol,
                'direction': t.direction,
                'price': t.price,
                'quantity': t.quantity
            })
            
        return json.dumps(trade_list, ensure_ascii=False)
        
    def generate_json_export(
        self,
        metrics,
        equity_curve: pd.DataFrame,
        trades: Optional[List] = None
    ) -> str:
        """
        生成JSON数据导出
        
        Args:
            metrics: PerformanceMetrics对象
            equity_curve: 净值曲线
            trades: 交易记录
            
        Returns:
            JSON字符串
        """
        # 序列化metrics
        if hasattr(metrics, '__dict__'):
            metrics_dict = {}
            for key, value in metrics.__dict__.items():
                if isinstance(value, (int, float, str, bool, type(None))):
                    metrics_dict[key] = value
                elif isinstance(value, pd.DataFrame):
                    metrics_dict[key] = value.to_dict() if not value.empty else None
                elif isinstance(value, pd.Series):
                    metrics_dict[key] = value.to_dict() if len(value) > 0 else None
                else:
                    metrics_dict[key] = str(value)
        else:
            metrics_dict = metrics
            
        # 序列化净值曲线
        equity_dict = None
        if equity_curve is not None and len(equity_curve) > 0:
            equity_dict = {
                'dates': equity_curve.index.strftime('%Y-%m-%d').tolist(),
                'values': equity_curve['equity'].tolist()
            }
            
        # 序列化交易记录
        trades_list = []
        if trades:
            for t in trades:
                trades_list.append({
                    'timestamp': str(t.timestamp),
                    'symbol': t.symbol,
                    'direction': t.direction,
                    'price': t.price,
                    'quantity': t.quantity,
                    'commission': getattr(t, 'commission', 0),
                    'slippage': getattr(t, 'slippage', 0)
                })
                
        export_data = {
            'strategy_name': self.config.strategy_name,
            'generated_at': datetime.now().isoformat(),
            'metrics': metrics_dict,
            'equity_curve': equity_dict,
            'trades': trades_list
        }
        
        return json.dumps(export_data, ensure_ascii=False, indent=2)
        
    def generate_markdown_report(
        self,
        metrics,
        equity_curve: Optional[pd.DataFrame] = None,
        trades: Optional[List] = None
    ) -> str:
        """
        生成Markdown文本报告
        
        Args:
            metrics: PerformanceMetrics对象
            equity_curve: 净值曲线
            trades: 交易记录
            
        Returns:
            Markdown字符串
        """
        if hasattr(metrics, 'to_dict'):
            metrics_dict = metrics.to_dict()
        else:
            metrics_dict = metrics
            
        md = []
        md.append(f"# {self.config.strategy_name} 回测报告")
        md.append("")
        md.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append("")
        
        # 收益指标
        md.append("## 收益指标")
        md.append("")
        md.append(f"| 指标 | 数值 |")
        md.append(f"|------|------|")
        md.append(f"| 总收益率 | {metrics_dict.get('total_return', 'N/A')} |")
        md.append(f"| 年化收益率 | {metrics_dict.get('annual_return', 'N/A')} |")
        md.append(f"| 卡玛比率 | {metrics_dict.get('calmar_ratio', 'N/A')} |")
        md.append("")
        
        # 风险指标
        md.append("## 风险指标")
        md.append("")
        md.append(f"| 指标 | 数值 |")
        md.append(f"|------|------|")
        md.append(f"| 最大回撤 | {metrics_dict.get('max_drawdown', 'N/A')} |")
        md.append(f"| 回撤持续 | {metrics_dict.get('max_drawdown_duration', 'N/A')} |")
        md.append(f"| 年化波动率 | {metrics_dict.get('volatility', 'N/A')} |")
        md.append(f"| VaR (95%) | {metrics_dict.get('var_95', 'N/A')} |")
        md.append("")
        
        # 风险调整收益
        md.append("## 风险调整收益")
        md.append("")
        md.append(f"| 指标 | 数值 |")
        md.append(f"|------|------|")
        md.append(f"| 夏普比率 | {metrics_dict.get('sharpe_ratio', 'N/A')} |")
        md.append(f"| 索提诺比率 | {metrics_dict.get('sortino_ratio', 'N/A')} |")
        md.append(f"| 信息比率 | {metrics_dict.get('information_ratio', 'N/A')} |")
        md.append("")
        
        # 交易统计
        if 'total_trades' in metrics_dict:
            md.append("## 交易统计")
            md.append("")
            md.append(f"| 指标 | 数值 |")
            md.append(f"|------|------|")
            md.append(f"| 总交易次数 | {metrics_dict.get('total_trades', 'N/A')} |")
            md.append(f"| 盈利次数 | {metrics_dict.get('winning_trades', 'N/A')} |")
            md.append(f"| 亏损次数 | {metrics_dict.get('losing_trades', 'N/A')} |")
            md.append(f"| 胜率 | {metrics_dict.get('win_rate', 'N/A')} |")
            md.append(f"| 盈亏比 | {metrics_dict.get('profit_loss_ratio', 'N/A')} |")
            md.append("")
            
        return "\n".join(md)
