# -*- coding: utf-8 -*-
"""
预定义处理模板

安全设计: AI 只能选择预定义模板和调整参数，不能执行任意代码
"""
from .base import BaseTemplate
from .spectroscopy import FTIRTemplate, RamanTemplate, UVVisTemplate, XRDTemplate, NMRTemplate
from .imaging import SEMTemplate, TEMTemplate, AFMTemplate, FluorescenceTemplate
from .chromatography import GCTemplate, HPLCTemplate, MSTemplate
from .general import CSVTemplate, TimeSeriesTemplate, StatisticsTemplate

# 模板注册表
TEMPLATE_REGISTRY = {
    # 光谱类
    "spectroscopy.ftir": FTIRTemplate,
    "spectroscopy.raman": RamanTemplate,
    "spectroscopy.uvvis": UVVisTemplate,
    "spectroscopy.xrd": XRDTemplate,
    "spectroscopy.nmr": NMRTemplate,
    # 成像类
    "imaging.sem": SEMTemplate,
    "imaging.tem": TEMTemplate,
    "imaging.afm": AFMTemplate,
    "imaging.fluorescence": FluorescenceTemplate,
    # 色谱类
    "chromatography.gc": GCTemplate,
    "chromatography.hplc": HPLCTemplate,
    "chromatography.ms": MSTemplate,
    # 通用类
    "general.csv": CSVTemplate,
    "general.timeseries": TimeSeriesTemplate,
    "general.statistics": StatisticsTemplate,
}

def get_template(template_name: str) -> BaseTemplate:
    """获取模板实例"""
    template_class = TEMPLATE_REGISTRY.get(template_name)
    if template_class is None:
        raise ValueError(f"Unknown template: {template_name}")
    return template_class()

__all__ = [
    "BaseTemplate",
    "TEMPLATE_REGISTRY",
    "get_template",
]
