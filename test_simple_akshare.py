"""
A股股票分析测试
使用 AkShare 获取数据 + 智谱AI 分析
"""
import os
import json
from datetime import datetime, timedelta

# 确保 .env 加载
from dotenv import load_dotenv
load_dotenv()

# 导入 AkShare 数据获取
from tradingagents.dataflows import akshare_utils as ak

# 导入智谱AI
from openai import OpenAI

# 配置智谱AI
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "5c9b4291a94540878c8fab0cddc8bc71.IlLUPbvGtiW32isQ"),
    base_url=os.getenv("BACKEND_URL", "https://open.bigmodel.cn/api/paas/v4")
)

def get_stock_data(ticker: str, days: int = 30):
    """获取股票数据"""
    end_date = datetime.now().strftime("%Y%m%d")
    start_date_obj = datetime.now() - timedelta(days=days)
    start_date = start_date_obj.strftime("%Y%m%d")
    
    # 获取日线数据
    df_daily = ak.get_stock_daily(ticker, start_date, end_date)
    
    # 获取实时行情
    df_quote = ak.get_stock_realtime_quote(ticker)
    
    return df_daily, df_quote

def analyze_stock(ticker: str):
    """分析股票"""
    print(f"\n{'='*50}")
    print(f"分析股票: {ticker}")
    print(f"{'='*50}")
    
    # 获取数据
    print("\n[1/3] 获取数据...")
    df_daily, df_quote = get_stock_data(ticker, 30)
    
    if df_quote.empty:
        print(f"无法获取 {ticker} 的数据")
        return
    
    # 提取关键信息
    quote = df_quote.iloc[0]
    stock_name = quote.get('名称', 'N/A')
    current_price = quote.get('最新价', 'N/A')
    change_pct = quote.get('涨跌幅', 'N/A')
    volume = quote.get('成交量', 'N/A')
    amount = quote.get('成交额', 'N/A')
    
    print(f"\n[2/3] 股票信息:")
    print(f"  名称: {stock_name}")
    print(f"  当前价格: {current_price}")
    print(f"  涨跌幅: {change_pct}%")
    print(f"  成交量: {volume}")
    print(f"  成交额: {amount}")
    
    # 构建提示词
    prompt = f"""请分析这只A股股票:

股票代码: {ticker}
股票名称: {stock_name}
当前价格: {current_price}
涨跌幅: {change_pct}%
成交量: {volume}
成交额: {amount}

请提供:
1. 基本面分析 (行业、业绩)
2. 技术面分析 (趋势、支撑位、压力位)
3. 资金面分析 (主力资金流向)
4. 综合投资建议 (买入/卖出/持有)
"""

    print(f"\n[3/3] 调用智谱AI分析...")
    
    try:
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system", "content": "你是一个专业的A股股票分析师，善于分析股票的基本面、技术面和资金面，给出投资建议。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        result = response.choices[0].message.content
        
        print(f"\n{'='*50}")
        print("分析结果:")
        print(f"{'='*50}")
        print(result)
        
    except Exception as e:
        print(f"\n调用智谱AI失败: {e}")
        # 打印完整错误
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 分析平安银行 (000001)
    analyze_stock("000001")
