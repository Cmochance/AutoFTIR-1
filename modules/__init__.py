# -*- coding: utf-8 -*-
"""
模块层（兼容性保留）

此模块保留用于向后兼容。
新代码请使用 core 模块。
"""
# 从 core 模块重新导出
from core.spectrum import (
    SpectrumData,
    read_spectrum,
    PeakRange,
    extract_top_peaks,
    format_peaks_for_prompt,
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
