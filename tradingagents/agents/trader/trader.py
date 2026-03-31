import functools
import time
import json
import os


def get_technical_analysis(ticker: str, days: int = 60) -> str:
    """
    获取技术分析报告
    
    Args:
        ticker: 股票代码
        days: 获取天数
        
    Returns:
        str: 技术分析报告文本
    """
    try:
        from tradingagents.dataflows.astock_utils import AStockData
        from tradingagents.dataflows.astock_technical import AStockTechnical
        from datetime import datetime, timedelta
        
        # 获取数据
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days * 2)).strftime('%Y%m%d')
        
        df = AStockData.get_daily(ticker, start_date, end_date)
        if df.empty:
            return "技术分析：数据获取失败"
        
        # 列名转换
        rename_map = {
            '日期': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume'
        }
        df = df.rename(columns=rename_map)
        
        # 计算技术指标
        df = AStockTechnical.calculate_all(df)
        
        # 获取最新值
        latest = df.iloc[-1]
        
        # 构建技术分析报告
        report = []
        report.append(f"=== {ticker} 技术分析报告 ===")
        report.append(f"日期: {latest.get('date', 'N/A')}")
        report.append(f"收盘价: {latest.get('close', 'N/A')}")
        report.append(f"成交量: {int(latest.get('volume', 0)):,}")
        report.append("")
        report.append("【均线】")
        for ma in ['ma5', 'ma10', 'ma20', 'ma30', 'ma60']:
            if ma in df.columns:
                val = latest.get(ma)
                if val and val == val:  # 检查 NaN
                    report.append(f"  MA{ma.replace('ma','')}: {val:.2f}")
        
        report.append("【MACD】")
        for macd_col in ['macd', 'macds', 'macdh']:
            if macd_col in df.columns:
                val = latest.get(macd_col)
                if val and val == val:
                    report.append(f"  {macd_col.upper()}: {val:.4f}")
        
        report.append("【RSI】")
        if 'rsi' in df.columns:
            val = latest.get('rsi')
            if val and val == val:
                report.append(f"  RSI(14): {val:.2f}")
        
        report.append("【KDJ】")
        for kdj_col in ['kdj_k', 'kdj_d', 'kdj_j']:
            if kdj_col in df.columns:
                val = latest.get(kdj_col)
                if val and val == val:
                    report.append(f"  {kdj_col.upper()}: {val:.2f}")
        
        # 添加策略信号
        from .strategy import analyze_stock, Signal
        
        report.append("")
        report.append("【策略信号】")
        
        for strategy_type in ['ma_crossover', 'rsi', 'macd', 'bollinger', 'combined']:
            result = analyze_stock(df, strategy_type)
            signal = result['signal'].value
            conf = result['confidence']
            report.append(f"  {strategy_type}: {signal} (置信度:{conf:.0%})")
        
        return "\n".join(report)
        
    except Exception as e:
        return f"技术分析获取失败: {str(e)}"


def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        
        # 尝试获取技术分析信号
        ticker = state.get("ticker", "000001.SZ")
        technical_report = get_technical_analysis(ticker)

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found."

        # 构建上下文，包含技术分析信号
        context = {
            "role": "user",
            "content": f"""Based on a comprehensive analysis by a team of analysts, here is an investment plan tailored for {company_name}. This plan incorporates insights from current technical market trends, macroeconomic indicators, and social media sentiment.

TECHNICAL ANALYSIS REPORT:
{technical_report}

Proposed Investment Plan: {investment_plan}

Use the technical analysis above as additional evidence for your trading decision. The strategy signals (MA Crossover, RSI, MACD, Bollinger Bands) provide quantitive buy/sell/hold recommendations based on historical price patterns.

Leverage these insights to make an informed and strategic decision.""",
        }

        messages = [
            {
                "role": "system",
                "content": f"""You are a trading agent analyzing market data to make investment decisions. Based on your analysis, provide a specific recommendation to buy, sell, or hold. End with a firm decision and always conclude your response with 'FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**' to confirm your recommendation. Do not forget to utilize lessons from past decisions to learn from your mistakes. Here is some reflections from similar situations you traded in and the lessons learned: {past_memory_str}""",
            },
            context,
        ]

        result = llm.invoke(messages)

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
            "technical_analysis": technical_report,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")

