# -*- coding: utf-8 -*-
"""
图表渲染引擎
"""
import io
from typing import Tuple

import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
import numpy as np

from backend.modules.data_processor.schemas import ProcessedData
from .schemas import ChartMetadata, ChartStyle
from .styles import get_style


class RenderEngine:
    """图表渲染引擎"""
    
    async def render(
        self,
        data: ProcessedData,
        style_name: str = "scientific",
    ) -> Tuple[plt.Figure, ChartMetadata]:
        """
        渲染图表
        
        Args:
            data: 处理后的数据
            style_name: 样式名称
            
        Returns:
            (Figure, ChartMetadata): 图表和元数据
        """
        style = get_style(style_name)
        
        # 创建图表
        fig, ax = plt.subplots(figsize=style.figure_size, dpi=style.dpi)
        
        # 应用样式
        self._apply_style(ax, style)
        
        # 绑制数据
        x, y = data.x.values, data.y.values
        ax.plot(x, y, linewidth=style.line_width, color=style.colors[0])
        
        # 标记峰
        if data.peaks:
            for peak in data.peaks[:5]:
                pos = peak.get("position")
                intensity = peak.get("intensity")
                if pos is not None and intensity is not None:
                    ax.axvline(pos, color=style.colors[1], linestyle="--", alpha=0.5)
                    ax.annotate(
                        f"{pos:.1f}",
                        xy=(pos, intensity),
                        xytext=(0, 10),
                        textcoords="offset points",
                        ha="center",
                        fontsize=style.font_size - 2,
                        color=style.colors[1],
                    )
        
        # 设置标签
        xlabel = f"{data.x_label}"
        if data.x_unit:
            xlabel += f" ({data.x_unit})"
        ylabel = f"{data.y_label}"
        if data.y_unit:
            ylabel += f" ({data.y_unit})"
        
        ax.set_xlabel(xlabel, fontsize=style.font_size)
        ax.set_ylabel(ylabel, fontsize=style.font_size)
        
        # 标题
        title = data.source_name or data.data_type.value
        ax.set_title(title, fontsize=style.font_size + 2, fontweight="bold")
        
        # 网格
        if style.grid:
            ax.grid(True, alpha=style.grid_alpha)
        
        plt.tight_layout()
        
        # 构建元数据
        metadata = ChartMetadata(
            chart_type="line",
            data_type=data.data_type.value,
            x_label=data.x_label,
            y_label=data.y_label,
            x_unit=data.x_unit,
            y_unit=data.y_unit,
            title=title,
            peaks=data.peaks,
            statistics=data.statistics,
        )
        
        return fig, metadata
    
    def _apply_style(self, ax, style: ChartStyle):
        """应用样式到坐标轴"""
        ax.tick_params(labelsize=style.font_size - 1)
        for spine in ax.spines.values():
            spine.set_linewidth(0.5)
