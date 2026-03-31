"""
RAG 注册表 - 管理向量存储和文档集合
"""
from typing import Optional, List, Dict, Any
import os
import pickle
from pathlib import Path


class RagRegistry:
    """RAG 注册表，管理多个知识库"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or "rag_data"
        self.collections: Dict[str, Any] = {}
        self._load_registry()
    
    def _load_registry(self):
        """加载注册表"""
        registry_file = os.path.join(self.base_dir, "registry.pkl")
        if os.path.exists(registry_file):
            try:
                with open(registry_file, 'rb') as f:
                    self.collections = pickle.load(f)
            except Exception:
                self.collections = {}
    
    def _save_registry(self):
        """保存注册表"""
        os.makedirs(self.base_dir, exist_ok=True)
        registry_file = os.path.join(self.base_dir, "registry.pkl")
        with open(registry_file, 'wb') as f:
            pickle.dump(self.collections, f)
    
    def create_collection(self, name: str, description: str = "", metadata: dict = None) -> bool:
        """创建新的知识库集合"""
        if name in self.collections:
            return False
        
        self.collections[name] = {
            'description': description,
            'metadata': metadata or {},
            'created_at': str(Path(name).stat().st_mtime) if os.path.exists(name) else None,
            'doc_count': 0
        }
        self._save_registry()
        return True
    
    def delete_collection(self, name: str) -> bool:
        """删除知识库集合"""
        if name not in self.collections:
            return False
        del self.collections[name]
        self._save_registry()
        return True
    
    def list_collections(self) -> List[str]:
        """列出所有知识库"""
        return list(self.collections.keys())
    
    def get_collection_info(self, name: str) -> Optional[dict]:
        """获取知识库信息"""
        return self.collections.get(name)
    
    def update_collection(self, name: str, **kwargs) -> bool:
        """更新知识库信息"""
        if name not in self.collections:
            return False
        self.collections[name].update(kwargs)
        self._save_registry()
        return True


# 全局注册表
_global_registry: Optional[RagRegistry] = None


def get_rag_registry(base_dir: str = None) -> RagRegistry:
    """获取全局 RAG 注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = RagRegistry(base_dir)
    return _global_registry


def create_knowledge_base(name: str, description: str = "", base_dir: str = None) -> bool:
    """创建知识库（便捷函数）"""
    registry = get_rag_registry(base_dir)
    return registry.create_collection(name, description)