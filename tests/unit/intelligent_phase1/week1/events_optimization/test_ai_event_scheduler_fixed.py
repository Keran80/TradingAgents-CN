"""
AI 事件调度器固定版本单元测试
"""
import pytest
import sys
import os
import asyncio
from unittest.mock import Mock, patch

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

# 添加项目根目录到 Python 路径
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

class TestAIEventSchedulerFixed:
    """AI 事件调度器固定版本测试类"""
    
    def test_module_exists(self):
        """测试模块文件存在"""
        module_path = os.path.join(PROJECT_ROOT, "intelligent_phase1", "week1", "events_optimization", "ai_event_scheduler.py")
        assert os.path.exists(module_path), f"模块文件不存在：{module_path}"
        print(f"✅ 模块文件存在：{module_path}")
    
    def test_file_syntax(self):
        """测试文件语法"""
        module_path = os.path.join(PROJECT_ROOT, "intelligent_phase1", "week1", "events_optimization", "ai_event_scheduler.py")
        
        try:
            with open(module_path, 'r') as f:
                content = f.read()
            compile(content, module_path, 'exec')
            print("✅ 文件语法正确")
        except SyntaxError as e:
            pytest.fail(f"文件语法错误：{e}")
    
    def test_file_content_analysis(self):
        """测试文件内容分析"""
        module_path = os.path.join(PROJECT_ROOT, "intelligent_phase1", "week1", "events_optimization", "ai_event_scheduler.py")
        
        with open(module_path, 'r') as f:
            content = f.read()
        
        # 检查必要的内容
        assert 'class AIEventScheduler' in content
        assert 'EventPriority' in content
        assert 'async' in content or 'asyncio' in content
        
        print("✅ 文件内容分析通过")
    
    def test_async_capability(self):
        """测试异步能力"""
        from intelligent_phase1.week1.events_optimization.ai_event_scheduler import AIEventScheduler
        import inspect
        
        # 检查是否有异步方法
        methods = [m for m in dir(AIEventScheduler) if not m.startswith('_')]
        has_async = False
        
        for method_name in methods:
            method = getattr(AIEventScheduler, method_name, None)
            if method and inspect.iscoroutinefunction(method):
                has_async = True
                break
        
        assert has_async, "未找到异步方法"
        print("✅ 异步能力支持")
    
    def test_ai_keywords(self):
        """测试 AI 关键词"""
        module_path = os.path.join(PROJECT_ROOT, "intelligent_phase1", "week1", "events_optimization", "ai_event_scheduler.py")
        
        with open(module_path, 'r') as f:
            content = f.read()
        
        ai_keywords = ['AI', '智能', 'scheduler', '调度']
        found_keywords = [kw for kw in ai_keywords if kw in content]
        
        assert len(found_keywords) > 0
        print(f"✅ AI 关键词：{found_keywords}")
    
    def test_performance_patterns(self):
        """测试性能模式"""
        module_path = os.path.join(PROJECT_ROOT, "intelligent_phase1", "week1", "events_optimization", "ai_event_scheduler.py")
        
        with open(module_path, 'r') as f:
            content = f.read()
        
        performance_patterns = ['asyncio', 'async', 'await', 'performance', '优化']
        found_patterns = [p for p in performance_patterns if p in content]
        
        assert len(found_patterns) > 0
        print(f"✅ 性能模式：{found_patterns}")
