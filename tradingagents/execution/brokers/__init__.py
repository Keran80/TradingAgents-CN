# -*- coding: utf-8 -*-
"""
A股券商适配器

支持 A 股主要券商的模拟接口：
- 通达信 (Tdx)
- 同花顺 (10jqka)
- 东方财富 (Eastmoney)

实际接入需要券商 API 凭证

Usage:
    from tradingagents.execution.brokers import TdxBroker
    
    broker = TdxBroker({
        "host": "218.75.126.9",
        "port": 7709,
    })
    broker.connect()
"""

import logging
import socket
import struct
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field

from ..broker import (
    BrokerInterface, Order, OrderType, OrderSide, OrderStatus,
    Quote, Trade, OrderResult
)

logger = logging.getLogger(__name__)


class MarketCode(Enum):
    """市场代码"""
    SHANGHAI = 1    # 上海
    SHENZHEN = 2    # 深圳


class CmdCode(Enum):
    """通达信命令码"""
    GET_MARKET_QUOTE = 0x001      # 获取行情
    GET_STOCK_LIST = 0x010        # 获取股票列表
    GET_KLINE = 0x107             # 获取K线
    GET_MINUTE = 0x108            # 分时数据
    GET_TRANSACTION = 0x112        # 分笔成交
    LOGIN = 0x001                 # 登录
    LOGOUT = 0x002                # 登出


class TdxApiCode(Enum):
    """通达信 API 错误码"""
    SUCCESS = 0
    INVALID_PASSWORD = -1
    LOGIN_FAILED = -2
    NO_PERMISSION = -3
    NO_DATA = -4
    UNKNOWN_ERROR = -99


@dataclass
class TdxConfig:
    """通达信配置"""
    host: str = "218.75.126.9"
    port: int = 7709
    version: str = "5.73"
    timeout: int = 10
    auto_reconnect: bool = True
    reconnect_interval: int = 5


class TdxBroker(BrokerInterface):
    """
    通达信券商适配器
    
    基于通达信 API 协议实现，支持 A 股交易
    实际使用需要券商开通 API 权限
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 配置参数
        self._host = config.get("host", "218.75.126.9") if config else "218.75.126.9"
        self._port = config.get("port", 7709) if config else 7709
        self._version = config.get("version", "5.73")
        self._timeout = config.get("timeout", 10)
        
        # 连接状态
        self._socket: Optional[socket.socket] = None
        self._lock = threading.Lock()
        self._seq = 0
        
        # 账户信息（登录后获取）
        self._account_id: str = ""
        self._client_id: int = 0
        
        # 缓存
        self._quotes: Dict[str, Quote] = {}
        self._last_fetch: Dict[str, float] = {}
        
    def connect(self) -> bool:
        """连接通达信服务器"""
        try:
            with self._lock:
                if self._connected:
                    return True
                    
                # 创建 socket
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.settimeout(self._timeout)
                self._socket.connect((self._host, self._port))
                
                # 发送登录请求
                if self._do_login():
                    self._connected = True
                    logger.info(f"Tdx connected to {self._host}:{self._port}")
                    return True
                else:
                    self._socket.close()
                    self._socket = None
                    return False
                    
        except Exception as e:
            logger.error(f"Tdx connect failed: {e}")
            return False
            
    def _do_login(self) -> bool:
        """执行登录"""
        # 通达信登录包格式
        # 包头(4) + 版本(2) + 序列号(2) + 命令(2) + 账号(20) + 密码(20) + 其他
        try:
            # 简化版登录（实际需要根据券商协议）
            login_data = self._build_login_packet()
            self._socket.send(login_data)
            
            # 接收响应
            response = self._socket.recv(1024)
            
            if len(response) >= 4:
                result = struct.unpack("<I", response[:4])[0]
                return result == 0
                
            return False
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
            
    def _build_login_packet(self) -> bytes:
        """构建登录包"""
        # 简化实现
        username = self.config.get("username", "").encode('gbk').ljust(16, b'\x00')
        password = self.config.get("password", "").encode('gbk').ljust(16, b'\x00')
        
        # 包结构: 长度(4) + 版本(2) + 命令(2) + 序列号(2) + 用户名(16) + 密码(16)
        header = struct.pack("<IHH", 36, 0x1001, self._next_seq())
        
        return header + username[:16] + password[:16]
        
    def _next_seq(self) -> int:
        """生成序列号"""
        self._seq = (self._seq + 1) % 65536
        return self._seq
        
    def disconnect(self) -> bool:
        """断开连接"""
        with self._lock:
            if self._socket:
                try:
                    self._socket.close()
                except:
                    pass
                self._socket = None
                
            self._connected = False
            logger.info("Tdx disconnected")
            return True
            
    def place_order(self, order: Order) -> OrderResult:
        """下单"""
        if not self._connected:
            return OrderResult(
                success=False,
                error_code="NOT_CONNECTED",
                message="Not connected to broker"
            )
            
        try:
            # 构建委托请求
            request = self._build_order_packet(order)
            self._socket.send(request)
            
            # 接收响应
            response = self._socket.recv(1024)
            
            if len(response) >= 4:
                result_code = struct.unpack("<I", response[:4])[0]
                
                if result_code == 0:
                    order_id = struct.unpack("<I", response[4:8])[0]
                    order.order_id = f"TDX{order_id}"
                    order.status = OrderStatus.SUBMITTED
                    
                    return OrderResult(
                        success=True,
                        order_id=order.order_id,
                        message="Order submitted",
                        order=order
                    )
                else:
                    return OrderResult(
                        success=False,
                        error_code=str(result_code),
                        message=f"Order failed: {result_code}",
                        order=order
                    )
                    
            return OrderResult(
                success=False,
                error_code="INVALID_RESPONSE",
                message="Invalid response"
            )
            
        except Exception as e:
            logger.error(f"Place order failed: {e}")
            return OrderResult(
                success=False,
                error_code="EXCEPTION",
                message=str(e)
            )
            
    def _build_order_packet(self, order: Order) -> bytes:
        """构建委托请求包"""
        # 市场代码
        market = 1 if order.symbol.endswith(".SH") else 2
        
        # 股票代码 (去除后缀)
        code = order.symbol.split(".")[0].encode('gbk').ljust(6, b'\x00')
        
        # 买卖方向
        side = 1 if order.side == OrderSide.BUY else 2
        
        # 委托价格 (放大1000倍以避免浮点)
        price = int(order.price * 1000)
        
        # 委托数量
        qty = order.quantity
        
        # 委托类型
        order_type = 0 if order.order_type == OrderType.LIMIT else 1
        
        # 构建请求包
        # 长度(4) + 版本(2) + 命令(2) + 序列号(2) + 市场(1) + 代码(6) + 方向(1) + 价格(4) + 数量(4) + 类型(1)
        header = struct.pack("<IHH", 22, 0x1A0A, self._next_seq())
        
        data = struct.pack(
            "<B6sBIIIB",
            market, code, side, price, qty, order_type
        )
        
        return header + data
            
    def cancel_order(self, order_id: str) -> OrderResult:
        """撤单"""
        if not self._connected:
            return OrderResult(
                success=False,
                error_code="NOT_CONNECTED",
                message="Not connected"
            )
            
        try:
            # 构建撤单请求
            request = self._build_cancel_packet(order_id)
            self._socket.send(request)
            
            response = self._socket.recv(1024)
            
            if len(response) >= 4:
                result = struct.unpack("<I", response[:4])[0]
                
                if result == 0:
                    return OrderResult(
                        success=True,
                        order_id=order_id,
                        message="Order cancelled"
                    )
                else:
                    return OrderResult(
                        success=False,
                        error_code=str(result),
                        message=f"Cancel failed: {result}"
                    )
                    
        except Exception as e:
            logger.error(f"Cancel order failed: {e}")
            return OrderResult(
                success=False,
                error_code="EXCEPTION",
                message=str(e)
            )
            
    def _build_cancel_packet(self, order_id: str) -> bytes:
        """构建撤单请求包"""
        # 提取委托序号
        seq = int(order_id.replace("TDX", ""))
        
        header = struct.pack("<IHH", 6, 0x1A0B, self._next_seq())
        data = struct.pack("<I", seq)
        
        return header + data
            
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """查询订单状态"""
        # 简化实现：返回 None 表示需要券商支持
        logger.warning("Order status query requires broker API support")
        return None
        
    def get_orders(self, symbol: Optional[str] = None,
                   status: Optional[OrderStatus] = None) -> List[Order]:
        """查询订单列表"""
        # 简化实现
        return []
        
    def get_trades(self, order_id: Optional[str] = None) -> List[Trade]:
        """查询成交记录"""
        return []
        
    def get_positions(self) -> List[Dict[str, Any]]:
        """查询持仓"""
        if not self._connected:
            return []
            
        # 简化实现：需要券商 API
        return []
        
    def get_account(self) -> Dict[str, Any]:
        """查询账户信息"""
        return {
            "account_id": self._account_id or "TDX",
            "cash": 0,
            "frozen_cash": 0,
            "total_assets": 0,
            "market_value": 0,
            "equity": 0
        }
        
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """获取行情"""
        # 检查缓存
        now = time.time()
        if symbol in self._quotes:
            if now - self._last_fetch.get(symbol, 0) < 1:
                return self._quotes[symbol]
                
        if not self._connected:
            return None
            
        try:
            quote = self._fetch_quote(symbol)
            if quote:
                self._quotes[symbol] = quote
                self._last_fetch[symbol] = now
                return quote
        except Exception as e:
            logger.error(f"Get quote failed for {symbol}: {e}")
            
        return None
        
    def _fetch_quote(self, symbol: str) -> Optional[Quote]:
        """获取实时行情"""
        # 市场代码
        market = 1 if symbol.endswith(".SH") else 2
        code = symbol.split(".")[0]
        
        # 构建请求
        header = struct.pack("<IHH", 9, CmdCode.GET_MARKET_QUOTE.value, self._next_seq())
        data = struct.pack(f"<B{len(code)}s", market, code.encode('gbk'))
        
        try:
            self._socket.send(header + data)
            response = self._socket.recv(1024)
            
            if len(response) >= 32:
                # 解析行情数据
                # 格式: 最新价, 开盘, 最高, 最低, 成交量, 成交额...
                values = struct.unpack("<ffffII", response[:28])
                
                return Quote(
                    symbol=symbol,
                    last_price=values[0] / 1000,
                    open_price=values[1] / 1000,
                    high_price=values[2] / 1000,
                    low_price=values[3] / 1000,
                    volume=values[4],
                    turnover=values[5],
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Fetch quote error: {e}")
            
        return None


class BrokerFactory:
    """券商工厂"""
    
    _BROKERS = {
        "tdx": TdxBroker,
        "simulator": "SimulatorAdapter",  # 动态导入
    }
    
    @classmethod
    def create(cls, broker_type: str, config: Dict[str, Any]) -> BrokerInterface:
        """
        创建券商实例
        
        Args:
            broker_type: 券商类型 (tdx/simulator/tiger/futu)
            config: 券商配置
            
        Returns:
            BrokerInterface 实例
        """
        if broker_type == "simulator":
            from ..live.adapters import SimulatorAdapter
            return SimulatorAdapter(config)
            
        elif broker_type == "tiger":
            from ..live.adapters import TigerAdapter
            return TigerAdapter(config)
            
        elif broker_type == "futu":
            from ..live.adapters import FutuAdapter
            return FutuAdapter(config)
            
        elif broker_type == "joinquant":
            from ..live.adapters import JoinQuantAdapter
            return JoinQuantAdapter(config)
            
        elif broker_type == "tdx":
            return TdxBroker(config)
            
        else:
            raise ValueError(f"Unknown broker type: {broker_type}")


__all__ = [
    "TdxBroker",
    "TdxConfig",
    "BrokerFactory",
]