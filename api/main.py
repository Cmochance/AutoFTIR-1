# -*- coding: utf-8 -*-
"""
AutoFTIR 统一后端 API

整合所有服务：
- AI 图像分析
- 图表参数提取
- 光谱数据处理

支持多种前端调用（Web/小程序/App）。
"""
from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from typing import Any, List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api.config import get_settings, DEFAULT_MODELS_ZHIPUAI, DEFAULT_MODELS_OPENAI
from api.services.ai_service import AIService
from api.services.chart_service import ChartService


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============== 响应模型 ==============

class HealthResponse(BaseModel):
    """健康检查响应"""
    ok: bool
    base_url: str
    has_api_key: bool
    ai_provider: str
    vlm_provider: str


class ModelsResponse(BaseModel):
    """模型列表响应"""
    base_url: str
    models: List[str]
    source: str = Field(description="remote|fallback")


class AnalyzeImageRequest(BaseModel):
    """图像分析请求"""
    model: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    image_base64: str = Field(min_length=1, description="纯 base64，不含 data:image/... 前缀")
    image_mime: str = Field(default="image/png")


class AnalyzeImageResponse(BaseModel):
    """图像分析响应"""
    text: str
    model: str


class ChartExtractionResponse(BaseModel):
    """图表提取响应"""
    success: bool
    data: Optional[dict] = None
    echarts_option: Optional[dict] = None
    highcharts_option: Optional[dict] = None
    chartjs_config: Optional[dict] = None
    error: Optional[str] = None


class ChartSchemaResponse(BaseModel):
    """图表 Schema 响应"""
    schema_: dict = Field(alias="schema")


# ============== 应用生命周期 ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()
    logger.info(f"🚀 AutoFTIR API starting in {settings.app_env} mode")
    logger.info(f"📡 AI Provider: {settings.ai_provider}")
    logger.info(f"🖼️ VLM Provider: {settings.vlm_provider}")
    yield
    logger.info("👋 AutoFTIR API shutting down")


# ============== 创建应用 ==============

app = FastAPI(
    title="AutoFTIR API",
    description="统一后端 API - AI 分析 / 图表提取 / 光谱处理",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 服务实例
ai_service = AIService()
chart_service = ChartService()


# ============== 系统端点 ==============

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
def health():
    """健康检查"""
    settings = get_settings()
    return HealthResponse(
        ok=True,
        base_url=settings.effective_ai_base_url,
        has_api_key=bool(settings.effective_ai_api_key),
        ai_provider=settings.ai_provider,
        vlm_provider=settings.vlm_provider,
    )


@app.get("/api/models", response_model=ModelsResponse, tags=["System"])
def list_models():
    """获取可用模型列表"""
    settings = get_settings()
    
    base_url = settings.effective_ai_base_url
    api_key = settings.effective_ai_api_key
    
    fallback_models = (
        DEFAULT_MODELS_OPENAI if settings.ai_provider == "openai_compat" 
        else DEFAULT_MODELS_ZHIPUAI
    )
    
    if not api_key:
        return ModelsResponse(base_url=base_url, models=fallback_models, source="fallback")
    
    # 尝试从远端获取模型列表
    try:
        models = ai_service.fetch_models_from_remote(base_url, api_key)
        if models:
            return ModelsResponse(base_url=base_url, models=sorted(set(models)), source="remote")
    except Exception:
        pass
    
    return ModelsResponse(base_url=base_url, models=fallback_models, source="fallback")


# ============== AI 分析端点 ==============

@app.post("/api/analyze-image", response_model=AnalyzeImageResponse, tags=["AI Analysis"])
def analyze_image(req: AnalyzeImageRequest):
    """
    AI 图像分析
    
    上传图像和提示词，返回 AI 分析结果。
    主要用于 FTIR 图谱分析。
    """
    try:
        text = ai_service.analyze_image(
            model=req.model,
            prompt=req.prompt,
            image_base64=req.image_base64,
            image_mime=req.image_mime,
        )
        return AnalyzeImageResponse(text=text, model=req.model)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI 调用失败：{e}")


# ============== 图表提取端点 ==============

@app.get("/api/v1/chart/schema", response_model=ChartSchemaResponse, tags=["Chart Extraction"])
async def get_chart_schema():
    """获取图表标准 JSON Schema"""
    schema = chart_service.get_schema()
    return ChartSchemaResponse(schema=schema)


@app.post("/api/v1/chart/extract", response_model=ChartExtractionResponse, tags=["Chart Extraction"])
async def extract_chart_from_image(
    file: UploadFile = File(..., description="图表图像文件"),
    hinting_text: Optional[str] = Query(None, description="辅助提示文本"),
    include_echarts: bool = Query(True, description="是否包含 ECharts 配置"),
    include_highcharts: bool = Query(False, description="是否包含 Highcharts 配置"),
    include_chartjs: bool = Query(False, description="是否包含 Chart.js 配置"),
    skip_preprocessing: bool = Query(False, description="是否跳过图像预处理"),
):
    """
    从图像提取图表数据
    
    上传图表图像，返回结构化的图表参数数据。
    可选返回多种前端框架的配置格式。
    """
    # 验证文件类型
    allowed_types = {"image/png", "image/jpeg", "image/webp", "image/gif", "image/bmp", "image/tiff"}
    if file.content_type not in allowed_types:
        return ChartExtractionResponse(
            success=False,
            error=f"不支持的文件类型: {file.content_type}"
        )
    
    try:
        image_bytes = await file.read()
        
        result = await chart_service.extract_from_image(
            image_bytes=image_bytes,
            hinting_text=hinting_text,
            skip_preprocessing=skip_preprocessing,
            include_echarts=include_echarts,
            include_highcharts=include_highcharts,
            include_chartjs=include_chartjs,
        )
        
        return ChartExtractionResponse(**result)
        
    except Exception as e:
        logger.exception(f"图表提取失败: {e}")
        return ChartExtractionResponse(success=False, error=str(e))


@app.post("/api/v1/chart/convert/echarts", tags=["Chart Extraction"])
async def convert_to_echarts(chart_data: dict):
    """将标准图表数据转换为 ECharts 配置"""
    try:
        option = chart_service.convert_to_echarts(chart_data)
        return {"success": True, "option": option}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/chart/convert/highcharts", tags=["Chart Extraction"])
async def convert_to_highcharts(chart_data: dict):
    """将标准图表数据转换为 Highcharts 配置"""
    try:
        option = chart_service.convert_to_highcharts(chart_data)
        return {"success": True, "option": option}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/chart/convert/chartjs", tags=["Chart Extraction"])
async def convert_to_chartjs(chart_data: dict):
    """将标准图表数据转换为 Chart.js 配置"""
    try:
        config = chart_service.convert_to_chartjs(chart_data)
        return {"success": True, "config": config}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== 开发模式启动 ==============

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
