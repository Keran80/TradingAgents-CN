# -*- coding: utf-8 -*-
"""
TradingAgents-CN - Factor Base Classes
因子基类和枚举定义
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
import pandas as pd
from abc import ABC, abstractmethod


class FactorCategory(Enum):
    """因子类别"""
    VALUE = "value"           # 价值因子
    GROWTH = "growth"         # 成长因子
    MOMENTUM = "momentum"     # 动量因子
    QUALITY = "quality"       # 质量因子
    SENTIMENT = "sentiment"   # 情绪因子
    TECHNICAL = "technical"   # 技术因子


class FactorType(Enum):
    """因子数据类型"""
    PRICE = "price"          # 价格类
    FUNDAMENTAL = "fundamental"  # 基本面
    VOLUME = "volume"        # 成交量
    DERIVED = "derived"       # 衍生
    COMPOSITE = "composite"   # 复合
    TECHNICAL = "technical"   # 技术指标
    MARKET = "market"         # 市场数据


@dataclass
class FactorInfo:
    """因子元信息"""
    name: str                          # 因子名称
    category: FactorCategory           # 因子类别
    factor_type: FactorType            # 因子类型
    description: str                   # 因子描述
    formula: str                       # 计算公式
    params: Dict[str, Any] = field(default_factory=dict)  # 参数
    author: str = "TradingAgents-CN"   # 作者
    version: str = "1.0.0"             # 版本
    tags: List[str] = field(default_factory=list)  # 标签


class BaseFactor(ABC):
    """
    因子基类
    
    所有因子都需要继承此类并实现 compute 方法。
    
    使用示例:
        class PE_Ratio(BaseFactor):
            name = "PE_Ratio"
            category = FactorCategory.VALUE
            factor_type = FactorType.FUNDAMENTAL
            
            def compute(self, data: pd.DataFrame) -> pd.Series:
                return data['close'] / data['net_income'] * 100
    """
    
    # 类属性（子类覆盖）
    name: str = ""
    category: FactorCategory = FactorCategory.TECHNICAL
    factor_type: FactorType = FactorType.DERIVED
    description: str = ""
    formula: str = ""
    params: Dict[str, Any] = {}
    
    def __init__(self, **kwargs):
        """初始化因子，可传入参数覆盖默认值"""
        self.params = {**self.params, **kwargs}
        self._validate_params()
    
    def _validate_params(self):
        """验证参数"""
        pass
    
    @abstractmethod
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """
        计算因子值
        
        Args:
            data: 包含所需数据的字典，键为数据类型名
                  常见键: 'daily' (日线数据), 'financial' (财务数据), 'moneyflow' (资金流)
                  
        Returns:
            pd.Series: 因子值，索引为股票代码
        """
        pass
    
    def get_info(self) -> FactorInfo:
        """获取因子元信息"""
        return FactorInfo(
            name=self.name,
            category=self.category,
            factor_type=self.factor_type,
            description=self.description,
            formula=self.formula,
            params=self.params
        )
    
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"


class CompositeFactor(BaseFactor):
    """
    复合因子 - 将多个因子组合
    
    支持：
    - 等权组合
    - 加权组合
    - 标准化后组合
    """
    
    name = "composite"
    category = FactorCategory.TECHNICAL
    factor_type = FactorType.COMPOSITE
    
    def __init__(
        self,
        factors: List[BaseFactor],
        weights: Optional[List[float]] = None,
        normalize: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.factors = factors
        self.normalize = normalize
        
        # 默认等权
        if weights is None:
            self.weights = [1.0 / len(factors)] * len(factors)
        else:
            self.weights = weights
    
    def compute(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """计算复合因子"""
        results = []
        
        for factor in self.factors:
            result = factor.compute(data)
            if self.normalize:
                # Z-score 标准化
                result = (result - result.mean()) / result.std()
            results.append(result)
        
        # 加权求和
        composite = sum(w * r for w, r in zip(self.weights, results))
        
        return composite


class FactorRegistry:
    """
    因子注册表
    
    管理所有因子，提供查询、筛选功能。
    
    使用示例:
        registry = FactorRegistry()
        
        # 获取所有价值因子
        value_factors = registry.get_by_category(FactorCategory.VALUE)
        
        # 按名称获取
        pe = registry.get("PE_Ratio")
        
        # 创建因子实例
        factor = registry.create("RSI", period=14)
    """
    
    _instance = None
    _factors: Dict[str, type] = {}
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, factor_class: type, name: Optional[str] = None):
        """
        注册因子类
        
        Args:
            factor_class: 因子类
            name: 因子名称，默认使用类属性 name
        """
        factor_name = name or getattr(factor_class, 'name', factor_class.__name__)
        cls._factors[factor_name] = factor_class
    
    @classmethod
    def get(cls, name: str) -> Optional[type]:
        """根据名称获取因子类"""
        return cls._factors.get(name)
    
    @classmethod
    def get_by_category(cls, category: FactorCategory) -> Dict[str, type]:
        """获取指定类别的所有因子"""
        return {
            name: cls_ for name, cls_ in cls._factors.items()
            if getattr(cls_, 'category', None) == category
        }
    
    @classmethod
    def get_by_tag(cls, tag: str) -> Dict[str, type]:
        """根据标签获取因子"""
        return {
            name: cls_ for name, cls_ in cls._factors.items()
            if tag in getattr(cls_, 'tags', [])
        }
    
    @classmethod
    def list_all(cls) -> List[str]:
        """列出所有已注册的因子"""
        return list(cls._factors.keys())
    
    @classmethod
    def create(cls, name: str, **kwargs) -> BaseFactor:
        """
        创建因子实例
        
        Args:
            name: 因子名称
            **kwargs: 因子参数
        """
        factor_class = cls.get(name)
        if factor_class is None:
            raise ValueError(f"Unknown factor: {name}")
        return factor_class(**kwargs)
    
    @classmethod
    def initialize(cls):
        """初始化注册表，导入所有因子"""
        if cls._initialized:
            return
        
        # 延迟导入，避免循环依赖
        from . import value, growth, momentum, quality, sentiment, technical
        
        cls._initialized = True


def get_registry() -> FactorRegistry:
    """获取因子注册表实例"""
    return FactorRegistry()
