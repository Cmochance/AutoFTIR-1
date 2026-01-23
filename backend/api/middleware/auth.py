# -*- coding: utf-8 -*-
"""
认证中间件
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.auth import verify_token


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件"""
    
    # 不需要认证的路径
    PUBLIC_PATHS = {
        "/api/health",
        "/api/auth/login",
        "/api/auth/register",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
    
    async def dispatch(self, request: Request, call_next):
        # 跳过公开路径
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        
        # 跳过 OPTIONS 请求（CORS 预检）
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # 验证 token（暂时禁用强制验证）
        # auth_header = request.headers.get("Authorization")
        # if not auth_header or not auth_header.startswith("Bearer "):
        #     return JSONResponse(
        #         status_code=401,
        #         content={"error": {"code": "AUTH_ERROR", "message": "缺少认证令牌"}}
        #     )
        # 
        # token = auth_header[7:]
        # if not verify_token(token):
        #     return JSONResponse(
        #         status_code=401,
        #         content={"error": {"code": "AUTH_ERROR", "message": "无效的令牌"}}
        #     )
        
        return await call_next(request)
