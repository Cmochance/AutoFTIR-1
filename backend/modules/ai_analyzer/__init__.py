# -*- coding: utf-8 -*-
"""
模块3: AI 深度分析

职责: 接收图像+元数据 → 结合知识库 → 生成专业分析报告
"""
from .analyzer import Analyzer
from .grounding import GoogleSearchGrounding
from .knowledge import KnowledgeRetriever
from .schemas import AnalysisReport, GroundingContext

__all__ = [
    "Analyzer",
    "GoogleSearchGrounding",
    "KnowledgeRetriever", 
    "AnalysisReport",
    "GroundingContext",
]

# 便捷入口
class AIAnalyzer:
    """AI 分析器门面类"""
    
    def __init__(self):
        self.analyzer = Analyzer()
        self.grounding = GoogleSearchGrounding()
        self.knowledge = KnowledgeRetriever()
    
    async def analyze(
        self,
        chart_output,
        use_grounding: bool = True,
        use_knowledge: bool = True,
    ) -> AnalysisReport:
        """
        AI 深度分析
        
        Args:
            chart_output: 图表输出（含图像和元数据）
            use_grounding: 是否使用 Google Search Grounding
            use_knowledge: 是否使用向量知识库
            
        Returns:
            AnalysisReport: 分析报告
        """
        # 1. 收集上下文
        context = GroundingContext()
        
        if use_grounding:
            search_context = await self.grounding.search(
                data_type=chart_output.metadata.data_type,
                keywords=chart_output.metadata.get_keywords(),
            )
            context.add_search_results(search_context)
        
        if use_knowledge:
            knowledge_context = await self.knowledge.retrieve(
                data_type=chart_output.metadata.data_type,
                embedding_text=chart_output.metadata.to_embedding_text(),
            )
            context.add_knowledge(knowledge_context)
        
        # 2. 调用 AI 分析
        report = await self.analyzer.analyze(
            image_bytes=chart_output.image_bytes,
            metadata=chart_output.metadata,
            context=context,
        )
        
        return report
