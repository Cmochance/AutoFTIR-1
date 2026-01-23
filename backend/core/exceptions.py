# -*- coding: utf-8 -*-
"""
统一异常定义
"""
from typing import Any, Optional


class AppException(Exception):
    """应用基础异常"""
    
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class NotFoundError(AppException):
    """资源未找到"""
    
    def __init__(self, message: str = "资源未找到", details: Optional[dict] = None):
        super().__init__(message, "NOT_FOUND", 404, details)


class ValidationError(AppException):
    """数据验证错误"""
    
    def __init__(self, message: str = "数据验证失败", details: Optional[dict] = None):
        super().__init__(message, "VALIDATION_ERROR", 400, details)


class AuthenticationError(AppException):
    """认证错误"""
    
    def __init__(self, message: str = "认证失败", details: Optional[dict] = None):
        super().__init__(message, "AUTH_ERROR", 401, details)


class QuotaExceededError(AppException):
    """配额超限"""
    
    def __init__(self, message: str = "本月分析配额已用完", details: Optional[dict] = None):
        super().__init__(message, "QUOTA_EXCEEDED", 429, details)


class AIServiceError(AppException):
    """AI 服务错误"""
    
    def __init__(self, message: str = "AI 服务调用失败", details: Optional[dict] = None):
        super().__init__(message, "AI_ERROR", 502, details)
