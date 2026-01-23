# -*- coding: utf-8 -*-
"""
图表渲染模块 Schema 定义
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ChartStyle:
    """图表样式"""
    name: str
    figure_size: tuple = (10, 6)
    dpi: int = 150
    font_family: str = "serif"
    font_size: int = 12
    line_width: float = 1.5
    colors: List[str] = field(default_factory=lambda: ["#1a1a1a", "#c73e3a", "#3d5a5b", "#6b6b6b"])
    grid: bool = True
    grid_alpha: float = 0.3


@dataclass
class ChartMetadata:
    """图表元数据"""
    chart_type: str
    data_type: str
    x_label: str
    y_label: str
    title: str = ""
    x_unit: str = ""
    y_unit: str = ""
    peaks: List[Dict[str, Any]] = field(default_factory=list)
    statistics: Dict[str, float] = field(default_factory=dict)
    
    def get_keywords(self) -> List[str]:
        """获取关键词（用于 AI 分析）"""
        keywords = [self.data_type, self.chart_type]
        for peak in self.peaks[:5]:
            keywords.append(f"{peak.get('position', '')} {self.x_unit}")
        return keywords
    
    def to_embedding_text(self) -> str:
        """生成用于 embedding 的文本"""
        return f"{self.data_type} {self.chart_type} {self.title} peaks: {self.peaks}"


@dataclass
class ChartOutput:
    """图表输出"""
    image_bytes: bytes
    image_format: str
    metadata: ChartMetadata
