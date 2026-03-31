"""
RAG 模块 - 检索增强生成
支持文档加载、向量存储、检索和 LLM 问答

使用示例：
```python
from tradingagents.rag import create_knowledge_base, load_document, chunk_document
from tradingagents.rag.retriever import create_retriever
from tradingagents.rag.qa import create_qa_system

# 1. 创建知识库
create_knowledge_base("投资知识库", "投资研究文档集合")

# 2. 加载和分块文档
docs = load_document("path/to/document.pdf")
chunks = chunk_document(docs[0], method='fixed', chunk_size=500)

# 3. 创建检索器
retriever = create_retriever(model_type='sentence-transformers')
retriever.add_documents(["doc1.pdf", "doc2.md"])

# 4. 创建问答系统
qa = create_qa_system(retriever, llm_provider='deepseek', api_key='your-key')
result = qa.ask("什么是ROE指标？")
print(result.answer)
```
"""
from .base import Document, DocumentChunk, RetrievalResult, QaResult, DocumentType
from .registry import RagRegistry, get_rag_registry, create_knowledge_base
from .loaders import load_document, load_directory, TextLoader, MarkdownLoader, PdfLoader
from .chunkers import chunk_document, FixedSizeChunker, SentenceChunker
from .embeddings import get_embedding_model, EmbeddingModel, SentenceTransformerEmbedding
from .vectorstore import create_vector_store, VectorStore, FaissVectorStore, InMemoryVectorStore
from .retriever import Retriever, HybridRetriever, create_retriever
from .qa import QaSystem, LLMConfig, get_llm, create_qa_system

__all__ = [
    # 基础类
    'Document',
    'DocumentChunk', 
    'RetrievalResult',
    'QaResult',
    'DocumentType',
    # 注册表
    'RagRegistry',
    'get_rag_registry',
    'create_knowledge_base',
    # 加载器
    'load_document',
    'load_directory',
    'TextLoader',
    'MarkdownLoader',
    'PdfLoader',
    # 分块器
    'chunk_document',
    'FixedSizeChunker',
    'SentenceChunker',
    # 嵌入
    'get_embedding_model',
    'EmbeddingModel',
    'SentenceTransformerEmbedding',
    # 向量存储
    'create_vector_store',
    'VectorStore',
    'FaissVectorStore',
    'InMemoryVectorStore',
    # 检索器
    'Retriever',
    'HybridRetriever',
    'create_retriever',
    # 问答
    'QaSystem',
    'LLMConfig',
    'get_llm',
    'create_qa_system'
]