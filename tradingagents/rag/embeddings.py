"""
文本嵌入模块
支持多种嵌入模型：Sentence-Transformers、OpenAI、HuggingFace
"""
from typing import List, Optional
import numpy as np


class EmbeddingModel:
    """嵌入模型基类"""
    
    def encode(self, texts: List[str]) -> List[np.ndarray]:
        """将文本编码为向量"""
        raise NotImplementedError
    
    @property
    def dimension(self) -> int:
        """返回向量维度"""
        raise NotImplementedError


class SentenceTransformerEmbedding(EmbeddingModel):
    """Sentence-Transformers 嵌入模型"""
    
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self._dimension = self.model.get_sentence_embedding_dimension()
        except ImportError:
            raise ImportError("请安装 sentence-transformers: pip install sentence-transformers")
    
    def encode(self, texts: List[str]) -> List[np.ndarray]:
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [emb for emb in embeddings]
    
    @property
    def dimension(self) -> int:
        return self._dimension


class OpenAIEmbedding(EmbeddingModel):
    """OpenAI Embedding 模型"""
    
    def __init__(self, model: str = "text-embedding-3-small", api_key: str = None, api_base: str = None):
        self.model = model
        self.api_key = api_key
        self.api_base = api_base or "https://api.openai.com/v1"
        
        # 获取维度
        self._dimension = 1536  # text-embedding-3-small
        if model == "text-embedding-3-large":
            self._dimension = 3072
    
    def encode(self, texts: List[str]) -> List[np.ndarray]:
        try:
            import openai
            import requests
            
            if self.api_key:
                openai.api_key = self.api_key
            
            # 使用 requests 直接调用
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            results = []
            # 批量处理（API 限制）
            batch_size = 100
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                
                response = requests.post(
                    f"{self.api_base}/embeddings",
                    headers=headers,
                    json={
                        "input": batch,
                        "model": self.model
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data['data']:
                        results.append(np.array(item['embedding']))
                else:
                    raise Exception(f"API 错误: {response.text}")
            
            return results
            
        except ImportError:
            raise ImportError("请安装 requests: pip install requests")
    
    @property
    def dimension(self) -> int:
        return self._dimension


class HuggingFaceEmbedding(EmbeddingModel):
    """HuggingFace 模型嵌入"""
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self.model.eval()
            self._dimension = self.model.config.hidden_size
            
            # 设备
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            
        except ImportError:
            raise ImportError("请安装 transformers: pip install transformers torch")
    
    def encode(self, texts: List[str]) -> List[np.ndarray]:
        import torch
        
        with torch.no_grad():
            inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            outputs = self.model(**inputs)
            
            # 使用 mean pooling
            attention_mask = inputs['attention_mask']
            token_embeddings = outputs.last_hidden_state
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            embeddings = (sum_embeddings / sum_mask).cpu().numpy()
        
        return [emb for emb in embeddings]
    
    @property
    def dimension(self) -> int:
        return self._dimension


class DummyEmbedding(EmbeddingModel):
    """虚拟嵌入（用于测试）"""
    
    def __init__(self, dimension: int = 768):
        self._dimension = dimension
    
    def encode(self, texts: List[str]) -> List[np.ndarray]:
        np.random.seed(42)
        return [np.random.randn(self._dimension) for _ in texts]
    
    @property
    def dimension(self) -> int:
        return self._dimension


def get_embedding_model(model_type: str = "sentence-transformers", **kwargs) -> EmbeddingModel:
    """获取嵌入模型实例
    
    Args:
        model_type: 模型类型 ('sentence-transformers', 'openai', 'huggingface', 'dummy')
        **kwargs: 模型参数
    
    Returns:
        嵌入模型实例
    """
    models = {
        'sentence-transformers': SentenceTransformerEmbedding,
        'openai': OpenAIEmbedding,
        'huggingface': HuggingFaceEmbedding,
        'dummy': DummyEmbedding,
    }
    
    if model_type not in models:
        print(f"未知模型类型 {model_type}，使用 dummy")
        model_type = 'dummy'
    
    return models[model_type](**kwargs)