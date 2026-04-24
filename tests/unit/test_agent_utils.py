# -*- coding: utf-8 -*-
"""
agent_utils.py 单元测试

测试通用上下文构建和记忆格式化函数
"""
import pytest

# 条件导入：如果 langchain_core 未安装，则跳过整个测试模块
try:
    from tradingagents.agents.utils.agent_utils import build_context_situation, format_memories
    HAS_LANGCHAIN_CORE = True
except ImportError:
    HAS_LANGCHAIN_CORE = False
    pytest.skip("langchain_core not installed", allow_module_level=True)


class TestBuildContextSituation:
    """build_context_situation 函数测试"""

    def test_build_with_all_reports(self):
        """测试包含所有报告类型的上下文构建"""
        state = {
            "market_report": "市场报告内容",
            "sentiment_report": "情绪报告内容",
            "news_report": "新闻报道内容",
            "fundamentals_report": "基本面报告内容",
        }
        
        result = build_context_situation(state)
        
        assert "市场报告内容" in result
        assert "情绪报告内容" in result
        assert "新闻报道内容" in result
        assert "基本面报告内容" in result
        # 应该用 \n\n 分隔
        assert "\n\n" in result

    def test_build_with_partial_reports(self):
        """测试部分报告缺失的情况"""
        state = {
            "market_report": "市场报告内容",
            # sentiment_report 缺失
            "news_report": "",  # 空字符串
            "fundamentals_report": None,  # None值
        }
        
        result = build_context_situation(state)
        
        assert "市场报告内容" in result
        # 空字符串和None不应出现在结果中
        assert result.count("\n\n") == 0  # 只有一个报告，没有分隔符

    def test_build_with_custom_reports(self):
        """测试自定义报告类型列表"""
        state = {
            "market_report": "市场报告",
            "sentiment_report": "情绪报告",
            "investment_plan": "投资计划",
        }
        
        result = build_context_situation(
            state, 
            reports=["market_report", "investment_plan"]
        )
        
        assert "市场报告" in result
        assert "投资计划" in result
        assert "情绪报告" not in result  # 不在reports列表中

    def test_build_with_empty_state(self):
        """测试空状态字典"""
        state = {}
        result = build_context_situation(state)
        assert result == ""

    def test_build_with_extra_keys(self):
        """测试状态字典包含额外键"""
        state = {
            "market_report": "市场报告",
            "extra_key1": "额外内容1",
            "extra_key2": "额外内容2",
            "fundamentals_report": "基本面",
        }
        
        result = build_context_situation(state)
        
        assert "市场报告" in result
        assert "基本面" in result
        assert "额外内容" not in result  # 不在默认reports中


class TestFormatMemories:
    """format_memories 函数测试"""

    def test_format_with_recommendations(self):
        """测试格式化推荐记忆"""
        memories = [
            {"recommendation": "第一次推荐"},
            {"recommendation": "第二次推荐"},
            {"recommendation": "第三次推荐"},
        ]
        
        result = format_memories(memories)
        
        assert "第一次推荐" in result
        assert "第二次推荐" in result
        assert "第三次推荐" in result
        assert "\n\n" in result

    def test_format_with_empty_memories(self):
        """测试空记忆列表"""
        memories = []
        result = format_memories(memories)
        assert result == ""

    def test_format_with_missing_field(self):
        """测试记忆中缺少指定字段"""
        memories = [
            {"recommendation": "推荐1"},
            {"other_field": "其他内容"},  # 缺少recommendation
            {"recommendation": "推荐2"},
        ]
        
        result = format_memories(memories)
        
        assert "推荐1" in result
        assert "推荐2" in result
        assert "其他内容" not in result

    def test_format_with_custom_field(self):
        """测试使用自定义字段"""
        memories = [
            {"analysis": "分析1", "recommendation": "推荐1"},
            {"analysis": "分析2", "recommendation": "推荐2"},
        ]
        
        result = format_memories(memories, field="analysis")
        
        assert "分析1" in result
        assert "分析2" in result
        assert "推荐" not in result  # 使用的是analysis字段

    def test_format_with_single_memory(self):
        """测试单个记忆"""
        memories = [{"recommendation": "唯一推荐"}]
        result = format_memories(memories)
        assert result == "唯一推荐"
        assert "\n\n" not in result  # 单个记忆不应有分隔符
