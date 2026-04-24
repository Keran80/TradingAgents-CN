"""
Yahoo Finance 数据接口

提供Yahoo Finance股票数据获取功能。
"""

from typing import Annotated
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import pandas as pd
import logging

from ..config import DATA_DIR
from ..data_source import get_data_source
from ..akshare_utils import AkShareUtils

logger = logging.getLogger(__name__)


def get_YFin_data_window(
    symbol: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    """获取指定时间窗口的YFin数据"""
    # calculate past days
    date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
    before = date_obj - relativedelta(days=look_back_days)
    start_date = before.strftime("%Y-%m-%d")

    # read in data
    data = pd.read_csv(
        os.path.join(
            DATA_DIR,
            f"market_data/price_data/{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
        )
    )

    # Extract just the date part for comparison
    data["DateOnly"] = data["Date"].str[:10]

    # Filter data between the start and end dates (inclusive)
    filtered_data = data[
        (data["DateOnly"] >= start_date) & (data["DateOnly"] <= curr_date)
    ]

    # Drop the temporary column we created
    filtered_data = filtered_data.drop("DateOnly", axis=1)

    # Set pandas display options to show the full DataFrame
    with pd.option_context(
        "display.max_rows", None, "display.max_columns", None, "display.width", None
    ):
        df_string = filtered_data.to_string()

    return (
        f"## Raw Market Data for {symbol} from {start_date} to {curr_date}:\n\n"
        + df_string
    )


def get_YFin_data_online(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
):
    """
    获取股票数据（自动路由：通达信 TDX 优先，失败回退 AkShare）

    数据源说明：
      - TDX（通达信）：直接 TCP 协议，速度最快，无需 API Key
      - AkShare：HTTP 数据源，覆盖面更广

    可通过环境变量 TRADINGAGENTS_DATA_SOURCE=tdx|akshare|auto 指定数据源

    Args:
        symbol: 股票代码（如 '000001' 或 '000001.SZ'）
        start_date: 开始日期 'YYYY-MM-DD'
        end_date: 结束日期 'YYYY-MM-DD'

    Returns:
        str: CSV 格式的股票数据字符串
    """
    datetime.strptime(start_date, "%Y-%m-%d")
    datetime.strptime(end_date, "%Y-%m-%d")

    # 通过数据源路由获取数据
    try:
        ds = get_data_source()
        df = ds.get_stock_data(symbol, start_date, end_date)
    except Exception as e:
        logger.warning(f"[Interface] 主数据源失败: {e}，尝试 AkShare 回退")
        df = AkShareUtils.get_stock_data(symbol, start_date, end_date)

    # 检查数据是否为空
    if df is None or df.empty:
        return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"

    # 重置索引，将日期作为列
    df = df.reset_index()

    # 确保列名标准化
    column_mapping = {
        'Date': 'Date',
        'Open': 'Open',
        'High': 'High',
        'Low': 'Low',
        'Close': 'Close',
        'Volume': 'Volume',
        'Amount': 'Amount',
        'Adj Close': 'Adj Close'
    }
    df = df.rename(columns=column_mapping)

    # 保留标准列
    cols_to_keep = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']
    cols_exist = [c for c in cols_to_keep if c in df.columns]
    df = df[cols_exist]

    # 转换日期格式
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')

    # 四舍五入数值
    for col in ['Open', 'High', 'Low', 'Close', 'Adj Close']:
        if col in df.columns:
            df[col] = df[col].round(2)

    # 转换为 CSV 字符串
    csv_string = df.to_csv(index=False)

    # 获取当前数据源名称
    try:
        from ..data_source import get_current_source_name
        source_name = get_current_source_name()
    except Exception:
        source_name = "Unknown"

    header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
    header += f"# Total records: {len(df)}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    header += f"# Data source: {source_name}\n\n"

    return header + csv_string


def get_YFin_data(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> pd.DataFrame:
    """获取YFin数据DataFrame"""
    # read in data
    data = pd.read_csv(
        os.path.join(
            DATA_DIR,
            f"market_data/price_data/{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
        )
    )

    if end_date > "2025-03-25":
        raise Exception(
            f"Get_YFin_Data: {end_date} is outside of the data range of 2015-01-01 to 2025-03-25"
        )

    # Extract just the date part for comparison
    data["DateOnly"] = data["Date"].str[:10]

    # Filter data between the start and end dates (inclusive)
    filtered_data = data[
        (data["DateOnly"] >= start_date) & (data["DateOnly"] <= end_date)
    ]

    # Drop the temporary column we created
    filtered_data = filtered_data.drop("DateOnly", axis=1)

    # remove the index from the dataframe
    filtered_data = filtered_data.reset_index(drop=True)

    return filtered_data
