# -*- coding: utf-8 -*-
"""
RAG Base 模块单元测试

测试范围：
- DocumentType 枚举
- Document 文档类
- DocumentChunk 分块类
- RetrievalResult 检索结果类
- QaResult 问答结果类
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 条件导入（处理依赖缺失）
try:
    from datetime import datetime
    from tradingagents.rag.base import (
        DocumentType,
        Document,
        DocumentChunk,
        RetrievalResult,
        QaResult,
    )
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装（tradingagents）", allow_module_level=True)


class TestDocumentType:
    """DocumentType 枚举测试"""

    def test_枚举值(self):
        """测试枚举值"""
        assert DocumentType.PDF.value == "pdf"
        assert DocumentType.MARKDOWN.value == "markdown"
        assert DocumentType.TEXT.value == "text"
        assert DocumentType.HTML.value == "html"
        assert DocumentType.JSON.value == "json"
        assert DocumentType.UNKNOWN.value == "unknown"

    def test_枚举数量(self):
        """测试枚举数量"""
        assert len(DocumentType) == 6


class TestDocument:
    """Document 文档类测试"""

    def test_创建文档(self):
        """测试创建文档"""
        doc = Document(
            id="doc_001",
            content="This is test content.",
            source="/path/to/file.txt",
            doc_type=DocumentType.TEXT,
        )
        assert doc.id == "doc_001"
        assert doc.content == "This is test content."
        assert doc.source == "/path/to/file.txt"
        assert doc.doc_type == DocumentType.TEXT

    def test_创建文档_默认元数据(self):
        """测试创建文档使用默认元数据"""
        doc = Document(
            id="doc_001",
            content="Content",
        )
        assert doc.metadata == {}

    def test_创建文档_自定义元数据(self):
        """测试创建文档使用自定义元数据"""
        doc = Document(
            id="doc_001",
            content="Content",
            metadata={"author": "test", "version": "1.0"},
        )
        assert doc.metadata["author"] == "test"
        assert doc.metadata["version"] == "1.0"

    def test_post_init_空ID生成(self):
        """测试空ID时自动生成"""
        doc = Document(
            id="",
            content="Content",
        )
        assert doc.id != ""
        assert doc.id.startswith("doc_")

    def test_post_init_空元数据初始化(self):
        """测试空元数据时初始化为空字典"""
        doc = Document(
            id="doc_001",
            content="Content",
            metadata=None,
        )
        assert doc.metadata == {}

    def test_创建时间(self):
        """测试创建时间"""
        doc = Document(
            id="doc_001",
            content="Content",
        )
        assert isinstance(doc.created_at, datetime)


class TestDocumentChunk:
    """DocumentChunk 分块类测试"""

    def test_创建分块(self):
        """测试创建分块"""
        chunk = DocumentChunk(
            id="chunk_001",
            content="Chunk content here.",
            document_id="doc_001",
            chunk_index=0,
        )
        assert chunk.id == "chunk_001"
        assert chunk.content == "Chunk content here."
        assert chunk.document_id == "doc_001"
        assert chunk.chunk_index == 0

    def test_创建分块_空ID生成(self):
        """测试空ID时自动生成"""
        chunk = DocumentChunk(
            id="",
            content="Content",
            document_id="doc_001",
            chunk_index=2,
        )
        assert chunk.id == "chunk_doc_001_2"

    def test_创建分块_带嵌入向量(self):
        """测试创建分块带嵌入向量"""
        embedding = [0.1, 0.2, 0.3, 0.4]
        chunk = DocumentChunk(
            id="chunk_001",
            content="Content",
            document_id="doc_001",
            chunk_index=0,
            embedding=embedding,
        )
        assert chunk.embedding == embedding

    def test_创建分块_默认元数据(self):
        """测试创建分块使用默认元数据"""
        chunk = DocumentChunk(
            id="chunk_001",
            content="Content",
            document_id="doc_001",
            chunk_index=0,
        )
        assert chunk.metadata == {}


class TestRetrievalResult:
    """RetrievalResult 检索结果类测试"""

    def test_创建检索结果(self):
        """测试创建检索结果"""
        chunk = DocumentChunk(
            id="chunk_001",
            content="Content",
            document_id="doc_001",
            chunk_index=0,
        )
        result = RetrievalResult(
            chunk=chunk,
            score=0.95,
            rank=1,
        )
        assert result.chunk is chunk
        assert result.score == 0.95
        assert result.rank == 1

    def test_repr(self):
        """测试字符串表示"""
        chunk = DocumentChunk(
            id="chunk_001",
            content="Content",
            document_id="doc_001",
            chunk_index=0,
        )
        result = RetrievalResult(
            chunk=chunk,
            score=0.8765,
            rank=2,
        )
        repr_str = repr(result)
        assert "chunk_001" in repr_str
        assert "0.8765" in repr_str
        assert "2" in repr_str

    def test_默认排名(self):
        """测试默认排名为0"""
        chunk = DocumentChunk(
            id="chunk_001",
            content="Content",
            document_id="doc_001",
            chunk_index=0,
        )
        result = RetrievalResult(
            chunk=chunk,
            score=0.9,
        )
        assert result.rank == 0


class TestQaResult:
    """QaResult 问答结果类测试"""

    def test_创建问答结果(self):
        """测试创建问答结果"""
        result = QaResult(
            question="What is the meaning of life?",
            answer="42",
        )
        assert result.question == "What is the meaning of life?"
        assert result.answer == "42"
        assert result.sources == []
        assert result.metadata == {}

    def test_创建问答结果_带来源(self):
        """测试创建问答结果带来源"""
        chunk = DocumentChunk(
            id="chunk_001",
            content="Content",
            document_id="doc_001",
            chunk_index=0,
        )
        source = RetrievalResult(chunk=chunk, score=0.9, rank=1)

        result = QaResult(
            question="Test question?",
            answer="Test answer",
            sources=[source],
            metadata={"confidence": 0.95},
        )
        assert len(result.sources) == 1
        assert result.metadata["confidence"] == 0.95

    def test_repr(self):
        """测试字符串表示"""
        result = QaResult(
            question="This is a very long question that should be truncated in repr",
            answer="This is also a very long answer that should be truncated in repr",
        )
        repr_str = repr(result)
        assert "This is a very long..." in repr_str
        assert "This is also a very..." in repr_str
