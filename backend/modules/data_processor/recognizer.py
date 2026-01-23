# -*- coding: utf-8 -*-
"""
AI 数据类型识别器

使用 Gemini 识别上传数据的类型并推荐处理模板
"""
import io
import json
from typing import Optional

import pandas as pd
import google.generativeai as genai

from backend.core.config import settings
from .schemas import DataType, RecognitionResult


# 配置 Gemini
genai.configure(api_key=settings.google_api_key)


RECOGNITION_PROMPT = """你是一个专业的科研数据分析专家。请分析以下数据文件，识别其数据类型。

## 文件信息
- 文件名: {filename}
- 文件大小: {file_size} bytes
- 列数: {num_columns}
- 行数: {num_rows}

## 数据预览（前10行）
```
{data_preview}
```

## 列名和数据类型
{column_info}

## 可选的数据类型
- spectroscopy.ftir: 傅里叶变换红外光谱（波数 vs 透射率/吸光度）
- spectroscopy.raman: 拉曼光谱（波数 vs 强度）
- spectroscopy.uvvis: 紫外可见光谱（波长 vs 吸光度）
- spectroscopy.xrd: X射线衍射（2θ vs 强度）
- spectroscopy.nmr: 核磁共振（化学位移 vs 强度）
- imaging.sem: 扫描电镜数据
- imaging.tem: 透射电镜数据
- imaging.afm: 原子力显微镜数据
- chromatography.gc: 气相色谱（时间 vs 信号）
- chromatography.hplc: 高效液相色谱（时间 vs 信号）
- chromatography.ms: 质谱数据
- general.csv: 通用CSV数据
- general.timeseries: 时间序列数据
- general.statistics: 统计数据

## 输出格式
请以JSON格式返回，包含以下字段：
{{
    "data_type": "选择的数据类型",
    "template_name": "对应的模板名称（与data_type相同）",
    "confidence": 0.0-1.0的置信度,
    "params": {{
        "x_column": "X轴列名",
        "y_column": "Y轴列名",
        "其他相关参数": "..."
    }},
    "reasoning": "简短的判断理由"
}}

只输出JSON，不要有其他文字。
"""


class DataRecognizer:
    """数据类型识别器"""
    
    def __init__(self):
        self.model = genai.GenerativeModel(settings.google_model)
    
    async def recognize(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> RecognitionResult:
        """
        识别数据类型
        
        Args:
            file_bytes: 文件字节内容
            filename: 文件名
            
        Returns:
            RecognitionResult: 识别结果
        """
        # 读取数据预览
        df = self._read_file(file_bytes, filename)
        
        # 构建提示词
        prompt = RECOGNITION_PROMPT.format(
            filename=filename,
            file_size=len(file_bytes),
            num_columns=len(df.columns),
            num_rows=len(df),
            data_preview=df.head(10).to_string(),
            column_info=self._get_column_info(df),
        )
        
        # 调用 Gemini
        response = self.model.generate_content(prompt)
        
        # 解析响应
        try:
            result_text = response.text.strip()
            # 移除可能的 markdown 代码块标记
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1]
                result_text = result_text.rsplit("```", 1)[0]
            
            result_dict = json.loads(result_text)
            
            return RecognitionResult(
                data_type=DataType(result_dict["data_type"]),
                template_name=result_dict["template_name"],
                confidence=float(result_dict.get("confidence", 0.8)),
                params=result_dict.get("params", {}),
                reasoning=result_dict.get("reasoning", ""),
            )
        except Exception as e:
            # 回退到通用CSV类型
            return RecognitionResult(
                data_type=DataType.CSV,
                template_name="general.csv",
                confidence=0.5,
                params={"x_column": df.columns[0], "y_column": df.columns[1] if len(df.columns) > 1 else df.columns[0]},
                reasoning=f"AI识别失败，使用默认类型: {str(e)}",
            )
    
    def _read_file(self, file_bytes: bytes, filename: str) -> pd.DataFrame:
        """读取文件为DataFrame"""
        suffix = filename.lower().split(".")[-1]
        
        try:
            if suffix == "csv":
                return pd.read_csv(io.BytesIO(file_bytes))
            elif suffix == "txt":
                # 尝试不同分隔符
                for sep in ["\t", " ", ","]:
                    try:
                        df = pd.read_csv(io.BytesIO(file_bytes), sep=sep)
                        if len(df.columns) > 1:
                            return df
                    except:
                        continue
                return pd.read_csv(io.BytesIO(file_bytes), sep=r"\s+", engine="python")
            elif suffix in ["xls", "xlsx"]:
                return pd.read_excel(io.BytesIO(file_bytes))
            else:
                return pd.read_csv(io.BytesIO(file_bytes))
        except Exception as e:
            raise ValueError(f"无法读取文件: {str(e)}")
    
    def _get_column_info(self, df: pd.DataFrame) -> str:
        """获取列信息"""
        info_lines = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            sample = str(df[col].iloc[0]) if len(df) > 0 else "N/A"
            info_lines.append(f"- {col}: {dtype}, 示例值: {sample}")
        return "\n".join(info_lines)
