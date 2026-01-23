"""
FastAPI 应用入口

提供 RESTful API 接口，定义 MCP Server Hook。

2026年1月 - GetPic 解耦式智能图表参数提取引擎
"""
import logging
from contextlib import asynccontextmanager
from typing import Literal
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

from core.config import get_settings
from core.orchestrator import ChartExtractOrchestrator, OrchestrationError, ExtractionResult
from schema.chart_standard import ChartStandard, get_chart_json_schema
from mcp_modules.img_processor import mcp_server as img_processor_mcp
from mcp_modules.vision_agent import mcp_server as vision_agent_mcp


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# MCP Server Hook - 主服务聚合
mcp_server = FastMCP("getpic-core")

# 注册子模块的 MCP Tools
mcp_server.include_router(img_processor_mcp)
mcp_server.include_router(vision_agent_mcp)


# ============== 响应模型 ==============

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(description="服务状态")
    version: str = Field(description="版本号")
    vlm_provider: str = Field(description="当前 VLM 提供商")


class ExtractionResponse(BaseModel):
    """提取结果响应"""
    success: bool = Field(description="是否成功")
    data: ChartStandard | None = Field(default=None, description="标准化图表数据")
    echarts_option: dict | None = Field(default=None, description="ECharts 配置")
    highcharts_option: dict | None = Field(default=None, description="Highcharts 配置")
    chartjs_config: dict | None = Field(default=None, description="Chart.js 配置")
    error: str | None = Field(default=None, description="错误信息")


class DetailedExtractionResponse(BaseModel):
    """详细提取结果响应（含元数据）"""
    success: bool
    data: ChartStandard | None = None
    metadata: dict | None = None
    echarts_option: dict | None = None
    error: str | None = None


class ConvertResponse(BaseModel):
    """格式转换响应"""
    success: bool
    option: dict


class SchemaResponse(BaseModel):
    """Schema 响应"""
    schema_: dict = Field(alias="schema")


# ============== 应用生命周期 ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()
    logger.info(f"🚀 GetPic starting in {settings.app_env} mode")
    logger.info(f"📡 VLM Provider: {settings.vlm_provider} ({settings.vlm_model})")
    yield
    logger.info("👋 GetPic shutting down")


# ============== 创建应用 ==============

app = FastAPI(
    title="GetPic",
    description="解耦式智能图表参数提取引擎，基于 MCP 协议架构",
    version="0.1.0",
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

# 编排器实例
orchestrator = ChartExtractOrchestrator()

# 支持的文件类型
ALLOWED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
    "image/bmp",
    "image/tiff",
}


# ============== API 端点 ==============

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    健康检查端点
    
    返回服务状态和配置信息。
    """
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        vlm_provider=settings.vlm_provider,
    )


@app.get("/api/v1/schema", response_model=SchemaResponse, tags=["Schema"])
async def get_schema():
    """
    获取 ChartStandard JSON Schema
    
    返回标准化图表数据的 JSON Schema 定义，
    可用于前端验证或 VLM Structured Outputs 配置。
    """
    return SchemaResponse(schema=get_chart_json_schema())


@app.post("/api/v1/extract/image", response_model=ExtractionResponse, tags=["Extraction"])
async def extract_from_image(
    file: UploadFile = File(..., description="图表图像文件"),
    hinting_text: str | None = Query(None, description="辅助提示文本，帮助模型理解上下文"),
    include_echarts: bool = Query(True, description="是否包含 ECharts 配置"),
    include_highcharts: bool = Query(False, description="是否包含 Highcharts 配置"),
    include_chartjs: bool = Query(False, description="是否包含 Chart.js 配置"),
    skip_preprocessing: bool = Query(False, description="是否跳过图像预处理"),
):
    """
    从图像提取图表数据
    
    上传图表图像，返回结构化的图表参数数据。
    可选返回多种前端框架的配置格式。
    
    **处理流程：**
    1. 图像预处理（归一化、压缩、去EXIF）
    2. VLM 图表识别（GPT-5o / Claude 4.5 / Gemini 2.0）
    3. 数据验证（Pydantic Schema）
    4. 格式转换（ECharts / Highcharts / Chart.js）
    
    **支持的图像格式：** PNG, JPEG, WebP, GIF, BMP, TIFF
    """
    # 验证文件类型
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}。支持: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )
    
    try:
        # 读取图像数据
        image_bytes = await file.read()
        logger.info(f"收到图像: {file.filename}, 大小: {len(image_bytes)} bytes")
        
        # 执行提取流程
        chart_data = await orchestrator.process_image(
            image_bytes,
            hinting_text,
            skip_preprocessing,
        )
        
        # 构建响应
        response = ExtractionResponse(success=True, data=chart_data)
        
        # 可选：转换为各种前端框架格式
        if include_echarts:
            response.echarts_option = orchestrator.to_echarts_option(chart_data)
        if include_highcharts:
            response.highcharts_option = orchestrator.to_highcharts_option(chart_data)
        if include_chartjs:
            response.chartjs_config = orchestrator.to_chartjs_config(chart_data)
        
        logger.info(f"提取成功: {chart_data.chart_type}, 系列数: {len(chart_data.series)}")
        return response
        
    except OrchestrationError as e:
        logger.error(f"提取失败: {e}")
        return ExtractionResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception(f"未知错误: {e}")
        return ExtractionResponse(success=False, error=f"服务器内部错误: {str(e)}")


@app.post("/api/v1/extract/image/detailed", response_model=DetailedExtractionResponse, tags=["Extraction"])
async def extract_from_image_detailed(
    file: UploadFile = File(..., description="图表图像文件"),
    hinting_text: str | None = Query(None, description="辅助提示文本"),
):
    """
    从图像提取图表数据（详细模式）
    
    返回包含处理元数据的详细结果，用于调试和分析。
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file.content_type}")
    
    try:
        image_bytes = await file.read()
        
        result = await orchestrator.process_image(
            image_bytes,
            hinting_text,
            skip_preprocessing=False,
            collect_metadata=True,
        )
        
        if isinstance(result, ExtractionResult):
            return DetailedExtractionResponse(
                success=True,
                data=result.chart,
                metadata=result.metadata.model_dump(),
                echarts_option=orchestrator.to_echarts_option(result.chart),
            )
        else:
            return DetailedExtractionResponse(
                success=True,
                data=result,
                echarts_option=orchestrator.to_echarts_option(result),
            )
        
    except OrchestrationError as e:
        return DetailedExtractionResponse(success=False, error=str(e))
    except Exception as e:
        return DetailedExtractionResponse(success=False, error=str(e))


@app.post("/api/v1/convert/echarts", response_model=ConvertResponse, tags=["Conversion"])
async def convert_to_echarts(chart: ChartStandard):
    """
    将标准图表数据转换为 ECharts 配置
    
    接收 ChartStandard 格式数据，返回 ECharts option 配置。
    """
    try:
        echarts_option = orchestrator.to_echarts_option(chart)
        return ConvertResponse(success=True, option=echarts_option)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/convert/highcharts", response_model=ConvertResponse, tags=["Conversion"])
async def convert_to_highcharts(chart: ChartStandard):
    """
    将标准图表数据转换为 Highcharts 配置
    
    接收 ChartStandard 格式数据，返回 Highcharts options 配置。
    """
    try:
        highcharts_option = orchestrator.to_highcharts_option(chart)
        return ConvertResponse(success=True, option=highcharts_option)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/convert/chartjs", response_model=ConvertResponse, tags=["Conversion"])
async def convert_to_chartjs(chart: ChartStandard):
    """
    将标准图表数据转换为 Chart.js 配置
    
    接收 ChartStandard 格式数据，返回 Chart.js config 配置。
    """
    try:
        chartjs_config = orchestrator.to_chartjs_config(chart)
        return ConvertResponse(success=True, option=chartjs_config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== 开发模式启动 ==============

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "core.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
