# -*- coding: utf-8 -*-
"""
向量知识库检索

使用 Supabase pgvector 存储和检索科研知识
"""
from typing import List

import google.generativeai as genai

from backend.core.config import settings
from backend.core.database import Database
from .schemas import KnowledgeChunk

# 配置 Gemini
genai.configure(api_key=settings.google_api_key)


class KnowledgeRetriever:
    """知识库检索器"""
    
    def __init__(self):
        self.embedding_model = settings.embedding_model
    
    async def retrieve(
        self,
        data_type: str,
        embedding_text: str,
        top_k: int = 5,
    ) -> List[KnowledgeChunk]:
        """
        检索相关知识
        
        Args:
            data_type: 数据类型
            embedding_text: 用于生成 embedding 的文本
            top_k: 返回数量
            
        Returns:
            List[KnowledgeChunk]: 知识片段
        """
        try:
            # 生成查询 embedding
            embedding = await self._get_embedding(embedding_text)
            
            # 查询向量数据库
            client = Database.get_client()
            
            # 使用 pgvector 的相似度搜索
            response = client.rpc(
                "match_knowledge",
                {
                    "query_embedding": embedding,
                    "match_threshold": 0.7,
                    "match_count": top_k,
                    "filter_data_type": data_type.split(".")[0],  # 使用大类过滤
                }
            ).execute()
            
            results = []
            for item in response.data or []:
                results.append(KnowledgeChunk(
                    content=item.get("content", ""),
                    source=item.get("metadata", {}).get("source", "知识库"),
                    similarity=item.get("similarity", 0),
                ))
            
            return results
            
        except Exception as e:
            # 知识库可能为空或不可用
            return []
    
    async def _get_embedding(self, text: str) -> List[float]:
        """生成文本 embedding"""
        result = genai.embed_content(
            model=self.embedding_model,
            content=text,
        )
        return result["embedding"]
    
    async def add_knowledge(
        self,
        content: str,
        metadata: dict,
    ) -> bool:
        """
        添加知识到数据库
        
        Args:
            content: 知识内容
            metadata: 元数据（来源、领域等）
            
        Returns:
            bool: 是否成功
        """
        try:
            embedding = await self._get_embedding(content)
            
            client = Database.get_client()
            client.table("knowledge_embeddings").insert({
                "content": content,
                "embedding": embedding,
                "metadata": metadata,
            }).execute()
            
            return True
        except Exception:
            return False
