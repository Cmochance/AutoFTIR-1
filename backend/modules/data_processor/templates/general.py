# -*- coding: utf-8 -*-
"""
通用数据处理模板

包括: CSV, TimeSeries, Statistics
"""
from typing import Any, Dict

import pandas as pd

from .base import BaseTemplate
from ..schemas import ProcessedData, DataType


class CSVTemplate(BaseTemplate):
    """通用 CSV 处理模板"""
    name = "general.csv"
    data_type = DataType.CSV
    
    def process(self, df: pd.DataFrame, params: Dict[str, Any]) -> ProcessedData:
        x_col = params.get("x_column", "0")
        y_col = params.get("y_column", "1")
        x, y = self._extract_columns(df, x_col, y_col)
        
        mask = ~(x.isna() | y.isna())
        x, y = x[mask], y[mask]
        
        # 推断标签
        x_label = x_col if x_col in df.columns else "X"
        y_label = y_col if y_col in df.columns else "Y"
        
        return ProcessedData(
            data_type=self.data_type,
            source_name="",
            df=df,
            x=x,
            y=y,
            x_label=x_label,
            y_label=y_label,
            statistics=self._calculate_statistics(y),
        )


class TimeSeriesTemplate(BaseTemplate):
    """时间序列处理模板"""
    name = "general.timeseries"
    data_type = DataType.TIMESERIES
    
    def process(self, df: pd.DataFrame, params: Dict[str, Any]) -> ProcessedData:
        x_col = params.get("x_column", "0")
        y_col = params.get("y_column", "1")
        x, y = self._extract_columns(df, x_col, y_col)
        
        # 尝试解析时间
        try:
            x = pd.to_datetime(x)
        except:
            pass
        
        mask = ~y.isna()
        x, y = x[mask], y[mask]
        
        return ProcessedData(
            data_type=self.data_type,
            source_name="",
            df=pd.DataFrame({"time": x, "value": y}),
            x=x,
            y=y,
            x_label="Time",
            y_label="Value",
            statistics=self._calculate_statistics(y),
        )


class StatisticsTemplate(BaseTemplate):
    """统计数据处理模板"""
    name = "general.statistics"
    data_type = DataType.STATISTICS
    
    def process(self, df: pd.DataFrame, params: Dict[str, Any]) -> ProcessedData:
        x_col = params.get("x_column", "0")
        y_col = params.get("y_column", "1")
        x, y = self._extract_columns(df, x_col, y_col)
        
        mask = ~(x.isna() | y.isna())
        x, y = x[mask], y[mask]
        
        return ProcessedData(
            data_type=self.data_type,
            source_name="",
            df=df,
            x=x,
            y=y,
            x_label="Category",
            y_label="Value",
            statistics=self._calculate_statistics(y),
        )
