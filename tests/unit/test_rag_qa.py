# -*- coding: utf-8 -*-
"""
RAG QA 模块单元测试

测试范围：
- LLMConfig 配置类
- BaseLLM 基类
- OpenAILLM（mock）
- DeepSeekLLM（mock）
- ZhipuLLM（mock）
- AnthropicLLM（mock）
- QaSystem 问答系统
- get_llm 便捷函数
- create_qa_system 便捷函数
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import numpy as np

# 条件导入（处理依赖缺失）
try:
    from tradingagents.rag.qa import (
        LLMConfig,
        BaseLLM,
        OpenAILLM,
        DeepSeekLLM,
        ZhipuLLM,
        AnthropicLLM,
        QaSystem,
        get_llm,
        create_qa_system,
    )
    from tradingagents.rag.base import DocumentChunk, RetrievalResult, QaResult
    from tradingagents.rag.retriever import Retriever
    from tradingagents.rag.vectorstore import InMemoryVectorStore
    from tradingagents.rag.embeddings import DummyEmbedding
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装（tradingagents）", allow_module_level=True)


class TestLLMConfig:
    """LLMConfig 配置类测试"""

    def test_初始化_默认参数(self):
        """测试初始化使用默认参数"""
        config = LLMConfig()
        assert config.provider == "openai"
        assert config.model == "gpt-3.5-turbo"
        assert config.api_key == ""
        assert config.api_base == ""
        assert config.temperature == 0.7
        assert config.max_tokens == 2000

    def test_初始化_自定义参数(self):
        """测试初始化使用自定义参数"""
        config = LLMConfig(
            provider="deepseek",
            model="deepseek-chat",
            api_key="test-key",
            api_base="https://api.deepseek.com/v1",
            temperature=0.5,
            max_tokens=1000
        )
        assert config.provider == "deepseek"
        assert config.model == "deepseek-chat"
        assert config.api_key == "test-key"
        assert config.temperature == 0.5
        assert config.max_tokens == 1000


class TestBaseLLM:
    """BaseLLM 基类测试"""

    def test_chat_未实现异常(self):
        """测试chat方法未实现时抛出异常"""
        config = LLMConfig()
        llm = BaseLLM(config)
        with pytest.raises(NotImplementedError):
            llm.chat([{"role": "user", "content": "test"}])


class TestOpenAILLM:
    """OpenAILLM 测试"""

    @patch('tradingagents.rag.qa.openai')
    def test_初始化_设置api_key(self, mock_openai):
        """测试初始化设置API key"""
        config = LLMConfig(api_key="test-key", api_base="https://test.api.com")
        llm = OpenAILLM(config)
        assert mock_openai.api_key == "test-key"
        assert mock_openai.api_base == "https://test.api.com"

    @patch('tradingagents.rag.qa.openai')
    def test_chat_成功(self, mock_openai):
        """测试聊天成功"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_openai.ChatCompletion.create.return_value = mock_response

        config = LLMConfig(api_key="test-key")
        llm = OpenAILLM(config)
        result = llm.chat([{"role": "user", "content": "Hello"}])
        assert result == "Test response"

    @patch('tradingagents.rag.qa.openai')
    def test_chat_异常处理(self, mock_openai):
        """测试聊天异常处理"""
        mock_openai.ChatCompletion.create.side_effect = Exception("API Error")

        config = LLMConfig(api_key="test-key")
        llm = OpenAILLM(config)
        result = llm.chat([{"role": "user", "content": "Hello"}])
        assert "LLM 调用失败" in result


class TestDeepSeekLLM:
    """DeepSeekLLM 测试"""

    @patch('tradingagents.rag.qa.requests.post')
    def test_chat_成功(self, mock_post):
        """测试聊天成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Test response'}}]
        }
        mock_post.return_value = mock_response

        config = LLMConfig(provider="deepseek", api_key="test-key")
        llm = DeepSeekLLM(config)
        result = llm.chat([{"role": "user", "content": "Hello"}])
        assert result == "Test response"

    @patch('tradingagents.rag.qa.requests.post')
    def test_chat_默认api_base(self, mock_post):
        """测试使用默认API地址"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Test'}}]
        }
        mock_post.return_value = mock_response

        config = LLMConfig(provider="deepseek", api_key="test-key")
        llm = DeepSeekLLM(config)
        llm.chat([{"role": "user", "content": "Hello"}])

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "deepseek.com" in call_args[0][0]

    @patch('tradingagents.rag.qa.requests.post')
    def test_chat_自定义api_base(self, mock_post):
        """测试使用自定义API地址"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Test'}}]
        }
        mock_post.return_value = mock_response

        config = LLMConfig(
            provider="deepseek",
            api_key="test-key",
            api_base="https://custom.api.com/v1"
        )
        llm = DeepSeekLLM(config)
        llm.chat([{"role": "user", "content": "Hello"}])

        call_args = mock_post.call_args
        assert "custom.api.com" in call_args[0][0]

    @patch('tradingagents.rag.qa.requests.post')
    def test_chat_api错误(self, mock_post):
        """测试API错误处理"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        config = LLMConfig(provider="deepseek", api_key="test-key")
        llm = DeepSeekLLM(config)
        result = llm.chat([{"role": "user", "content": "Hello"}])
        assert "API 错误" in result

    @patch('tradingagents.rag.qa.requests.post')
    def test_chat_异常处理(self, mock_post):
        """测试异常处理"""
        mock_post.side_effect = Exception("Network Error")

        config = LLMConfig(provider="deepseek", api_key="test-key")
        llm = DeepSeekLLM(config)
        result = llm.chat([{"role": "user", "content": "Hello"}])
        assert "LLM 调用失败" in result


class TestZhipuLLM:
    """ZhipuLLM 测试"""

    @patch('tradingagents.rag.qa.requests.post')
    def test_chat_成功(self, mock_post):
        """测试聊天成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Test response'}}]
        }
        mock_post.return_value = mock_response

        config = LLMConfig(provider="zhipu", api_key="test-key")
        llm = ZhipuLLM(config)
        result = llm.chat([{"role": "user", "content": "Hello"}])
        assert result == "Test response"

    @patch('tradingagents.rag.qa.requests.post')
    def test_chat_默认api_base(self, mock_post):
        """测试使用默认API地址"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Test'}}]
        }
        mock_post.return_value = mock_response

        config = LLMConfig(provider="zhipu", api_key="test-key")
        llm = ZhipuLLM(config)
        llm.chat([{"role": "user", "content": "Hello"}])

        call_args = mock_post.call_args
        assert "bigmodel.cn" in call_args[0][0]


class TestAnthropicLLM:
    """AnthropicLLM 测试"""

    @patch('tradingagents.rag.qa.requests.post')
    def test_chat_成功(self, mock_post):
        """测试聊天成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content': [{'text': 'Test response'}]
        }
        mock_post.return_value = mock_response

        config = LLMConfig(provider="anthropic", api_key="test-key")
        llm = AnthropicLLM(config)
        result = llm.chat([
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ])
        assert result == "Test response"

    @patch('tradingagents.rag.qa.requests.post')
    def test_chat_消息格式转换(self, mock_post):
        """测试消息格式转换（system消息分离）"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content': [{'text': 'Test'}]
        }
        mock_post.return_value = mock_response

        config = LLMConfig(provider="anthropic", api_key="test-key")
        llm = AnthropicLLM(config)
        llm.chat([
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Hello"}
        ])

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs['json']['system'] == "System prompt"


class TestQaSystem:
    """QaSystem 问答系统测试"""

    def setup_method(self):
        """设置测试环境"""
        vector_store = InMemoryVectorStore(dimension=768)
        embedding_model = DummyEmbedding(dimension=768)
        self.retriever = Retriever(
            vector_store=vector_store,
            embedding_model=embedding_model
        )

    def test_初始化_默认提示词(self):
        """测试初始化使用默认提示词"""
        qa = QaSystem(retriever=self.retriever)
        assert "投资研究助手" in qa.system_prompt

    def test_初始化_自定义提示词(self):
        """测试初始化使用自定义提示词"""
        qa = QaSystem(
            retriever=self.retriever,
            system_prompt="Custom system prompt"
        )
        assert qa.system_prompt == "Custom system prompt"

    def test_ask_无检索结果_返回默认答案(self):
        """测试无检索结果时返回默认答案"""
        qa = QaSystem(retriever=self.retriever)
        result = qa.ask("Test question?")
        assert isinstance(result, QaResult)
        assert result.question == "Test question?"
        assert "没有找到" in result.answer
        assert result.sources == []

    def test_ask_有检索结果_无LLM_返回检索摘要(self):
        """测试有检索结果但无LLM时返回检索摘要"""
        qa = QaSystem(retriever=self.retriever)

        # 添加文档到检索系统
        chunk = DocumentChunk(
            id="c1",
            content="This is test content for retrieval.",
            document_id="d1",
            chunk_index=0
        )
        embedding = np.random.randn(768)
        self.retriever.vector_store.add_chunks([chunk], [embedding])

        result = qa.ask("test content", top_k=5)
        assert isinstance(result, QaResult)
        assert "检索到" in result.answer
        assert len(result.sources) == 1

    def test_ask_有检索结果_有LLM_调用LLM_使用_mock(self):
        """测试有检索结果且有LLM时调用LLM"""
        mock_llm = Mock()
        mock_llm.chat.return_value = "LLM generated answer"

        qa = QaSystem(
            retriever=self.retriever,
            llm=mock_llm
        )

        # 添加文档
        chunk = DocumentChunk(
            id="c1",
            content="Test content for LLM QA.",
            document_id="d1",
            chunk_index=0
        )
        embedding = np.random.randn(768)
        self.retriever.vector_store.add_chunks([chunk], [embedding])

        result = qa.ask("test question")
        assert result.answer == "LLM generated answer"
        mock_llm.chat.assert_called_once()

    def test_ask_包含来源信息(self):
        """测试包含来源信息"""
        qa = QaSystem(retriever=self.retriever)

        chunk = DocumentChunk(
            id="c1",
            content="Test content with source info.",
            document_id="d1",
            chunk_index=0
        )
        embedding = np.random.randn(768)
        self.retriever.vector_store.add_chunks([chunk], [embedding])

        result = qa.ask("test question", include_sources=True)
        assert len(result.sources) == 1

    def test_ask_不包含来源信息(self):
        """测试不包含来源信息"""
        qa = QaSystem(retriever=self.retriever)

        chunk = DocumentChunk(
            id="c1",
            content="Test content without sources.",
            document_id="d1",
            chunk_index=0
        )
        embedding = np.random.randn(768)
        self.retriever.vector_store.add_chunks([chunk], [embedding])

        result = qa.ask("test question", include_sources=False)
        assert result.sources == []

    def test_ask_自定义top_k_使用_mock(self):
        """测试使用自定义top_k"""
        mock_retriever = Mock()
        mock_retriever.search.return_value = []

        qa = QaSystem(retriever=mock_retriever)
        qa.ask("test question", top_k=10)
        mock_retriever.search.assert_called_once_with("test question", top_k=10)

    def test_ask_streaming_无LLM_返回提示(self):
        """测试流式问答无LLM时返回提示"""
        qa = QaSystem(retriever=self.retriever)
        chunks = list(qa.ask_streaming("test question"))
        assert "请配置 LLM" in chunks[0]

    def test_ask_streaming_有LLM_使用_mock(self):
        """测试流式问答有LLM时调用流式接口"""
        mock_llm = Mock()
        mock_llm.chat_streaming.return_value = iter(["chunk1", "chunk2"])

        qa = QaSystem(
            retriever=self.retriever,
            llm=mock_llm
        )

        # Mock search返回空
        self.retriever.search = Mock(return_value=[])

        chunks = list(qa.ask_streaming("test question"))
        assert len(chunks) == 2
        mock_llm.chat_streaming.assert_called_once()

    def test_问答结果元数据(self):
        """测试问答结果包含元数据"""
        qa = QaSystem(retriever=self.retriever)

        chunk = DocumentChunk(
            id="c1",
            content="Test metadata content.",
            document_id="d1",
            chunk_index=0
        )
        embedding = np.random.randn(768)
        self.retriever.vector_store.add_chunks([chunk], [embedding])

        result = qa.ask("test question")
        assert 'retrieved_docs' in result.metadata
        assert result.metadata['retrieved_docs'] == 1


class TestGetLLM:
    """get_llm 便捷函数测试"""

    def test_获取_openai(self):
        """测试获取OpenAI LLM"""
        with patch('tradingagents.rag.qa.openai'):
            config = LLMConfig(provider="openai", api_key="test-key")
            llm = get_llm(config)
            assert isinstance(llm, OpenAILLM)

    def test_获取_deepseek(self):
        """测试获取DeepSeek LLM"""
        config = LLMConfig(provider="deepseek", api_key="test-key")
        llm = get_llm(config)
        assert isinstance(llm, DeepSeekLLM)

    def test_获取_zhipu(self):
        """测试获取智谱LLM"""
        config = LLMConfig(provider="zhipu", api_key="test-key")
        llm = get_llm(config)
        assert isinstance(llm, ZhipuLLM)

    def test_获取_anthropic(self):
        """测试获取Anthropic LLM"""
        config = LLMConfig(provider="anthropic", api_key="test-key")
        llm = get_llm(config)
        assert isinstance(llm, AnthropicLLM)

    def test_获取_unknown_使用_openai(self):
        """测试获取未知provider时使用OpenAI"""
        with patch('tradingagents.rag.qa.openai'):
            config = LLMConfig(provider="unknown", api_key="test-key")
            llm = get_llm(config)
            assert isinstance(llm, OpenAILLM)


class TestCreateQaSystem:
    """create_qa_system 便捷函数测试"""

    def test_创建问答系统_默认参数_使用_mock(self):
        """测试创建问答系统使用默认参数"""
        vector_store = InMemoryVectorStore(dimension=768)
        embedding_model = DummyEmbedding(dimension=768)
        retriever = Retriever(
            vector_store=vector_store,
            embedding_model=embedding_model
        )

        with patch('tradingagents.rag.qa.get_llm') as mock_get_llm:
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm

            qa = create_qa_system(
                retriever=retriever,
                llm_provider="deepseek",
                llm_model="deepseek-chat",
                api_key="test-key"
            )

            assert isinstance(qa, QaSystem)
            mock_get_llm.assert_called_once()

    def test_创建问答系统_自定义提示词_使用_mock(self):
        """测试创建问答系统使用自定义提示词"""
        vector_store = InMemoryVectorStore(dimension=768)
        embedding_model = DummyEmbedding(dimension=768)
        retriever = Retriever(
            vector_store=vector_store,
            embedding_model=embedding_model
        )

        with patch('tradingagents.rag.qa.get_llm', return_value=Mock()):
            qa = create_qa_system(
                retriever=retriever,
                system_prompt="Custom prompt"
            )

            assert qa.system_prompt == "Custom prompt"
