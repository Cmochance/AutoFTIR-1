"""
视觉分析 MCP Tool

暴露为 MCP Tool: `analyze_chart_image`
核心图表识别能力，调用 VLM 提取结构化数据。

2026年1月 - 端到端 VLM 方案
"""
from typing import Annotated
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

from schema.chart_standard import ChartStandard
from .vlm_client import (
    get_vlm_client,
    VLMClientError,
    VLMConnectionError,
    VLMResponseError,
    VLMRateLimitError,
)


# 创建 MCP Server 实例
mcp_server = FastMCP("vision_agent")


class ChartExtractionError(Exception):
    """图表提取异常"""
    pass


class ExtractionResult(BaseModel):
    """提取结果（带元数据）"""
    chart: ChartStandard = Field(description="提取的图表数据")
    provider: str = Field(description="使用的 VLM 提供商")
    model: str = Field(description="使用的模型")


@mcp_server.tool()
async def analyze_chart_image(
    image_bytes: Annotated[bytes, Field(description="预处理后的图像字节数据")],
    hinting_text: Annotated[str | None, Field(description="辅助提示文本，帮助模型理解上下文")] = None,
    detect_dual_axis: Annotated[bool, Field(description="是否自动检测双Y轴")] = True,
) -> ChartStandard:
    """
    图表数据提取
    
    MCP Tool: analyze_chart_image
    
    使用 VLM（GPT-5o / Claude 4.5 / Gemini 2.0 Pro）分析图表图像，
    提取结构化的图表参数数据。
    
    特性：
    - 端到端 VLM 方案，无需传统 OCR
    - 支持数值估算（当数值未标注时）
    - 自动检测双Y轴图表
    - 自动重试机制
    
    Args:
        image_bytes: 预处理后的图像字节数据（建议使用 normalize_image 处理）
        hinting_text: 可选的辅助提示文本，帮助模型理解上下文
            例如："This is a quarterly sales report" 或 "单位是万元"
        detect_dual_axis: 是否自动检测双Y轴，默认 True
        
    Returns:
        ChartStandard: 标准化的图表数据结构
        
    Raises:
        ChartExtractionError: 提取失败
        
    Example:
        >>> result = await analyze_chart_image(
        ...     image_bytes=processed_image,
        ...     hinting_text="2026年Q1销售数据",
        ... )
        >>> print(result.chart_type)
        >>> print(result.series[0].data)
    """
    try:
        client = get_vlm_client()
        result = await client.extract_chart(
            image_bytes,
            hinting_text,
            detect_dual_axis,
        )
        return result
    except VLMConnectionError as e:
        raise ChartExtractionError(f"VLM 连接失败: {str(e)}") from e
    except VLMRateLimitError as e:
        raise ChartExtractionError(f"VLM 速率限制，请稍后重试: {str(e)}") from e
    except VLMResponseError as e:
        raise ChartExtractionError(f"VLM 响应异常: {str(e)}") from e
    except VLMClientError as e:
        raise ChartExtractionError(f"VLM 调用失败: {str(e)}") from e
    except Exception as e:
        raise ChartExtractionError(f"图表提取失败: {str(e)}") from e


@mcp_server.tool()
async def analyze_chart_image_with_provider(
    image_bytes: Annotated[bytes, Field(description="图像字节数据")],
    provider: Annotated[str, Field(description="VLM 提供商: openai/anthropic/gemini")],
    hinting_text: Annotated[str | None, Field(description="辅助提示文本")] = None,
) -> ExtractionResult:
    """
    使用指定提供商提取图表数据
    
    MCP Tool: analyze_chart_image_with_provider
    
    允许指定使用哪个 VLM 提供商进行提取，用于：
    - A/B 测试不同模型的效果
    - 特定场景下选择最优模型
    - 故障转移
    
    Args:
        image_bytes: 图像字节数据
        provider: VLM 提供商 (openai/anthropic/gemini)
        hinting_text: 辅助提示文本
        
    Returns:
        ExtractionResult: 包含图表数据和使用的模型信息
    """
    try:
        client = get_vlm_client(provider)
        chart = await client.extract_chart(image_bytes, hinting_text)
        return ExtractionResult(
            chart=chart,
            provider=provider,
            model=client.model,
        )
    except VLMClientError as e:
        raise ChartExtractionError(f"VLM 调用失败 ({provider}): {str(e)}") from e
    except Exception as e:
        raise ChartExtractionError(f"图表提取失败: {str(e)}") from e


@mcp_server.tool()
async def batch_analyze_charts(
    images: Annotated[list[bytes], Field(description="图像字节数据列表")],
    hinting_text: Annotated[str | None, Field(description="共享的辅助提示文本")] = None,
) -> list[ChartStandard | None]:
    """
    批量提取多个图表
    
    MCP Tool: batch_analyze_charts
    
    并发处理多个图表图像，提高批量处理效率。
    失败的图表返回 None，不影响其他图表的处理。
    
    Args:
        images: 图像字节数据列表
        hinting_text: 共享的辅助提示文本
        
    Returns:
        list[ChartStandard | None]: 提取结果列表，失败项为 None
    """
    import asyncio
    
    async def extract_one(image_bytes: bytes) -> ChartStandard | None:
        try:
            client = get_vlm_client()
            return await client.extract_chart(image_bytes, hinting_text)
        except Exception:
            return None
    
    results = await asyncio.gather(*[extract_one(img) for img in images])
    return list(results)
