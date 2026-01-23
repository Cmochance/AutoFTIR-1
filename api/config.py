# -*- coding: utf-8 -*-
"""
统一配置管理

从环境变量或 .env 文件加载配置。
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional


def _try_load_dotenv() -> None:
    """尝试加载 .env 文件"""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    try:
        from dotenv import dotenv_values, load_dotenv
        load_dotenv(dotenv_path=env_path, override=False)
        
        values = dotenv_values(env_path)
        for raw_key, value in values.items():
            if not raw_key or value is None:
                continue
            key = str(raw_key).strip().lstrip("\ufeff")
            if not key:
                continue
            current = os.environ.get(key)
            if current is None or not current.strip():
                os.environ[key] = str(value).strip()
    except Exception:
        return


_try_load_dotenv()


class Settings:
    """应用配置"""
    
    # 环境配置
    app_env: str = os.environ.get("APP_ENV", "development")
    debug: bool = os.environ.get("DEBUG", "true").lower() in ("1", "true", "yes")
    
    # 服务配置
    host: str = os.environ.get("HOST", "0.0.0.0")
    port: int = int(os.environ.get("PORT", "9000"))
    
    # AI 配置（智谱）
    zhipuai_api_key: str = os.environ.get("ZHIPUAI_API_KEY", "")
    zhipuai_base_url: str = os.environ.get("ZHIPUAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4").rstrip("/")
    
    # AI 配置（OpenAI 兼容）
    ai_provider: str = os.environ.get("AI_PROVIDER", "zhipuai_sdk").lower()
    ai_api_key: str = os.environ.get("AI_API_KEY", "")
    ai_base_url: str = os.environ.get("AI_BASE_URL", "").rstrip("/")
    
    # VLM 配置（图表提取）
    vlm_provider: str = os.environ.get("VLM_PROVIDER", "openai")
    vlm_model: str = os.environ.get("VLM_MODEL", "gpt-4o")
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "")
    
    # 图像处理配置
    max_image_dimension: int = int(os.environ.get("MAX_IMAGE_DIMENSION", "2048"))
    output_format: str = os.environ.get("OUTPUT_FORMAT", "WEBP")
    
    @property
    def effective_ai_api_key(self) -> str:
        """获取有效的 AI API Key"""
        return self.ai_api_key or self.zhipuai_api_key
    
    @property
    def effective_ai_base_url(self) -> str:
        """获取有效的 AI Base URL"""
        return self.ai_base_url or self.zhipuai_base_url
    
    @property
    def effective_vlm_api_key(self) -> str:
        """获取有效的 VLM API Key"""
        if self.vlm_provider == "openai":
            return self.openai_api_key
        elif self.vlm_provider == "anthropic":
            return self.anthropic_api_key
        elif self.vlm_provider == "gemini":
            return self.gemini_api_key
        return self.openai_api_key


@lru_cache
def get_settings() -> Settings:
    """获取缓存的配置实例"""
    return Settings()


# 默认模型列表
DEFAULT_MODELS_ZHIPUAI: List[str] = [
    "glm-4-plus",
    "glm-4-air-250414",
    "glm-4-airx",
    "glm-4-long",
    "glm-4-flashx",
    "glm-4-flash-250414",
    "glm-4v-plus-0111",
    "glm-4v",
    "glm-4v-flash",
]

DEFAULT_MODELS_OPENAI: List[str] = [
    "gemini-3-flash",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gpt-4o",
    "gpt-4o-mini",
]
