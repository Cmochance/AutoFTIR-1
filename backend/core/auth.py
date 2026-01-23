# -*- coding: utf-8 -*-
"""
认证模块

基于 Supabase Auth
"""
from typing import Optional
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Header

from .database import Database
from .exceptions import AuthenticationError


@dataclass
class User:
    """用户信息"""
    id: str
    email: str
    metadata: dict


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> User:
    """
    从请求头获取当前用户
    
    Args:
        authorization: Bearer token
        
    Returns:
        User: 当前用户
        
    Raises:
        AuthenticationError: 认证失败
    """
    if not authorization:
        raise AuthenticationError("缺少认证令牌")
    
    if not authorization.startswith("Bearer "):
        raise AuthenticationError("无效的认证格式")
    
    token = authorization[7:]
    
    try:
        client = Database.get_client()
        response = client.auth.get_user(token)
        
        if response.user is None:
            raise AuthenticationError("无效的令牌")
        
        return User(
            id=response.user.id,
            email=response.user.email or "",
            metadata=response.user.user_metadata or {},
        )
    except Exception as e:
        raise AuthenticationError(f"认证失败: {str(e)}")


def verify_token(token: str) -> bool:
    """
    验证令牌有效性
    
    Args:
        token: JWT 令牌
        
    Returns:
        bool: 是否有效
    """
    try:
        client = Database.get_client()
        response = client.auth.get_user(token)
        return response.user is not None
    except Exception:
        return False
