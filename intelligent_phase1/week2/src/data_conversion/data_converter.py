#!/usr/bin/env python3
"""
数据转换和清洗模块 - 智能数据转换引擎
支持多种数据格式转换、数据清洗、质量检查和性能优化
"""

import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

class DataConverter:
    """智能数据转换器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据转换器
        
        Args:
            config: 配置字典
        """
        self.config = config or {
            "default_format": "pandas",
            "enable_cache": True,
            "max_cache_size": 1000,
            "quality_check": True,
            "performance_optimization": True
        }
        
        self.cache = {}
        self.conversion_stats = {
            "total_conversions": 0,
            "successful_conversions": 0,
            "failed_conversions": 0,
            "avg_conversion_time": 0.0
        }
        
        # 支持的格式映射
        self.supported_formats = {
            "pandas": self._convert_to_pandas,
            "numpy": self._convert_to_numpy,
            "json": self._convert_to_json,
            "dict": self._convert_to_dict,
            "list": self._convert_to_list
        }
        
        logger.info(f"数据转换器初始化完成，配置: {self.config}")
    
    async def convert(self, data: Any, target_format: str, 
                     options: Optional[Dict[str, Any]] = None) -> Any:
        """
        转换数据到目标格式
        
        Args:
            data: 输入数据
            target_format: 目标格式 (pandas, numpy, json, dict, list)
            options: 转换选项
            
        Returns:
            转换后的数据
            
        Raises:
            ValueError: 不支持的格式或转换失败
        """
        start_time = datetime.now()
        self.conversion_stats["total_conversions"] += 1
        
        try:
            # 检查缓存
            cache_key = self._generate_cache_key(data, target_format, options)
            if self.config.get("enable_cache", True) and cache_key in self.cache:
                logger.debug(f"从缓存获取转换结果: {cache_key}")
                return self.cache[cache_key]
            
            # 验证目标格式
            if target_format not in self.supported_formats:
                raise ValueError(f"不支持的格式: {target_format}。支持的格式: {list(self.supported_formats.keys())}")
            
            # 执行转换
            converter = self.supported_formats[target_format]
            result = await converter(data, options or {})
            
            # 质量检查
            if self.config.get("quality_check", True):
                await self._quality_check(result, target_format)
            
            # 性能优化
            if self.config.get("performance_optimization", True):
                result = await self._optimize_performance(result, target_format)
            
            # 更新缓存
            if self.config.get("enable_cache", True):
                self._update_cache(cache_key, result)
            
            # 更新统计
            conversion_time = (datetime.now() - start_time).total_seconds()
            self.conversion_stats["successful_conversions"] += 1
            self.conversion_stats["avg_conversion_time"] = (
                self.conversion_stats["avg_conversion_time"] * 
                (self.conversion_stats["successful_conversions"] - 1) + 
                conversion_time
            ) / self.conversion_stats["successful_conversions"]
            
            logger.info(f"数据转换成功: {target_format}, 耗时: {conversion_time:.3f}s")
            return result
            
        except Exception as e:
            self.conversion_stats["failed_conversions"] += 1
            logger.error(f"数据转换失败: {target_format}, 错误: {str(e)}")
            raise
    
    async def _convert_to_pandas(self, data: Any, options: Dict[str, Any]) -> pd.DataFrame:
        """转换为Pandas DataFrame"""
        try:
            if isinstance(data, pd.DataFrame):
                return data
            
            if isinstance(data, dict):
                # 字典转DataFrame
                if all(isinstance(v, (list, tuple, np.ndarray)) for v in data.values()):
                    # 等长列表字典
                    return pd.DataFrame(data)
                else:
                    # 单行数据
                    return pd.DataFrame([data])
            
            if isinstance(data, list):
                if len(data) == 0:
                    return pd.DataFrame()
                
                # 列表转DataFrame
                if all(isinstance(item, dict) for item in data):
                    # 字典列表
                    return pd.DataFrame(data)
                elif all(isinstance(item, (list, tuple)) for item in data):
                    # 二维列表
                    columns = options.get("columns", [f"col_{i}" for i in range(len(data[0]))])
                    return pd.DataFrame(data, columns=columns)
                else:
                    # 一维列表
                    return pd.DataFrame(data, columns=["value"])
            
            if isinstance(data, np.ndarray):
                # NumPy数组转DataFrame
                if data.ndim == 1:
                    return pd.DataFrame(data, columns=["value"])
                else:
                    columns = options.get("columns", [f"col_{i}" for i in range(data.shape[1])])
                    return pd.DataFrame(data, columns=columns)
            
            # 其他类型尝试直接转换
            return pd.DataFrame([data])
            
        except Exception as e:
            raise ValueError(f"转换为Pandas DataFrame失败: {str(e)}")
    
    async def _convert_to_numpy(self, data: Any, options: Dict[str, Any]) -> np.ndarray:
        """转换为NumPy数组"""
        try:
            if isinstance(data, np.ndarray):
                return data
            
            if isinstance(data, pd.DataFrame):
                return data.to_numpy()
            
            if isinstance(data, list):
                return np.array(data)
            
            if isinstance(data, dict):
                # 字典转数组
                values = list(data.values())
                if all(isinstance(v, (list, tuple, np.ndarray)) for v in values):
                    # 多维数据
                    return np.column_stack(values)
                else:
                    # 单维数据
                    return np.array(values)
            
            # 其他类型
            return np.array([data])
            
        except Exception as e:
            raise ValueError(f"转换为NumPy数组失败: {str(e)}")
    
    async def _convert_to_json(self, data: Any, options: Dict[str, Any]) -> str:
        """转换为JSON字符串"""
        try:
            # 处理特殊类型
            if isinstance(data, pd.DataFrame):
                data = data.to_dict(orient="records")
            elif isinstance(data, np.ndarray):
                data = data.tolist()
            elif isinstance(data, np.generic):
                data = data.item()
            
            # 序列化选项
            indent = options.get("indent", 2)
            ensure_ascii = options.get("ensure_ascii", False)
            
            return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
            
        except Exception as e:
            raise ValueError(f"转换为JSON失败: {str(e)}")
    
    async def _convert_to_dict(self, data: Any, options: Dict[str, Any]) -> Dict[str, Any]:
        """转换为字典"""
        try:
            if isinstance(data, dict):
                return data
            
            if isinstance(data, pd.DataFrame):
                orient = options.get("orient", "records")
                return data.to_dict(orient=orient)
            
            if isinstance(data, np.ndarray):
                # NumPy数组转字典
                if data.ndim == 1:
                    return {f"col_{i}": value for i, value in enumerate(data)}
                else:
                    result = {}
                    for i in range(data.shape[1]):
                        result[f"col_{i}"] = data[:, i].tolist()
                    return result
            
            if isinstance(data, list):
                # 列表转字典
                if len(data) == 0:
                    return {}
                
                if all(isinstance(item, dict) for item in data):
                    # 字典列表合并
                    result = {}
                    for item in data:
                        result.update(item)
                    return result
                else:
                    return {f"item_{i}": value for i, value in enumerate(data)}
            
            # 其他类型
            return {"value": data}
            
        except Exception as e:
            raise ValueError(f"转换为字典失败: {str(e)}")
    
    async def _convert_to_list(self, data: Any, options: Dict[str, Any]) -> List[Any]:
        """转换为列表"""
        try:
            if isinstance(data, list):
                return data
            
            if isinstance(data, pd.DataFrame):
                return data.to_dict(orient="records")
            
            if isinstance(data, np.ndarray):
                return data.tolist()
            
            if isinstance(data, dict):
                return list(data.values())
            
            # 其他类型
            return [data]
            
        except Exception as e:
            raise ValueError(f"转换为列表失败: {str(e)}")
    
    async def _quality_check(self, data: Any, target_format: str) -> None:
        """数据质量检查"""
        try:
            if target_format == "pandas" and isinstance(data, pd.DataFrame):
                # 检查空值
                null_count = data.isnull().sum().sum()
                if null_count > 0:
                    logger.warning(f"DataFrame中包含 {null_count} 个空值")
                
                # 检查数据类型
                dtypes = data.dtypes.to_dict()
                logger.debug(f"DataFrame数据类型: {dtypes}")
            
            elif target_format == "numpy" and isinstance(data, np.ndarray):
                # 检查NaN值
                nan_count = np.isnan(data).sum()
                if nan_count > 0:
                    logger.warning(f"NumPy数组中包含 {nan_count} 个NaN值")
                
                # 检查形状
                logger.debug(f"NumPy数组形状: {data.shape}")
            
            # 通用检查
            if data is None:
                raise ValueError("转换结果为None")
            
            logger.debug(f"数据质量检查通过: {target_format}")
            
        except Exception as e:
            logger.warning(f"数据质量检查失败: {str(e)}")
    
    async def _optimize_performance(self, data: Any, target_format: str) -> Any:
        """性能优化"""
        try:
            if target_format == "pandas" and isinstance(data, pd.DataFrame):
                # 优化DataFrame内存使用
                if len(data) > 1000:
                    # 对于大数据集，优化数据类型
                    for col in data.columns:
                        if data[col].dtype == "object":
                            # 尝试转换为分类类型
                            unique_ratio = data[col].nunique() / len(data)
                            if unique_ratio < 0.5:
                                data[col] = data[col].astype("category")
            
            elif target_format == "numpy" and isinstance(data, np.ndarray):
                # 优化NumPy数组数据类型
                if data.dtype == "object":
                    # 尝试转换为数值类型
                    try:
                        data = data.astype(np.float64)
                    except:
                        pass
            
            return data
            
        except Exception as e:
            logger.warning(f"性能优化失败: {str(e)}")
            return data
    
    def _generate_cache_key(self, data: Any, target_format: str, 
                           options: Optional[Dict[str, Any]]) -> str:
        """生成缓存键"""
        import hashlib
        
        # 创建缓存键的字符串表示
        key_parts = [
            str(target_format),
            str(options or {}),
            str(type(data))
        ]
        
        # 对于可哈希的数据类型，添加数据本身
        try:
            if isinstance(data, (str, int, float, bool, tuple)):
                key_parts.append(str(data))
            elif isinstance(data, dict):
                key_parts.append(json.dumps(data, sort_keys=True))
            elif isinstance(data, list):
                key_parts.append(json.dumps(data, sort_keys=True))
        except:
            # 对于不可哈希的类型，使用类型和长度
            key_parts.append(f"{type(data).__name__}_{len(data) if hasattr(data, '__len__') else 'unknown'}")
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _update_cache(self, key: str, value: Any) -> None:
        """更新缓存"""
        max_size = self.config.get("max_cache_size", 1000)
        
        if len(self.cache) >= max_size:
            # 移除最旧的条目（简单实现）
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[key] = value
    
    async def batch_convert(self, data_list: List[Any], target_format: str,
                           options: Optional[Dict[str, Any]] = None) -> List[Any]:
        """批量转换数据"""
        tasks = [self.convert(data, target_format, options) for data in data_list]
        return await asyncio.gather(*tasks)
    
    async def transform_data(self, data: Any, 
                            transformations: List[Dict[str, Any]]) -> Any:
        """
        应用数据转换流水线
        
        Args:
            data: 输入数据
            transformations: 转换步骤列表
            
        Returns:
            转换后的数据
        """
        current_data = data
        
        for transform in transformations:
            transform_type = transform.get("type")
            params = transform.get("params", {})
            
            if transform_type == "filter":
                current_data = await self._apply_filter(current_data, params)
            elif transform_type == "map":
                current_data = await self._apply_map(current_data, params)
            elif transform_type == "aggregate":
                current_data = await self._apply_aggregate(current_data, params)
            elif transform_type == "sort":
                current_data = await self._apply_sort(current_data, params)
            elif transform_type == "format":
                current_data = await self.convert(current_data, params.get("format", "pandas"), params)
            else:
                logger.warning(f"未知的转换类型: {transform_type}")
        
        return current_data
    
    async def _apply_filter(self, data: Any, params: Dict[str, Any]) -> Any:
        """应用过滤"""
        if isinstance(data, pd.DataFrame):
            condition = params.get("condition")
            if condition:
                # 简单的条件过滤
                return data.query(condition)
        return data
    
    async def _apply_map(self, data: Any, params: Dict[str, Any]) -> Any:
        """应用映射"""
        if isinstance(data, pd.DataFrame):
            column = params.get("column")
            func = params.get("function")
            if column and func:
                # 简单的列映射
                if func == "log":
                    data[column] = np.log(data[column])
                elif func == "exp":
                    data[column] = np.exp(data[column])
                elif func == "normalize":
                    data[column] = (data[column] - data[column].mean()) / data[column].std()
        return data
    
    async def _apply_aggregate(self, data: Any, params: Dict[str, Any]) -> Any:
        """应用聚合"""
        if isinstance(data, pd.DataFrame):
            group_by = params.get("group_by")
            agg_func = params.get("agg_func", "mean")
            
            if group_by:
                return data.groupby(group_by).agg(agg_func)
        return data
    
    async def _apply_sort(self, data: Any, params: Dict[str, Any]) -> Any:
        """应用排序"""
        if isinstance(data, pd.DataFrame):
            by = params.get("by")
            ascending = params.get("ascending", True)
            
            if by:
                return data.sort_values(by=by, ascending=ascending)
        return data
    
    def get_stats(self) -> Dict[str, Any]:
        """获取转换统计信息"""
        return {
            **self.conversion_stats,
            "cache_size": len(self.cache),
            "supported_formats": list(self.supported_formats.keys()),
            "config": self.config
        }
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()
        logger.info("数据转换缓存已清空")


# 异步演示函数
async def demo_data_converter():
    """演示数据转换器功能"""
    print("🧪 演示智能数据转换器")
    print("=" * 60)
    
    # 创建转换器
    converter = DataConverter({
        "default_format": "pandas",
        "enable_cache": True,
        "max_cache_size": 100,
        "quality_check": True,
        "performance_optimization": True
    })
    
    # 测试数据
    test_data = [
        {"name": "股票A", "price": 100.5, "volume": 1000},
        {"name": "股票B", "price": 200.3, "volume": 2000},
        {"name": "股票C", "price": 150.7, "volume": 1500}
    ]
    
    print("1. 转换为Pandas DataFrame:")
    df = await converter.convert(test_data, "pandas")
    print(f"   DataFrame形状: {df.shape}")
    print(f"   列名: {list(df.columns)}")
    print(f"   前2行:\n{df.head(2)}")
    
    print("\n2. 转换为NumPy数组:")
    np_array = await converter.convert(test_data, "numpy")
    print(f"   NumPy数组形状: {np_array.shape}")
    print(f"   数据类型: {np_array.dtype}")
    
    print("\n3. 转换为JSON:")
    json_str = await converter.convert(test_data, "json", {"indent": 2})
    print(f"   JSON长度: {len(json_str)} 字符")
    print(f"   前100字符: {json_str[:100]}...")
    
    print("\n4. 转换为字典:")
    dict_data = await converter.convert(test_data, "dict")
    print(f"   字典键: {list(dict_data.keys())}")
