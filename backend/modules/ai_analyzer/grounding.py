# -*- coding: utf-8 -*-
"""
Google Search Grounding

使用 Gemini 的 Google Search Grounding 功能获取最新信息
"""
from typing import List

import google.generativeai as genai

from backend.core.config import settings
from .schemas import SearchResult

# 配置 Gemini
genai.configure(api_key=settings.google_api_key)


class GoogleSearchGrounding:
    """Google Search Grounding"""
    
    def __init__(self):
        # 使用支持 grounding 的模型
        self.model = genai.GenerativeModel(
            settings.google_model,
            tools="google_search_retrieval",
        )
    
    async def search(
        self,
        data_type: str,
        keywords: List[str],
    ) -> List[SearchResult]:
        """
        搜索相关科研信息
        
        Args:
            data_type: 数据类型
            keywords: 关键词列表
            
        Returns:
            List[SearchResult]: 搜索结果
        """
        query = f"{data_type} analysis {' '.join(keywords[:5])} scientific research"
        
        try:
            response = self.model.generate_content(
                f"Search for recent scientific papers and analysis guides about: {query}. "
                f"Summarize the most relevant findings for {data_type} data analysis."
            )
            
            # 解析 grounding 结果
            # 注意：实际的 grounding 响应格式可能需要根据 API 更新调整
            results = []
            
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata'):
                    for chunk in getattr(candidate.grounding_metadata, 'grounding_chunks', []):
                        results.append(SearchResult(
                            title=getattr(chunk, 'title', 'Reference'),
                            snippet=getattr(chunk, 'chunk', '')[:200],
                            url=getattr(chunk, 'uri', ''),
                        ))
            
            # 如果没有 grounding 结果，使用响应文本
            if not results and response.text:
                results.append(SearchResult(
                    title="AI Search Summary",
                    snippet=response.text[:500],
                    url="",
                ))
            
            return results
            
        except Exception as e:
            # Grounding 可能不可用，返回空结果
            return []
