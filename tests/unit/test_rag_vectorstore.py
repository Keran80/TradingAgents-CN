# -*- coding: utf-8 -*-
"""
RAG VectorStore 模块单元测试

测试范围：
- VectorStore 基类
- InMemoryVectorStore 内存向量存储
- FaissVectorStore FAISS向量存储（mock）
- get_vector_store 便捷函数
- create_vector_store 便捷函数
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
    from tradingagents.rag.vectorstore import (
        VectorStore,
        InMemoryVectorStore,
        FaissVectorStore,
        get_vector_store,
        create_vector_store,
    )
    from tradingagents.rag.base import DocumentChunk, RetrievalResult
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装（tradingagents）", allow_module_level=True)


class TestVectorStore:
    """VectorStore 基类测试"""

    def test_add_chunks_未实现异常(self):
        """测试add_chunks方法未实现时抛出异常"""
        store = VectorStore()
        with pytest.raises(NotImplementedError):
            store.add_chunks([], [])

    def test_search_未实现异常(self):
        """测试search方法未实现时抛出异常"""
        store = VectorStore()
        with pytest.raises(NotImplementedError):
            store.search(np.array([0.1] * 128))

    def test_save_未实现异常(self):
        """测试save方法未实现时抛出异常"""
        store = VectorStore()
        with pytest.raises(NotImplementedError):
            store.save("/tmp/test")

    def test_load_未实现异常(self):
        """测试load方法未实现时抛出异常"""
        store = VectorStore()
        with pytest.raises(NotImplementedError):
            store.load("/tmp/test")


class TestInMemoryVectorStore:
    """InMemoryVectorStore 内存向量存储测试"""

    def test_初始化_默认维度(self):
        """测试初始化使用默认维度"""
        store = InMemoryVectorStore()
        assert store.dimension == 768
        assert store.chunks == []
        assert store.embeddings == []

    def test_初始化_自定义维度(self):
        """测试初始化使用自定义维度"""
        store = InMemoryVectorStore(dimension=512)
        assert store.dimension == 512

    def test_add_chunks_添加数据(self):
        """测试添加文档块和向量"""
        store = InMemoryVectorStore(dimension=128)
        chunks = [
            DocumentChunk(id="c1", content="text 1", document_id="d1", chunk_index=0),
            DocumentChunk(id="c2", content="text 2", document_id="d1", chunk_index=1),
        ]
        embeddings = [np.random.randn(128) for _ in range(2)]

        store.add_chunks(chunks, embeddings)
        assert len(store.chunks) == 2
        assert len(store.embeddings) == 2

    def test_add_chunks_空列表(self):
        """测试添加空列表"""
        store = InMemoryVectorStore(dimension=128)
        store.add_chunks([], [])
        assert len(store.chunks) == 0
        assert len(store.embeddings) == 0

    def test_add_chunks_多次添加(self):
        """测试多次添加数据"""
        store = InMemoryVectorStore(dimension=128)
        chunk1 = [DocumentChunk(id="c1", content="text 1", document_id="d1", chunk_index=0)]
        emb1 = [np.random.randn(128)]
        store.add_chunks(chunk1, emb1)

        chunk2 = [DocumentChunk(id="c2", content="text 2", document_id="d1", chunk_index=1)]
        emb2 = [np.random.randn(128)]
        store.add_chunks(chunk2, emb2)

        assert len(store.chunks) == 2
        assert len(store.embeddings) == 2

    def test_search_空存储(self):
        """测试搜索空存储返回空列表"""
        store = InMemoryVectorStore(dimension=128)
        query = np.random.randn(128)
        results = store.search(query, top_k=5)
        assert results == []

    def test_search_单文档返回正确(self):
        """测试搜索单个文档返回正确结果"""
        store = InMemoryVectorStore(dimension=128)
        chunk = DocumentChunk(id="c1", content="test content", document_id="d1", chunk_index=0)
        embedding = np.random.randn(128)
        store.add_chunks([chunk], [embedding])

        results = store.search(embedding, top_k=1)
        assert len(results) == 1
        assert results[0].chunk.id == "c1"
        assert results[0].rank == 1

    def test_search_返回正确数量(self):
        """测试搜索返回正确数量"""
        store = InMemoryVectorStore(dimension=128)
        chunks = [
            DocumentChunk(id=f"c{i}", content=f"text {i}", document_id="d1", chunk_index=i)
            for i in range(5)
        ]
        embeddings = [np.random.randn(128) for _ in range(5)]
        store.add_chunks(chunks, embeddings)

        query = np.random.randn(128)
        results = store.search(query, top_k=3)
        assert len(results) == 3

    def test_search_top_k_大于总数(self):
        """测试top_k大于总数时返回所有结果"""
        store = InMemoryVectorStore(dimension=128)
        chunks = [
            DocumentChunk(id=f"c{i}", content=f"text {i}", document_id="d1", chunk_index=i)
            for i in range(3)
        ]
        embeddings = [np.random.randn(128) for _ in range(3)]
        store.add_chunks(chunks, embeddings)

        query = np.random.randn(128)
        results = store.search(query, top_k=10)
        assert len(results) == 3

    def test_search_分数范围(self):
        """测试搜索分数在合理范围内"""
        store = InMemoryVectorStore(dimension=128)
        chunk = DocumentChunk(id="c1", content="test", document_id="d1", chunk_index=0)
        embedding = np.random.randn(128)
        store.add_chunks([chunk], [embedding])

        results = store.search(embedding, top_k=1)
        # 余弦相似度应在[-1, 1]范围内
        assert -1.0 <= results[0].score <= 1.0

    def test_save_保存文件(self, tmp_path):
        """测试保存向量存储"""
        store = InMemoryVectorStore(dimension=128)
        chunk = DocumentChunk(id="c1", content="test", document_id="d1", chunk_index=0)
        embedding = np.random.randn(128)
        store.add_chunks([chunk], [embedding])

        save_path = str(tmp_path / "vectorstore")
        store.save(save_path)
        assert os.path.exists(os.path.join(save_path, "vectorstore.pkl"))

    def test_load_加载数据(self, tmp_path):
        """测试加载向量存储"""
        store = InMemoryVectorStore(dimension=128)
        chunk = DocumentChunk(id="c1", content="test", document_id="d1", chunk_index=0)
        embedding = np.random.randn(128)
        store.add_chunks([chunk], [embedding])

        save_path = str(tmp_path / "vectorstore")
        store.save(save_path)

        # 创建新实例并加载
        store2 = InMemoryVectorStore(dimension=128)
        store2.load(save_path)
        assert len(store2.chunks) == 1
        assert store2.chunks[0].id == "c1"
        assert store2.dimension == 128

    def test_search_余弦相似度正确性(self):
        """测试余弦相似度计算正确性"""
        store = InMemoryVectorStore(dimension=4)
        # 创建两个相同的向量
        vec = np.array([1.0, 0.0, 0.0, 0.0])
        chunk1 = DocumentChunk(id="c1", content="similar", document_id="d1", chunk_index=0)
        chunk2 = DocumentChunk(id="c2", content="different", document_id="d1", chunk_index=1)
        vec2 = np.array([0.0, 1.0, 0.0, 0.0])
        store.add_chunks([chunk1, chunk2], [vec, vec2])

        # 查询与chunk1相同的向量
        results = store.search(vec, top_k=2)
        assert len(results) == 2
        # 最相似的应该是chunk1
        assert results[0].chunk.id == "c1"


class TestFaissVectorStore:
    """FaissVectorStore FAISS向量存储测试"""

    def test_初始化_faiss不可用抛出异常(self):
        """测试FAISS不可用时抛出异常"""
        with patch.dict('sys.modules', {'faiss': None}):
            with pytest.raises(ImportError) as exc_info:
                FaissVectorStore(dimension=128)
            assert "faiss" in str(exc_info.value)

    @patch('tradingagents.rag.vectorstore.faiss')
    def test_初始化_Flat索引(self, mock_faiss):
        """测试初始化Flat索引"""
        mock_index = Mock()
        mock_faiss.IndexFlatL2.return_value = mock_index

        store = FaissVectorStore(dimension=128, index_type="Flat")
        assert store.dimension == 128
        assert store.index_type == "Flat"
        mock_faiss.IndexFlatL2.assert_called_once_with(128)

    @patch('tradingagents.rag.vectorstore.faiss')
    def test_初始化_IVF索引(self, mock_faiss):
        """测试初始化IVF索引"""
        mock_index = Mock()
        mock_faiss.IndexIVFFlat.return_value = mock_index

        store = FaissVectorStore(dimension=128, index_type="IVF")
        assert store.index_type == "IVF"
        mock_faiss.IndexIVFFlat.assert_called_once()

    @patch('tradingagents.rag.vectorstore.faiss')
    def test_初始化_HNSW索引(self, mock_faiss):
        """测试初始化HNSW索引"""
        mock_index = Mock()
        mock_faiss.IndexHNSWFlat.return_value = mock_index

        store = FaissVectorStore(dimension=128, index_type="HNSW")
        assert store.index_type == "HNSW"
        mock_faiss.IndexHNSWFlat.assert_called_once()

    @patch('tradingagents.rag.vectorstore.faiss')
    def test_初始化_未知类型使用默认_Flat(self, mock_faiss):
        """测试初始化未知类型时使用默认Flat"""
        mock_index = Mock()
        mock_faiss.IndexFlatL2.return_value = mock_index

        store = FaissVectorStore(dimension=128, index_type="Unknown")
        mock_faiss.IndexFlatL2.assert_called_once_with(128)

    @patch('tradingagents.rag.vectorstore.faiss')
    def test_add_chunks_添加数据(self, mock_faiss):
        """测试添加文档块"""
        mock_index = Mock()
        mock_index.ntotal = 0
        mock_faiss.IndexFlatL2.return_value = mock_index

        store = FaissVectorStore(dimension=128, index_type="Flat")
        chunks = [
            DocumentChunk(id="c1", content="text 1", document_id="d1", chunk_index=0),
        ]
        embeddings = [np.random.randn(128).astype('float32')]

        store.add_chunks(chunks, embeddings)
        mock_index.add.assert_called_once()
        assert len(store.chunks) == 1

    @patch('tradingagents.rag.vectorstore.faiss')
    def test_add_chunks_空列表(self, mock_faiss):
        """测试添加空列表"""
        mock_index = Mock()
        mock_faiss.IndexFlatL2.return_value = mock_index

        store = FaissVectorStore(dimension=128, index_type="Flat")
        store.add_chunks([], [])
        mock_index.add.assert_not_called()

    @patch('tradingagents.rag.vectorstore.faiss')
    def test_add_chunks_维度不匹配抛出异常(self, mock_faiss):
        """测试维度不匹配时抛出异常"""
        mock_index = Mock()
        mock_faiss.IndexFlatL2.return_value = mock_index

        store = FaissVectorStore(dimension=128, index_type="Flat")
        chunks = [DocumentChunk(id="c1", content="text", document_id="d1", chunk_index=0)]
        embeddings = [np.random.randn(256)]  # 维度不匹配

        with pytest.raises(ValueError) as exc_info:
            store.add_chunks(chunks, embeddings)
        assert "维度不匹配" in str(exc_info.value)

    @patch('tradingagents.rag.vectorstore.faiss')
    def test_add_chunks_IVF索引训练(self, mock_faiss):
        """测试IVF索引训练"""
        mock_index = Mock()
        mock_index.is_trained = False
        mock_index.ntotal = 0
        mock_faiss.IndexIVFFlat.return_value = mock_index

        store = FaissVectorStore(dimension=128, index_type="IVF")
        chunks = [DocumentChunk(id="c1", content="text", document_id="d1", chunk_index=0)]
        embeddings = [np.random.randn(128).astype('float32')]

        store.add_chunks(chunks, embeddings)
        mock_index.train.assert_called_once()
        mock_index.add.assert_called_once()

    @patch('tradingagents.rag.vectorstore.faiss')
    def test_search_空索引返回空列表(self, mock_faiss):
        """测试搜索空索引返回空列表"""
        mock_index = Mock()
        mock_index.ntotal = 0
        mock_faiss.IndexFlatL2.return_value = mock_index

        store = FaissVectorStore(dimension=128, index_type="Flat")
        query = np.random.randn(128)
        results = store.search(query, top_k=5)
        assert results == []

    @patch('tradingagents.rag.vectorstore.faiss')
    def test_search_返回正确数量(self, mock_faiss):
        """测试搜索返回正确数量"""
        mock_index = Mock()
        mock_index.ntotal = 5
        mock_index.search.return_value = (
            np.array([[0.1, 0.2, 0.3]]),
            np.array([[0, 1, 2]])
        )
        mock_faiss.IndexFlatL2.return_value = mock_index

        store = FaissVectorStore(dimension=128, index_type="Flat")
        store.chunks = [
            DocumentChunk(id=f"c{i}", content=f"text {i}", document_id="d1", chunk_index=i)
            for i in range(5)
        ]

        query = np.random.randn(128)
        results = store.search(query, top_k=3)
        assert len(results) == 3

    @patch('tradingagents.rag.vectorstore.faiss')
    def test_search_分数转换正确(self, mock_faiss):
        """测试分数转换正确（L2距离转相似度）"""
        mock_index = Mock()
        mock_index.ntotal = 1
        mock_index.search.return_value = (
            np.array([[0.5]]),  # L2距离
            np.array([[0]])
        )
        mock_faiss.IndexFlatL2.return_value = mock_index

        store = FaissVectorStore(dimension=128, index_type="Flat")
        store.chunks = [DocumentChunk(id="c1", content="text", document_id="d1", chunk_index=0)]

        query = np.random.randn(128)
        results = store.search(query, top_k=1)
        # score = 1.0 / (1.0 + dist) = 1.0 / 1.5 = 0.666...
        expected_score = 1.0 / (1.0 + 0.5)
        assert abs(results[0].score - expected_score) < 0.001

    @patch('tradingagents.rag.vectorstore.faiss')
    def test_search_查询维度不匹配抛出异常(self, mock_faiss):
        """测试查询向量维度不匹配时抛出异常"""
        mock_index = Mock()
        mock_index.ntotal = 1
        mock_faiss.IndexFlatL2.return_value = mock_index

        store = FaissVectorStore(dimension=128, index_type="Flat")
        store.chunks = [DocumentChunk(id="c1", content="text", document_id="d1", chunk_index=0)]

        query = np.random.randn(256)  # 维度不匹配
        with pytest.raises(ValueError) as exc_info:
            store.search(query, top_k=5)
        assert "维度不匹配" in str(exc_info.value)

    @patch('tradingagents.rag.vectorstore.faiss')
    def test_save_保存文件(self, mock_faiss, tmp_path):
        """测试保存向量存储"""
        mock_index = Mock()
        mock_faiss.IndexFlatL2.return_value = mock_index

        store = FaissVectorStore(dimension=128, index_type="Flat")
        save_path = str(tmp_path / "vectorstore")
        store.save(save_path)

        assert os.path.exists(os.path.join(save_path, "index.faiss"))
        assert os.path.exists(os.path.join(save_path, "chunks.pkl"))
        assert os.path.exists(os.path.join(save_path, "config.pkl"))

        mock_faiss.write_index.assert_called_once()

    @patch('tradingagents.rag.vectorstore.faiss')
    def test_load_加载数据(self, mock_faiss, tmp_path):
        """测试加载向量存储"""
        mock_index = Mock()
        mock_faiss.IndexFlatL2.return_value = mock_index

        store = FaissVectorStore(dimension=128, index_type="Flat")
        save_path = str(tmp_path / "vectorstore")

        # 模拟保存
        os.makedirs(save_path)
        mock_faiss.write_index = Mock()
        store.save(save_path)

        # 模拟加载
        mock_loaded_index = Mock()
        mock_faiss.read_index.return_value = mock_loaded_index

        # 写入测试数据
        import pickle
        with open(os.path.join(save_path, "chunks.pkl"), 'wb') as f:
            pickle.dump([DocumentChunk(id="c1", content="test", document_id="d1", chunk_index=0)], f)
        with open(os.path.join(save_path, "config.pkl"), 'wb') as f:
            pickle.dump({'dimension': 128, 'index_type': 'Flat'}, f)

        store2 = FaissVectorStore(dimension=128, index_type="Flat")
        store2.load(save_path)
        assert len(store2.chunks) == 1
        assert store2.dimension == 128


class TestGetVectorStore:
    """get_vector_store 便捷函数测试"""

    def setup_method(self):
        """设置测试环境"""
        import tradingagents.rag.vectorstore as vs_module
        vs_module._vector_store = None

    def test_获取_inmemory存储(self):
        """测试获取内存向量存储"""
        store = get_vector_store(dimension=128, use_faiss=False)
        assert isinstance(store, InMemoryVectorStore)
        assert store.dimension == 128

    def test_获取_单例模式(self):
        """测试单例模式"""
        import tradingagents.rag.vectorstore as vs_module
        vs_module._vector_store = None

        store1 = get_vector_store(use_faiss=False)
        store2 = get_vector_store(use_faiss=False)
        assert store1 is store2

    @patch.dict('sys.modules', {'faiss': None})
    def test_faiss不可用_回退到_inmemory(self):
        """测试FAISS不可用时回退到内存存储"""
        import tradingagents.rag.vectorstore as vs_module
        vs_module._vector_store = None

        store = get_vector_store(use_faiss=True)
        assert isinstance(store, InMemoryVectorStore)


class TestCreateVectorStore:
    """create_vector_store 便捷函数测试"""

    def test_创建_inmemory存储(self):
        """测试创建内存向量存储"""
        store = create_vector_store(dimension=256, use_faiss=False)
        assert isinstance(store, InMemoryVectorStore)
        assert store.dimension == 256

    @patch.dict('sys.modules', {'faiss': None})
    def test_faiss不可用_创建_inmemory(self):
        """测试FAISS不可用时创建内存存储"""
        store = create_vector_store(dimension=128, use_faiss=True)
        assert isinstance(store, InMemoryVectorStore)
