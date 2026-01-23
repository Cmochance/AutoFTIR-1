# -*- coding: utf-8 -*-
"""
成像类数据处理模板

包括: SEM, TEM, AFM, Fluorescence
"""
from typing import Any, Dict

import pandas as pd

from .base import BaseTemplate
from ..schemas import ProcessedData, DataType


class SEMTemplate(BaseTemplate):
    """SEM 数据处理模板"""
    name = "imaging.sem"
    data_type = DataType.SEM
    
    def process(self, df: pd.DataFrame, params: Dict[str, Any]) -> ProcessedData:
        x_col = params.get("x_column", "0")
        y_col = params.get("y_column", "1")
        x, y = self._extract_columns(df, x_col, y_col)
        
        return ProcessedData(
            data_type=self.data_type,
            source_name="",
            df=df,
            x=x,
            y=y,
            x_label="Position",
            y_label="Intensity",
            statistics=self._calculate_statistics(y),
        )


class TEMTemplate(BaseTemplate):
    """TEM 数据处理模板"""
    name = "imaging.tem"
    data_type = DataType.TEM
    
    def process(self, df: pd.DataFrame, params: Dict[str, Any]) -> ProcessedData:
        x_col = params.get("x_column", "0")
        y_col = params.get("y_column", "1")
        x, y = self._extract_columns(df, x_col, y_col)
        
        return ProcessedData(
            data_type=self.data_type,
            source_name="",
            df=df,
            x=x,
            y=y,
            x_label="Position",
            y_label="Intensity",
            statistics=self._calculate_statistics(y),
        )


class AFMTemplate(BaseTemplate):
    """AFM 数据处理模板"""
    name = "imaging.afm"
    data_type = DataType.AFM
    
    def process(self, df: pd.DataFrame, params: Dict[str, Any]) -> ProcessedData:
        x_col = params.get("x_column", "0")
        y_col = params.get("y_column", "1")
        x, y = self._extract_columns(df, x_col, y_col)
        
        return ProcessedData(
            data_type=self.data_type,
            source_name="",
            df=df,
            x=x,
            y=y,
            x_label="X",
            y_label="Height",
            x_unit="μm",
            y_unit="nm",
            statistics=self._calculate_statistics(y),
        )


class FluorescenceTemplate(BaseTemplate):
    """荧光显微镜数据处理模板"""
    name = "imaging.fluorescence"
    data_type = DataType.FLUORESCENCE
    
    def process(self, df: pd.DataFrame, params: Dict[str, Any]) -> ProcessedData:
        x_col = params.get("x_column", "0")
        y_col = params.get("y_column", "1")
        x, y = self._extract_columns(df, x_col, y_col)
        
        return ProcessedData(
            data_type=self.data_type,
            source_name="",
            df=df,
            x=x,
            y=y,
            x_label="Wavelength",
            y_label="Fluorescence Intensity",
            x_unit="nm",
            y_unit="a.u.",
            statistics=self._calculate_statistics(y),
        )
