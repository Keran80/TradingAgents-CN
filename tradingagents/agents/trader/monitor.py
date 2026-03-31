# -*- coding: utf-8 -*-
"""
自选股监控模块
集成 stock-monitor skill 的预警规则
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import json


class StockMonitor:
    """自选股监控器"""
    
    def __init__(self):
        self.watchlist: List[Dict] = []
        self.alerts: List[Dict] = []
    
    def add_stock(self, code: str, name: str, 
                 stock_type: str = "individual",
                 market: str = "sh",
                 cost: float = 0,
                 alerts_config: Optional[Dict] = None):
        """
        添加自选股
        
        Args:
            code: 股票代码（6位数字，如 600362）
            name: 股票名称
            stock_type: 个股类型 (individual/etf/gold)
            market: 市场 (sh/sz)
            cost: 持仓成本
            alerts_config: 预警配置
        """
        # 默认预警配置
        default_config = {
            "cost_pct_above": 15.0,
            "cost_pct_below": -12.0,
            "change_pct_above": 4.0 if stock_type == "individual" else 2.0,
            "change_pct_below": -4.0 if stock_type == "individual" else -2.0,
            "volume_surge": 2.0,
            "ma_monitor": True,
            "rsi_monitor": True,
            "gap_monitor": True,
            "trailing_stop": True,
        }
        
        config = alerts_config or default_config
        
        stock = {
            "code": code,
            "name": name,
            "type": stock_type,
            "market": market,
            "cost": cost,
            "alerts": config,
        }
        
        self.watchlist.append(stock)
        return self
    
    def check_alerts(self, stock_data: Dict) -> List[Dict]:
        """
        检查股票是否触发预警
        
        Args:
            stock_data: 股票实时数据
            
        Returns:
            List[Dict]: 触发预警列表
        """
        alerts = []
        code = stock_data.get('code', stock_data.get('ts_code', ''))
        
        # 查找对应自选股配置
        watch = next((s for s in self.watchlist if s['code'] == code), None)
        if not watch:
            return alerts
        
        config = watch['alerts']
        
        # 1. 成本百分比预警
        if watch['cost'] > 0:
            current_price = stock_data.get('close', 0)
            if current_price > 0:
                pct_change = (current_price - watch['cost']) / watch['cost'] * 100
                
                if pct_change >= config.get('cost_pct_above', 15):
                    alerts.append({
                        "level": "警告",
                        "rule": "成本百分比",
                        "message": f"盈利 {pct_change:.1f}% (>{config.get('cost_pct_above')}%)",
                        "action": "考虑止盈"
                    })
                elif pct_change <= config.get('cost_pct_below', -12):
                    alerts.append({
                        "level": "紧急",
                        "rule": "成本百分比",
                        "message": f"亏损 {abs(pct_change):.1f}% (<{config.get('cost_pct_below')}%)",
                        "action": "考虑止损"
                    })
        
        # 2. 日内涨跌幅预警
        change_pct = stock_data.get('pct_change', 0)
        threshold = config.get('change_pct_above', 4.0)
        
        if change_pct >= threshold:
            alerts.append({
                "level": "提醒",
                "rule": "日内涨幅",
                "message": f"涨幅 {change_pct:.2f}% (>{threshold}%)",
                "action": "关注是否封板"
            })
        elif change_pct <= -threshold:
            alerts.append({
                "level": "警告",
                "rule": "日内跌幅",
                "message": f"跌幅 {abs(change_pct):.2f}% (<{-threshold}%)",
                "action": "关注支撑位"
            })
        
        # 3. 成交量异动
        if 'volume' in stock_data and 'avg_volume' in stock_data:
            if stock_data['avg_volume'] > 0:
                volume_ratio = stock_data['volume'] / stock_data['avg_volume']
                
                if volume_ratio >= config.get('volume_surge', 2.0):
                    alerts.append({
                        "level": "警告",
                        "rule": "放量",
                        "message": f"成交量是均量的 {volume_ratio:.1f} 倍",
                        "action": "关注量价配合"
                    })
                elif volume_ratio <= 0.5:
                    alerts.append({
                        "level": "提醒",
                        "rule": "缩量",
                        "message": f"成交量是均量的 {volume_ratio:.1f} 倍",
                        "action": "观望为主"
                    })
        
        # 4. 均线金叉/死叉
        if config.get('ma_monitor', True) and 'ma5' in stock_data and 'ma10' in stock_data:
            ma5 = stock_data['ma5']
            ma10 = stock_data['ma10']
            
            if ma5 and ma10:
                # 简化判断：当前多头排列
                if ma5 > ma10:
                    alerts.append({
                        "level": "提醒",
                        "rule": "均线多头",
                        "message": f"MA5({ma5:.2f}) > MA10({ma10:.2f})",
                        "action": "保持多头思维"
                    })
                else:
                    alerts.append({
                        "level": "警告",
                        "rule": "均线空头",
                        "message": f"MA5({ma5:.2f}) < MA10({ma10:.2f})",
                        "action": "谨慎观望"
                    })
        
        # 5. RSI 超买超卖
        if config.get('rsi_monitor', True) and 'rsi' in stock_data:
            rsi = stock_data['rsi']
            
            if rsi:
                if rsi >= 70:
                    alerts.append({
                        "level": "警告",
                        "rule": "RSI超买",
                        "message": f"RSI({rsi:.1f}) >= 70",
                        "action": "考虑减仓"
                    })
                elif rsi <= 30:
                    alerts.append({
                        "level": "警告",
                        "rule": "RSI超卖",
                        "message": f"RSI({rsi:.1f}) <= 30",
                        "action": "关注反弹机会"
                    })
        
        return alerts
    
    def scan_watchlist(self, market_data: Dict) -> Dict:
        """
        扫描整个自选股列表
        
        Args:
            market_data: 市场数据 {code: data}
            
        Returns:
            Dict: 扫描结果
        """
        results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_stocks": len(self.watchlist),
            "alerts": [],
            "summary": {
                "urgent": 0,
                "warning": 0,
                "info": 0,
            }
        }
        
        for stock in self.watchlist:
            code = stock['code']
            data = market_data.get(code, {})
            
            if not data:
                continue
            
            stock_alerts = self.check_alerts(data)
            
            for alert in stock_alerts:
                alert['code'] = code
                alert['name'] = stock['name']
                results['alerts'].append(alert)
                
                # 统计分级
                if alert['level'] == '紧急':
                    results['summary']['urgent'] += 1
                elif alert['level'] == '警告':
                    results['summary']['warning'] += 1
                else:
                    results['summary']['info'] += 1
        
        return results
    
    def format_alerts(self, results: Dict) -> str:
        """格式化预警结果"""
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"  自选股监控报告 - {results['timestamp']}")
        lines.append(f"{'='*60}")
        lines.append(f"监控股票数: {results['total_stocks']}")
        lines.append(f"预警总数: {len(results['alerts'])}")
        lines.append(f"  紧急: {results['summary']['urgent']}")
        lines.append(f"  警告: {results['summary']['warning']}")
        lines.append(f"  提醒: {results['summary']['info']}")
        
        if results['alerts']:
            lines.append("\n【预警详情】")
            
            # 按级别排序
            level_order = {'紧急': 0, '警告': 1, '提醒': 2}
            sorted_alerts = sorted(results['alerts'], 
                                  key=lambda x: level_order.get(x['level'], 3))
            
            for alert in sorted_alerts:
                level_icon = {
                    '紧急': '[!]',
                    '警告': '[*]',
                    '提醒': '[i]'
                }.get(alert['level'], '[?]')
                
                lines.append(f"\n{level_icon} [{alert['level']}] {alert['code']} {alert['name']}")
                lines.append(f"   规则: {alert['rule']}")
                lines.append(f"   状态: {alert['message']}")
                lines.append(f"   建议: {alert['action']}")
        else:
            lines.append("\n✅ 无预警信号，保持现有仓位")
        
        return "\n".join(lines)


# 全局监控器实例
_monitor = StockMonitor()


def add_watch(code: str, name: str, **kwargs):
    """添加自选股便捷函数"""
    return _monitor.add_stock(code, name, **kwargs)


def check_stock(code: str, data: Dict) -> List[Dict]:
    """检查单只股票便捷函数"""
    return _monitor.check_alerts({"code": code, **data})


def scan_all(market_data: Dict) -> Dict:
    """扫描全部自选股便捷函数"""
    return _monitor.scan_watchlist(market_data)


if __name__ == "__main__":
    # 测试监控功能
    print("自选股监控测试")
    
    # 添加自选股
    monitor = StockMonitor()
    monitor.add_stock("600519", "贵州茅台", cost=1600)
    monitor.add_stock("000001", "平安银行", cost=12)
    monitor.add_stock("600362", "江西铜业", stock_type="individual", cost=57)
    
    # 模拟市场数据
    test_data = {
        "600519": {
            "close": 1850.0,
            "pct_change": 3.5,
            "volume": 50000000,
            "avg_volume": 30000000,
            "ma5": 1800,
            "ma10": 1750,
            "rsi": 72,
        },
        "000001": {
            "close": 11.5,
            "pct_change": -5.2,
            "volume": 150000000,
            "avg_volume": 80000000,
            "ma5": 11.2,
            "ma10": 11.8,
            "rsi": 28,
        },
    }
    
    results = monitor.scan_watchlist(test_data)
    print(monitor.format_alerts(results))
