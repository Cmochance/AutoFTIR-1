"""全局共享类型定义"""
from typing import TypeAlias

# 基础类型别名
ImageBytes: TypeAlias = bytes
JSONDict: TypeAlias = dict[str, any]

# 处理状态
class ProcessingStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
