"""
图像处理滤镜 - 高性能图像预处理

使用 Pillow 实现图像归一化、增强等操作。
"""
from io import BytesIO
from PIL import Image, ImageEnhance, ImageOps


def resize_image(img: Image.Image, max_dimension: int) -> Image.Image:
    """
    等比例缩放图像
    
    Args:
        img: PIL Image 对象
        max_dimension: 最大边长限制
        
    Returns:
        缩放后的图像
    """
    width, height = img.size
    if max(width, height) <= max_dimension:
        return img
    
    if width > height:
        new_width = max_dimension
        new_height = int(height * (max_dimension / width))
    else:
        new_height = max_dimension
        new_width = int(width * (max_dimension / height))
    
    return img.resize((new_width, new_height), Image.Resampling.LANCZOS)


def auto_contrast(img: Image.Image) -> Image.Image:
    """
    自动对比度增强
    
    Args:
        img: PIL Image 对象
        
    Returns:
        增强后的图像
    """
    if img.mode == "RGBA":
        # 保留 alpha 通道
        rgb = img.convert("RGB")
        enhanced = ImageOps.autocontrast(rgb, cutoff=1)
        enhanced.putalpha(img.split()[3])
        return enhanced
    return ImageOps.autocontrast(img, cutoff=1)


def strip_exif(img: Image.Image) -> Image.Image:
    """
    移除 EXIF 元数据（隐私保护）
    
    Args:
        img: PIL Image 对象
        
    Returns:
        无 EXIF 的图像
    """
    data = list(img.getdata())
    clean_img = Image.new(img.mode, img.size)
    clean_img.putdata(data)
    return clean_img


def convert_to_webp(img: Image.Image, quality: int = 85) -> bytes:
    """
    转换为 WEBP 格式
    
    Args:
        img: PIL Image 对象
        quality: 压缩质量 (1-100)
        
    Returns:
        WEBP 格式的字节数据
    """
    buffer = BytesIO()
    # 确保是 RGB 模式
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")
    
    img.save(buffer, format="WEBP", quality=quality)
    return buffer.getvalue()
