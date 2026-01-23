# -*- coding: utf-8 -*-
"""
模板基类
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List

import pandas as pd
from pydantic import BaseModel

from ..schemas import ProcessedData, DataType


class BaseTemplate(ABC):
    """处理模板基类"""
    
    # 子类需要定义
    name: str = "base"
    data_type: DataType = DataType.CSV
    
    @abstractmethod
    def process(self, df: pd.DataFrame, params: Dict[str, Any]) -> ProcessedData:
        """
        处理数据
        
        Args:
            df: 原始数据
            params: 处理参数
            
        Returns:
            ProcessedData: 处理后的数据
        """
        pass
    
    def _calculate_statistics(self, y: pd.Series) -> Dict[str, float]:
        """计算基本统计量"""
        return {
            "min": float(y.min()),
            "max": float(y.max()),
            "mean": float(y.mean()),
            "std": float(y.std()),
            "median": float(y.median()),
        }
    
    def _extract_columns(
        self,
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
    ) -> tuple[pd.Series, pd.Series]:
        """提取 X、Y 列"""
        # 支持列名或索引
        if x_col in df.columns:
            x = df[x_col]
        elif x_col.isdigit():
            x = df.iloc[:, int(x_col)]
        else:
            x = df.iloc[:, 0]
        
        if y_col in df.columns:
            y = df[y_col]
        elif y_col.isdigit():
            y = df.iloc[:, int(y_col)]
        else:
            y = df.iloc[:, 1] if len(df.columns) > 1 else df.iloc[:, 0]
        
        return pd.to_numeric(x, errors="coerce"), pd.to_numeric(y, errors="coerce")
