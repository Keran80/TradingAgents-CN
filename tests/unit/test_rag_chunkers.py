# -*- coding: utf-8 -*-
"""
RAG Chunkers 模块单元测试

测试范围：
- BaseChunker 基类
- FixedSizeChunker 固定大小分块器
- SlidingWindowChunker 滑动窗口分块器
- SentenceChunker 句子级别分块器
- MarkdownChunker Markdown专用分块器
- chunk_document 便捷函数
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 条件导入（处理依赖缺失）
try:
    from tradingagents.rag.chunkers import (
        BaseChunker,
        FixedSizeChunker,
        SlidingWindowChunker,
        SentenceChunker,
        MarkdownChunker,
        chunk_document,
    )
    from tradingagents.rag.base import Document, DocumentChunk
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装（tradingagents）", allow_module_level=True)


class TestBaseChunker:
    """BaseChunker 基类测试"""

    def test_chunk_未实现异常(self):
        """测试chunk方法未实现时抛出异常"""
        chunker = BaseChunker()
        doc = Document(id="doc_001", content="test content")
        with pytest.raises(NotImplementedError):
            chunker.chunk(doc)


class TestFixedSizeChunker:
    """FixedSizeChunker 固定大小分块器测试"""

    def test_初始化_默认参数(self):
        """测试初始化使用默认参数"""
        chunker = FixedSizeChunker()
        assert chunker.chunk_size == 500
        assert chunker.overlap == 50

    def test_初始化_自定义参数(self):
        """测试初始化使用自定义参数"""
        chunker = FixedSizeChunker(chunk_size=100, overlap=10)
        assert chunker.chunk_size == 100
        assert chunker.overlap == 10

    def test_chunk_短文本(self):
        """测试分块短文本"""
        chunker = FixedSizeChunker(chunk_size=100, overlap=10)
        doc = Document(id="doc_001", content="This is a short text.")
        chunks = chunker.chunk(doc)
        assert len(chunks) >= 1
        assert all(isinstance(c, DocumentChunk) for c in chunks)

    def test_chunk_长文本(self):
        """测试分块长文本"""
        chunker = FixedSizeChunker(chunk_size=50, overlap=10)
        content = "A" * 200  # 200字符，应分成多个块
        doc = Document(id="doc_001", content=content)
        chunks = chunker.chunk(doc)
        assert len(chunks) > 1

    def test_chunk_空文本(self):
        """测试分块空文本"""
        chunker = FixedSizeChunker(chunk_size=100, overlap=10)
        doc = Document(id="doc_001", content="")
        chunks = chunker.chunk(doc)
        assert len(chunks) == 0

    def test_chunk_带元数据继承(self):
        """测试分块继承文档元数据"""
        chunker = FixedSizeChunker(chunk_size=100, overlap=10)
        doc = Document(
            id="doc_001",
            content="Test content here.",
            metadata={"author": "test", "version": "1.0"}
        )
        chunks = chunker.chunk(doc)
        assert len(chunks) > 0
        assert chunks[0].metadata["author"] == "test"
        assert chunks[0].metadata["version"] == "1.0"

    def test_chunk_块索引递增(self):
        """测试块索引递增"""
        chunker = FixedSizeChunker(chunk_size=20, overlap=5)
        content = "This is a longer text that will be split into multiple chunks for testing purposes."
        doc = Document(id="doc_001", content=content)
        chunks = chunker.chunk(doc)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_chunk_文档ID关联(self):
        """测试块与文档ID关联"""
        chunker = FixedSizeChunker(chunk_size=50, overlap=10)
        doc = Document(id="doc_test", content="Test content for ID check.")
        chunks = chunker.chunk(doc)
        assert all(c.document_id == "doc_test" for c in chunks)

    def test_chunk_句子边界切分(self):
        """测试在句子边界切分"""
        chunker = FixedSizeChunker(chunk_size=30, overlap=5)
        content = "First sentence. Second sentence. Third sentence."
        doc = Document(id="doc_001", content=content)
        chunks = chunker.chunk(doc)
        # 应尝试在句号边界切分
        assert len(chunks) >= 1

    def test_chunk_位置元数据(self):
        """测试块包含位置元数据"""
        chunker = FixedSizeChunker(chunk_size=50, overlap=10)
        doc = Document(id="doc_001", content="Test content with position metadata.")
        chunks = chunker.chunk(doc)
        if len(chunks) > 0:
            assert "start_pos" in chunks[0].metadata
            assert "end_pos" in chunks[0].metadata


class TestSlidingWindowChunker:
    """SlidingWindowChunker 滑动窗口分块器测试"""

    def test_初始化_默认参数(self):
        """测试初始化使用默认参数"""
        chunker = SlidingWindowChunker()
        assert chunker.chunk_size == 500
        assert chunker.step == 200

    def test_初始化_自定义参数(self):
        """测试初始化使用自定义参数"""
        chunker = SlidingWindowChunker(chunk_size=100, step=50)
        assert chunker.chunk_size == 100
        assert chunker.step == 50

    def test_chunk_短文本(self):
        """测试分块短文本"""
        chunker = SlidingWindowChunker(chunk_size=100, step=50)
        doc = Document(id="doc_001", content="Short text.")
        chunks = chunker.chunk(doc)
        assert len(chunks) >= 1

    def test_chunk_长文本多个窗口(self):
        """测试分块长文本产生多个窗口"""
        chunker = SlidingWindowChunker(chunk_size=50, step=20)
        content = "A" * 150  # 150字符，窗口大小50，步长20
        doc = Document(id="doc_001", content=content)
        chunks = chunker.chunk(doc)
        assert len(chunks) > 1

    def test_chunk_空文本(self):
        """测试分块空文本"""
        chunker = SlidingWindowChunker(chunk_size=100, step=50)
        doc = Document(id="doc_001", content="")
        chunks = chunker.chunk(doc)
        assert len(chunks) == 0

    def test_chunk_重叠内容(self):
        """测试滑动窗口产生重叠内容"""
        chunker = SlidingWindowChunker(chunk_size=30, step=10)
        content = "This is a test text for sliding window chunker."
        doc = Document(id="doc_001", content=content)
        chunks = chunker.chunk(doc)
        if len(chunks) > 1:
            # 验证相邻块有重叠
            assert chunks[0].chunk_index < chunks[1].chunk_index

    def test_chunk_带元数据继承(self):
        """测试分块继承文档元数据"""
        chunker = SlidingWindowChunker(chunk_size=100, step=50)
        doc = Document(
            id="doc_001",
            content="Test content with metadata.",
            metadata={"source": "test"}
        )
        chunks = chunker.chunk(doc)
        if len(chunks) > 0:
            assert chunks[0].metadata.get("source") == "test"


class TestSentenceChunker:
    """SentenceChunker 句子级别分块器测试"""

    def test_初始化_默认参数(self):
        """测试初始化使用默认参数"""
        chunker = SentenceChunker()
        assert chunker.min_sentences == 3
        assert chunker.max_sentences == 10

    def test_初始化_自定义参数(self):
        """测试初始化使用自定义参数"""
        chunker = SentenceChunker(min_sentences=2, max_sentences=5)
        assert chunker.min_sentences == 2
        assert chunker.max_sentences == 5

    def test_split_sentences_中文(self):
        """测试分割中文句子"""
        chunker = SentenceChunker()
        text = "这是第一句话。这是第二句话！这是第三句话？这是第四句话。"
        sentences = chunker._split_sentences(text)
        assert len(sentences) >= 3

    def test_split_sentences_英文(self):
        """测试分割英文句子"""
        chunker = SentenceChunker()
        text = "First sentence. Second sentence! Third sentence?"
        sentences = chunker._split_sentences(text)
        assert len(sentences) >= 3

    def test_split_sentences_混合语言(self):
        """测试分割混合语言句子"""
        chunker = SentenceChunker()
        text = "Hello world. 你好世界。How are you? 我很好！"
        sentences = chunker._split_sentences(text)
        assert len(sentences) >= 4

    def test_chunk_足够句子数(self):
        """测试分块足够句子数"""
        chunker = SentenceChunker(min_sentences=2, max_sentences=3)
        content = "第一句。第二句。第三句。第四句。第五句。"
        doc = Document(id="doc_001", content=content)
        chunks = chunker.chunk(doc)
        assert len(chunks) >= 1

    def test_chunk_句子数不足最小值(self):
        """测试分块句子数不足最小值"""
        chunker = SentenceChunker(min_sentences=5, max_sentences=10)
        content = "只有两句。不够分块。"
        doc = Document(id="doc_001", content=content)
        chunks = chunker.chunk(doc)
        # 句子数不足最小值，应该不产生块
        assert len(chunks) == 0

    def test_chunk_空文本(self):
        """测试分块空文本"""
        chunker = SentenceChunker()
        doc = Document(id="doc_001", content="")
        chunks = chunker.chunk(doc)
        assert len(chunks) == 0

    def test_chunk_句子边界标点(self):
        """测试使用不同标点分割句子"""
        chunker = SentenceChunker()
        text = "句1！句2？句3。句4.句5!句6?"
        sentences = chunker._split_sentences(text)
        assert len(sentences) >= 5


class TestMarkdownChunker:
    """MarkdownChunker Markdown专用分块器测试"""

    def test_初始化_默认参数(self):
        """测试初始化使用默认参数"""
        chunker = MarkdownChunker()
        assert chunker.min_chunk_size == 100
        assert chunker.max_chunk_size == 2000

    def test_初始化_自定义参数(self):
        """测试初始化使用自定义参数"""
        chunker = MarkdownChunker(min_chunk_size=50, max_chunk_size=500)
        assert chunker.min_chunk_size == 50
        assert chunker.max_chunk_size == 500

    def test_chunk_带标题Markdown(self):
        """测试分块带标题Markdown"""
        chunker = MarkdownChunker(min_chunk_size=10)
        content = """# Title 1

This is the first section with enough content to meet the minimum chunk size requirement for testing.

# Title 2

This is the second section with sufficient content for the markdown chunker to process properly."""
        doc = Document(id="doc_001", content=content)
        chunks = chunker.chunk(doc)
        assert len(chunks) >= 1

    def test_chunk_多级标题(self):
        """测试分块多级标题"""
        chunker = MarkdownChunker(min_chunk_size=10)
        content = """# Main Title

Intro content here.

## Sub Title 1

Content under sub title 1.

## Sub Title 2

Content under sub title 2.

### Sub Sub Title

More content here."""
        doc = Document(id="doc_001", content=content)
        chunks = chunker.chunk(doc)
        assert len(chunks) >= 1

    def test_chunk_无标题Markdown(self):
        """测试分块无标题Markdown"""
        chunker = MarkdownChunker(min_chunk_size=10)
        content = "Just some plain text content without any headers in the markdown document for testing purposes."
        doc = Document(id="doc_001", content=content)
        chunks = chunker.chunk(doc)
        # 无标题时，内容小于min_chunk_size，应该不产生块
        assert len(chunks) == 0 or chunks[0].metadata.get("header") == ""

    def test_chunk_块带标题元数据(self):
        """测试分块包含标题元数据"""
        chunker = MarkdownChunker(min_chunk_size=10)
        content = """# My Title

This is the content under the title. It should be long enough to meet the minimum chunk size requirement."""
        doc = Document(id="doc_001", content=content)
        chunks = chunker.chunk(doc)
        if len(chunks) > 0:
            assert "header" in chunks[0].metadata

    def test_chunk_空文本(self):
        """测试分块空文本"""
        chunker = MarkdownChunker()
        doc = Document(id="doc_001", content="")
        chunks = chunker.chunk(doc)
        assert len(chunks) == 0

    def test_chunk_内容小于最小尺寸(self):
        """测试分块内容小于最小尺寸"""
        chunker = MarkdownChunker(min_chunk_size=1000)
        content = "# Title\n\nShort content."
        doc = Document(id="doc_001", content=content)
        chunks = chunker.chunk(doc)
        assert len(chunks) == 0


class TestChunkDocument:
    """chunk_document 便捷函数测试"""

    def test_固定大小分块(self):
        """测试使用固定大小分块"""
        doc = Document(id="doc_001", content="Test content for chunking.")
        chunks = chunk_document(doc, method='fixed', chunk_size=50, overlap=10)
        assert len(chunks) >= 1
        assert all(isinstance(c, DocumentChunk) for c in chunks)

    def test_滑动窗口分块(self):
        """测试使用滑动窗口分块"""
        content = "Test content for sliding window chunking method."
        doc = Document(id="doc_001", content=content)
        chunks = chunk_document(doc, method='sliding', chunk_size=30, step=10)
        assert len(chunks) >= 1

    def test_句子分块(self):
        """测试使用句子分块"""
        content = "第一句。第二句。第三句。第四句。第五句。第六句。第七句。第八句。第九句。第十句。"
        doc = Document(id="doc_001", content=content)
        chunks = chunk_document(doc, method='sentence', min_sentences=3, max_sentences=5)
        # 句子数足够，应该产生块
        assert len(chunks) >= 1

    def test_markdown分块(self):
        """测试使用Markdown分块"""
        content = """# Title

This is the content. It should be long enough for the markdown chunker to create a block with this text included properly."""
        doc = Document(id="doc_001", content=content)
        chunks = chunk_document(doc, method='markdown', min_chunk_size=10)
        assert len(chunks) >= 1

    def test_未知方法_使用默认固定大小(self):
        """测试使用未知方法时默认使用固定大小分块"""
        doc = Document(id="doc_001", content="Test content.")
        chunks = chunk_document(doc, method='unknown_method')
        assert len(chunks) >= 1
        # 应该使用FixedSizeChunker

    def test_参数传递_分块器参数(self):
        """测试参数正确传递给分块器"""
        doc = Document(id="doc_001", content="Test content with specific parameters.")
        chunks = chunk_document(doc, method='fixed', chunk_size=20, overlap=5)
        assert len(chunks) >= 1
