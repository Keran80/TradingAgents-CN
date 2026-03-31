"""
向量存储模块 - FAISS 实现
支持向量索引构建、相似度搜索、持久化
"""
from typing import List, Optional, Tuple
import os
import pickle
import numpy as np

from ..base import DocumentChunk, RetrievalResult


class VectorStore:
    """向量存储基类"""
    
    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[np.ndarray]) -> None:
        """添加文档块和对应的向量"""
        raise NotImplementedError
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[RetrievalResult]:
        """搜索相似文档"""
        raise NotImplementedError
    
    def save(self, path: str) -> None:
        """保存向量存储"""
        raise NotImplementedError
    
    def load(self, path: str) -> None:
        """加载向量存储"""
        raise NotImplementedError


class FaissVectorStore(VectorStore):
    """FAISS 向量存储实现"""
    
    def __init__(self, dimension: int = 768, index_type: str = "IVF"):
        """
        初始化 FAISS 向量存储
        
        Args:
            dimension: 向量维度
            index_type: 索引类型 ('Flat', 'IVF', 'HNSW')
        """
        self.dimension = dimension
        self.index_type = index_type
        self.chunks: List[DocumentChunk] = []
        self.index = None
        self._init_index()
    
    def _init_index(self):
        """初始化 FAISS 索引"""
        try:
            import faiss
        except ImportError:
            raise ImportError("请安装 faiss: pip install faiss-cpu 或 faiss-gpu")
        
        if self.index_type == "Flat":
            self.index = faiss.IndexFlatL2(self.dimension)
        
        elif self.index_type == "IVF":
            # IVF 索引，需要先训练
            quantizer = faiss.IndexFlatL2(self.dimension)
            nlist = 100  # 聚类数量
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
        
        elif self.index_type == "HNSW":
            # HNSW 索引
            self.index = faiss.IndexHNSWFlat(self.dimension, 32)
        
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
    
    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[np.ndarray]) -> None:
        """添加文档块和向量"""
        if not chunks or not embeddings:
            return
        
        # 确保向量维度匹配
        embeddings_array = np.array(embeddings).astype('float32')
        
        if embeddings_array.shape[1] != self.dimension:
            raise ValueError(f"向量维度不匹配: 期望 {self.dimension}, 实际 {embeddings_array.shape[1]}")
        
        # 添加到索引
        if self.index_type == "IVF" and not self.index.is_trained:
            print("训练 IVF 索引...")
            self.index.train(embeddings_array)
        
        self.index.add(embeddings_array)
        self.chunks.extend(chunks)
        
        print(f"已添加 {len(chunks)} 个文档块到向量索引")
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[RetrievalResult]:
        """搜索相似文档"""
        if self.index is None or self.index.ntotal == 0:
            return []
        
        # 确保查询向量维度正确
        query_vector = np.array([query_embedding]).astype('float32')
        
        if query_vector.shape[1] != self.dimension:
            raise ValueError(f"查询向量维度不匹配: 期望 {self.dimension}, 实际 {query_vector.shape[1]}")
        
        # 搜索
        distances, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))
        
        # 构建结果
        results = []
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx >= 0 and idx < len(self.chunks):
                # 转换距离为相似度分数 (L2 距离越小越相似)
                score = 1.0 / (1.0 + dist)
                
                result = RetrievalResult(
                    chunk=self.chunks[idx],
                    score=score,
                    rank=rank + 1
                )
                results.append(result)
        
        return results
    
    def save(self, path: str) -> None:
        """保存向量存储"""
        os.makedirs(path, exist_ok=True)
        
        # 保存 FAISS 索引
        import faiss
        faiss.write_index(self.index, os.path.join(path, "index.faiss"))
        
        # 保存文档块
        with open(os.path.join(path, "chunks.pkl"), 'wb') as f:
            pickle.dump(self.chunks, f)
        
        # 保存配置
        config = {
            'dimension': self.dimension,
            'index_type': self.index_type
        }
        with open(os.path.join(path, "config.pkl"), 'wb') as f:
            pickle.dump(config, f)
        
        print(f"向量存储已保存到: {path}")
    
    def load(self, path: str) -> None:
        """加载向量存储"""
        import faiss
        
        # 加载配置
        with open(os.path.join(path, "config.pkl"), 'rb') as f:
            config = pickle.load(f)
        self.dimension = config['dimension']
        self.index_type = config['index_type']
        
        # 加载 FAISS 索引
        self.index = faiss.read_index(os.path.join(path, "index.faiss"))
        
        # 加载文档块
        with open(os.path.join(path, "chunks.pkl"), 'rb') as f:
            self.chunks = pickle.load(f)
        
        print(f"向量存储已加载: {len(self.chunks)} 个文档块")


class InMemoryVectorStore(VectorStore):
    """内存向量存储（简单实现，无需 FAISS）"""
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.chunks: List[DocumentChunk] = []
        self.embeddings: List[np.ndarray] = []
    
    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[np.ndarray]) -> None:
        """添加文档块和向量"""
        self.chunks.extend(chunks)
        self.embeddings.extend(embeddings)
        print(f"已添加 {len(chunks)} 个文档块到内存向量存储")
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[RetrievalResult]:
        """使用余弦相似度搜索"""
        if not self.embeddings:
            return []
        
        query = np.array(query_embedding).reshape(1, -1)
        embeddings_matrix = np.array(self.embeddings)
        
        # 计算余弦相似度
        norms = np.linalg.norm(embeddings_matrix, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        normalized = embeddings_matrix / norms
        
        query_norm = query / np.linalg.norm(query)
        similarities = np.dot(normalized, query_norm.T).flatten()
        
        # 获取 top_k
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for rank, idx in enumerate(top_indices):
            result = RetrievalResult(
                chunk=self.chunks[idx],
                score=float(similarities[idx]),
                rank=rank + 1
            )
            results.append(result)
        
        return results
    
    def save(self, path: str) -> None:
        """保存向量存储"""
        os.makedirs(path, exist_ok=True)
        
        data = {
            'chunks': self.chunks,
            'embeddings': self.embeddings,
            'dimension': self.dimension
        }
        
        with open(os.path.join(path, "vectorstore.pkl"), 'wb') as f:
            pickle.dump(data, f)
        
        print(f"向量存储已保存到: {path}")
    
    def load(self, path: str) -> None:
        """加载向量存储"""
        with open(os.path.join(path, "vectorstore.pkl"), 'rb') as f:
            data = pickle.load(f)
        
        self.chunks = data['chunks']
        self.embeddings = data['embeddings']
        self.dimension = data['dimension']
        
        print(f"向量存储已加载: {len(self.chunks)} 个文档块")


# 全局向量存储实例
_vector_store: Optional[VectorStore] = None


def get_vector_store(dimension: int = 768, use_faiss: bool = True) -> VectorStore:
    """获取全局向量存储实例"""
    global _vector_store
    
    if _vector_store is None:
        if use_faiss:
            try:
                import faiss
                _vector_store = FaissVectorStore(dimension)
                print("使用 FAISS 向量存储")
            except ImportError:
                print("FAISS 不可用，使用内存向量存储")
                _vector_store = InMemoryVectorStore(dimension)
        else:
            _vector_store = InMemoryVectorStore(dimension)
            print("使用内存向量存储")
    
    return _vector_store


def create_vector_store(dimension: int = 768, use_faiss: bool = True) -> VectorStore:
    """创建新的向量存储实例"""
    if use_faiss:
        try:
            import faiss
            return FaissVectorStore(dimension)
        except ImportError:
            return InMemoryVectorStore(dimension)
    return InMemoryVectorStore(dimension)