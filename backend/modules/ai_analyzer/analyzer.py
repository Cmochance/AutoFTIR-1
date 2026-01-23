# -*- coding: utf-8 -*-
"""
AI 分析器

使用 Gemini 进行图像分析
"""
import base64
import json
from typing import Optional

import google.generativeai as genai

from backend.core.config import settings
from backend.modules.chart_renderer.schemas import ChartMetadata
from .schemas import AnalysisReport, GroundingContext
from .prompts import load_prompt

# 配置 Gemini
genai.configure(api_key=settings.google_api_key)


class Analyzer:
    """AI 分析器"""
    
    def __init__(self):
        self.model = genai.GenerativeModel(settings.google_model)
    
    async def analyze(
        self,
        image_bytes: bytes,
        metadata: ChartMetadata,
        context: Optional[GroundingContext] = None,
    ) -> AnalysisReport:
        """
        分析图表
        
        Args:
            image_bytes: 图像字节
            metadata: 图表元数据
            context: 知识增强上下文
            
        Returns:
            AnalysisReport: 分析报告
        """
        # 加载提示词模板
        prompt_template = load_prompt(metadata.data_type)
        
        # 构建提示词
        prompt = prompt_template.format(
            data_type=metadata.data_type,
            chart_type=metadata.chart_type,
            peaks=json.dumps(metadata.peaks, ensure_ascii=False),
            statistics=json.dumps(metadata.statistics, ensure_ascii=False),
            grounding_context=context.to_prompt_context() if context else "无额外参考资料",
        )
        
        # 添加输出格式要求
        prompt += """

## 输出格式
请以 JSON 格式返回分析结果：
{
    "summary": "概述（100-200字）",
    "key_findings": ["发现1", "发现2", ...],
    "peak_assignments": [
        {"position": "位置", "assignment": "归属", "confidence": "高/中/低"}
    ],
    "suggestions": ["建议1", "建议2", ...],
    "references": ["参考来源1", ...],
    "confidence": 0.0-1.0
}

只输出 JSON，不要有其他文字。
"""
        
        # 准备图像
        image_part = {
            "mime_type": "image/png",
            "data": base64.b64encode(image_bytes).decode("utf-8"),
        }
        
        # 调用 Gemini
        response = self.model.generate_content([prompt, image_part])
        
        # 解析响应
        try:
            result_text = response.text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1]
                result_text = result_text.rsplit("```", 1)[0]
            
            result_dict = json.loads(result_text)
            
            return AnalysisReport(
                summary=result_dict.get("summary", ""),
                key_findings=result_dict.get("key_findings", []),
                peak_assignments=result_dict.get("peak_assignments", []),
                suggestions=result_dict.get("suggestions", []),
                references=result_dict.get("references", []),
                confidence=float(result_dict.get("confidence", 0.8)),
            )
        except Exception as e:
            # 回退：直接返回原始响应
            return AnalysisReport(
                summary=response.text[:500] if response.text else "分析失败",
                key_findings=[],
                peak_assignments=[],
                suggestions=["请检查数据质量后重试"],
                references=[],
                confidence=0.3,
            )
