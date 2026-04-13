"""
集成测试示例
"""
import pytest
import sys
import os

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 添加项目根目录到 Python 路径
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

class TestIntegration:
    """集成测试类"""
    
    def test_import_intelligent_modules(self):
        """测试智能模块导入"""
        try:
            from intelligent_phase1.week1.events_optimization import ai_event_scheduler
            from intelligent_phase1.week1.plugins_enhancement import advanced_plugins
            print("✅ 智能模块导入成功")
        except ImportError as e:
            pytest.fail(f"模块导入失败：{e}")
    
    def test_async_operations(self):
        """测试异步操作"""
        import asyncio
        
        async def test_async():
            await asyncio.sleep(0.01)
            return True
        
        result = asyncio.run(test_async())
        assert result is True
        print("✅ 异步操作正常")
    
    def test_file_structure(self):
        """测试文件结构"""
        # 检查关键目录存在 (使用正确的路径)
        dirs = [
            "tradingagents",
            "intelligent_phase1",
            "tests"
        ]
        
        for dir_name in dirs:
            dir_path = os.path.join(PROJECT_ROOT, "..", dir_name)
            assert os.path.exists(dir_path), f"目录不存在：{dir_path}"
        
        print("✅ 文件结构正确")
    
    def test_config_files(self):
        """测试配置文件"""
        config_files = [
            "pyproject.toml",
            "pytest.ini"
        ]
        
        for config_file in config_files:
            config_path = os.path.join(PROJECT_ROOT, "..", config_file)
            assert os.path.exists(config_path), f"配置文件不存在：{config_path}"
        
        print("✅ 配置文件存在")

class TestFunctional:
    """功能测试类"""
    
    def test_project_metadata(self):
        """测试项目元数据"""
        # 检查项目基本信息 (使用正确的路径)
        readme_path = os.path.join(PROJECT_ROOT, "..", "README.md")
        pyproject_path = os.path.join(PROJECT_ROOT, "..", "pyproject.toml")
        
        assert os.path.exists(readme_path), f"README.md 不存在"
        assert os.path.exists(pyproject_path), f"pyproject.toml 不存在"
        
        print("✅ 项目元数据完整")
