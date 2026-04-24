# -*- coding: utf-8 -*-
"""
RAG Embeddings 模块单元测试

测试范围：
- EmbeddingModel 基类
- SentenceTransformerEmbedding 句向量模型（mock）
- OpenAIEmbedding OpenAI嵌入模型（mock）
- HuggingFaceEmbedding HuggingFace模型（mock）
- DummyEmbedding 虚拟嵌入模型
- get_embedding_model 便捷函数
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import numpy as np

# 条件导入（处理依赖缺失）
try:
    from tradingagents.rag.embeddings import (
        EmbeddingModel,
        SentenceTransformerEmbedding,
        OpenAIEmbedding,
        HuggingFaceEmbedding,
        DummyEmbedding,
        get_embedding_model,
    )
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装（tradingagents）", allow_module_level=True)


class TestEmbeddingModel:
    """EmbeddingModel 基类测试"""

    def test_encode_未实现异常(self):
        """测试encode方法未实现时抛出异常"""
        model = EmbeddingModel()
        with pytest.raises(NotImplementedError):
            model.encode(["test text"])

    def test_dimension_未实现异常(self):
        """测试dimension属性未实现时抛出异常"""
        model = EmbeddingModel()
        with pytest.raises(NotImplementedError):
            _ = model.dimension


class TestDummyEmbedding:
    """DummyEmbedding 虚拟嵌入模型测试"""

    def test_初始化_默认维度(self):
        """测试初始化使用默认维度"""
        model = DummyEmbedding()
        assert model.dimension == 768

    def test_初始化_自定义维度(self):
        """测试初始化使用自定义维度"""
        model = DummyEmbedding(dimension=512)
        assert model.dimension == 512

    def test_encode_单文本(self):
        """测试编码单个文本"""
        model = DummyEmbedding(dimension=128)
        texts = ["test text"]
        embeddings = model.encode(texts)
        assert len(embeddings) == 1
        assert isinstance(embeddings[0], np.ndarray)
        assert embeddings[0].shape == (128,)

    def test_encode_多文本(self):
        """测试编码多个文本"""
        model = DummyEmbedding(dimension=64)
        texts = ["text 1", "text 2", "text 3"]
        embeddings = model.encode(texts)
        assert len(embeddings) == 3
        for emb in embeddings:
            assert isinstance(emb, np.ndarray)
            assert emb.shape == (64,)

    def test_encode_空列表(self):
        """测试编码空列表"""
        model = DummyEmbedding(dimension=128)
        embeddings = model.encode([])
        assert len(embeddings) == 0

    def test_encode_中文文本(self):
        """测试编码中文文本"""
        model = DummyEmbedding(dimension=128)
        texts = ["你好世界", "测试中文"]
        embeddings = model.encode(texts)
        assert len(embeddings) == 2
        assert all(isinstance(e, np.ndarray) for e in embeddings)

    def test_encode_确定性输出(self):
        """测试编码输出确定性（种子固定）"""
        model = DummyEmbedding(dimension=128)
        texts = ["test text"]
        emb1 = model.encode(texts)[0]
        emb2 = model.encode(texts)[0]
        np.testing.assert_array_equal(emb1, emb2)

    def test_encode_不同文本不同向量(self):
        """测试不同文本产生不同向量"""
        model = DummyEmbedding(dimension=128)
        texts = ["text A", "text B"]
        embeddings = model.encode(texts)
        with pytest.raises(AssertionError):
            np.testing.assert_array_equal(embeddings[0], embeddings[1])


class TestSentenceTransformerEmbedding:
    """SentenceTransformerEmbedding 句向量模型测试"""

    @patch('tradingagents.rag.embeddings.SentenceTransformer')
    def test_初始化_成功(self, mock_st):
        """测试初始化成功"""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_st.return_value = mock_model

        model = SentenceTransformerEmbedding(model_name="test-model")
        assert model._dimension == 384
        mock_st.assert_called_once_with("test-model")

    @patch('tradingagents.rag.embeddings.SentenceTransformer')
    def test_初始化_默认模型(self, mock_st):
        """测试初始化使用默认模型"""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_st.return_value = mock_model

        model = SentenceTransformerEmbedding()
        mock_st.assert_called_once_with("paraphrase-multilingual-MiniLM-L12-v2")

    def test_初始化_导入失败(self):
        """测试导入失败时抛出异常"""
        with patch.dict('sys.modules', {'sentence_transformers': None}):
            with pytest.raises(ImportError) as exc_info:
                SentenceTransformerEmbedding()
            assert "sentence-transformers" in str(exc_info.value)

    @patch('tradingagents.rag.embeddings.SentenceTransformer')
    def test_encode_单文本(self, mock_st):
        """测试编码单个文本"""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 128
        mock_model.encode.return_value = np.array([[0.1] * 128])
        mock_st.return_value = mock_model

        model = SentenceTransformerEmbedding()
        embeddings = model.encode(["test text"])
        assert len(embeddings) == 1
        assert isinstance(embeddings[0], np.ndarray)

    @patch('tradingagents.rag.embeddings.SentenceTransformer')
    def test_encode_多文本(self, mock_st):
        """测试编码多个文本"""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 128
        mock_model.encode.return_value = np.array([[0.1] * 128, [0.2] * 128])
        mock_st.return_value = mock_model

        model = SentenceTransformerEmbedding()
        embeddings = model.encode(["text 1", "text 2"])
        assert len(embeddings) == 2


class TestOpenAIEmbedding:
    """OpenAIEmbedding OpenAI嵌入模型测试"""

    def test_初始化_默认参数(self):
        """测试初始化使用默认参数"""
        model = OpenAIEmbedding(api_key="test-key")
        assert model.model == "text-embedding-3-small"
        assert model.api_key == "test-key"
        assert model.api_base == "https://api.openai.com/v1"
        assert model._dimension == 1536

    def test_初始化_自定义模型_小模型(self):
        """测试初始化使用小模型"""
        model = OpenAIEmbedding(model="text-embedding-3-small", api_key="test-key")
        assert model._dimension == 1536

    def test_初始化_自定义模型_大模型(self):
        """测试初始化使用大模型"""
        model = OpenAIEmbedding(model="text-embedding-3-large", api_key="test-key")
        assert model._dimension == 3072

    def test_初始化_自定义api_base(self):
        """测试初始化使用自定义API地址"""
        model = OpenAIEmbedding(
            api_key="test-key",
            api_base="https://custom.api.com/v1"
        )
        assert model.api_base == "https://custom.api.com/v1"

    @patch('tradingagents.rag.embeddings.requests.post')
    def test_encode_成功(self, mock_post):
        """测试编码成功"""
        model = OpenAIEmbedding(api_key="test-key")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'embedding': [0.1] * 1536},
                {'embedding': [0.2] * 1536}
            ]
        }
        mock_post.return_value = mock_response

        embeddings = model.encode(["text 1", "text 2"])
        assert len(embeddings) == 2
        assert isinstance(embeddings[0], np.ndarray)
        assert embeddings[0].shape == (1536,)

    @patch('tradingagents.rag.embeddings.requests.post')
    def test_encode_批量处理(self, mock_post):
        """测试批量处理（超过100条）"""
        model = OpenAIEmbedding(api_key="test-key")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [{'embedding': [0.1] * 1536}]
        }
        mock_post.return_value = mock_response

        texts = [f"text {i}" for i in range(150)]  # 超过batch_size=100
        embeddings = model.encode(texts)
        assert len(embeddings) == 150
        # 应调用2次API（100 + 50）
        assert mock_post.call_count == 2

    @patch('tradingagents.rag.embeddings.requests.post')
    def test_encode_api错误(self, mock_post):
        """测试API错误处理"""
        model = OpenAIEmbedding(api_key="test-key")
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            model.encode(["test text"])
        assert "API 错误" in str(exc_info.value)

    def test_dimension(self):
        """测试维度属性"""
        model = OpenAIEmbedding(api_key="test-key")
        assert model.dimension == 1536


class TestHuggingFaceEmbedding:
    """HuggingFaceEmbedding HuggingFace模型测试"""

    @patch('tradingagents.rag.embeddings.AutoTokenizer')
    @patch('tradingagents.rag.embeddings.AutoModel')
    @patch('tradingagents.rag.embeddings.torch')
    def test_初始化_成功(self, mock_torch, mock_automodel, mock_autotokenizer):
        """测试初始化成功"""
        mock_tokenizer = Mock()
        mock_autotokenizer.from_pretrained.return_value = mock_tokenizer

        mock_model = Mock()
        mock_model.config.hidden_size = 768
        mock_model.eval = Mock()
        mock_model.to = Mock()
        mock_automodel.from_pretrained.return_value = mock_model

        mock_torch.device = Mock(return_value="cpu")
        mock_torch.cuda.is_available.return_value = False

        from tradingagents.rag.embeddings import HuggingFaceEmbedding
        model = HuggingFaceEmbedding(model_name="test-model")
        assert model._dimension == 768

    @patch.dict('sys.modules', {'transformers': None, 'torch': None})
    def test_初始化_导入失败(self):
        """测试导入失败时抛出异常"""
        # 重新导入以触发异常
        import importlib
        import tradingagents.rag.embeddings
        importlib.reload(tradingagents.rag.embeddings)

        from tradingagents.rag.embeddings import HuggingFaceEmbedding
        with pytest.raises(ImportError) as exc_info:
            HuggingFaceEmbedding()
        assert "transformers" in str(exc_info.value) or "torch" in str(exc_info.value)


class TestGetEmbeddingModel:
    """get_embedding_model 便捷函数测试"""

    def test_获取_dummy模型(self):
        """测试获取dummy模型"""
        model = get_embedding_model('dummy', dimension=128)
        assert isinstance(model, DummyEmbedding)
        assert model.dimension == 128

    def test_获取_unknown模型_使用_dummy(self):
        """测试获取未知模型时使用dummy"""
        model = get_embedding_model('unknown_model')
        assert isinstance(model, DummyEmbedding)

    @patch.dict('sys.modules', {'sentence_transformers': None})
    def test_获取_sentence_transformers_导入失败_使用_dummy(self):
        """测试sentence-transformers不可用时使用dummy"""
        model = get_embedding_model('sentence-transformers')
        # 由于依赖缺失，应该使用dummy
        assert isinstance(model, DummyEmbedding)
