"""
MCP 协议接口定义

定义 MCP Tools 的标准接口和响应格式。
"""
from pydantic import BaseModel, Field
from typing import Any


class MCPToolResult(BaseModel):
    """MCP Tool 执行结果"""
    success: bool = Field(description="执行是否成功")
    data: Any | None = Field(default=None, description="返回数据")
    error: str | None = Field(default=None, description="错误信息")


class ImageProcessRequest(BaseModel):
    """图像处理请求"""
    image_data: bytes = Field(description="原始图像字节数据")
    max_dimension: int = Field(default=2048, description="最大尺寸限制")
    output_format: str = Field(default="WEBP", description="输出格式")


class ChartExtractRequest(BaseModel):
    """图表提取请求"""
    image_data: bytes = Field(description="处理后的图像数据")
    hinting_text: str | None = Field(default=None, description="辅助提示文本")
