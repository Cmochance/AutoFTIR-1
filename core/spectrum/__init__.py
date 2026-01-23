# -*- coding: utf-8 -*-
"""光谱数据处理模块"""
from .reader import SpectrumData, read_spectrum
from .peaks import PeakRange, extract_top_peaks, format_peaks_for_prompt
from .plotter import (
    render_plot_png_bytes,
    render_waterfall_png_bytes,
    build_code_template,
)

__all__ = [
    "SpectrumData",
    "read_spectrum",
    "PeakRange",
    "extract_top_peaks",
    "format_peaks_for_prompt",
    "render_plot_png_bytes",
    "render_waterfall_png_bytes",
    "build_code_template",
]
