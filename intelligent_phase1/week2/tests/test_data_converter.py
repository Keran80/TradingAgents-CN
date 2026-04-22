#!/usr/bin/env python3
"""
数据转换器测试
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_conversion.data_converter import DataConverter

async def test_data_converter():
    """测试数据转换器"""
    print("🧪 测试数据转换器")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 0
    
    try:
        # 创建转换器
        converter = DataConverter()
        
        # 测试数据
        test_data = [
            {"symbol": "000001", "price": 100.5, "volume": 1000},
            {"symbol": "000002", "price": 200.3, "volume": 2000},
            {"symbol": "000003", "price": 150.7, "volume": 1500}
        ]
        
        # 测试1: 转换为Pandas DataFrame
        print("1. 测试转换为Pandas DataFrame...")
        total_tests += 1
        try:
            df = await converter.convert(test_data, "pandas")
            assert isinstance(df, type(pd.DataFrame()))
            assert df.shape == (3, 3)
            assert list(df.columns) == ["symbol", "price", "volume"]
            print("   ✅ 转换为Pandas DataFrame通过")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ 转换为Pandas DataFrame失败: {e}")
        
        # 测试2: 转换为NumPy数组
        print("2. 测试转换为NumPy数组...")
        total_tests += 1
        try:
            np_array = await converter.convert(test_data, "numpy")
            assert isinstance(np_array, np.ndarray)
            assert np_array.shape == (3, 3)
            print("   ✅ 转换为NumPy数组通过")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ 转换为NumPy数组失败: {e}")
        
        # 测试3: 转换为JSON
        print("3. 测试转换为JSON...")
        total_tests += 1
        try:
            json_str = await converter.convert(test_data, "json")
            assert isinstance(json_str, str)
            assert len(json_str) > 0
            # 验证JSON格式
            import json as json_module
            parsed = json_module.loads(json_str)
            assert isinstance(parsed, list)
            assert len(parsed) == 3
            print("   ✅ 转换为JSON通过")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ 转换为JSON失败: {e}")
        
        # 测试4: 转换为字典
        print("4. 测试转换为字典...")
        total_tests += 1
        try:
            dict_data = await converter.convert(test_data, "dict")
            assert isinstance(dict_data, dict)
            assert "symbol" in dict_data
            assert len(dict_data["symbol"]) == 3
            print("   ✅ 转换为字典通过")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ 转换为字典失败: {e}")
        
        # 测试5: 转换为列表
        print("5. 测试转换为列表...")
        total_tests += 1
        try:
            list_data = await converter.convert(test_data, "list")
            assert isinstance(list_data, list)
            assert len(list_data) == 3
            print("   ✅ 转换为列表通过")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ 转换为列表失败: {e}")
        
        # 测试6: 批量转换
        print("6. 测试批量转换...")
        total_tests += 1
        try:
            data_list = [test_data, test_data]
            results = await converter.batch_convert(data_list, "pandas")
            assert isinstance(results, list)
            assert len(results) == 2
            assert all(isinstance(r, type(pd.DataFrame())) for r in results)
            print("   ✅ 批量转换通过")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ 批量转换失败: {e}")
        
        # 测试7: 数据转换流水线
        print("7. 测试数据转换流水线...")
        total_tests += 1
        try:
            transformations = [
                {"type": "format", "params": {"format": "pandas"}},
                {"type": "sort", "params": {"by": "price", "ascending": False}},
                {"type": "filter", "params": {"condition": "price > 120"}}
            ]
            
            transformed = await converter.transform_data(test_data, transformations)
            assert isinstance(transformed, type(pd.DataFrame()))
            assert len(transformed) == 2  # 过滤后应该剩2行
            print("   ✅ 数据转换流水线通过")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ 数据转换流水线失败: {e}")
        
        # 测试8: 获取统计信息
        print("8. 测试获取统计信息...")
        total_tests += 1
        try:
            stats = converter.get_stats()
            assert isinstance(stats, dict)
            assert "total_conversions" in stats
            assert "successful_conversions" in stats
            assert stats["total_conversions"] >= total_tests - 1  # 减去当前测试
            print("   ✅ 获取统计信息通过")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ 获取统计信息失败: {e}")
        
        # 测试9: 缓存功能
        print("9. 测试缓存功能...")
        total_tests += 1
        try:
            # 第一次转换（应该计算）
            start_time = asyncio.get_event_loop().time()
            result1 = await converter.convert(test_data, "pandas")
            time1 = asyncio.get_event_loop().time() - start_time
            
            # 第二次转换（应该从缓存获取）
            start_time = asyncio.get_event_loop().time()
            result2 = await converter.convert(test_data, "pandas")
            time2 = asyncio.get_event_loop().time() - start_time
            
            # 缓存应该使第二次更快
            print(f"   第一次转换时间: {time1:.4f}s")
            print(f"   第二次转换时间: {time2:.4f}s")
            print(f"   缓存加速比: {time1/time2:.2f}x")
            
            # 验证结果相同
            assert result1.equals(result2)
            print("   ✅ 缓存功能通过")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ 缓存功能失败: {e}")
        
        # 测试10: 清空缓存
        print("10. 测试清空缓存...")
        total_tests += 1
        try:
            converter.clear_cache()
            stats = converter.get_stats()
            assert stats["cache_size"] == 0
            print("   ✅ 清空缓存通过")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ 清空缓存失败: {e}")
        
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
    # 导入必要的库
    try:
        import pandas as pd
        import numpy as np
    except ImportError as e:
        print(f"❌ 缺少依赖库: {e}")
        print("请安装: pip install pandas numpy")
        sys.exit(1)
    
    # 运行测试
    success = asyncio.run(test_data_converter())
    sys.exit(0 if success else 1)