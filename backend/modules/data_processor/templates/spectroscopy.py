# -*- coding: utf-8 -*-
"""
光谱类数据处理模板

包括: FTIR, Raman, UV-Vis, XRD, NMR
"""
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from .base import BaseTemplate
from ..schemas import ProcessedData, DataType


class SpectroscopyParams(BaseModel):
    """光谱处理参数"""
    x_column: str = "0"
    y_column: str = "1"
    baseline_correction: bool = True
    smoothing_window: int = Field(ge=1, le=50, default=5)
    normalize: bool = False
    peak_detection: bool = True
    peak_threshold: float = Field(ge=0, le=1, default=0.1)


def _smooth(y: np.ndarray, window: int) -> np.ndarray:
    """简单移动平均平滑"""
    if window <= 1:
        return y
    w = int(window)
    if w % 2 == 0:
        w += 1
    if y.size < w:
        return y
    kernel = np.ones(w, dtype=float) / float(w)
    return np.convolve(y, kernel, mode="same")


def _baseline_correction(y: np.ndarray) -> np.ndarray:
    """简单基线校正（线性）"""
    x = np.arange(len(y))
    # 使用首尾点拟合直线
    slope = (y[-1] - y[0]) / (len(y) - 1)
    baseline = y[0] + slope * x
    return y - baseline


def _detect_peaks(x: np.ndarray, y: np.ndarray, threshold: float) -> List[Dict[str, Any]]:
    """峰检测"""
    peaks = []
    y_smooth = _smooth(y, 5)
    y_range = y_smooth.max() - y_smooth.min()
    min_prominence = y_range * threshold
    
    for i in range(1, len(y_smooth) - 1):
        if y_smooth[i] > y_smooth[i-1] and y_smooth[i] > y_smooth[i+1]:
            # 局部最大值
            prominence = y_smooth[i] - min(y_smooth[max(0, i-10):i].min(), 
                                            y_smooth[i+1:min(len(y_smooth), i+11)].min())
            if prominence >= min_prominence:
                peaks.append({
                    "position": float(x[i]),
                    "intensity": float(y[i]),
                    "prominence": float(prominence),
                })
    
    # 按强度排序，取前10个
    peaks.sort(key=lambda p: p["intensity"], reverse=True)
    return peaks[:10]


class FTIRTemplate(BaseTemplate):
    """FTIR 光谱处理模板"""
    
    name = "spectroscopy.ftir"
    data_type = DataType.FTIR
    
    def process(self, df: pd.DataFrame, params: Dict[str, Any]) -> ProcessedData:
        p = SpectroscopyParams(**params)
        
        # 提取数据
        x, y = self._extract_columns(df, p.x_column, p.y_column)
        
        # 清理无效值
        mask = ~(x.isna() | y.isna())
        x, y = x[mask].values, y[mask].values
        
        # 处理
        if p.smoothing_window > 1:
            y = _smooth(y, p.smoothing_window)
        
        if p.baseline_correction:
            y = _baseline_correction(y)
        
        if p.normalize:
            y = (y - y.min()) / (y.max() - y.min())
        
        # 峰检测
        peaks = []
        if p.peak_detection:
            peaks = _detect_peaks(x, y, p.peak_threshold)
        
        # 构建结果
        result_df = pd.DataFrame({"wavenumber": x, "intensity": y})
        
        return ProcessedData(
            data_type=self.data_type,
            source_name="",
            df=result_df,
            x=pd.Series(x),
            y=pd.Series(y),
            x_label="Wavenumber",
            y_label="Transmittance" if y.mean() > 50 else "Absorbance",
            x_unit="cm⁻¹",
            y_unit="%" if y.mean() > 50 else "a.u.",
            statistics=self._calculate_statistics(pd.Series(y)),
            peaks=peaks,
        )


class RamanTemplate(BaseTemplate):
    """Raman 光谱处理模板"""
    
    name = "spectroscopy.raman"
    data_type = DataType.RAMAN
    
    def process(self, df: pd.DataFrame, params: Dict[str, Any]) -> ProcessedData:
        p = SpectroscopyParams(**params)
        x, y = self._extract_columns(df, p.x_column, p.y_column)
        
        mask = ~(x.isna() | y.isna())
        x, y = x[mask].values, y[mask].values
        
        if p.smoothing_window > 1:
            y = _smooth(y, p.smoothing_window)
        
        if p.baseline_correction:
            y = _baseline_correction(y)
        
        peaks = _detect_peaks(x, y, p.peak_threshold) if p.peak_detection else []
        
        result_df = pd.DataFrame({"raman_shift": x, "intensity": y})
        
        return ProcessedData(
            data_type=self.data_type,
            source_name="",
            df=result_df,
            x=pd.Series(x),
            y=pd.Series(y),
            x_label="Raman Shift",
            y_label="Intensity",
            x_unit="cm⁻¹",
            y_unit="a.u.",
            statistics=self._calculate_statistics(pd.Series(y)),
            peaks=peaks,
        )


class UVVisTemplate(BaseTemplate):
    """UV-Vis 光谱处理模板"""
    
    name = "spectroscopy.uvvis"
    data_type = DataType.UVVIS
    
    def process(self, df: pd.DataFrame, params: Dict[str, Any]) -> ProcessedData:
        p = SpectroscopyParams(**params)
        x, y = self._extract_columns(df, p.x_column, p.y_column)
        
        mask = ~(x.isna() | y.isna())
        x, y = x[mask].values, y[mask].values
        
        if p.smoothing_window > 1:
            y = _smooth(y, p.smoothing_window)
        
        peaks = _detect_peaks(x, y, p.peak_threshold) if p.peak_detection else []
        
        result_df = pd.DataFrame({"wavelength": x, "absorbance": y})
        
        return ProcessedData(
            data_type=self.data_type,
            source_name="",
            df=result_df,
            x=pd.Series(x),
            y=pd.Series(y),
            x_label="Wavelength",
            y_label="Absorbance",
            x_unit="nm",
            y_unit="a.u.",
            statistics=self._calculate_statistics(pd.Series(y)),
            peaks=peaks,
        )


class XRDTemplate(BaseTemplate):
    """XRD 衍射处理模板"""
    
    name = "spectroscopy.xrd"
    data_type = DataType.XRD
    
    def process(self, df: pd.DataFrame, params: Dict[str, Any]) -> ProcessedData:
        p = SpectroscopyParams(**params)
        x, y = self._extract_columns(df, p.x_column, p.y_column)
        
        mask = ~(x.isna() | y.isna())
        x, y = x[mask].values, y[mask].values
        
        if p.smoothing_window > 1:
            y = _smooth(y, p.smoothing_window)
        
        if p.baseline_correction:
            y = _baseline_correction(y)
        
        peaks = _detect_peaks(x, y, p.peak_threshold) if p.peak_detection else []
        
        result_df = pd.DataFrame({"2theta": x, "intensity": y})
        
        return ProcessedData(
            data_type=self.data_type,
            source_name="",
            df=result_df,
            x=pd.Series(x),
            y=pd.Series(y),
            x_label="2θ",
            y_label="Intensity",
            x_unit="°",
            y_unit="counts",
            statistics=self._calculate_statistics(pd.Series(y)),
            peaks=peaks,
        )


class NMRTemplate(BaseTemplate):
    """NMR 光谱处理模板"""
    
    name = "spectroscopy.nmr"
    data_type = DataType.NMR
    
    def process(self, df: pd.DataFrame, params: Dict[str, Any]) -> ProcessedData:
        p = SpectroscopyParams(**params)
        x, y = self._extract_columns(df, p.x_column, p.y_column)
        
        mask = ~(x.isna() | y.isna())
        x, y = x[mask].values, y[mask].values
        
        if p.smoothing_window > 1:
            y = _smooth(y, p.smoothing_window)
        
        peaks = _detect_peaks(x, y, p.peak_threshold) if p.peak_detection else []
        
        result_df = pd.DataFrame({"chemical_shift": x, "intensity": y})
        
        return ProcessedData(
            data_type=self.data_type,
            source_name="",
            df=result_df,
            x=pd.Series(x),
            y=pd.Series(y),
            x_label="Chemical Shift",
            y_label="Intensity",
            x_unit="ppm",
            y_unit="a.u.",
            statistics=self._calculate_statistics(pd.Series(y)),
            peaks=peaks,
        )
