# -*- coding: utf-8 -*-
"""
图表导出器
"""
import io
from abc import ABC, abstractmethod

import matplotlib.pyplot as plt


class BaseExporter(ABC):
    """导出器基类"""
    
    @abstractmethod
    def export(self, figure: plt.Figure) -> bytes:
        pass


class PNGExporter(BaseExporter):
    """PNG 导出器"""
    
    def export(self, figure: plt.Figure) -> bytes:
        buf = io.BytesIO()
        figure.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
        buf.seek(0)
        plt.close(figure)
        return buf.getvalue()


class SVGExporter(BaseExporter):
    """SVG 导出器"""
    
    def export(self, figure: plt.Figure) -> bytes:
        buf = io.BytesIO()
        figure.savefig(buf, format="svg", bbox_inches="tight")
        buf.seek(0)
        plt.close(figure)
        return buf.getvalue()


class PDFExporter(BaseExporter):
    """PDF 导出器"""
    
    def export(self, figure: plt.Figure) -> bytes:
        buf = io.BytesIO()
        figure.savefig(buf, format="pdf", bbox_inches="tight")
        buf.seek(0)
        plt.close(figure)
        return buf.getvalue()
