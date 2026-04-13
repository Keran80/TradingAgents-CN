#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多数据源适配器
支持从多个数据源获取股票数据
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataRequest:
    """数据请求"""
    symbol: str
    start_date: str
    end_date: str
    frequency: str = "daily"  # daily, weekly, monthly
    fields: List[str] = None
    data_source: str = "auto"  # auto, akshare, tushare, yfinance
    
    def __post_init__(self):
        if self.fields is None:
            self.fields = ["open", "high", "low", "close", "volume"]

@dataclass
class DataResponse:
    """数据响应"""
    symbol: str
    data: pd.DataFrame
    data_source: str
    fetch_time: datetime
    success: bool
    error_message: str = ""

class MultiSourceAdapter:
    """多数据源适配器"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.available_sources = ["akshare", "tushare", "yfinance"]
        self.source_priority = self.config.get("source_priority", ["akshare", "tushare", "yfinance"])
        
    async def fetch_data(self, request: DataRequest) -> DataResponse:
        """获取数据（自动选择数据源）"""
        fetch_time = datetime.now()
        
        # 如果指定了数据源，直接使用
        if request.data_source != "auto" and request.data_source in self.available_sources:
            data = await self._fetch_from_source(request, request.data_source)
            success = not data.empty
            return DataResponse(
                symbol=request.symbol,
                data=data,
                data_source=request.data_source,
                fetch_time=fetch_time,
                success=success,
                error_message="" if success else f"{request.data_source} 数据获取失败"
            )
        
        # 自动选择数据源（按优先级尝试）
        for source in self.source_priority:
            try:
                data = await self._fetch_from_source(request, source)
                if not data.empty:
                    logger.info(f"✅ 从 {source} 获取 {request.symbol} 数据成功")
                    return DataResponse(
                        symbol=request.symbol,
                        data=data,
                        data_source=source,
                        fetch_time=fetch_time,
                        success=True
                    )
            except Exception as e:
                logger.warning(f"⚠️ {source} 获取失败: {e}")
                continue
        
        # 所有数据源都失败
        logger.error(f"❌ 所有数据源获取 {request.symbol} 失败")
        return DataResponse(
            symbol=request.symbol,
            data=pd.DataFrame(),
            data_source="",
            fetch_time=fetch_time,
            success=False,
            error_message="所有数据源获取失败"
        )
    
    async def _fetch_from_source(self, request: DataRequest, source: str) -> pd.DataFrame:
        """从指定数据源获取数据"""
        if source == "akshare":
            return await self._fetch_akshare(request)
        elif source == "tushare":
            return await self._fetch_tushare(request)
        elif source == "yfinance":
            return await self._fetch_yfinance(request)
        else:
            raise ValueError(f"不支持的数据源: {source}")
    
    async def _fetch_akshare(self, request: DataRequest) -> pd.DataFrame:
        """从AKShare获取数据"""
        logger.debug(f"📡 从AKShare获取 {request.symbol} 数据")
        
        try:
            import akshare as ak
            
            # 获取股票数据
            if request.frequency == "daily":
                df = ak.stock_zh_a_hist(
                    symbol=request.symbol,
                    period="daily",
                    start_date=request.start_date,
                    end_date=request.end_date,
                    adjust="qfq"  # 前复权
                )
            elif request.frequency == "weekly":
                df = ak.stock_zh_a_hist(
                    symbol=request.symbol,
                    period="weekly",
                    start_date=request.start_date,
                    end_date=request.end_date,
                    adjust="qfq"
                )
            elif request.frequency == "monthly":
                df = ak.stock_zh_a_hist(
                    symbol=request.symbol,
                    period="monthly",
                    start_date=request.start_date,
                    end_date=request.end_date,
                    adjust="qfq"
                )
            else:
                raise ValueError(f"不支持的频率: {request.frequency}")
            
            if df.empty:
                logger.warning(f"⚠️ AKShare返回空数据: {request.symbol}")
                return pd.DataFrame()
            
            # 重命名列
            column_map = {
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "振幅": "amplitude",
                "涨跌幅": "change_pct",
                "涨跌额": "change",
                "换手率": "turnover"
            }
            
            df = df.rename(columns=column_map)
            
            # 设置索引
            if 'date' in df.columns:
                if 'time' in df.columns:
                    df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))
                    df.set_index('datetime', inplace=True)
                else:
                    df.set_index('date', inplace=True)
            
            # 只保留请求的字段
            available_columns = [col for col in request.fields if col in df.columns]
            if not available_columns:
                available_columns = ['open', 'high', 'low', 'close', 'volume']
            
            result = df[available_columns]
            
            logger.debug(f"✅ AKShare获取成功: {len(result)} 条数据")
            return result
            
        except Exception as e:
            logger.error(f"❌ AKShare获取失败: {e}")
            return pd.DataFrame()
    
    async def _fetch_tushare(self, request: DataRequest) -> pd.DataFrame:
        """从Tushare获取数据"""
        logger.debug(f"📡 从Tushare获取 {request.symbol} 数据")
        
        try:
            import tushare as ts
            
            # 设置token（如果有）
            tushare_token = self.config.get("tushare_token")
            if tushare_token:
                ts.set_token(tushare_token)
            
            pro = ts.pro_api()
            
            # Tushare股票代码格式
            symbol = request.symbol
            if not symbol.endswith(('.SH', '.SZ')):
                # 添加后缀
                if symbol.startswith('6'):
                    symbol = f"{symbol}.SH"
                else:
                    symbol = f"{symbol}.SZ"
            
            # 获取日线数据
            df = pro.daily(
                ts_code=symbol,
                start_date=request.start_date,
                end_date=request.end_date
            )
            
            if df.empty:
                logger.warning(f"⚠️ Tushare返回空数据: {request.symbol}")
                return pd.DataFrame()
            
            # 重命名和格式化
            df = df.rename(columns={
                "trade_date": "date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "vol": "volume",
                "amount": "amount"
            })
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            
            # 只保留请求的字段
            available_columns = [col for col in request.fields if col in df.columns]
            if not available_columns:
                available_columns = ['open', 'high', 'low', 'close', 'volume']
            
            result = df[available_columns]
            
            logger.debug(f"✅ Tushare获取成功: {len(result)} 条数据")
            return result
            
        except Exception as e:
            logger.error(f"❌ Tushare获取失败: {e}")
            return pd.DataFrame()
    
    async def _fetch_yfinance(self, request: DataRequest) -> pd.DataFrame:
        """从Yahoo Finance获取数据（主要用于美股）"""
        logger.debug(f"📡 从Yahoo Finance获取 {request.symbol} 数据")
        
        try:
            import yfinance as yf
            
            # Yahoo Finance股票代码格式
            symbol = request.symbol
            if symbol.endswith(('.SS', '.SZ')):
                # 中国股票需要特殊处理
                symbol = symbol.replace('.SS', '.SS').replace('.SZ', '.SZ')
            elif not any(symbol.endswith(ext) for ext in ['.SI', '.HK', '.TO', '.L']):
                # 默认添加 .SI 后缀
                symbol = f"{symbol}.SI"
            
            # 下载数据
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=request.start_date,
                end=request.end_date,
                interval="1d" if request.frequency == "daily" else "1wk"
            )
            
            if df.empty:
                logger.warning(f"⚠️ Yahoo Finance返回空数据: {request.symbol}")
                return pd.DataFrame()
            
            # 重命名列
            df = df.rename(columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume"
            })
            
            # 只保留请求的字段
            available_columns = [col for col in request.fields if col in df.columns]
            if not available_columns:
                available_columns = ['open', 'high', 'low', 'close', 'volume']
            
            result = df[available_columns]
            
            logger.debug(f"✅ Yahoo Finance获取成功: {len(result)} 条数据")
            return result
            
        except Exception as e:
            logger.error(f"❌ Yahoo Finance获取失败: {e}")
            return pd.DataFrame()
    
    async def batch_fetch(self, requests: List[DataRequest]) -> Dict[str, DataResponse]:
        """批量获取数据"""
        tasks = []
        for request in requests:
            tasks.append(self.fetch_data(request))
        
        results = await asyncio.gather(*tasks)
        
        # 转换为字典
        result_dict = {}
        for response in results:
            result_dict[response.symbol] = response
        
        success_count = sum(1 for r in results if r.success)
        logger.info(f"✅ 批量获取完成，成功: {success_count}/{len(requests)}")
        
        return result_dict

# 示例使用
async def example_usage():
    """示例用法"""
    print("🚀 多数据源适配器示例")
    print("=" * 50)
    
    # 创建适配器
    adapter = MultiSourceAdapter()
    
    # 创建数据请求
    requests = [
        DataRequest(
            symbol="000001",
            start_date="2024-01-01",
            end_date="2024-01-31",
            fields=["open", "high", "low", "close", "volume"]
        ),
        DataRequest(
            symbol="600519",
            start_date="2024-01-01",
            end_date="2024-01-31",
            data_source="akshare"
        )
    ]
    
    # 批量获取数据
    print("批量获取数据...")
    results = await adapter.batch_fetch(requests)
    
    print("\n📊 获取结果:")
    print("=" * 60)
    for symbol, response in results.items():
        if response.success:
            print(f"✅ {symbol}: 从 {response.data_source} 获取 {len(response.data)} 条数据")
        else:
            print(f"❌ {symbol}: 获取失败 - {response.error_message}")
    
    print("=" * 60)
    
    # 显示第一个成功的数据
    for symbol, response in results.items():
        if response.success and not response.data.empty:
            print(f"\n{symbol} 数据预览:")
            print(response.data.head())
            break
    
    print("\n✅ 示例完成！")

if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())