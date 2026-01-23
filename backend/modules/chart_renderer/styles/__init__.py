# -*- coding: utf-8 -*-
"""
预设样式库

- scientific: 科研图表样式（默认）
- publication: 期刊级样式（高 DPI，特定字体）
- presentation: 演示用样式（大字体，高对比度）
"""
from .scientific import ScientificStyle
from .publication import PublicationStyle
from .presentation import PresentationStyle

STYLE_REGISTRY = {
    "scientific": ScientificStyle,
    "publication": PublicationStyle,
    "presentation": PresentationStyle,
}

def get_style(style_name: str):
    """获取样式实例"""
    style_class = STYLE_REGISTRY.get(style_name, ScientificStyle)
    return style_class()

__all__ = ["STYLE_REGISTRY", "get_style"]
