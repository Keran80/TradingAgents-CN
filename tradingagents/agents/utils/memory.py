import chromadb
from chromadb.config import Settings
from openai import OpenAI
from functools import lru_cache
from typing import Dict, Any, List, Tuple
import hashlib
import threading


# 模块级别的 Embedding 缓存（跨实例共享）
_embedding_cache: Dict[str, Tuple[str, List[float]]] = {}
_cache_lock = threading.Lock()


class FinancialSituationMemory:
    def __init__(self, name, config):
        if config["backend_url"] == "http://localhost:11434/v1":
            self.embedding = "nomic-embed-text"
        else:
            self.embedding = "text-embedding-3-small"
        self.client = OpenAI(base_url=config["backend_url"])
        self.chroma_client = chromadb.Client(Settings(allow_reset=True))
        self.situation_collection = self.chroma_client.create_collection(name=name)
        self._embedding_cache: Dict[str, List[float]] = {}

    def _get_cache_key(self, text: str) -> str:
        """生成缓存键（使用文本哈希）"""
        return hashlib.md5(text.encode()).hexdigest()

    def get_embedding(self, text: str) -> List[float]:
        """Get OpenAI embedding for a text (带缓存)"""
        
        cache_key = self._get_cache_key(text)
        
        # 先检查实例缓存
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        # 再检查全局缓存
        global_key = f"{self.embedding}:{cache_key}"
        with _cache_lock:
            if global_key in _embedding_cache:
                cached_embedding = _embedding_cache[global_key][1]
                self._embedding_cache[cache_key] = cached_embedding
                return cached_embedding
        
        # 调用 API 获取
        response = self.client.embeddings.create(
            model=self.embedding, input=text
        )
        embedding = response.data[0].embedding
        
        # 存入缓存
        self._embedding_cache[cache_key] = embedding
        with _cache_lock:
            _embedding_cache[global_key] = (self.embedding, embedding)
        
        return embedding

    @staticmethod
    def clear_embedding_cache():
        """清除所有 Embedding 缓存"""
        global _embedding_cache
        with _cache_lock:
            _embedding_cache.clear()

    def add_situations(self, situations_and_advice):
        """Add financial situations and their corresponding advice. Parameter is a list of tuples (situation, rec)"""

        situations = []
        advice = []
        ids = []
        embeddings = []

        offset = self.situation_collection.count()

        for i, (situation, recommendation) in enumerate(situations_and_advice):
            situations.append(situation)
            advice.append(recommendation)
            ids.append(str(offset + i))
            embeddings.append(self.get_embedding(situation))

        self.situation_collection.add(
            documents=situations,
            metadatas=[{"recommendation": rec} for rec in advice],
            embeddings=embeddings,
            ids=ids,
        )

    def get_memories(self, current_situation, n_matches=1):
        """Find matching recommendations using OpenAI embeddings"""
        query_embedding = self.get_embedding(current_situation)

        results = self.situation_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_matches,
            include=["metadatas", "documents", "distances"],
        )

        matched_results = []
        for i in range(len(results["documents"][0])):
            matched_results.append(
                {
                    "matched_situation": results["documents"][0][i],
                    "recommendation": results["metadatas"][0][i]["recommendation"],
                    "similarity_score": 1 - results["distances"][0][i],
                }
            )

        return matched_results


if __name__ == "__main__":
    # Example usage
    matcher = FinancialSituationMemory()

    # Example data
    example_data = [
        (
            "High inflation rate with rising interest rates and declining consumer spending",
            "Consider defensive sectors like consumer staples and utilities. Review fixed-income portfolio duration.",
        ),
        (
            "Tech sector showing high volatility with increasing institutional selling pressure",
            "Reduce exposure to high-growth tech stocks. Look for value opportunities in established tech companies with strong cash flows.",
        ),
        (
            "Strong dollar affecting emerging markets with increasing forex volatility",
            "Hedge currency exposure in international positions. Consider reducing allocation to emerging market debt.",
        ),
        (
            "Market showing signs of sector rotation with rising yields",
            "Rebalance portfolio to maintain target allocations. Consider increasing exposure to sectors benefiting from higher rates.",
        ),
    ]

    # Add the example situations and recommendations
    matcher.add_situations(example_data)

    # Example query
    current_situation = """
    Market showing increased volatility in tech sector, with institutional investors 
    reducing positions and rising interest rates affecting growth stock valuations
    """

    try:
        recommendations = matcher.get_memories(current_situation, n_matches=2)

        for i, rec in enumerate(recommendations, 1):
            print(f"\nMatch {i}:")
            print(f"Similarity Score: {rec['similarity_score']:.2f}")
            print(f"Matched Situation: {rec['matched_situation']}")
            print(f"Recommendation: {rec['recommendation']}")

    except Exception as e:
        print(f"Error during recommendation: {str(e)}")

