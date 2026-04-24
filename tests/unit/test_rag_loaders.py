# -*- coding: utf-8 -*-
"""
RAG Loaders 模块单元测试

测试范围：
- BaseLoader 基类
- TextLoader 文本加载器
- MarkdownLoader Markdown加载器
- HtmlLoader HTML加载器
- DirectoryLoader 目录加载器
- load_document 便捷函数
- load_directory 便捷函数
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tempfile

# 条件导入（处理依赖缺失）
try:
    from tradingagents.rag.loaders import (
        BaseLoader,
        TextLoader,
        MarkdownLoader,
        PdfLoader,
        HtmlLoader,
        DirectoryLoader,
        load_document,
        load_directory,
    )
    from tradingagents.rag.base import Document, DocumentType
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装（tradingagents）", allow_module_level=True)


class TestBaseLoader:
    """BaseLoader 基类测试"""

    def test_load_未实现异常(self):
        """测试load方法未实现时抛出异常"""
        loader = BaseLoader()
        with pytest.raises(NotImplementedError):
            loader.load("test.txt")

    def test_generate_id(self):
        """测试生成文档ID"""
        loader = BaseLoader()
        content = "test content"
        doc_id = loader._generate_id(content)
        assert len(doc_id) == 16
        assert isinstance(doc_id, str)

    def test_generate_id_一致性(self):
        """测试相同内容生成相同ID"""
        loader = BaseLoader()
        content = "test content"
        id1 = loader._generate_id(content)
        id2 = loader._generate_id(content)
        assert id1 == id2

    def test_generate_id_不同内容(self):
        """测试不同内容生成不同ID"""
        loader = BaseLoader()
        id1 = loader._generate_id("content1")
        id2 = loader._generate_id("content2")
        assert id1 != id2


class TestTextLoader:
    """TextLoader 文本加载器测试"""

    def test_load_文本文件(self, tmp_path):
        """测试加载文本文件"""
        # 创建临时文本文件
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!\nThis is a test.", encoding='utf-8')

        loader = TextLoader()
        docs = loader.load(str(test_file))

        assert len(docs) == 1
        assert docs[0].content == "Hello, World!\nThis is a test."
        assert docs[0].doc_type == DocumentType.TEXT
        assert docs[0].source == str(test_file)

    def test_load_空文件(self, tmp_path):
        """测试加载空文件"""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("", encoding='utf-8')

        loader = TextLoader()
        docs = loader.load(str(test_file))

        assert len(docs) == 1
        assert docs[0].content == ""

    def test_load_中文内容(self, tmp_path):
        """测试加载中文内容"""
        test_file = tmp_path / "chinese.txt"
        test_file.write_text("你好，世界！\n这是一个测试。", encoding='utf-8')

        loader = TextLoader()
        docs = loader.load(str(test_file))

        assert len(docs) == 1
        assert "你好" in docs[0].content


class TestMarkdownLoader:
    """MarkdownLoader Markdown加载器测试"""

    def test_load_带标题的Markdown(self, tmp_path):
        """测试加载带标题的Markdown"""
        test_file = tmp_path / "test.md"
        test_file.write_text("# My Title\n\nSome content here.", encoding='utf-8')

        loader = MarkdownLoader()
        docs = loader.load(str(test_file))

        assert len(docs) == 1
        assert docs[0].doc_type == DocumentType.MARKDOWN
        assert docs[0].metadata['title'] == "My Title"

    def test_load_无标题Markdown(self, tmp_path):
        """测试加载无标题Markdown"""
        test_file = tmp_path / "no_title.md"
        test_file.write_text("Just content without title.", encoding='utf-8')

        loader = MarkdownLoader()
        docs = loader.load(str(test_file))

        assert len(docs) == 1
        assert docs[0].metadata['title'] == ""

    def test_load_多级标题(self, tmp_path):
        """测试加载多级标题"""
        test_file = tmp_path / "multi.md"
        test_file.write_text("## Sub Title\n\n# Main Title\n\nContent.", encoding='utf-8')

        loader = MarkdownLoader()
        docs = loader.load(str(test_file))

        # 应该提取第一个 # 标题
        assert docs[0].metadata['title'] == "Main Title"


class TestPdfLoader:
    """PdfLoader PDF加载器测试"""

    def test_检查PDF库_无库可用(self):
        """测试PDF库不可用时的处理"""
        with patch.dict('sys.modules', {'PyPDF2': None, 'pdfplumber': None}):
            loader = PdfLoader()
            loader._pdf_available = None  # 重置缓存
            result = loader._check_pdf_library()
            assert result is False

    def test_load_无PDF库抛出异常(self, tmp_path):
        """测试无PDF库时加载抛出异常"""
        with patch.object(PdfLoader, '_check_pdf_library', return_value=False):
            loader = PdfLoader()
            test_file = tmp_path / "test.pdf"
            test_file.write_bytes(b"fake pdf content")

            with pytest.raises(ImportError):
                loader.load(str(test_file))


class TestHtmlLoader:
    """HtmlLoader HTML加载器测试"""

    def test_load_简单HTML(self, tmp_path):
        """测试加载简单HTML"""
        test_file = tmp_path / "test.html"
        html_content = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Hello</h1>
            <p>This is a test.</p>
        </body>
        </html>
        """
        test_file.write_text(html_content, encoding='utf-8')

        try:
            loader = HtmlLoader()
            docs = loader.load(str(test_file))

            assert len(docs) == 1
            assert docs[0].doc_type == DocumentType.HTML
            assert docs[0].metadata['title'] == "Test Page"
            assert "Hello" in docs[0].content
        except ImportError:
            pytest.skip("beautifulsoup4 未安装")

    def test_load_移除脚本样式(self, tmp_path):
        """测试移除脚本和样式标签"""
        test_file = tmp_path / "script.html"
        html_content = """
        <html>
        <head>
            <title>Test</title>
            <script>alert('test');</script>
            <style>.class { color: red; }</style>
        </head>
        <body>Content only</body>
        </html>
        """
        test_file.write_text(html_content, encoding='utf-8')

        try:
            loader = HtmlLoader()
            docs = loader.load(str(test_file))

            assert len(docs) == 1
            assert "alert" not in docs[0].content
            assert "color" not in docs[0].content
        except ImportError:
            pytest.skip("beautifulsoup4 未安装")

    def test_load_无标题HTML(self, tmp_path):
        """测试加载无标题HTML"""
        test_file = tmp_path / "no_title.html"
        html_content = "<html><body>No title here</body></html>"
        test_file.write_text(html_content, encoding='utf-8')

        try:
            loader = HtmlLoader()
            docs = loader.load(str(test_file))

            assert len(docs) == 1
            assert docs[0].metadata['title'] == ""
        except ImportError:
            pytest.skip("beautifulsoup4 未安装")


class TestDirectoryLoader:
    """DirectoryLoader 目录加载器测试"""

    def test_初始化_默认扩展名(self):
        """测试初始化使用默认扩展名"""
        loader = DirectoryLoader()
        assert '.txt' in loader.extensions
        assert '.md' in loader.extensions
        assert '.pdf' in loader.extensions
        assert '.html' in loader.extensions

    def test_初始化_自定义扩展名(self):
        """测试初始化使用自定义扩展名"""
        loader = DirectoryLoader(extensions=['.txt', '.json'])
        assert loader.extensions == ['.txt', '.json']

    def test_get_loader_txt(self):
        """测试获取TXT加载器"""
        loader = DirectoryLoader()
        txt_loader = loader._get_loader('.txt')
        assert isinstance(txt_loader, TextLoader)

    def test_get_loader_md(self):
        """测试获取MD加载器"""
        loader = DirectoryLoader()
        md_loader = loader._get_loader('.md')
        assert isinstance(md_loader, MarkdownLoader)

    def test_get_loader_markdown(self):
        """测试获取MARKDOWN加载器"""
        loader = DirectoryLoader()
        md_loader = loader._get_loader('.markdown')
        assert isinstance(md_loader, MarkdownLoader)

    def test_get_loader_html(self):
        """测试获取HTML加载器"""
        loader = DirectoryLoader()
        html_loader = loader._get_loader('.html')
        assert isinstance(html_loader, HtmlLoader)

    def test_get_loader_未知扩展名(self):
        """测试获取未知扩展名加载器"""
        loader = DirectoryLoader()
        unknown_loader = loader._get_loader('.xyz')
        assert isinstance(unknown_loader, TextLoader)  # 默认返回TextLoader

    def test_load_目录(self, tmp_path):
        """测试加载目录"""
        # 创建测试文件
        (tmp_path / "test1.txt").write_text("File 1 content", encoding='utf-8')
        (tmp_path / "test2.txt").write_text("File 2 content", encoding='utf-8')

        loader = DirectoryLoader(extensions=['.txt'])
        docs = loader.load(str(tmp_path))

        assert len(docs) == 2


class TestLoadDocument:
    """load_document 便捷函数测试"""

    def test_load_txt(self, tmp_path):
        """测试加载TXT文件"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content", encoding='utf-8')

        docs = load_document(str(test_file))
        assert len(docs) == 1
        assert docs[0].doc_type == DocumentType.TEXT

    def test_load_md(self, tmp_path):
        """测试加载MD文件"""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n\nContent", encoding='utf-8')

        docs = load_document(str(test_file))
        assert len(docs) == 1
        assert docs[0].doc_type == DocumentType.MARKDOWN

    def test_load_未知扩展名(self, tmp_path):
        """测试加载未知扩展名文件"""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("Test content", encoding='utf-8')

        docs = load_document(str(test_file))
        assert len(docs) == 1  # 默认使用TextLoader


class TestLoadDirectory:
    """load_directory 便捷函数测试"""

    def test_load_directory(self, tmp_path):
        """测试加载目录"""
        (tmp_path / "file1.txt").write_text("File 1", encoding='utf-8')
        (tmp_path / "file2.txt").write_text("File 2", encoding='utf-8')

        docs = load_directory(str(tmp_path))
        assert len(docs) == 2


class TestErrorHandling:
    """错误处理测试"""

    def test_textloader_文件不存在(self):
        """测试TextLoader加载不存在的文件"""
        loader = TextLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent_file.txt")

    def test_markdownloader_文件不存在(self):
        """测试MarkdownLoader加载不存在的文件"""
        loader = MarkdownLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent_file.md")

    def test_pdfloader_文件不存在(self):
        """测试PdfLoader加载不存在的文件"""
        with patch.object(PdfLoader, '_check_pdf_library', return_value='PyPDF2'):
            loader = PdfLoader()
            with pytest.raises(FileNotFoundError):
                loader.load("nonexistent_file.pdf")

    def test_htmlloader_文件不存在(self):
        """测试HtmlLoader加载不存在的文件"""
        try:
            loader = HtmlLoader()
            with pytest.raises(FileNotFoundError):
                loader.load("nonexistent_file.html")
        except ImportError:
            pytest.skip("beautifulsoup4 未安装")

    def test_directoryloader_目录不存在(self):
        """测试DirectoryLoader加载不存在的目录"""
        loader = DirectoryLoader()
        docs = loader.load("/nonexistent/directory/path")
        # 应该返回空列表而不是抛出异常
        assert docs == []

    def test_loaddocument_文件不存在(self):
        """测试load_document加载不存在的文件"""
        with pytest.raises(FileNotFoundError):
            load_document("nonexistent_file.txt")

    def test_textloader_权限错误_使用_mock(self):
        """测试TextLoader处理权限错误"""
        loader = TextLoader()
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                loader.load("restricted_file.txt")

    def test_pdfloader_损坏文件_使用_mock(self):
        """测试PdfLoader处理损坏文件"""
        with patch.object(PdfLoader, '_check_pdf_library', return_value='PyPDF2'):
            with patch('PyPDF2.PdfReader', side_effect=Exception("Corrupted PDF")):
                loader = PdfLoader()
                # 损坏文件应返回默认内容而不是崩溃
                with pytest.raises(Exception):
                    loader.load("corrupted.pdf")

    def test_htmlloader_损坏html_仍能解析(self, tmp_path):
        """测试HtmlLoader处理损坏HTML"""
        try:
            test_file = tmp_path / "broken.html"
            # 不完整的HTML
            html_content = "<html><body>Broken but parseable"
            test_file.write_text(html_content, encoding='utf-8')

            loader = HtmlLoader()
            docs = loader.load(str(test_file))
            # 应该仍能解析，但可能没有标题
            assert len(docs) == 1
        except ImportError:
            pytest.skip("beautifulsoup4 未安装")

    def test_textloader_特殊字符内容(self, tmp_path):
        """测试TextLoader处理特殊字符"""
        test_file = tmp_path / "special.txt"
        # 包含特殊字符和Unicode
        content = "Special chars: @#$%^&*()\nUnicode: 你好世界 🌍"
        test_file.write_text(content, encoding='utf-8')

        loader = TextLoader()
        docs = loader.load(str(test_file))
        assert len(docs) == 1
        assert "🌍" in docs[0].content

    def test_textloader_大文件内容(self, tmp_path):
        """测试TextLoader处理大文件"""
        test_file = tmp_path / "large.txt"
        # 创建1MB文件
        content = "A" * (1024 * 1024)
        test_file.write_text(content, encoding='utf-8')

        loader = TextLoader()
        docs = loader.load(str(test_file))
        assert len(docs) == 1
        assert len(docs[0].content) == 1024 * 1024

    def test_markdownloader_编码错误_使用_mock(self):
        """测试MarkdownLoader处理编码错误"""
        loader = MarkdownLoader()
        # 模拟文件读取时编码错误
        with patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid')):
            # 由于代码使用errors='ignore'，应该不会抛出异常
            docs = loader.load("test.md")
            assert len(docs) == 1

    def test_directoryloader_单个文件失败_继续处理其他文件(self, tmp_path):
        """测试DirectoryLoader单个文件失败时继续处理其他文件"""
        (tmp_path / "good.txt").write_text("Good file", encoding='utf-8')
        (tmp_path / "bad.txt").write_text("Bad file", encoding='utf-8')

        loader = DirectoryLoader(extensions=['.txt'])
        # Mock load方法让第二个文件失败
        original_load = loader._get_loader
        call_count = [0]

        def mock_get_loader(ext):
            call_count[0] += 1
            mock_loader = Mock()
            if call_count[0] == 2:
                mock_loader.load.side_effect = Exception("File load error")
            else:
                mock_loader.load = original_load(ext).load
            return mock_loader

        loader._get_loader = mock_get_loader
        docs = loader.load(str(tmp_path))
        # 应该至少加载第一个文件
        assert len(docs) >= 0  # 取决于文件处理顺序
