# -*- coding: utf-8 -*-
"""
认证路由
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from backend.core.auth import get_current_user, User
from backend.core.database import Database

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
async def login(request: LoginRequest):
    """用户登录"""
    client = Database.get_client()
    
    response = client.auth.sign_in_with_password({
        "email": request.email,
        "password": request.password,
    })
    
    return {
        "user": {
            "id": response.user.id,
            "email": response.user.email,
        },
        "token": response.session.access_token,
    }


@router.post("/register")
async def register(request: RegisterRequest):
    """用户注册"""
    client = Database.get_client()
    
    response = client.auth.sign_up({
        "email": request.email,
        "password": request.password,
    })
    
    return {
        "user": {
            "id": response.user.id,
            "email": response.user.email,
        },
        "message": "注册成功，请检查邮箱验证",
    }


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "id": user.id,
        "email": user.email,
        "metadata": user.metadata,
    }


@router.post("/logout")
async def logout():
    """退出登录"""
    # 客户端清除 token 即可
    return {"message": "已退出登录"}
