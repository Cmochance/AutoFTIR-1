"""
图像预处理 MCP Tool

暴露为 MCP Tool: `normalize_image`
用于图像归一化处理，降低 Token 消耗并提高识别准确度。

2026年1月 - 使用最新库版本
"""
from io import BytesIO
from typing import Annotated
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

from .filters import resize_image, auto_contrast, strip_exif, convert_to_webp


# 创建 MCP Server 实例
mcp_server = FastMCP("img_processor")


# 支持的输入图像格式
SUPPORTED_INPUT_FORMATS = {"JPEG", "PNG", "GIF", "BMP", "TIFF", "WEBP", "ICO"}

# 支持的输出格式
SUPPORTED_OUTPUT_FORMATS = {"WEBP", "PNG", "JPEG"}


class ImageProcessingError(Exception):
    """图像处理异常"""
    pass


class InvalidImageError(ImageProcessingError):
    """无效图像文件异常"""
    pass


class UnsupportedFormatError(ImageProcessingError):
    """不支持的图像格式异常"""
    pass


class ImageInfo(BaseModel):
    """图像信息（用于调试和日志）"""
    original_format: str | None = Field(description="原始图像格式")
    original_size: tuple[int, int] = Field(description="原始尺寸 (width, height)")
    original_mode: str = Field(description="原始色彩模式")
    processed_size: tuple[int, int] = Field(description="处理后尺寸")
    output_format: str = Field(description="输出格式")
    output_bytes: int = Field(description="输出字节数")


class NormalizeResult(BaseModel):
    """归一化处理结果"""
    image_data: bytes = Field(description="处理后的图像字节数据")
    info: ImageInfo = Field(description="图像处理信息")


def _validate_image(image_bytes: bytes) -> Image.Image:
    """
    验证并加载图像
    
    Args:
        image_bytes: 图像字节数据
        
    Returns:
        PIL Image 对象
        
    Raises:
        InvalidImageError: 无效的图像文件
        UnsupportedFormatError: 不支持的图像格式
    """
    if not image_bytes:
        raise InvalidImageError("图像数据为空")
    
    if len(image_bytes) < 8:
        raise InvalidImageError("图像数据过小，无法识别")
    
    try:
        img = Image.open(BytesIO(image_bytes))
        img.verify()  # 验证图像完整性
        # verify() 后需要重新打开
        img = Image.open(BytesIO(image_bytes))
    except UnidentifiedImageError:
        raise InvalidImageError("无法识别的图像格式，请确保文件是有效的图像")
    except Exception as e:
        raise InvalidImageError(f"图像文件损坏或无效: {str(e)}")
    
    # 检查格式支持
    if img.format and img.format.upper() not in SUPPORTED_INPUT_FORMATS:
        raise UnsupportedFormatError(
            f"不支持的图像格式: {img.format}。"
            f"支持的格式: {', '.join(SUPPORTED_INPUT_FORMATS)}"
        )
    
    return img


@mcp_server.tool()
def normalize_image(
    image_bytes: Annotated[bytes, Field(description="原始图像字节数据")],
    max_dimension: Annotated[int, Field(default=2048, ge=100, le=4096, description="最大边长限制 (100-4096)")] = 2048,
    output_format: Annotated[str, Field(default="WEBP", description="输出格式: WEBP/PNG/JPEG")] = "WEBP",
    enhance_contrast: Annotated[bool, Field(default=True, description="是否增强对比度")] = True,
    quality: Annotated[int, Field(default=85, ge=1, le=100, description="压缩质量 (1-100)")] = 85,
) -> bytes:
    """
    图像归一化处理
    
    MCP Tool: normalize_image
    
    处理流程：
    1. 验证图像有效性
    2. 尺寸限制（降低 Token 消耗）
    3. 自动对比度增强（提高识别准确度）
    4. 移除 EXIF 元数据（隐私保护）
    5. 格式转换为 WEBP（更优的压缩/质量比）
    
    Args:
        image_bytes: 原始图像字节数据
        max_dimension: 最大边长限制，默认 2048px
        output_format: 输出格式，默认 WEBP
        enhance_contrast: 是否增强对比度
        quality: 压缩质量 (1-100)
        
    Returns:
        处理后的图像字节数据
        
    Raises:
        InvalidImageError: 无效的图像文件
        UnsupportedFormatError: 不支持的图像格式
        ImageProcessingError: 图像处理失败
    """
    # 验证输出格式
    output_format = output_format.upper()
    if output_format not in SUPPORTED_OUTPUT_FORMATS:
        raise UnsupportedFormatError(
            f"不支持的输出格式: {output_format}。"
            f"支持的格式: {', '.join(SUPPORTED_OUTPUT_FORMATS)}"
        )
    
    try:
        # 1. 验证并加载图像
        img = _validate_image(image_bytes)
        
        # 2. 尺寸调整
        img = resize_image(img, max_dimension)
        
        # 3. 对比度增强
        if enhance_contrast:
            img = auto_contrast(img)
        
        # 4. 移除 EXIF
        img = strip_exif(img)
        
        # 5. 格式转换
        if output_format == "WEBP":
            return convert_to_webp(img, quality)
        else:
            buffer = BytesIO()
            # 处理色彩模式
            if output_format == "JPEG" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(buffer, format=output_format, quality=quality)
            return buffer.getvalue()
            
    except (InvalidImageError, UnsupportedFormatError):
        raise
    except Exception as e:
        raise ImageProcessingError(f"图像处理失败: {str(e)}") from e


@mcp_server.tool()
def normalize_image_with_info(
    image_bytes: Annotated[bytes, Field(description="原始图像字节数据")],
    max_dimension: Annotated[int, Field(default=2048, ge=100, le=4096, description="最大边长限制")] = 2048,
    output_format: Annotated[str, Field(default="WEBP", description="输出格式")] = "WEBP",
    enhance_contrast: Annotated[bool, Field(default=True, description="是否增强对比度")] = True,
    quality: Annotated[int, Field(default=85, ge=1, le=100, description="压缩质量")] = 85,
) -> NormalizeResult:
    """
    图像归一化处理（带详细信息）
    
    MCP Tool: normalize_image_with_info
    
    与 normalize_image 相同的处理流程，但返回详细的处理信息，
    用于调试、日志记录和 Agent 决策。
    
    Returns:
        NormalizeResult: 包含处理后图像数据和详细信息
    """
    output_format = output_format.upper()
    if output_format not in SUPPORTED_OUTPUT_FORMATS:
        raise UnsupportedFormatError(f"不支持的输出格式: {output_format}")
    
    try:
        # 验证并加载图像
        img = _validate_image(image_bytes)
        
        # 记录原始信息
        original_format = img.format
        original_size = img.size
        original_mode = img.mode
        
        # 处理流程
        img = resize_image(img, max_dimension)
        if enhance_contrast:
            img = auto_contrast(img)
        img = strip_exif(img)
        
        processed_size = img.size
        
        # 格式转换
        if output_format == "WEBP":
            output_data = convert_to_webp(img, quality)
        else:
            buffer = BytesIO()
            if output_format == "JPEG" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(buffer, format=output_format, quality=quality)
            output_data = buffer.getvalue()
        
        return NormalizeResult(
            image_data=output_data,
            info=ImageInfo(
                original_format=original_format,
                original_size=original_size,
                original_mode=original_mode,
                processed_size=processed_size,
                output_format=output_format,
                output_bytes=len(output_data),
            )
        )
        
    except (InvalidImageError, UnsupportedFormatError):
        raise
    except Exception as e:
        raise ImageProcessingError(f"图像处理失败: {str(e)}") from e


@mcp_server.tool()
def get_image_info(
    image_bytes: Annotated[bytes, Field(description="图像字节数据")],
) -> dict:
    """
    获取图像基本信息
    
    MCP Tool: get_image_info
    
    用于 Agent 在处理前了解图像特征，辅助决策。
    
    Returns:
        dict: 图像信息字典
    """
    try:
        img = _validate_image(image_bytes)
        return {
            "format": img.format,
            "mode": img.mode,
            "size": img.size,
            "width": img.size[0],
            "height": img.size[1],
            "is_animated": getattr(img, "is_animated", False),
            "n_frames": getattr(img, "n_frames", 1),
        }
    except (InvalidImageError, UnsupportedFormatError):
        raise
    except Exception as e:
        raise ImageProcessingError(f"获取图像信息失败: {str(e)}") from e
