# -*- coding: utf-8 -*-
"""
配置管理

使用 pydantic-settings 管理环境变量和配置
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用
    app_name: str = "SciData"
    app_env: str = "development"
    debug: bool = True
    
    # 服务器
    host: str = "0.0.0.0"
    port: int = 9000
    
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: Optional[str] = None
    
    # Google AI
    google_api_key: str = ""
    google_model: str = "gemini-2.0-flash"
    
    # 知识库
    embedding_model: str = "models/text-embedding-004"
    embedding_dimension: int = 768
    
    # CORS
    cors_origins: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
