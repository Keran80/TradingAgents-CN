# -*- coding: utf-8 -*-
"""
RAG Registry 模块单元测试

测试范围：
- RagRegistry 类
- 创建/删除集合
- 列表/获取信息
- 更新集合
- 全局注册表
- 便捷函数
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tempfile
import shutil

# 条件导入（处理依赖缺失）
try:
    from datetime import datetime
    from tradingagents.rag.registry import (
        RagRegistry,
        get_rag_registry,
        create_knowledge_base,
    )
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装（tradingagents）", allow_module_level=True)


class TestRagRegistry:
    """RagRegistry 类测试"""

    def setup_method(self):
        """设置测试环境"""
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """清理测试环境"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_初始化_默认目录(self):
        """测试初始化使用默认目录"""
        registry = RagRegistry()
        assert registry.base_dir == "rag_data"
        assert registry.collections == {}

    def test_初始化_自定义目录(self):
        """测试初始化使用自定义目录"""
        registry = RagRegistry(base_dir=self.test_dir)
        assert registry.base_dir == self.test_dir

    def test_创建集合(self):
        """测试创建集合"""
        registry = RagRegistry(base_dir=self.test_dir)
        result = registry.create_collection("test_kb", description="Test knowledge base")
        assert result is True
        assert "test_kb" in registry.collections

    def test_创建集合_重复名称(self):
        """测试创建重复名称集合"""
        registry = RagRegistry(base_dir=self.test_dir)
        registry.create_collection("test_kb")
        result = registry.create_collection("test_kb")
        assert result is False

    def test_创建集合_带元数据(self):
        """测试创建集合带元数据"""
        registry = RagRegistry(base_dir=self.test_dir)
        metadata = {"author": "test", "version": "1.0"}
        registry.create_collection("test_kb", metadata=metadata)
        assert registry.collections["test_kb"]["metadata"] == metadata

    def test_删除集合(self):
        """测试删除集合"""
        registry = RagRegistry(base_dir=self.test_dir)
        registry.create_collection("test_kb")
        result = registry.delete_collection("test_kb")
        assert result is True
        assert "test_kb" not in registry.collections

    def test_删除集合_不存在(self):
        """测试删除不存在的集合"""
        registry = RagRegistry(base_dir=self.test_dir)
        result = registry.delete_collection("non_existent")
        assert result is False

    def test_列出集合(self):
        """测试列出集合"""
        registry = RagRegistry(base_dir=self.test_dir)
        registry.create_collection("kb1")
        registry.create_collection("kb2")
        registry.create_collection("kb3")

        collections = registry.list_collections()
        assert len(collections) == 3
        assert "kb1" in collections
        assert "kb2" in collections
        assert "kb3" in collections

    def test_获取集合信息_存在(self):
        """测试获取存在的集合信息"""
        registry = RagRegistry(base_dir=self.test_dir)
        registry.create_collection("test_kb", description="Test KB")
        info = registry.get_collection_info("test_kb")
        assert info is not None
        assert info["description"] == "Test KB"

    def test_获取集合信息_不存在(self):
        """测试获取不存在的集合信息"""
        registry = RagRegistry(base_dir=self.test_dir)
        info = registry.get_collection_info("non_existent")
        assert info is None

    def test_更新集合(self):
        """测试更新集合"""
        registry = RagRegistry(base_dir=self.test_dir)
        registry.create_collection("test_kb")
        result = registry.update_collection("test_kb", description="Updated", doc_count=10)
        assert result is True
        assert registry.collections["test_kb"]["description"] == "Updated"
        assert registry.collections["test_kb"]["doc_count"] == 10

    def test_更新集合_不存在(self):
        """测试更新不存在的集合"""
        registry = RagRegistry(base_dir=self.test_dir)
        result = registry.update_collection("non_existent", description="test")
        assert result is False

    def test_保存和加载注册表(self):
        """测试保存和加载注册表"""
        registry = RagRegistry(base_dir=self.test_dir)
        registry.create_collection("kb1")
        registry.create_collection("kb2")
        registry._save_registry()

        # 创建新实例加载
        registry2 = RagRegistry(base_dir=self.test_dir)
        collections = registry2.list_collections()
        assert len(collections) == 2
        assert "kb1" in collections
        assert "kb2" in collections

    def test_加载不存在的注册表(self):
        """测试加载不存在的注册表"""
        empty_dir = os.path.join(self.test_dir, "empty")
        os.makedirs(empty_dir)
        registry = RagRegistry(base_dir=empty_dir)
        assert registry.collections == {}


class TestGlobalRegistry:
    """全局注册表测试"""

    def setup_method(self):
        """设置测试环境"""
        # 重置全局注册表
        try:
            from tradingagents.rag import registry as reg_module
            reg_module._global_registry = None
        except ImportError:
            pytest.skip("依赖未安装", allow_module_level=True)

    def test_获取全局注册表_首次创建(self):
        """测试首次获取创建全局注册表"""
        registry = get_rag_registry()
        assert registry is not None
        assert isinstance(registry, RagRegistry)

    def test_获取全局注册表_单例模式(self):
        """测试全局注册表单例模式"""
        registry1 = get_rag_registry()
        registry2 = get_rag_registry()
        assert registry1 is registry2

    def test_获取全局注册表_自定义目录(self):
        """测试获取全局注册表使用自定义目录"""
        test_dir = tempfile.mkdtemp()
        registry = get_rag_registry(base_dir=test_dir)
        assert registry.base_dir == test_dir

        # 清理
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)


class TestCreateKnowledgeBase:
    """create_knowledge_base 便捷函数测试"""

    def setup_method(self):
        """设置测试环境"""
        try:
            from tradingagents.rag import registry as reg_module
            reg_module._global_registry = None
        except ImportError:
            pytest.skip("依赖未安装", allow_module_level=True)
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """清理测试环境"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        # 重置全局注册表
        try:
            from tradingagents.rag import registry as reg_module
            reg_module._global_registry = None
        except ImportError:
            pass

    def test_创建知识库(self):
        """测试创建知识库"""
        result = create_knowledge_base("test_kb", description="Test KB", base_dir=self.test_dir)
        assert result is True

    def test_创建知识库_验证注册表(self):
        """测试创建知识库后注册表更新"""
        create_knowledge_base("test_kb", base_dir=self.test_dir)
        registry = get_rag_registry(base_dir=self.test_dir)
        assert "test_kb" in registry.list_collections()
