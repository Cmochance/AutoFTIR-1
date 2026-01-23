# -*- coding: utf-8 -*-
"""
数据库连接

使用 Supabase 作为数据库后端
"""
from typing import Optional
from functools import lru_cache

from supabase import create_client, Client

from .config import settings


class Database:
    """数据库连接管理"""
    
    _client: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """获取 Supabase 客户端"""
        if cls._client is None:
            cls._client = create_client(
                settings.supabase_url,
                settings.supabase_key,
            )
        return cls._client
    
    @classmethod
    def get_service_client(cls) -> Client:
        """获取服务端 Supabase 客户端（绕过 RLS）"""
        if settings.supabase_service_key:
            return create_client(
                settings.supabase_url,
                settings.supabase_service_key,
            )
        return cls.get_client()


@lru_cache()
def get_db() -> Database:
    """获取数据库实例"""
    return Database()
