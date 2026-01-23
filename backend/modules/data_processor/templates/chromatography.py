# -*- coding: utf-8 -*-
"""
色谱类数据处理模板

包括: GC, HPLC, MS
"""
from typing import Any, Dict

import pandas as pd

from .base import BaseTemplate
from ..schemas import ProcessedData, DataType


class GCTemplate(BaseTemplate):
    """气相色谱处理模板"""
    name = "chromatography.gc"
    data_type = DataType.GC
    
    def process(self, df: pd.DataFrame, params: Dict[str, Any]) -> ProcessedData:
        x_col = params.get("x_column", "0")
        y_col = params.get("y_column", "1")
        x, y = self._extract_columns(df, x_col, y_col)
        
        mask = ~(x.isna() | y.isna())
        x, y = x[mask], y[mask]
        
        return ProcessedData(
            data_type=self.data_type,
            source_name="",
            df=pd.DataFrame({"time": x, "signal": y}),
            x=x,
            y=y,
            x_label="Retention Time",
            y_label="Signal",
            x_unit="min",
            y_unit="a.u.",
            statistics=self._calculate_statistics(y),
        )


class HPLCTemplate(BaseTemplate):
    """高效液相色谱处理模板"""
    name = "chromatography.hplc"
    data_type = DataType.HPLC
    
    def process(self, df: pd.DataFrame, params: Dict[str, Any]) -> ProcessedData:
        x_col = params.get("x_column", "0")
        y_col = params.get("y_column", "1")
        x, y = self._extract_columns(df, x_col, y_col)
        
        mask = ~(x.isna() | y.isna())
        x, y = x[mask], y[mask]
        
        return ProcessedData(
            data_type=self.data_type,
            source_name="",
            df=pd.DataFrame({"time": x, "absorbance": y}),
            x=x,
            y=y,
            x_label="Retention Time",
            y_label="Absorbance",
            x_unit="min",
            y_unit="mAU",
            statistics=self._calculate_statistics(y),
        )


class MSTemplate(BaseTemplate):
    """质谱处理模板"""
    name = "chromatography.ms"
    data_type = DataType.MS
    
    def process(self, df: pd.DataFrame, params: Dict[str, Any]) -> ProcessedData:
        x_col = params.get("x_column", "0")
        y_col = params.get("y_column", "1")
        x, y = self._extract_columns(df, x_col, y_col)
        
        mask = ~(x.isna() | y.isna())
        x, y = x[mask], y[mask]
        
        return ProcessedData(
            data_type=self.data_type,
            source_name="",
            df=pd.DataFrame({"mz": x, "intensity": y}),
            x=x,
            y=y,
            x_label="m/z",
            y_label="Relative Intensity",
            x_unit="",
            y_unit="%",
            statistics=self._calculate_statistics(y),
        )
