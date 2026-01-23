# -*- coding: utf-8 -*-
"""
模块2: 图像绑定引擎

职责: 接收处理后数据 → 应用样式模板 → 生成科研图表 → 导出多格式
"""
from .engine import RenderEngine
from .exporters import PNGExporter, SVGExporter, PDFExporter
from .schemas import ChartOutput, ChartMetadata, ChartStyle

__all__ = [
    "RenderEngine",
    "PNGExporter", "SVGExporter", "PDFExporter",
    "ChartOutput", "ChartMetadata", "ChartStyle",
]

# 便捷入口
class ChartRenderer:
    """图表渲染器门面类"""
    
    def __init__(self):
        self.engine = RenderEngine()
        self.exporters = {
            "png": PNGExporter(),
            "svg": SVGExporter(),
            "pdf": PDFExporter(),
        }
    
    async def render(
        self,
        processed_data,
        style: str = "scientific",
        output_format: str = "png",
    ) -> ChartOutput:
        """
        渲染图表
        
        Args:
            processed_data: 处理后的数据
            style: 样式名称 (scientific/publication/presentation)
            output_format: 输出格式 (png/svg/pdf)
            
        Returns:
            ChartOutput: 图表输出
        """
        # 1. 使用引擎绑制图表
        figure, metadata = await self.engine.render(processed_data, style)
        
        # 2. 导出为指定格式
        exporter = self.exporters.get(output_format, self.exporters["png"])
        image_bytes = exporter.export(figure)
        
        return ChartOutput(
            image_bytes=image_bytes,
            image_format=output_format,
            metadata=metadata,
        )
