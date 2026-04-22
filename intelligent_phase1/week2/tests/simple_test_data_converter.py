#!/usr/bin/env python3
"""
简化版数据转换器测试（不依赖pandas/numpy）
"""

import asyncio
import sys
import os
import json

# 修改导入路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 创建简化版DataConverter
class SimpleDataConverter:
    """简化版数据转换器"""
    
    def __init__(self, config=None):
        self.config = config or {
            "default_format": "json",
            "enable_cache": True,
            "quality_check": True
        }
        self.cache = {}
        self.stats = {
            "total_conversions": 0,
            "successful_conversions": 0,
            "failed_conversions": 0
        }
    
    async def convert(self, data, target_format, options=None):
        """简化转换方法"""
        self.stats["total_conversions"] += 1
        
        try:
            if target_format == "json":
                result = json.dumps(data, ensure_ascii=False, indent=2)
            elif target_format == "dict":
                if isinstance(data, dict):
                    result = data
                elif isinstance(data, list):
                    result = {f"item_{i}": item for i, item in enumerate(data)}
                else:
                    result = {"value": data}
            elif target_format == "list":
                if isinstance(data, list):
                    result = data
                elif isinstance(data, dict):
                    result = list(data.values())
                else:
                    result = [data]
            else:
                raise ValueError(f"不支持的格式: {target_format}")
            
            self.stats["successful_conversions"] += 1
            return result
            
        except Exception as e:
            self.stats["failed_conversions"] += 1
            raise
    
    def get_stats(self):
        return self.stats

async def test_simple_converter():
    """测试简化版转换器"""
    print("🧪 测试简化版数据转换器")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 0
    
    try:
        converter = SimpleDataConverter()
        
        # 测试数据
        test_data = [
            {"symbol": "000001", "price": 100.5, "volume": 1000},
            {"symbol": "000002", "price": 200.3, "volume": 2000},
            {"symbol": "000003", "price": 150.7, "volume": 1500}
        ]
        
        # 测试1: 转换为JSON
        print("1. 测试转换为JSON...")
        total_tests += 1
        try:
            json_str = await converter.convert(test_data, "json")
            assert isinstance(json_str, str)
            assert len(json_str) > 0
            parsed = json.loads(json_str)
            assert isinstance(parsed, list)
            assert len(parsed) == 3
            print("   ✅ 转换为JSON通过")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ 转换为JSON失败: {e}")
        
        # 测试2: 转换为字典
        print("2. 测试转换为字典...")
        total_tests += 1
        try:
            dict_data = await converter.convert(test_data, "dict")
            assert isinstance(dict_data, dict)
            assert "item_0" in dict_data
            assert dict_data["item_0"]["symbol"] == "000001"
            print("   ✅ 转换为字典通过")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ 转换为字典失败: {e}")
        
        # 测试3: 转换为列表
        print("3. 测试转换为列表...")
        total_tests += 1
        try:
            list_data = await converter.convert(test_data, "list")
            assert isinstance(list_data, list)
            assert len(list_data) == 3
            print("   ✅ 转换为列表通过")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ 转换为列表失败: {e}")
        
        # 测试4: 获取统计信息
        print("4. 测试获取统计信息...")
        total_tests += 1
        try:
            stats = converter.get_stats()
            assert isinstance(stats, dict)
            assert stats["total_conversions"] == 3
            assert stats["successful_conversions"] == 3
            print("   ✅ 获取统计信息通过")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ 获取统计信息失败: {e}")
        
        # 测试结果
        print(f"\n📊 测试结果: {tests_passed}/{total_tests} 通过")
        if tests_passed == total_tests:
            print("🎉 所有测试通过!")
            return True
        else:
            print(f"⚠️  {total_tests - tests_passed} 个测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_converter())
    sys.exit(0 if success else 1)