# -*- coding: utf-8 -*-
"""
科研图表样式
"""
from ..schemas import ChartStyle


class ScientificStyle(ChartStyle):
    """科研风格"""
    
    def __init__(self):
        super().__init__(
            name="scientific",
            figure_size=(10, 6),
            dpi=150,
            font_family="serif",
            font_size=12,
            line_width=1.5,
            colors=["#1a1a1a", "#c73e3a", "#3d5a5b", "#6b6b6b", "#8a8a8a"],
            grid=True,
            grid_alpha=0.3,
        )
