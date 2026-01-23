# -*- coding: utf-8 -*-
"""
历史记录路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.core.auth import get_current_user, User
from backend.core.database import Database

router = APIRouter()


@router.get("/")
async def list_history(
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取分析历史列表"""
    client = Database.get_client()
    
    offset = (page - 1) * page_size
    
    response = client.table("analyses") \
        .select("*") \
        .eq("user_id", user.id) \
        .order("created_at", desc=True) \
        .range(offset, offset + page_size - 1) \
        .execute()
    
    return {
        "items": response.data,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{analysis_id}")
async def get_history_detail(
    analysis_id: str,
    user: User = Depends(get_current_user),
):
    """获取分析详情"""
    client = Database.get_client()
    
    response = client.table("analyses") \
        .select("*") \
        .eq("id", analysis_id) \
        .eq("user_id", user.id) \
        .single() \
        .execute()
    
    return response.data


@router.delete("/{analysis_id}")
async def delete_history(
    analysis_id: str,
    user: User = Depends(get_current_user),
):
    """删除分析记录"""
    client = Database.get_client()
    
    client.table("analyses") \
        .delete() \
        .eq("id", analysis_id) \
        .eq("user_id", user.id) \
        .execute()
    
    return {"message": "删除成功"}
