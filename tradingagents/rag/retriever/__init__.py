"""
检索系统模块
实现混合检索：向量检索 + 关键词检索
"""
from typing import List, Optional, Dict, Any
import os
import pickle
import numpy as np

from ..base import Document, DocumentChunk, RetrievalResult
from ..loaders import load_document, load_directory
from ..chunkers import chunk_document
from ..vectorstore import create_vector_store, VectorStore
from ..embeddings import get_embedding_model, EmbeddingModel


class Retriever:
    """检索器"""
    
    def __init__(
        self,
        vector_store: VectorStore = None,
        embedding_model: EmbeddingModel = None,
        chunk_size: int = 500,
        chunk_method: str = 'fixed'
    ):
        self.vector_store = vector_store or create_vector_store(use_faiss=False)
        self.embedding_model = embedding_model or get_embedding_model('dummy')
        self.chunk_size = chunk_size
        self.chunk_method = chunk_method
        
        self.documents: Dict[str, Document] = {}
    
    def add_documents(self, sources: List[str], chunk_size: int = None, chunk_method: str = None) -> int:
        """添加文档到检索系统
        
        Args:
            sources: 文件路径列表
            chunk_size: 分块大小
            chunk_method: 分块方法
        
        Returns:
            添加的文档块数量
        """
        chunk_size = chunk_size or self.chunk_size
        chunk_method = chunk_method or self.chunk_method
        
        all_chunks = []
        
        for source in sources:
            # 加载文档
            docs = load_document(source)
            
            for doc in docs:
                self.documents[doc.id] = doc
                
                # 分块
                chunks = chunk_document(doc, method=chunk_method, chunk_size=chunk_size)
                all_chunks.extend(chunks)
        
        # 生成嵌入
        if all_chunks:
            texts = [chunk.content for chunk in all_chunks]
            embeddings = self.embedding_model.encode(texts)
            
            # 添加到向量存储
            self.vector_store.add_chunks(all_chunks, embeddings)
        
        return len(all_chunks)
    
    def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
        
        Returns:
            检索结果列表
        """
        # 生成查询向量
        query_embeddings = self.embedding_model.encode([query])
        
        # 向量检索
        results = self.vector_store.search(query_embeddings[0], top_k=top_k)
        
        return results
    
    def search_with_rerank(self, query: str, top_k: int = 10, rerank_top: int = 5) -> List[RetrievalResult]:
        """检索 + 重排序"""
        # 初步检索
        results = self.search(query, top_k=top_k)
        
        # 简单重排序：根据关键词匹配度
        query_keywords = set(query.lower().split())
        
        reranked = []
        for r in results:
            chunk_keywords = set(r.chunk.content.lower().split())
            overlap = len(query_keywords & chunk_keywords)
            r.score = r.score * 0.7 + (overlap / max(len(query_keywords), 1)) * 0.3
            reranked.append(r)
        
        # 重新排序
        reranked.sort(key=lambda x: x.score, reverse=True)
        
        return reranked[:rerank_top]
    
    def save(self, path: str) -> None:
        """保存检索系统"""
        os.makedirs(path, exist_ok=True)
        
        # 保存向量存储
        self.vector_store.save(os.path.join(path, "vectorstore"))
        
        # 保存文档
        with open(os.path.join(path, "documents.pkl"), 'wb') as f:
            pickle.dump(self.documents, f)
        
        # 保存配置
        config = {
            'chunk_size': self.chunk_size,
            'chunk_method': self.chunk_method
        }
        with open(os.path.join(path, "config.pkl"), 'wb') as f:
            pickle.dump(config, f)
        
        print(f"检索系统已保存到: {path}")
    
    def load(self, path: str) -> None:
        """加载检索系统"""
        # 加载配置
        with open(os.path.join(path, "config.pkl"), 'rb') as f:
            config = pickle.load(f)
        self.chunk_size = config['chunk_size']
        self.chunk_method = config['chunk_method']
        
        # 加载向量存储
        self.vector_store = create_vector_store(use_faiss=False)
        self.vector_store.load(os.path.join(path, "vectorstore"))
        
        # 加载文档
        with open(os.path.join(path, "documents.pkl"), 'rb') as f:
            self.documents = pickle.load(f)
        
        print(f"检索系统已加载: {len(self.documents)} 个文档")


class HybridRetriever(Retriever):
    """混合检索器 - 结合向量和关键词检索"""
    
    def __init__(self, vector_weight: float = 0.7, **kwargs):
        super().__init__(**kwargs)
        self.vector_weight = vector_weight
        self.keyword_index: Dict[str, List[str]] = {}
    
    def _build_keyword_index(self):
        """构建关键词倒排索引"""
        self.keyword_index = {}
        
        for chunk_id, chunk in zip(
            [c.id for c in self.vector_store.chunks],
            self.vector_store.chunks
        ):
            words = chunk.content.lower().split()
            for word in words:
                if len(word) > 1:  # 过滤单字
                    if word not in self.keyword_index:
                        self.keyword_index[word] = []
                    self.keyword_index[word].append(chunk_id)
    
    def add_documents(self, sources: List[str], **kwargs) -> int:
        """添加文档并构建关键词索引"""
        count = super().add_documents(sources, **kwargs)
        self._build_keyword_index()
        return count
    
    def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """混合检索"""
        # 向量检索
        vector_results = super().search(query, top_k * 2)
        
        # 关键词检索
        query_words = query.lower().split()
        keyword_scores: Dict[str, float] = {}
        
        for word in query_words:
            if word in self.keyword_index:
                for chunk_id in self.keyword_index[word]:
                    keyword_scores[chunk_id] = keyword_scores.get(chunk_id, 0) + 1
        
        # 合并分数
        combined_results = {}
        
        for r in vector_results:
            chunk_id = r.chunk.id
            vector_score = r.score
            
            keyword_score = keyword_scores.get(chunk_id, 0) / max(len(query_words), 1)
            
            # 综合分数
            final_score = (
                vector_score * self.vector_weight +
                keyword_score * (1 - self.vector_weight)
            )
            
            combined_results[chunk_id] = RetrievalResult(
                chunk=r.chunk,
                score=final_score,
                rank=0
            )
        
        # 排序
        sorted_results = sorted(combined_results.values(), key=lambda x: x.score, reverse=True)
        
        # 更新排名
        for i, r in enumerate(sorted_results[:top_k]):
            r.rank = i + 1
        
        return sorted_results[:top_k]


def create_retriever(
    model_type: str = 'sentence-transformers',
    use_faiss: bool = True,
    chunk_size: int = 500,
    chunk_method: str = 'fixed'
) -> Retriever:
    """创建检索器实例"""
    embedding_model = get_embedding_model(model_type)
    vector_store = create_vector_store(dimension=embedding_model.dimension, use_faiss=use_faiss)
    
    return Retriever(
        vector_store=vector_store,
        embedding_model=embedding_model,
        chunk_size=chunk_size,
        chunk_method=chunk_method
    )