"""
文本分块器模块
支持多种分块策略：固定大小、滑动窗口、句子级别
"""
from typing import List, Optional
import re
import hashlib

from ..base import Document, DocumentChunk


class BaseChunker:
    """分块器基类"""
    
    def chunk(self, document: Document) -> List[DocumentChunk]:
        raise NotImplementedError


class FixedSizeChunker(BaseChunker):
    """固定大小分块器"""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, document: Document) -> List[DocumentChunk]:
        content = document.content
        chunks = []
        
        start = 0
        index = 0
        
        while start < len(content):
            end = start + self.chunk_size
            
            # 尝试在句子边界切分
            if end < len(content):
                # 查找最后一个句号、逗号或空格
                boundary = content.rfind('.', start, end)
                if boundary > start + self.chunk_size * 0.5:
                    end = boundary + 1
            
            chunk_text = content[start:end].strip()
            
            if chunk_text:
                chunk_id = hashlib.md5(f"{document.id}_{index}".encode()).hexdigest()[:16]
                
                chunk = DocumentChunk(
                    id=chunk_id,
                    content=chunk_text,
                    document_id=document.id,
                    chunk_index=index,
                    metadata={
                        **document.metadata,
                        'start_pos': start,
                        'end_pos': end
                    }
                )
                chunks.append(chunk)
            
            start = end - self.overlap
            index += 1
            
            if start >= len(content):
                break
        
        return chunks


class SlidingWindowChunker(BaseChunker):
    """滑动窗口分块器 - 保留更多上下文"""
    
    def __init__(self, chunk_size: int = 500, step: int = 200):
        self.chunk_size = chunk_size
        self.step = step
    
    def chunk(self, document: Document) -> List[DocumentChunk]:
        content = document.content
        chunks = []
        index = 0
        
        for start in range(0, len(content), self.step):
            end = min(start + self.chunk_size, len(content))
            chunk_text = content[start:end].strip()
            
            if chunk_text:
                chunk_id = hashlib.md5(f"{document.id}_{index}".encode()).hexdigest()[:16]
                
                chunk = DocumentChunk(
                    id=chunk_id,
                    content=chunk_text,
                    document_id=document.id,
                    chunk_index=index,
                    metadata={
                        **document.metadata,
                        'start_pos': start,
                        'end_pos': end
                    }
                )
                chunks.append(chunk)
            
            index += 1
            
            if end >= len(content):
                break
        
        return chunks


class SentenceChunker(BaseChunker):
    """句子级别分块器"""
    
    def __init__(self, min_sentences: int = 3, max_sentences: int = 10):
        self.min_sentences = min_sentences
        self.max_sentences = max_sentences
    
    def _split_sentences(self, text: str) -> List[str]:
        """按句子分割"""
        # 简单实现，支持中英文句子边界
        sentence_pattern = r'[。！？\.\!\?]+'
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def chunk(self, document: Document) -> List[DocumentChunk]:
        sentences = self._split_sentences(document.content)
        chunks = []
        
        current_chunk = []
        current_len = 0
        index = 0
        
        for sent in sentences:
            current_chunk.append(sent)
            current_len += len(sent)
            
            if len(current_chunk) >= self.max_sentences or current_len >= self.chunk_size:
                chunk_text = '。'.join(current_chunk)
                if not chunk_text.endswith('。'):
                    chunk_text += '。'
                
                chunk_id = hashlib.md5(f"{document.id}_{index}".encode()).hexdigest()[:16]
                
                chunk = DocumentChunk(
                    id=chunk_id,
                    content=chunk_text,
                    document_id=document.id,
                    chunk_index=index,
                    metadata=document.metadata
                )
                chunks.append(chunk)
                
                # 保留部分重叠
                overlap_count = max(1, len(current_chunk) // 3)
                current_chunk = current_chunk[-overlap_count:]
                current_len = sum(len(s) for s in current_chunk)
                index += 1
        
        # 处理剩余内容
        if current_chunk and len(current_chunk) >= self.min_sentences:
            chunk_text = '。'.join(current_chunk)
            if not chunk_text.endswith('。'):
                chunk_text += '。'
            
            chunk_id = hashlib.md5(f"{document.id}_{index}".encode()).hexdigest()[:16]
            
            chunk = DocumentChunk(
                id=chunk_id,
                content=chunk_text,
                document_id=document.id,
                chunk_index=index,
                metadata=document.metadata
            )
            chunks.append(chunk)
        
        return chunks


class MarkdownChunker(BaseChunker):
    """Markdown 专用分块器 - 按标题层级分块"""
    
    def __init__(self, min_chunk_size: int = 100, max_chunk_size: int = 2000):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
    
    def chunk(self, document: Document) -> List[DocumentChunk]:
        content = document.content
        chunks = []
        
        # 按标题分割
        header_pattern = r'^(#{1,6})\s+(.+)$'
        lines = content.split('\n')
        
        current_section = []
        current_header = ""
        
        for line in lines:
            match = re.match(header_pattern, line)
            
            if match:
                # 保存之前的内容
                if current_section:
                    chunk_text = '\n'.join(current_section)
                    if len(chunk_text) >= self.min_chunk_size:
                        chunks.append(self._create_chunk(
                            document, chunk_text, current_header, len(chunks)
                        ))
                
                current_header = match.group(2).strip()
                current_section = [line]
            
            else:
                current_section.append(line)
        
        # 保存最后一部分
        if current_section:
            chunk_text = '\n'.join(current_section)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(self._create_chunk(
                    document, chunk_text, current_header, len(chunks)
                ))
        
        return chunks
    
    def _create_chunk(self, document: Document, content: str, header: str, index: int) -> DocumentChunk:
        chunk_id = hashlib.md5(f"{document.id}_{index}".encode()).hexdigest()[:16]
        
        return DocumentChunk(
            id=chunk_id,
            content=content,
            document_id=document.id,
            chunk_index=index,
            metadata={
                **document.metadata,
                'header': header
            }
        )


def chunk_document(document: Document, method: str = 'fixed', **kwargs) -> List[DocumentChunk]:
    """便捷函数：分块文档
    
    Args:
        document: 文档对象
        method: 分块方法 ('fixed', 'sliding', 'sentence', 'markdown')
        **kwargs: 分块器参数
    
    Returns:
        分块列表
    """
    chunkers = {
        'fixed': FixedSizeChunker,
        'sliding': SlidingWindowChunker,
        'sentence': SentenceChunker,
        'markdown': MarkdownChunker,
    }
    
    chunker_class = chunkers.get(method, FixedSizeChunker)
    chunker = chunker_class(**kwargs)
    
    return chunker.chunk(document)