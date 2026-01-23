# -*- coding: utf-8 -*-
"""
模板执行器

安全地执行预定义的数据处理模板
"""
import io
from typing import Any, Dict

import pandas as pd

from .schemas import DataType, ProcessedData
from .templates import get_template


class TemplateExecutor:
    """模板执行器"""
    
    async def execute(
        self,
        file_bytes: bytes,
        data_type: DataType,
        template_name: str,
        params: Dict[str, Any],
    ) -> ProcessedData:
        """
        执行处理模板
        
        Args:
            file_bytes: 文件字节
            data_type: 数据类型
            template_name: 模板名称
            params: 处理参数
            
        Returns:
            ProcessedData: 处理后的数据
        """
        # 获取模板
        template = get_template(template_name)
        
        # 读取数据
        df = self._read_data(file_bytes, params)
        
        # 执行处理
        result = template.process(df, params)
        
        # 设置数据类型
        result.data_type = data_type
        result.template_used = template_name
        result.params_used = params
        
        return result
    
    def _read_data(self, file_bytes: bytes, params: Dict[str, Any]) -> pd.DataFrame:
        """读取数据"""
        # 根据参数决定如何读取
        encoding = params.get("encoding", "utf-8")
        sep = params.get("separator", ",")
        
        try:
            return pd.read_csv(
                io.BytesIO(file_bytes),
                encoding=encoding,
                sep=sep if sep != "auto" else None,
                engine="python" if sep == "auto" else "c",
            )
        except:
            # 回退策略
            for enc in ["utf-8-sig", "utf-8", "gb18030", "gbk"]:
                try:
                    return pd.read_csv(io.BytesIO(file_bytes), encoding=enc)
                except:
                    continue
            raise ValueError("无法读取文件")
