# -*- coding: utf-8 -*-
"""
模块1: 数据识别与处理

职责: 接收原始数据 → AI 识别类型 → 选择处理模板 → 输出标准化数据
"""
from .recognizer import DataRecognizer
from .executor import TemplateExecutor
from .schemas import ProcessedData, DataType

__all__ = ["DataRecognizer", "TemplateExecutor", "ProcessedData", "DataType"]

# 便捷入口
class DataProcessor:
    """数据处理器门面类"""
    
    def __init__(self):
        self.recognizer = DataRecognizer()
        self.executor = TemplateExecutor()
    
    async def process(self, file_bytes: bytes, filename: str) -> ProcessedData:
        """
        处理原始数据文件
        
        Args:
            file_bytes: 文件字节
            filename: 文件名
            
        Returns:
            ProcessedData: 处理后的标准化数据
        """
        # 1. AI 识别数据类型和推荐模板
        recognition = await self.recognizer.recognize(file_bytes, filename)
        
        # 2. 执行处理模板
        result = await self.executor.execute(
            file_bytes=file_bytes,
            data_type=recognition.data_type,
            template_name=recognition.template_name,
            params=recognition.params,
        )
        
        return result
