# -*- coding: utf-8 -*-
"""
每日复盘模块
集成 stock-daily-analysis skill 的分析框架
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json


class DailyAnalysis:
    """每日复盘分析"""
    
    def __init__(self):
        self.analysis_cache = {}
    
    def get_market_data(self, ticker: str) -> Optional[Dict]:
        """
        获取市场数据
        
        Args:
            ticker: 股票代码
            
        Returns:
            Dict: 市场数据
        """
        try:
            from tradingagents.dataflows.astock_utils import AStockData
            from tradingagents.dataflows.astock_technical import AStockTechnical
            
            # 获取最近60天数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=120)).strftime('%Y%m%d')
            
            df = AStockData.get_daily(ticker, start_date, end_date)
            
            if df.empty:
                return None
            
            # 列名转换
            rename_map = {
                '日期': 'date', '开盘': 'open', '收盘': 'close',
                '最高': 'high', '最低': 'low', '成交量': 'volume',
                '股票简称': 'name'
            }
            df = df.rename(columns=rename_map)
            
            # 计算技术指标
            df = AStockTechnical.calculate_all(df)
            
            latest = df.iloc[-1]
            
            return {
                'ticker': ticker,
                'name': latest.get('name', ticker),
                'date': str(latest.get('date', '')),
                'close': latest.get('close'),
                'pct_change': latest.get('pct_change'),
                'volume': latest.get('volume'),
                'ma5': latest.get('ma5'),
                'ma10': latest.get('ma10'),
                'ma20': latest.get('ma20'),
                'ma30': latest.get('ma30'),
                'ma60': latest.get('ma60'),
                'macd': latest.get('macd'),
                'macds': latest.get('macds'),
                'macdh': latest.get('macdh'),
                'rsi': latest.get('rsi'),
                'kdj_k': latest.get('kdj_k'),
                'kdj_d': latest.get('kdj_d'),
                'kdj_j': latest.get('kdj_j'),
                'boll_upper': latest.get('boll_upper'),
                'boll_mid': latest.get('boll_mid'),
                'boll_lower': latest.get('boll_lower'),
                'atr': latest.get('atr'),
            }
        except Exception as e:
            print(f"获取数据失败: {e}")
            return None
    
    def analyze_ma(self, data: Dict) -> Dict:
        """均线分析"""
        ma5 = data.get('ma5')
        ma10 = data.get('ma10')
        ma20 = data.get('ma20')
        
        result = {
            'status': 'unknown',
            'score': 0,
            'reason': '',
        }
        
        if all(v and v == v for v in [ma5, ma10, ma20]):
            # 多头排列
            if ma5 > ma10 > ma20:
                result['status'] = 'bullish'
                result['score'] = 25
                result['reason'] = f'MA5({ma5:.2f}) > MA10({ma10:.2f}) > MA20({ma20:.2f}) 多头排列'
            # 空头排列
            elif ma5 < ma10 < ma20:
                result['status'] = 'bearish'
                result['score'] = 0
                result['reason'] = f'MA5({ma5:.2f}) < MA10({ma10:.2f}) < MA20({ma20:.2f}) 空头排列'
            # 震荡
            else:
                result['status'] = 'neutral'
                result['score'] = 10
                result['reason'] = '均线震荡整理'
        
        return result
    
    def analyze_macd(self, data: Dict) -> Dict:
        """MACD分析"""
        macd = data.get('macd')
        macds = data.get('macds')
        
        result = {
            'status': 'unknown',
            'score': 0,
            'reason': '',
        }
        
        if macd and macds and macd == macd and macds == macds:
            # 金叉
            # 需要前一交易日的数据才能判断金叉，这里简化处理
            if macd > macds:
                result['status'] = 'bullish'
                result['score'] = 25
                result['reason'] = f'MACD({macd:.4f}) > Signal({macds:.4f}) 多头'
            else:
                result['status'] = 'bearish'
                result['score'] = 0
                result['reason'] = f'MACD({macd:.4f}) < Signal({macds:.4s}) 空头'
        
        return result
    
    def analyze_rsi(self, data: Dict) -> Dict:
        """RSI分析"""
        rsi = data.get('rsi')
        
        result = {
            'status': 'unknown',
            'score': 0,
            'reason': '',
        }
        
        if rsi and rsi == rsi:
            if rsi > 70:
                result['status'] = 'overbought'
                result['score'] = 0
                result['reason'] = f'RSI({rsi:.1f}) 超买区域，注意回调风险'
            elif rsi < 30:
                result['status'] = 'oversold'
                result['score'] = 15
                result['reason'] = f'RSI({rsi:.1f}) 超卖区域，关注反弹机会'
            elif 40 <= rsi <= 70:
                result['status'] = 'strong'
                result['score'] = 20
                result['reason'] = f'RSI({rsi:.1f}) 强势区域'
            else:
                result['status'] = 'neutral'
                result['score'] = 10
                result['reason'] = f'RSI({rsi:.1f}) 震荡区域'
        
        return result
    
    def analyze_volume(self, data: Dict) -> Dict:
        """成交量分析"""
        volume = data.get('volume')
        
        result = {
            'status': 'unknown',
            'score': 0,
            'reason': '',
        }
        
        if volume:
            # 这里简化处理，实际应计算平均量
            if volume > 100000000:  # 1亿以上算放量
                result['status'] = 'surge'
                result['score'] = 15
                result['reason'] = f'成交量放大: {volume/100000000:.1f}亿'
            else:
                result['status'] = 'normal'
                result['score'] = 10
                result['reason'] = '成交量正常'
        
        return result
    
    def calculate_bias(self, data: Dict) -> float:
        """计算乖离率"""
        close = data.get('close')
        ma5 = data.get('ma5')
        
        if close and ma5 and close == close and ma5 == ma5:
            return (close - ma5) / ma5 * 100
        return 0
    
    def analyze(self, ticker: str) -> Dict:
        """
        执行完整分析
        
        Args:
            ticker: 股票代码
            
        Returns:
            Dict: 分析结果
        """
        # 获取数据
        data = self.get_market_data(ticker)
        
        if not data:
            return {'error': f'无法获取 {ticker} 的数据'}
        
        # 各项分析
        ma_analysis = self.analyze_ma(data)
        macd_analysis = self.analyze_macd(data)
        rsi_analysis = self.analyze_rsi(data)
        volume_analysis = self.analyze_volume(data)
        bias = self.calculate_bias(data)
        
        # 计算总分
        total_score = (
            ma_analysis['score'] +
            macd_analysis['score'] +
            rsi_analysis['score'] +
            volume_analysis['score']
        )
        
        # 评级
        if total_score >= 85:
            rating = '强烈买入'
        elif total_score >= 70:
            rating = '买入'
        elif total_score >= 50:
            rating = '观望'
        else:
            rating = '卖出'
        
        return {
            'ticker': ticker,
            'name': data.get('name', ticker),
            'date': data.get('date'),
            'close': data.get('close'),
            'pct_change': data.get('pct_change'),
            'analysis': {
                'ma': ma_analysis,
                'macd': macd_analysis,
                'rsi': rsi_analysis,
                'volume': volume_analysis,
                'bias': bias,
            },
            'score': total_score,
            'rating': rating,
        }
    
    def format_report(self, result: Dict) -> str:
        """格式化分析报告"""
        if 'error' in result:
            return f"分析错误: {result['error']}"
        
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"  {result['name']}({result['ticker']}) 每日分析")
        lines.append(f"{'='*60}")
        lines.append(f"日期: {result['date']}")
        lines.append(f"收盘价: {result['close']:.2f}")
        if result.get('pct_change'):
            change = result['pct_change']
            sign = '+' if change > 0 else ''
            lines.append(f"涨跌幅: {sign}{change:.2f}%")
        
        lines.append("\n【技术指标】")
        
        ma = result['analysis']['ma']
        lines.append(f"均线: {ma['reason']} ({ma['score']}分)")
        
        macd = result['analysis']['macd']
        lines.append(f"MACD: {macd['reason']} ({macd['score']}分)")
        
        rsi = result['analysis']['rsi']
        lines.append(f"RSI: {rsi['reason']} ({rsi['score']}分)")
        
        vol = result['analysis']['volume']
        lines.append(f"成交量: {vol['reason']} ({vol['score']}分)")
        
        bias = result['analysis']['bias']
        lines.append(f"乖离率: {bias:+.2f}%")
        
        lines.append(f"\n【信号评分】: {result['score']}/100")
        lines.append(f"【评级】: {result['rating']}")
        
        # 操作建议
        lines.append("\n【操作建议】")
        
        if result['score'] >= 85:
            lines.append("- 强烈买入信号，可考虑建仓或加仓")
            lines.append(f"- 止损位: {result['close'] * 0.95:.2f} (-5%)")
        elif result['score'] >= 70:
            lines.append("- 买入信号，可适当建仓")
            lines.append(f"- 止损位: {result['close'] * 0.93:.2f} (-7%)")
        elif result['score'] >= 50:
            lines.append("- 建议观望，等待更明确信号")
        else:
            lines.append("- 建议卖出或减仓")
            lines.append(f"- 止损位: {result['close'] * 0.90:.2f} (-10%)")
        
        lines.append("\n" + "="*60)
        
        return "\n".join(lines)


def analyze_stock(ticker: str) -> Dict:
    """便捷分析函数"""
    analyzer = DailyAnalysis()
    return analyzer.analyze(ticker)


def generate_report(ticker: str) -> str:
    """生成分析报告便捷函数"""
    analyzer = DailyAnalysis()
    result = analyzer.analyze(ticker)
    return analyzer.format_report(result)


if __name__ == "__main__":
    # 测试
    print("每日复盘分析测试")
    
    analyzer = DailyAnalysis()
    
    # 测试获取数据
    data = analyzer.get_market_data("000001.SZ")
    
    if data:
        print(f"数据获取成功: {data.get('name')}")
        print(f"收盘价: {data.get('close')}")
    else:
        print("数据获取失败，使用模拟数据测试")
        
        # 模拟分析
        result = {
            'ticker': '000001',
            'name': '平安银行',
            'date': '2024-01-01',
            'close': 12.50,
            'pct_change': 1.2,
            'analysis': {
                'ma': {'status': 'bullish', 'score': 25, 'reason': '多头排列'},
                'macd': {'status': 'bullish', 'score': 25, 'reason': '金叉'},
                'rsi': {'status': 'strong', 'score': 20, 'reason': 'RSI=55'},
                'volume': {'status': 'normal', 'score': 10, 'reason': '成交量正常'},
                'bias': 1.5,
            },
            'score': 80,
            'rating': '买入',
        }
        
        print(analyzer.format_report(result))
