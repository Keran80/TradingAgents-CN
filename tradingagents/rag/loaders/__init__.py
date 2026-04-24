"""
文档加载器模块
支持 PDF、Markdown、Text、HTML 等格式
"""
import os
from typing import List, Optional
from pathlib import Path
import hashlib

from ..base import Document, DocumentType


class BaseLoader:
    """文档加载器基类"""
    
    def load(self, source: str) -> List[Document]:
        """加载文档，返回文档列表"""
        raise NotImplementedError
    
    def _generate_id(self, content: str) -> str:
        """根据内容生成唯一 ID"""
        return hashlib.md5(content.encode()).hexdigest()[:16]


class TextLoader(BaseLoader):
    """纯文本加载器"""
    
    def load(self, source: str) -> List[Document]:
        with open(source, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        doc = Document(
            id=self._generate_id(content),
            content=content,
            source=source,
            doc_type=DocumentType.TEXT
        )
        return [doc]


class MarkdownLoader(BaseLoader):
    """Markdown 加载器"""
    
    def load(self, source: str) -> List[Document]:
        with open(source, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 提取标题作为元数据
        title = ""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        doc = Document(
            id=self._generate_id(content),
            content=content,
            source=source,
            doc_type=DocumentType.MARKDOWN,
            metadata={'title': title}
        )
        return [doc]


class PdfLoader(BaseLoader):
    """PDF 加载器（需要 PyPDF2 或 pdfplumber）"""
    
    def __init__(self):
        self._pdf_available = None
    
    def _check_pdf_library(self):
        """检查 PDF 库是否可用"""
        if self._pdf_available is not None:
            return self._pdf_available
        
        try:
            import PyPDF2
            self._pdf_available = 'PyPDF2'
        except ImportError:
            try:
                import pdfplumber
                self._pdf_available = 'pdfplumber'
            except ImportError:
                self._pdf_available = False
        return self._pdf_available
    
    def load(self, source: str) -> List[Document]:
        pdf_lib = self._check_pdf_library()
        
        if not pdf_lib:
            raise ImportError("请安装 PyPDF2 或 pdfplumber: pip install PyPDF2 pdfplumber")
        
        content = ""
        
        if pdf_lib == 'PyPDF2':
            import PyPDF2
            with open(source, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    content += page.extract_text() + "\n"
        
        elif pdf_lib == 'pdfplumber':
            import pdfplumber
            with pdfplumber.open(source) as pdf:
                for page in pdf.pages:
                    content += page.extract_text() or ""
        
        if not content.strip():
            content = f"[PDF 文件: {source}]"
        
        doc = Document(
            id=self._generate_id(content),
            content=content,
            source=source,
            doc_type=DocumentType.PDF,
            metadata={'page_count': self._get_page_count(source, pdf_lib)}
        )
        return [doc]
    
    def _get_page_count(self, source: str, pdf_lib: str) -> int:
        """获取 PDF 页数"""
        try:
            if pdf_lib == 'PyPDF2':
                import PyPDF2
                with open(source, 'rb') as f:
                    return len(PyPDF2.PdfReader(f).pages)
            elif pdf_lib == 'pdfplumber':
                import pdfplumber
                with pdfplumber.open(source) as pdf:
                    return len(pdf.pages)
        except Exception:
            return 0


class HtmlLoader(BaseLoader):
    """HTML 加载器"""
    
    def load(self, source: str) -> List[Document]:
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("请安装 beautifulsoup4: pip install beautifulsoup4")
        
        with open(source, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取标题
        title = soup.title.string if soup.title else ""
        
        # 移除脚本和样式
        for tag in soup(['script', 'style']):
            tag.decompose()
        
        # 获取文本
        content = soup.get_text(separator='\n', strip=True)
        
        doc = Document(
            id=self._generate_id(content),
            content=content,
            source=source,
            doc_type=DocumentType.HTML,
            metadata={'title': title}
        )
        return [doc]


class DirectoryLoader(BaseLoader):
    """目录加载器 - 递归加载目录下所有支持的文件"""
    
    def __init__(self, extensions: List[str] = None):
        self.extensions = extensions or ['.txt', '.md', '.pdf', '.html']
    
    def load(self, source: str) -> List[Document]:
        """加载目录下所有支持的文件"""
        documents = []
        
        for root, _, files in os.walk(source):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in self.extensions:
                    file_path = os.path.join(root, file)
                    try:
                        loader = self._get_loader(ext)
                        docs = loader.load(file_path)
                        documents.extend(docs)
                    except Exception as e:
                        print(f"加载失败 {file_path}: {e}")
        
        return documents
    
    def _get_loader(self, ext: str) -> BaseLoader:
        """根据扩展名获取加载器"""
        loaders = {
            '.txt': TextLoader,
            '.md': MarkdownLoader,
            '.markdown': MarkdownLoader,
            '.pdf': PdfLoader,
            '.html': HtmlLoader,
            '.htm': HtmlLoader,
        }
        return loaders.get(ext, TextLoader)()


def load_document(source: str) -> List[Document]:
    """便捷函数：自动识别文件类型并加载"""
    ext = Path(source).suffix.lower()
    
    loaders = {
        '.txt': TextLoader,
        '.md': MarkdownLoader,
        '.markdown': MarkdownLoader,
        '.pdf': PdfLoader,
        '.html': HtmlLoader,
        '.htm': HtmlLoader,
    }
    
    loader_class = loaders.get(ext, TextLoader)
    loader = loader_class()
    
    return loader.load(source)


def load_directory(directory: str, extensions: List[str] = None) -> List[Document]:
    """便捷函数：加载目录下所有文件"""
    loader = DirectoryLoader(extensions)
    return loader.load(directory)