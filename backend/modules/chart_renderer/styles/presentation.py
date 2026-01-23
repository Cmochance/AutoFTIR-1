# -*- coding: utf-8 -*-
"""
演示用图表样式
"""
from ..schemas import ChartStyle


class PresentationStyle(ChartStyle):
    """演示风格 - 大字体，高对比度"""
    
    def __init__(self):
        super().__init__(
            name="presentation",
            figure_size=(12, 8),
            dpi=100,
            font_family="sans-serif",
            font_size=16,
            line_width=2.5,
            colors=["#2563eb", "#dc2626", "#16a34a", "#ca8a04", "#9333ea"],
            grid=True,
            grid_alpha=0.4,
        )
