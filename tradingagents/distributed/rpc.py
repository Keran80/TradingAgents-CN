# -*- coding: utf-8 -*-
"""
RPC 通信层

支持：
- 同步/异步 RPC
- 消息序列化
- 连接池
- 故障转移
"""

import asyncio
import json
import pickle
import hashlib
import time
import uuid
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class SerializationType(Enum):
    """序列化类型"""
    JSON = "json"
    PICKLE = "pickle"
    MSGPACK = "msgpack"


@dataclass
class RPCMessage:
    """RPC 消息"""
    msg_id: str
    msg_type: MessageType
    method: str
    params: Dict[str, Any]
    data: Optional[Any] = None
    timestamp: float = field(default_factory=time.time)
    trace_id: Optional[str] = None
    
    def to_bytes(self, serializer: SerializationType = SerializationType.JSON) -> bytes:
        """序列化消息（带长度前缀）"""
        obj = {
            'msg_id': self.msg_id,
            'msg_type': self.msg_type.value,
            'method': self.method,
            'params': self.params,
            'data': self.data,
            'timestamp': self.timestamp,
            'trace_id': self.trace_id
        }

        if serializer == SerializationType.JSON:
            payload = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        elif serializer == SerializationType.PICKLE:
            payload = pickle.dumps(obj)
        else:
            payload = json.dumps(obj, ensure_ascii=False).encode('utf-8')

        # 添加 4 字节长度前缀（大端序）
        length_prefix = len(payload).to_bytes(4, byteorder='big')
        return length_prefix + payload

    @classmethod
    def from_bytes(cls, data: bytes, serializer: SerializationType = SerializationType.JSON) -> 'RPCMessage':
        """反序列化消息"""
        if serializer == SerializationType.PICKLE:
            obj = pickle.loads(data)
        else:
            obj = json.loads(data.decode('utf-8'))

        return cls(
            msg_id=obj['msg_id'],
            msg_type=MessageType(obj['msg_type']),
            method=obj['method'],
            params=obj['params'],
            data=obj.get('data'),
            timestamp=obj['timestamp'],
            trace_id=obj.get('trace_id')
        )


class MessageProtocol(ABC):
    """消息协议基类"""
    
    @abstractmethod
    async def connect(self) -> bool:
        pass
    
    @abstractmethod
    async def disconnect(self):
        pass
    
    @abstractmethod
    async def send(self, message: RPCMessage) -> bool:
        pass
    
    @abstractmethod
    async def receive(self) -> Optional[RPCMessage]:
        pass
    
    @abstractmethod
    async def keep_alive(self):
        pass


class RPCServer:
    """
    RPC 服务器
    
    基于 asyncio 实现异步 RPC 服务
    """
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8765,
        serializer: SerializationType = SerializationType.JSON
    ):
        self.host = host
        self.port = port
        self.serializer = serializer
        
        # 方法注册表
        self.methods: Dict[str, Callable] = {}
        
        # 连接管理
        self.connections: Dict[str, asyncio.StreamReader] = {}
        
        # 运行状态
        self._running = False
        self._server: Optional[asyncio.Server] = None
        
        # 回调
        self.on_connect: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
    
    def register_method(self, name: str, handler: Callable):
        """注册 RPC 方法"""
        self.methods[name] = handler
        logger.info(f"RPC 方法注册: {name}")
    
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """处理客户端连接"""
        addr = writer.get_extra_info('peername')
        client_id = f"{addr[0]}:{addr[1]}"
        self.connections[client_id] = reader
        
        logger.info(f"客户端连接: {client_id}")
        
        if self.on_connect:
            await self._safe_callback(self.on_connect, client_id)
        
        try:
            while self._running:
                try:
                    # 读取消息长度前缀（4字节）
                    length_data = await reader.readexactly(4)
                    msg_length = int.from_bytes(length_data, byteorder='big')

                    # 读取完整消息
                    data = await reader.readexactly(msg_length)

                    # 解析消息
                    message = RPCMessage.from_bytes(data, self.serializer)
                    
                    # 处理请求
                    if message.msg_type == MessageType.REQUEST:
                        await self._process_request(message, writer)
                        
                except Exception as e:
                    logger.error(f"处理客户端错误: {e}")
                    break
                    
        except asyncio.CancelledError:
            pass
        finally:
            if client_id in self.connections:
                del self.connections[client_id]
            writer.close()
            await writer.wait_closed()
            logger.info(f"客户端断开: {client_id}")
            
            if self.on_disconnect:
                await self._safe_callback(self.on_disconnect, client_id)
    
    async def _process_request(self, message: RPCMessage, writer: asyncio.StreamWriter):
        """处理 RPC 请求"""
        method_name = message.method
        params = message.params
        
        try:
            if method_name not in self.methods:
                raise ValueError(f"方法不存在: {method_name}")
            
            handler = self.methods[method_name]
            
            # 调用方法
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**params)
            else:
                result = handler(**params)
            
            # 发送响应
            response = RPCMessage(
                msg_id=message.msg_id,
                msg_type=MessageType.RESPONSE,
                method=method_name,
                params={},
                data=result
            )
            
        except Exception as e:
            # 发送错误
            response = RPCMessage(
                msg_id=message.msg_id,
                msg_type=MessageType.ERROR,
                method=method_name,
                params={},
                data={'error': str(e)}
            )
        
        # 发送响应
        writer.write(response.to_bytes(self.serializer))
        await writer.drain()
    
    async def _safe_callback(self, callback, *args):
        """安全执行回调"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args)
            else:
                callback(*args)
        except Exception as e:
            logger.error(f"回调执行错误: {e}")
    
    async def start(self):
        """启动 RPC 服务器"""
        self._running = True
        self._server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port
        )
        
        addr = self._server.sockets[0].getsockname()
        logger.info(f"RPC 服务器启动: {addr}")
    
    async def stop(self):
        """停止 RPC 服务器"""
        self._running = False
        
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        
        logger.info("RPC 服务器停止")
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


class RPCClient:
    """
    RPC 客户端
    
    支持同步/异步调用，连接池，故障转移
    """
    
    def __init__(
        self,
        servers: List[str],  # ["host:port", ...]
        serializer: SerializationType = SerializationType.JSON,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        self.servers = servers
        self.serializer = serializer
        self.timeout = timeout
        self.max_retries = max_retries
        
        # 连接池
        self._connections: Dict[str, tuple] = {}  # server -> (reader, writer)
        
        # 当前服务器索引
        self._current_idx = 0
    
    async def _get_connection(self, server: str) -> Optional[tuple]:
        """获取连接"""
        if server in self._connections:
            reader, writer = self._connections[server]
            try:
                # 检查连接是否有效
                if not reader.at_eof():
                    return (reader, writer)
            except:
                pass
        
        # 建立新连接
        host, port = server.split(':')
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, int(port)),
                timeout=5.0
            )
            self._connections[server] = (reader, writer)
            logger.info(f"RPC 连接建立: {server}")
            return (reader, writer)
        except Exception as e:
            logger.error(f"RPC 连接失败: {server}, {e}")
            return None
    
    async def call(
        self,
        method: str,
        params: Optional[Dict] = None,
        trace_id: Optional[str] = None
    ) -> Optional[Any]:
        """
        发起 RPC 调用
        
        支持故障转移：当前服务器失败自动切换下一个
        """
        params = params or {}
        
        # 尝试所有服务器
        for i in range(len(self.servers)):
            server = self.servers[self._current_idx]
            
            for retry in range(self.max_retries):
                try:
                    # 获取连接
                    conn = await self._get_connection(server)
                    if not conn:
                        break
                    
                    reader, writer = conn
                    
                    # 发送请求
                    message = RPCMessage(
                        msg_id=str(uuid.uuid4()),
                        msg_type=MessageType.REQUEST,
                        method=method,
                        params=params,
                        trace_id=trace_id
                    )
                    
                    writer.write(message.to_bytes(self.serializer))
                    await writer.drain()

                    # 等待响应（读取长度前缀 + 消息体）
                    length_data = await asyncio.wait_for(
                        reader.readexactly(4),
                        timeout=self.timeout
                    )
                    msg_length = int.from_bytes(length_data, byteorder='big')

                    data = await asyncio.wait_for(
                        reader.readexactly(msg_length),
                        timeout=self.timeout
                    )

                    response = RPCMessage.from_bytes(data, self.serializer)
                    
                    if response.msg_type == MessageType.ERROR:
                        raise Exception(response.data.get('error', '未知错误'))
                    
                    return response.data
                    
                except asyncio.TimeoutError:
                    logger.warning(f"RPC 调用超时: {server}, retry {retry}")
                except Exception as e:
                    logger.error(f"RPC 调用失败: {server}, {e}")
                
                # 重试失败，关闭连接
                if server in self._connections:
                    try:
                        self._connections[server][1].close()
                    except:
                        pass
                    del self._connections[server]
            
            # 当前服务器失败，切换下一个
            self._current_idx = (self._current_idx + 1) % len(self.servers)
        
        return None
    
    async def call_async(self, method: str, **kwargs) -> Optional[Any]:
        """异步调用（简洁语法）"""
        return await self.call(method, kwargs)
    
    async def close(self):
        """关闭所有连接"""
        for server, (reader, writer) in self._connections.items():
            writer.close()
            await writer.wait_closed()
        
        self._connections.clear()
        logger.info("RPC 客户端关闭")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# 便捷函数
def create_rpc_client(host: str, port: int, **kwargs) -> RPCClient:
    """创建 RPC 客户端"""
    return RPCClient([f"{host}:{port}"], **kwargs)