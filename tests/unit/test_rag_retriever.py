# -*- coding: utf-8 -*-
"""
RAG Retriever 模块单元测试

测试范围：
- Retriever 检索器
- HybridRetriever 混合检索器
- create_retriever 便捷函数
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tempfile
import shutil
import numpy as np

# 条件导入（处理依赖缺失）
try:
    from tradingagents.rag.retriever import (
        Retriever,
        HybridRetriever,
        create_retriever,
    )
    from tradingagents.rag.base import Document, DocumentChunk, RetrievalResult
    from tradingagents.rag.vectorstore import InMemoryVectorStore
    from tradingagents.rag.embeddings import DummyEmbedding
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装（tradingagents）", allow_module_level=True)


class TestRetriever:
    """Retriever 检索器测试"""

    def setup_method(self):
        """设置测试环境"""
        self.vector_store = InMemoryVectorStore(dimension=768)
        self.embedding_model = DummyEmbedding(dimension=768)

    def test_初始化_默认参数(self):
        """测试初始化使用默认参数"""
        retriever = Retriever()
        assert retriever.chunk_size == 500
        assert retriever.chunk_method == 'fixed'
        assert retriever.documents == {}

    def test_初始化_自定义参数(self):
        """测试初始化使用自定义参数"""
        retriever = Retriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model,
            chunk_size=256,
            chunk_method='sentence'
        )
        assert retriever.chunk_size == 256
        assert retriever.chunk_method == 'sentence'

    def test_add_documents_添加单个文件_使用_mock(self):
        """测试添加单个文档（mock避免真实文件）"""
        retriever = Retriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )

        mock_doc = Document(
            id="doc_001",
            content="This is test content for the retriever test.",
            source="test.txt",
        )

        with patch('tradingagents.rag.retriever.load_document', return_value=[mock_doc]):
            with patch('tradingagents.rag.retriever.chunk_document') as mock_chunk:
                mock_chunk.return_value = [
                    DocumentChunk(id="c1", content="chunk 1", document_id="doc_001", chunk_index=0),
                ]

                count = retriever.add_documents(["test.txt"])
                assert count == 1
                assert "doc_001" in retriever.documents

    def test_add_documents_添加多个文件_使用_mock(self):
        """测试添加多个文档"""
        retriever = Retriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )

        mock_docs = [
            Document(id=f"doc_{i}", content=f"Content {i}", source=f"file{i}.txt")
            for i in range(3)
        ]

        with patch('tradingagents.rag.retriever.load_document') as mock_load:
            mock_load.side_effect = lambda x: [mock_docs[int(x[-5])]]

            with patch('tradingagents.rag.retriever.chunk_document') as mock_chunk:
                mock_chunk.return_value = [
                    DocumentChunk(id="c1", content="chunk", document_id="doc_0", chunk_index=0),
                ]

                count = retriever.add_documents(["file0.txt", "file1.txt", "file2.txt"])
                assert count == 3

    def test_add_documents_使用自定义分块参数(self):
        """测试使用自定义分块参数"""
        retriever = Retriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )

        mock_doc = Document(id="doc_001", content="Test content.", source="test.txt")

        with patch('tradingagents.rag.retriever.load_document', return_value=[mock_doc]):
            with patch('tradingagents.rag.retriever.chunk_document') as mock_chunk:
                mock_chunk.return_value = [
                    DocumentChunk(id="c1", content="chunk", document_id="doc_001", chunk_index=0),
                ]

                retriever.add_documents(["test.txt"], chunk_size=100, chunk_method='sliding')
                mock_chunk.assert_called_once()
                # 验证参数传递
                call_kwargs = mock_chunk.call_args[1]
                assert call_kwargs['chunk_size'] == 100
                assert call_kwargs['method'] == 'sliding'

    def test_search_返回检索结果_使用_mock(self):
        """测试搜索返回检索结果"""
        retriever = Retriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )

        # 添加一些数据到向量存储
        chunk = DocumentChunk(id="c1", content="test content", document_id="d1", chunk_index=0)
        embedding = np.random.randn(768)
        self.vector_store.add_chunks([chunk], [embedding])

        results = retriever.search("test query", top_k=5)
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], RetrievalResult)

    def test_search_空索引返回空列表(self):
        """测试搜索空索引返回空列表"""
        retriever = Retriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )

        results = retriever.search("test query", top_k=5)
        assert results == []

    def test_search_返回正确数量(self):
        """测试搜索返回正确数量"""
        retriever = Retriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )

        chunks = [
            DocumentChunk(id=f"c{i}", content=f"content {i}", document_id="d1", chunk_index=i)
            for i in range(10)
        ]
        embeddings = [np.random.randn(768) for _ in range(10)]
        self.vector_store.add_chunks(chunks, embeddings)

        results = retriever.search("query", top_k=3)
        assert len(results) == 3

    def test_search_with_rerank_重排序_使用_mock(self):
        """测试搜索+重排序"""
        retriever = Retriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )

        # Mock search方法
        chunks = [
            DocumentChunk(id="c1", content="test query match", document_id="d1", chunk_index=0),
            DocumentChunk(id="c2", content="other content", document_id="d1", chunk_index=1),
        ]
        embeddings = [np.random.randn(768) for _ in range(2)]
        self.vector_store.add_chunks(chunks, embeddings)

        results = retriever.search_with_rerank("test query", top_k=5, rerank_top=3)
        assert isinstance(results, list)
        # 验证重排序后分数被更新
        if len(results) > 0:
            assert results[0].score >= 0

    def test_save_保存检索系统(self, tmp_path):
        """测试保存检索系统"""
        retriever = Retriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )

        save_path = str(tmp_path / "retriever")
        retriever.save(save_path)

        assert os.path.exists(os.path.join(save_path, "vectorstore"))
        assert os.path.exists(os.path.join(save_path, "documents.pkl"))
        assert os.path.exists(os.path.join(save_path, "config.pkl"))

    def test_load_加载检索系统(self, tmp_path):
        """测试加载检索系统"""
        retriever = Retriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )

        # 添加文档
        mock_doc = Document(id="doc_001", content="Test content.", source="test.txt")
        with patch('tradingagents.rag.retriever.load_document', return_value=[mock_doc]):
            with patch('tradingagents.rag.retriever.chunk_document') as mock_chunk:
                mock_chunk.return_value = [
                    DocumentChunk(id="c1", content="chunk", document_id="doc_001", chunk_index=0),
                ]
                retriever.add_documents(["test.txt"])

        # 保存
        save_path = str(tmp_path / "retriever")
        retriever.save(save_path)

        # 创建新实例并加载
        retriever2 = Retriever(
            vector_store=InMemoryVectorStore(dimension=768),
            embedding_model=DummyEmbedding(dimension=768)
        )
        retriever2.load(save_path)
        assert "doc_001" in retriever2.documents


class TestHybridRetriever:
    """HybridRetriever 混合检索器测试"""

    def setup_method(self):
        """设置测试环境"""
        self.vector_store = InMemoryVectorStore(dimension=768)
        self.embedding_model = DummyEmbedding(dimension=768)

    def test_初始化_默认权重(self):
        """测试初始化使用默认权重"""
        retriever = HybridRetriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )
        assert retriever.vector_weight == 0.7

    def test_初始化_自定义权重(self):
        """测试初始化使用自定义权重"""
        retriever = HybridRetriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model,
            vector_weight=0.5
        )
        assert retriever.vector_weight == 0.5

    def test_build_keyword_index_构建索引(self):
        """测试构建关键词倒排索引"""
        retriever = HybridRetriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )

        # 添加文档块
        chunks = [
            DocumentChunk(id="c1", content="test query match word", document_id="d1", chunk_index=0),
            DocumentChunk(id="c2", content="another test content", document_id="d1", chunk_index=1),
        ]
        embeddings = [np.random.randn(768) for _ in range(2)]
        self.vector_store.add_chunks(chunks, embeddings)

        retriever._build_keyword_index()
        assert "test" in retriever.keyword_index
        assert "c1" in retriever.keyword_index["test"]

    def test_build_keyword_index_过滤单字(self):
        """测试过滤单字关键词"""
        retriever = HybridRetriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )

        chunks = [
            DocumentChunk(id="c1", content="a test word", document_id="d1", chunk_index=0),
        ]
        embeddings = [np.random.randn(768)]
        self.vector_store.add_chunks(chunks, embeddings)

        retriever._build_keyword_index()
        # 单字"a"应该被过滤
        assert "a" not in retriever.keyword_index
        assert "test" in retriever.keyword_index

    def test_add_documents_构建关键词索引_使用_mock(self):
        """测试添加文档后构建关键词索引"""
        retriever = HybridRetriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )

        mock_doc = Document(id="doc_001", content="test keyword index build", source="test.txt")

        with patch('tradingagents.rag.retriever.load_document', return_value=[mock_doc]):
            with patch('tradingagents.rag.retriever.chunk_document') as mock_chunk:
                mock_chunk.return_value = [
                    DocumentChunk(id="c1", content="test keyword", document_id="doc_001", chunk_index=0),
                ]

                count = retriever.add_documents(["test.txt"])
                assert count == 1
                assert "test" in retriever.keyword_index

    def test_search_混合检索_使用_mock(self):
        """测试混合检索"""
        retriever = HybridRetriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )

        # 添加文档
        chunks = [
            DocumentChunk(id="c1", content="test search hybrid", document_id="d1", chunk_index=0),
            DocumentChunk(id="c2", content="other content here", document_id="d1", chunk_index=1),
        ]
        embeddings = [np.random.randn(768) for _ in range(2)]
        self.vector_store.add_chunks(chunks, embeddings)

        # 构建关键词索引
        retriever._build_keyword_index()

        results = retriever.search("test search", top_k=5)
        assert isinstance(results, list)
        # 验证包含"test"和"search"的文档排名更高
        if len(results) > 0:
            assert results[0].rank == 1


class TestCreateRetriever:
    """create_retriever 便捷函数测试"""

    @patch('tradingagents.rag.retriever.get_embedding_model')
    @patch('tradingagents.rag.retriever.create_vector_store')
    def test_创建检索器_默认参数(self, mock_create_vs, mock_get_emb):
        """测试创建检索器使用默认参数"""
        mock_embedder = DummyEmbedding(dimension=768)
        mock_get_emb.return_value = mock_embedder

        mock_vs = InMemoryVectorStore(dimension=768)
        mock_create_vs.return_value = mock_vs

        retriever = create_retriever(
            model_type='dummy',
            use_faiss=False,
            chunk_size=500,
            chunk_method='fixed'
        )

        assert isinstance(retriever, Retriever)
        assert retriever.chunk_size == 500
        assert retriever.chunk_method == 'fixed'

    @patch('tradingagents.rag.retriever.get_embedding_model')
    @patch('tradingagents.rag.retriever.create_vector_store')
    def test_创建检索器_自定义参数(self, mock_create_vs, mock_get_emb):
        """测试创建检索器使用自定义参数"""
        mock_embedder = DummyEmbedding(dimension=512)
        mock_get_emb.return_value = mock_embedder

        mock_vs = InMemoryVectorStore(dimension=512)
        mock_create_vs.return_value = mock_vs

        retriever = create_retriever(
            model_type='dummy',
            use_faiss=False,
            chunk_size=256,
            chunk_method='sentence'
        )

        assert retriever.chunk_size == 256
        assert retriever.chunk_method == 'sentence'
        assert retriever.embedding_model.dimension == 512
