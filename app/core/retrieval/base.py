"""
Schema Retriever 接口定义

定义 SchemaRetriever Protocol，将 retrieval 从 ChromaDB 硬编码中解耦，
解锁多 embedding 对比。
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable, Optional
from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    """检索返回的片段"""
    content: str
    score: float
    metadata: dict


@runtime_checkable
class SchemaRetriever(Protocol):
    """Schema 检索的统一接口"""
    
    def retrieve(self, question: str, limit: int = 4) -> str:
        """
        返回 schema 上下文字符串（保持与现有 adapter 兼容）
        
        Args:
            question: 用户问题
            limit: 返回的最大片段数
            
        Returns:
            str: 拼接的 schema 上下文字符串
        """
        ...
    
    def ingest(self, documents: list[dict]) -> None:
        """
        批量写入向量库（建索引）
        
        Args:
            documents: [{"document": str, "metadata": dict}, ...]
        """
        ...
