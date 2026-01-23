# -*- coding: utf-8 -*-
"""
分析路由
"""
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Query, Depends

from backend.core.auth import get_current_user, User
from backend.modules import DataProcessor, ChartRenderer, AIAnalyzer

router = APIRouter()

# 模块实例
data_processor = DataProcessor()
chart_renderer = ChartRenderer()
ai_analyzer = AIAnalyzer()


@router.post("/process")
async def process_data(
    file: UploadFile = File(..., description="数据文件"),
    # user: User = Depends(get_current_user),  # 暂时禁用认证
):
    """
    处理上传的数据文件
    
    - 自动识别数据类型
    - 应用处理模板
    - 返回处理后的数据
    """
    file_bytes = await file.read()
    
    result = await data_processor.process(file_bytes, file.filename or "data.csv")
    
    return {
        "success": True,
        "data": result.to_dict(),
    }


@router.post("/render")
async def render_chart(
    file: UploadFile = File(..., description="数据文件"),
    style: str = Query("scientific", description="图表样式"),
    format: str = Query("png", description="输出格式"),
):
    """
    绑制图表
    
    - 处理数据
    - 生成图表
    - 返回图表图像
    """
    file_bytes = await file.read()
    
    # 1. 处理数据
    processed_data = await data_processor.process(file_bytes, file.filename or "data.csv")
    
    # 2. 绑制图表
    chart_output = await chart_renderer.render(processed_data, style, format)
    
    return {
        "success": True,
        "image_base64": chart_output.image_bytes.hex(),  # TODO: 改为 base64
        "metadata": chart_output.metadata.__dict__ if hasattr(chart_output.metadata, '__dict__') else {},
    }


@router.post("/full")
async def full_analysis(
    file: UploadFile = File(..., description="数据文件"),
    style: str = Query("scientific", description="图表样式"),
    use_grounding: bool = Query(True, description="是否使用 Google Search"),
    use_knowledge: bool = Query(True, description="是否使用知识库"),
):
    """
    完整分析流程
    
    1. 数据处理
    2. 图表绑制
    3. AI 深度分析
    """
    file_bytes = await file.read()
    
    # 1. 处理数据
    processed_data = await data_processor.process(file_bytes, file.filename or "data.csv")
    
    # 2. 绑制图表
    chart_output = await chart_renderer.render(processed_data, style, "png")
    
    # 3. AI 分析
    report = await ai_analyzer.analyze(chart_output, use_grounding, use_knowledge)
    
    return {
        "success": True,
        "processed_data": processed_data.to_dict(),
        "chart_metadata": chart_output.metadata.__dict__ if hasattr(chart_output.metadata, '__dict__') else {},
        "report": report.__dict__ if hasattr(report, '__dict__') else str(report),
    }
