# -*- coding: utf-8 -*-
"""
AutoFTIR 核心业务模块

完全解耦的业务逻辑层，不依赖任何 Web 框架。
"""
# 只导出 spectrum 相关功能
# getpic 作为独立模块在 modules/getpic 中
from .spectrum import (
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