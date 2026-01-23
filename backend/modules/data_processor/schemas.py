# -*- coding: utf-8 -*-
"""
数据处理模块 Schema 定义
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

import pandas as pd
from pydantic import BaseModel, Field


class DataCategory(str, Enum):
    """数据大类"""
    SPECTROSCOPY = "spectroscopy"
    IMAGING = "imaging"
    CHROMATOGRAPHY = "chromatography"
    GENERAL = "general"


class DataType(str, Enum):
    """数据类型"""
    # 光谱类
    FTIR = "spectroscopy.ftir"
    RAMAN = "spectroscopy.raman"
    UVVIS = "spectroscopy.uvvis"
    XRD = "spectroscopy.xrd"
    NMR = "spectroscopy.nmr"
    
    # 成像类
    SEM = "imaging.sem"
    TEM = "imaging.tem"
    AFM = "imaging.afm"
    FLUORESCENCE = "imaging.fluorescence"
    
    # 色谱类
    GC = "chromatography.gc"
    HPLC = "chromatography.hplc"
    MS = "chromatography.ms"
    
    # 通用类
    CSV = "general.csv"
    TIMESERIES = "general.timeseries"
    STATISTICS = "general.statistics"


class RecognitionResult(BaseModel):
    """数据识别结果"""
    data_type: DataType
    template_name: str
    confidence: float = Field(ge=0, le=1)
    params: Dict[str, Any] = Field(default_factory=dict)
    reasoning: str = ""


@dataclass
class ProcessedData:
    """处理后的标准化数据"""
    # 基本信息
    data_type: DataType
    source_name: str
    
    # 数据内容
    df: pd.DataFrame
    x: pd.Series
    y: pd.Series
    
    # 额外信息
    x_label: str = "X"
    y_label: str = "Y"
    x_unit: str = ""
    y_unit: str = ""
    
    # 处理信息
    template_used: str = ""
    params_used: Dict[str, Any] = field(default_factory=dict)
    
    # 统计信息
    statistics: Dict[str, float] = field(default_factory=dict)
    
    # 峰信息（如果适用）
    peaks: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "data_type": self.data_type.value,
            "source_name": self.source_name,
            "x_label": self.x_label,
            "y_label": self.y_label,
            "x_unit": self.x_unit,
            "y_unit": self.y_unit,
            "template_used": self.template_used,
            "params_used": self.params_used,
            "statistics": self.statistics,
            "peaks": self.peaks,
            "data_shape": list(self.df.shape),
        }
