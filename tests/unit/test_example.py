"""
基础单元测试示例
"""
import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import_project():
    """测试项目是否可以正常导入"""
    try:
        # 尝试导入项目模块
        import tradingagents
        assert tradingagents is not None
        print("✅ 项目导入成功")
    except ImportError as e:
        pytest.fail(f"项目导入失败: {e}")

def test_basic_math():
    """基础数学测试"""
    assert 1 + 1 == 2
    assert 2 * 2 == 4
    assert 10 / 2 == 5

class TestExampleClass:
    """示例测试类"""
    
    def test_string_operations(self):
        """字符串操作测试"""
        text = "TradingAgents-CN"
        assert "Trading" in text
        assert text.startswith("Trading")
        assert text.endswith("CN")
    
    def test_list_operations(self):
        """列表操作测试"""
        numbers = [1, 2, 3, 4, 5]
        assert len(numbers) == 5
        assert sum(numbers) == 15
        assert numbers[0] == 1
        assert numbers[-1] == 5

@pytest.mark.slow
def test_slow_operation():
    """标记为慢速测试的示例"""
    # 模拟慢速操作
    import time
    time.sleep(0.1)  # 短暂延迟
    assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
