# 通达信数据接口集成说明

## 概述

本版本新增了**通达信（TDX）**直连数据源，通过 `pytdx` 库直接访问通达信行情服务器，获取 A 股实时和历史数据。

## 通达信数据源优势

| 特性 | 通达信 (TDX) | AkShare |
|------|------------|---------|
| 连接方式 | TCP 直连，延迟极低 | HTTP 请求 |
| API Key | **不需要** | 不需要 |
| 实时行情 | **支持（含五档报价）** | 支持 |
| 历史日线 | **支持（全量历史）** | 支持 |
| 分钟线 | **支持（1/5/15/30/60分钟）** | 支持 |
| 财务数据 | 基础财务指标 | 较完整 |
| 新闻/情绪 | 不支持 | **支持** |
| 宏观数据 | 不支持 | **支持** |
| 稳定性 | **极高（官方协议）** | 中（爬虫）|
| 速度 | **极快（<50ms）** | 中（~500ms）|

**建议**：使用默认 `auto` 模式，系统会优先使用通达信，新闻/情绪分析自动使用 AkShare。

## 快速开始

### 安装依赖

```bash
pip install pytdx
# 或
pip install -r requirements.txt
```

### 测试连接

```bash
python test_tdx.py
```

### 使用方式

#### 方式一：直接使用通达信接口

```python
from tradingagents.dataflows.tdx_utils import (
    get_stock_data,          # 获取 K 线数据
    get_realtime_quotes,     # 获取实时报价
    get_finance_info,        # 获取财务信息
    get_xdxr_info,           # 获取除权除息信息
    TdxStockUtils,           # 工具类
)

# 获取日线数据
df = get_stock_data("000001", "2024-01-01", "2024-12-31")
print(df.tail(5))

# 获取实时行情（含五档报价）
qt = get_realtime_quotes(["000001", "600519", "000858"])
print(qt[["code", "price", "vol", "bid1", "ask1"]])

# 获取财务信息
info = get_finance_info("000001")
print(f"总股本: {info['total_shares']:,.0f} 股")
print(f"净资产: {info['net_assets']:,.0f} 元")
print(f"每股净资产: {info['net_asset_per_share']:.2f} 元")

# 获取分钟线
min_df = get_stock_data("000001", "2024-12-01", "2024-12-31", k_type="5min")
```

#### 方式二：通过数据源路由（推荐）

```python
from tradingagents.dataflows.data_source import get_data_source, set_data_source

# 自动模式（优先TDX，失败回退AkShare）—— 默认行为
ds = get_data_source()
df = ds.get_stock_data("000001", "2024-01-01", "2024-12-31")

# 强制使用通达信
set_data_source("tdx")
ds = get_data_source()

# 强制使用 AkShare
set_data_source("akshare")
ds = get_data_source()
```

#### 方式三：通过环境变量配置

在 `.env` 文件中添加：

```bash
# 数据源选择: tdx | akshare | auto（默认）
TRADINGAGENTS_DATA_SOURCE=tdx

# （可选）指定通达信服务器，默认自动选择最优
TRADINGAGENTS_TDX_SERVER=218.75.126.9
TRADINGAGENTS_TDX_PORT=7709
```

## 通达信服务器列表

以下服务器均为通达信公开行情服务器，免费访问：

| 服务器 IP | 端口 | 说明 |
|---------|-----|------|
| 218.75.126.9 | 7709 | 推荐（实测可用） |
| 119.147.212.81 | 7709 | 备用 |
| 121.14.110.210 | 7709 | 备用 |
| 221.231.141.60 | 7709 | 备用 |
| 14.215.128.18 | 7709 | 备用 |

系统会自动选择最快的可用服务器，无需手动配置。

## K 线类型说明

| k_type 参数 | 说明 |
|------------|------|
| `daily` | 日线（默认）|
| `1min` | 1分钟线 |
| `5min` | 5分钟线 |
| `15min` | 15分钟线 |
| `30min` | 30分钟线 |
| `60min` | 60分钟线 |
| `weekly` | 周线 |
| `monthly` | 月线 |

## 股票代码格式

通达信接口支持多种代码格式，自动识别市场：

```python
# 以下写法均支持
get_stock_data("000001", ...)      # 纯数字（深交所）
get_stock_data("000001.SZ", ...)   # 带交易所后缀
get_stock_data("600519", ...)      # 纯数字（上交所）
get_stock_data("600519.SH", ...)   # 带交易所后缀
```

代码识别规则：
- `6xxxx`、`5xxxx` → 上交所 (SH)
- `0xxxx`、`1xxxx`、`2xxxx`、`3xxxx` → 深交所 (SZ)

## 注意事项

1. **交易时间**：分钟线数据只在交易时段（9:30-15:00）有实时数据，非交易时段返回历史数据
2. **历史数据**：通达信服务器保存完整历史数据，理论上可获取上市以来所有日线数据
3. **复权处理**：日线数据默认进行前复权处理（基于除权除息数据计算）
4. **财务数据**：通达信财务数据为摘要数据，如需详细财报请使用 AkShare 或 Tushare
5. **连接限制**：通达信对高频请求有一定限制，系统已内置 50ms 间隔，正常使用无需担心

## 架构图

```
TradingAgents-CN
├── 数据层（dataflows/）
│   ├── data_source.py        # 数据源路由（自动选择）
│   ├── tdx_utils.py          # 通达信(pytdx)适配器  [NEW]
│   ├── akshare_stock_utils.py # AkShare 适配器
│   ├── astock_utils.py       # A股工具集（新闻/北向资金等）
│   ├── interface.py          # 统一接口（已更新为自动路由）
│   └── ...
├── 分析层（agents/）
│   ├── 基本面分析师
│   ├── 技术分析师
│   ├── 新闻分析师
│   └── 情绪分析师
└── 决策层（graph/）
    └── 多 Agent 辩论 + 风控
```
