"""
RAG 基础数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class DocumentType(Enum):
    """文档类型"""
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"
    JSON = "json"
    UNKNOWN = "unknown"


@dataclass
class Document:
    """文档对象"""
    id: str
    content: str
    metadata: dict = field(default_factory=dict)
    doc_type: DocumentType = DocumentType.UNKNOWN
    source: str = ""  # 文件路径或 URL
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.id:
            self.id = f"doc_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        if not self.metadata:
            self.metadata = {}


@dataclass
class DocumentChunk:
    """文档分块"""
    id: str
    content: str
    document_id: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = f"chunk_{self.document_id}_{self.chunk_index}"


@dataclass
class RetrievalResult:
    """检索结果"""
    chunk: DocumentChunk
    score: float  # 相似度分数
    rank: int = 0
    
    def __repr__(self):
        return f"RetrievalResult(chunk={self.chunk.id}, score={self.score:.4f}, rank={self.rank})"


@dataclass
class QaResult:
    """问答结果"""
    question: str
    answer: str
    sources: List[RetrievalResult] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def __repr__(self):
        return f"QaResult(question='{self.question[:30]}...', answer='{self.answer[:50]}...')"