# -*- coding: utf-8 -*-
"""
依赖注入模块 - P1 优化项
基于 Protocol 的依赖注入模式
"""
from typing import Protocol, Any, Dict, List
from dataclasses import dataclass


# ========== Protocol 定义 ==========

class DataSource(Protocol):
    """数据源协议"""
    def fetch(self, symbol: str) -> Dict[str, Any]:
        """获取数据"""
        ...
    
    def fetch_batch(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """批量获取数据"""
        ...


class Backtester(Protocol):
    """回测器协议"""
    def run(self, strategy: Any, data: List[Dict]) -> Dict[str, Any]:
        """执行回测"""
        ...


class RiskManager(Protocol):
    """风险管理器协议"""
    def check(self, position: Dict) -> bool:
        """检查风险"""
        ...
    
    def calculate_var(self, portfolio: List) -> float:
        """计算 VaR"""
        ...


# ========== 具体实现 ==========

@dataclass
class StockDataSource:
    """股票数据源实现"""
    api_key: str
    base_url: str = "https://api.example.com"
    
    def fetch(self, symbol: str) -> Dict[str, Any]:
        # 实现细节
        return {"symbol": symbol, "price": 100.0}
    
    def fetch_batch(self, symbols: List[str]) -> List[Dict[str, Any]]:
        return [self.fetch(s) for s in symbols]


@dataclass
class SimpleBacktester:
    """简单回测器实现"""
    initial_capital: float = 100000.0
    
    def run(self, strategy: Any, data: List[Dict]) -> Dict[str, Any]:
        # 实现细节
        return {"sharpe": 1.5, "returns": 0.1}


# ========== 依赖注入容器 ==========

class Container:
    """依赖注入容器"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
    
    def register(self, name: str, service: Any) -> None:
        """注册服务"""
        self._services[name] = service
    
    def get(self, name: str) -> Any:
        """获取服务"""
        if name not in self._services:
            raise KeyError(f"服务未注册：{name}")
        return self._services[name]
    
    def __getitem__(self, name: str) -> Any:
        return self.get(name)


# ========== 使用示例 ==========

def create_container() -> Container:
    """创建依赖注入容器"""
    container = Container()
    
    # 注册数据源
    container.register("data_source", StockDataSource(api_key="xxx"))
    
    # 注册回测器
    container.register("backtester", SimpleBacktester(initial_capital=100000))
    
    return container


# 使用方式:
# container = create_container()
# data_source = container["data_source"]
# data = data_source.fetch("600519")
