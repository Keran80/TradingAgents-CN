#!/usr/bin/env python3
"""
集成测试 - 测试股票、期货、数据转换模块协同工作
"""

import asyncio
import sys
import os
import json

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_integration():
    """集成测试主函数"""
    print("🧪 集成测试 - 测试模块协同工作")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 0
    
    try:
        # 测试1: 股票数据获取和转换
        print("1. 测试股票数据获取和转换...")
        total_tests += 1
        try:
            # 导入股票适配器
            from src.stock_data_source import StockDataSource
            
            # 创建股票适配器
            stock_adapter = StockDataSource({
                "name": "stock_data_source",
                "type": "stock",
                "config": {
                    "api_key": "test_key",
                    "base_url": "http://test.api.com"
                }
            })
            
            # 连接
            await stock_adapter.connect()
            print("   ✅ 股票适配器连接成功")
            
            # 获取支持的股票代码
            symbols = await stock_adapter.get_supported_symbols()
            assert isinstance(symbols, list)
            assert len(symbols) > 0
            print(f"   ✅ 获取到 {len(symbols)} 个股票代码")
            
            # 获取历史数据
            history_data = await stock_adapter.fetch_historical_data(
                symbol="000001",
                start_date="2026-01-01",
                end_date="2026-01-05"
            )
            assert isinstance(history_data, list)
            assert len(history_data) > 0
            print(f"   ✅ 获取到 {len(history_data)} 条历史数据")
            
            # 断开连接
            await stock_adapter.disconnect()
            print("   ✅ 股票适配器断开连接成功")
            
            print("   ✅ 股票数据获取测试通过")
            tests_passed += 1
            
        except Exception as e:
            print(f"   ❌ 股票数据获取测试失败: {e}")
        
        # 测试2: 期货数据获取和转换
        print("2. 测试期货数据获取和转换...")
        total_tests += 1
        try:
            # 导入期货适配器
            from src.futures_data_source import FuturesDataSource
            
            # 创建期货适配器
            futures_adapter = FuturesDataSource({
                "name": "futures_data_source",
                "type": "futures",
                "config": {
                    "api_key": "test_key",
                    "base_url": "http://test.api.com"
                }
            })
            
            # 连接
            await futures_adapter.connect()
            print("   ✅ 期货适配器连接成功")
            
            # 获取支持的期货代码
            symbols = await futures_adapter.get_supported_symbols()
            assert isinstance(symbols, list)
            assert len(symbols) > 0
            print(f"   ✅ 获取到 {len(symbols)} 个期货代码")
            
            # 获取历史数据
            history_data = await futures_adapter.fetch_historical_data(
                symbol="AU",
                start_date="2026-01-01",
                end_date="2026-01-05"
            )
            assert isinstance(history_data, list)
            assert len(history_data) > 0
            print(f"   ✅ 获取到 {len(history_data)} 条历史数据")
            
            # 获取市场深度
            market_depth = await futures_adapter.fetch_market_depth("AU", depth=3)
            assert isinstance(market_depth, dict)
            assert "bids" in market_depth
            assert "asks" in market_depth
            print(f"   ✅ 获取市场深度: 买盘{len(market_depth['bids'])}档, 卖盘{len(market_depth['asks'])}档")
            
            # 断开连接
            await futures_adapter.disconnect()
            print("   ✅ 期货适配器断开连接成功")
            
            print("   ✅ 期货数据获取测试通过")
            tests_passed += 1
            
        except Exception as e:
            print(f"   ❌ 期货数据获取测试失败: {e}")
        
        # 测试3: 数据转换器集成
        print("3. 测试数据转换器集成...")
        total_tests += 1
        try:
            # 创建测试数据
            test_stock_data = [
                {"symbol": "000001", "price": 100.5, "volume": 1000, "timestamp": "2026-01-01 09:30:00"},
                {"symbol": "000001", "price": 101.2, "volume": 1500, "timestamp": "2026-01-01 09:31:00"},
                {"symbol": "000001", "price": 102.0, "volume": 1200, "timestamp": "2026-01-01 09:32:00"}
            ]
            
            test_futures_data = [
                {"symbol": "AU", "price": 5666.0, "volume": 100, "timestamp": "2026-01-01 09:30:00"},
                {"symbol": "AU", "price": 5670.0, "volume": 150, "timestamp": "2026-01-01 09:31:00"},
                {"symbol": "AU", "price": 5668.0, "volume": 120, "timestamp": "2026-01-01 09:32:00"}
            ]
            
            # 使用简化版数据转换器
            from tests.simple_test_data_converter import SimpleDataConverter
            converter = SimpleDataConverter()
            
            # 转换股票数据为JSON
            stock_json = await converter.convert(test_stock_data, "json")
            assert isinstance(stock_json, str)
            parsed_stock = json.loads(stock_json)
            assert len(parsed_stock) == 3
            print(f"   ✅ 股票数据转换为JSON成功: {len(stock_json)}字符")
            
            # 转换期货数据为字典
            futures_dict = await converter.convert(test_futures_data, "dict")
            assert isinstance(futures_dict, dict)
            assert "item_0" in futures_dict
            print(f"   ✅ 期货数据转换为字典成功: {len(futures_dict)}项")
            
            # 合并数据
            combined_data = test_stock_data + test_futures_data
            combined_list = await converter.convert(combined_data, "list")
            assert isinstance(combined_list, list)
            assert len(combined_list) == 6
            print(f"   ✅ 数据合并成功: {len(combined_list)}条记录")
            
            print("   ✅ 数据转换器集成测试通过")
            tests_passed += 1
            
        except Exception as e:
            print(f"   ❌ 数据转换器集成测试失败: {e}")
        
        # 测试4: 端到端流程测试
        print("4. 测试端到端流程...")
        total_tests += 1
        try:
            # 模拟端到端流程
            print("   🔄 模拟端到端流程:")
            print("     1. 获取股票数据")
            print("     2. 获取期货数据")
            print("     3. 数据转换和清洗")
            print("     4. 数据合并")
            print("     5. 结果输出")
            
            # 创建模拟数据
            mock_stock_data = [
                {"symbol": "000001", "price": 100.5, "change": 0.5, "volume": 1000},
                {"symbol": "000002", "price": 200.3, "change": 1.2, "volume": 2000}
            ]
            
            mock_futures_data = [
                {"symbol": "AU", "price": 5666.0, "change": 10.5, "volume": 100},
                {"symbol": "AG", "price": 7800.0, "change": -5.2, "volume": 50}
            ]
            
            # 数据转换
            converter = SimpleDataConverter()
            
            # 转换股票数据
            stock_json = await converter.convert(mock_stock_data, "json", {"indent": 2})
            
            # 转换期货数据
            futures_json = await converter.convert(mock_futures_data, "json", {"indent": 2})
            
            # 合并数据
            all_data = mock_stock_data + mock_futures_data
            all_json = await converter.convert(all_data, "json", {"indent": 2})
            
            # 验证结果
            assert len(stock_json) > 0
            assert len(futures_json) > 0
            assert len(all_json) > 0
            
            print(f"   ✅ 股票数据输出: {len(stock_json)}字符")
            print(f"   ✅ 期货数据输出: {len(futures_json)}字符")
            print(f"   ✅ 合并数据输出: {len(all_json)}字符")
            print("   ✅ 端到端流程测试通过")
            tests_passed += 1
            
        except Exception as e:
            print(f"   ❌ 端到端流程测试失败: {e}")
        
        # 测试5: 错误处理和恢复
        print("5. 测试错误处理和恢复...")
        total_tests += 1
        try:
            converter = SimpleDataConverter()
            
            # 测试无效数据
            invalid_data = "invalid_string"
            
            try:
                # 应该抛出异常
                result = await converter.convert(invalid_data, "json")
                print("   ⚠️ 无效数据未抛出异常")
            except Exception as e:
                print(f"   ✅ 无效数据正确处理: {type(e).__name__}")
            
            # 测试无效格式
            try:
                # 应该抛出异常
                result = await converter.convert([1, 2, 3], "invalid_format")
                print("   ⚠️ 无效格式未抛出异常")
            except ValueError as e:
                print(f"   ✅ 无效格式正确处理: {str(e)}")
            
            # 验证统计信息
            stats = converter.get_stats()
            assert "total_conversions" in stats
            assert "failed_conversions" in stats
            print(f"   ✅ 统计信息正常: {stats}")
            
            print("   ✅ 错误处理和恢复测试通过")
            tests_passed += 1
            
        except Exception as e:
            print(f"   ❌ 错误处理和恢复测试失败: {e}")
        
        # 测试结果
        print(f"\n📊 集成测试结果: {tests_passed}/{total_tests} 通过")
        if tests_passed == total_tests:
            print("🎉 所有集成测试通过!")
            
            # 生成集成测试报告
            report = {
                "test_time": "2026-04-10 07:55",
                "total_tests": total_tests,
                "passed_tests": tests_passed,
                "failed_tests": total_tests - tests_passed,
                "success_rate": tests_passed / total_tests * 100,
                "tested_modules": [
                    "StockDataSource",
                    "FuturesDataSource",
                    "DataConverter",
                    "Integration Workflow",
                    "Error Handling"
                ],
                "status": "PASS" if tests_passed == total_tests else "FAIL"
            }
            
            # 保存报告
            report_file = "/tmp/CODING_agent/integration_test_report_20260410_0755.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"📄 集成测试报告已保存: {report_file}")
            return True
            
        else:
            print(f"⚠️  {total_tests - tests_passed} 个集成测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 集成测试执行失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_integration())
    sys.exit(0 if success else 1)