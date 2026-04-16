"""
ChromaDB Schema Retriever 实现

使用 ChromaDB 作为向量数据库的 SchemaRetriever 实现。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import chromadb

from app.config.settings import get_settings


class ChromaSchemaRetriever:
    """ChromaDB 向量检索实现"""
    
    def __init__(self, embedding: Optional[Any] = None):
        """
        初始化 ChromaDB 检索器
        
        Args:
            embedding: embedding 函数（暂不强制使用，保持现有 ChromaDB 内嵌 embedding）
        """
        settings = get_settings()
        self._client = chromadb.PersistentClient(
            path=str(Path(settings.vector_db_path) / "schema_store")
        )
        self._collection = self._client.get_collection("schema_docs")
        self._embedding = embedding
    
    def retrieve(self, question: str, limit: int = 4) -> str:
        """
        检索与问题相关的 schema 片段
        
        Args:
            question: 用户问题
            limit: 返回的最大片段数
            
        Returns:
            str: 拼接的 schema 上下文字符串
        """
        result = self._collection.query(
            query_texts=[question],
            n_results=limit,
            include=["documents"]
        )
        documents = (result.get("documents") or [[]])[0]
        if documents:
            return "\n\n".join(documents)
        return ""
    
    def ingest(self, documents: list[dict]) -> None:
        """
        批量写入向量库
        
        Args:
            documents: [{"document": str, "metadata": dict}, ...]
        """
        texts = [d["document"] for d in documents]
        metadatas = [d.get("metadata", {}) for d in documents]
        self._collection.add_texts(texts=texts, metadatas=metadatas)
