"""配置管理模块 - 2026年标准配置"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 环境配置
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # VLM 配置
    vlm_provider: str = "openai"  # openai | anthropic | gemini
    vlm_model: str = "gpt-5o"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 图像处理配置
    max_image_dimension: int = 2048
    output_format: str = "WEBP"
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """获取缓存的配置实例"""
    return Settings()
