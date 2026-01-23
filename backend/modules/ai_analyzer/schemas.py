# -*- coding: utf-8 -*-
"""
AI 分析模块 Schema 定义
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    snippet: str
    url: str


@dataclass
class KnowledgeChunk:
    """知识片段"""
    content: str
    source: str
    similarity: float


@dataclass
class GroundingContext:
    """知识增强上下文"""
    search_results: List[SearchResult] = field(default_factory=list)
    knowledge_chunks: List[KnowledgeChunk] = field(default_factory=list)
    
    def add_search_results(self, results: List[SearchResult]):
        self.search_results.extend(results)
    
    def add_knowledge(self, chunks: List[KnowledgeChunk]):
        self.knowledge_chunks.extend(chunks)
    
    def to_prompt_context(self) -> str:
        """转换为提示词上下文"""
        parts = []
        
        if self.search_results:
            parts.append("## 来自网络搜索的参考资料")
            for i, result in enumerate(self.search_results[:5], 1):
                parts.append(f"{i}. **{result.title}**")
                parts.append(f"   {result.snippet}")
                parts.append(f"   来源: {result.url}")
                parts.append("")
        
        if self.knowledge_chunks:
            parts.append("## 来自知识库的参考资料")
            for i, chunk in enumerate(self.knowledge_chunks[:5], 1):
                parts.append(f"{i}. {chunk.content[:200]}...")
                parts.append(f"   来源: {chunk.source}")
                parts.append("")
        
        return "\n".join(parts)


@dataclass
class AnalysisReport:
    """分析报告"""
    summary: str
    key_findings: List[str]
    peak_assignments: List[Dict[str, Any]]
    suggestions: List[str]
    references: List[str]
    confidence: float = 0.8
    
    def to_markdown(self) -> str:
        """转换为 Markdown"""
        parts = [
            "# 分析报告",
            "",
            "## 概述",
            self.summary,
            "",
            "## 关键发现",
        ]
        
        for finding in self.key_findings:
            parts.append(f"- {finding}")
        
        if self.peak_assignments:
            parts.append("")
            parts.append("## 峰归属")
            parts.append("| 位置 | 归属 | 置信度 |")
            parts.append("|------|------|--------|")
            for assignment in self.peak_assignments:
                parts.append(
                    f"| {assignment.get('position', '')} | "
                    f"{assignment.get('assignment', '')} | "
                    f"{assignment.get('confidence', '')} |"
                )
        
        parts.append("")
        parts.append("## 建议")
        for suggestion in self.suggestions:
            parts.append(f"- {suggestion}")
        
        if self.references:
            parts.append("")
            parts.append("## 参考来源")
            for ref in self.references:
                parts.append(f"- {ref}")
        
        return "\n".join(parts)
