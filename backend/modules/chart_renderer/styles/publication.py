# -*- coding: utf-8 -*-
"""
期刊级图表样式
"""
from ..schemas import ChartStyle


class PublicationStyle(ChartStyle):
    """期刊级样式 - 高 DPI，黑白友好"""
    
    def __init__(self):
        super().__init__(
            name="publication",
            figure_size=(8, 6),
            dpi=300,
            font_family="serif",
            font_size=14,
            line_width=1.0,
            colors=["#000000", "#666666", "#999999", "#cccccc"],
            grid=False,
            grid_alpha=0.2,
        )
