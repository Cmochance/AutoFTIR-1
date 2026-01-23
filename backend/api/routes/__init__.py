# -*- coding: utf-8 -*-
"""
路由定义
"""
from .analyze import router as analyze_router
from .auth import router as auth_router
from .history import router as history_router

__all__ = ["analyze_router", "auth_router", "history_router"]
